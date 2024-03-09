from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
import cv2
import tempfile
import numpy as np
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token
import MySQLdb.cursors
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, TextAreaField, SelectMultipleField, validators
from wtforms import SubmitField
import mysql.connector
from flask import Flask, send_file, abort
import imghdr
import io
import base64
from flask import flash  # Import flash if you haven't already
import logging
from flask import send_from_directory
import re
import os
import json
#logging.basicConfig(filename='app.log', level=logging.INFO)

app = Flask(__name__)
app.secret_key = 'secret_key'
bcrypt = Bcrypt(app)
app.config['JWT_SECRET_KEY'] = '1a2b3c4d5e6d7g8h9i10'  # Change this to your JWT Secret Key
jwt = JWTManager(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'computing@123!'
app.config['MYSQL_DB'] = 'loginapp'

mysql = MySQL(app)

@app.route('/pythonlogin/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', [username])
        account = cursor.fetchone()
        if account and bcrypt.check_password_hash(account['password'], password):
            access_token = create_access_token(identity=username)
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session['jwt_token'] = access_token  # Storing JWT token in session
            return redirect(url_for('home'))
        else:
            flash("Incorrect username/password!", "danger")
    return render_template('auth/login.html', title="Login")

@app.route('/pythonlogin/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM accounts WHERE username LIKE %s", [username])
        account = cursor.fetchone()
        if account:
            flash("Account already exists!", "danger")
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash("Invalid email address!", "danger")
        elif not re.match(r'[A-Za-z0-9]+', username):
             flash("Username must contain only characters and numbers!", "danger")
        elif not username or not password or not email:
            flash("Please fill out the form!", "danger")
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, email, hashed_password))
            mysql.connection.commit()
            flash("You have successfully registered!", "success")
            return redirect(url_for('login'))
    elif request.method == 'POST':
        flash("Please fill out the form!", "danger")
    return render_template('auth/register.html', title="Register")

@app.route('/')
def home():
    if 'loggedin' in session:
        user_id = session['id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM images WHERE user_id = %s', [user_id])
        images = cursor.fetchall()  # Fetches all user's images
        return render_template('home/home.html', username=session['username'], images=images)
    else:
        return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if 'loggedin' in session:
        # Retrieve user account details from the database using the stored session['id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', [session['id']])
        account = cursor.fetchone()  # This fetches the user's account details as a dictionary

        # Check if account details are found
        if account:
            return render_template('auth/profile.html', account=account, title="Profile")
        else:
            # If no account found with the session ID, clear the session and redirect to login
            session.pop('loggedin', None)
            session.pop('id', None)
            session.pop('username', None)
            flash("Unable to find account details.", "danger")
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))


#app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
#os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# App configuration
#UPLOAD_FOLDER = 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads'
UPLOAD_FOLDER = './static/images/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class UploadForm(FlaskForm):
    file = FileField('Image File', validators=[FileRequired()], render_kw={"multiple": True})
    submit = SubmitField('Save Images')

def store_image_in_db(user_id, file_path, file_name, metadata):
    # Open the file in binary mode
    with open(file_path, 'rb') as file:
        binary_data = file.read()  # Read the entire file as binary data

    try:
        cursor = mysql.connection.cursor()
        # Adjusted SQL query to include the binary data
        sql_insert_query = """ INSERT INTO images (user_id, image_name, image_path, image, metadata) VALUES (%s, %s, %s, %s, %s)"""
        cursor.execute(sql_insert_query, (user_id, file_name, file_path, binary_data, metadata))
        mysql.connection.commit()
        print("Image inserted successfully into the images table")
    except Exception as e:
        print(f"Failed to insert image into MySQL table {e}")
    finally:
        cursor.close()


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    form = UploadForm()
    if request.method == 'POST' and form.validate_on_submit():
        user_id = session['id']
        files = request.files.getlist('file')  # Adjusted for correct form field name
        successful_uploads = 0
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{user_id}_{file.filename}")
                user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(user_id))
                if not os.path.exists(user_folder):
                    os.makedirs(user_folder)
                file_path = os.path.join(user_folder, filename)
                file.save(file_path)
                store_image_in_db(user_id, file_path, filename, "{}") 
                successful_uploads += 1
        if successful_uploads:
            flash(f'Successfully uploaded {successful_uploads} images.', 'success')
            return redirect(url_for('upload_file'))  
        else:
            flash('No files were uploaded.', 'danger')
    return render_template('home/upload.html', form=form)

@app.route('/image/<int:image_id>')
def serve_image(image_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor here
    cursor.execute('SELECT image, image_name FROM images WHERE image_id = %s', (image_id,))
    image = cursor.fetchone()
    if image:
        try:
            image_binary = io.BytesIO(image['image'])
            image_format = imghdr.what(None, h=image['image'])
            mimetype = f'image/{image_format}' if image_format else 'application/octet-stream'
            return send_file(image_binary, mimetype=mimetype, as_attachment=False)
        except Exception as e:
            print(f"Error serving image: {e}")
            abort(500)
    else:
        abort(404)

@app.route('/serve_audio/<int:audio_id>')
def serve_audio(audio_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT audio_blob, audio_name FROM audio_library WHERE audio_id = %s', (audio_id,))
    audio = cursor.fetchone()
    if audio:
        try:
            audio_binary = io.BytesIO(audio['audio_blob'])
            mimetype = 'audio/mpeg'  # Assuming all audio files are mp3 format
            return send_file(audio_binary, mimetype=mimetype, as_attachment=False)
        except Exception as e:
            print(f"Error serving audio: {e}")
            abort(500)
    else:
        abort(404)

class VideoCreationForm(FlaskForm):
    videoTitle = StringField('Video Title', [validators.DataRequired()])
    videoDescription = TextAreaField('Video Description')
    imageSelect = SelectMultipleField('Select Images for Video', coerce=int)

@app.route('/create', methods=['GET', 'POST'])
def create():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    form = VideoCreationForm(request.form)
    user_id = session['id']
    output_video_path = None  # Initialize the variable to ensure it's set

    # Initialize cursor outside of the POST block to fetch images and audio files for the user
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT image_id, image_name, image_path FROM images WHERE user_id = %s', (user_id,))
    images = cursor.fetchall()
    cursor.execute('SELECT audio_id, audio_name, audio_path FROM audio_library')
    audio_files = cursor.fetchall()

    # Handle form submission
    if request.method == 'POST' and form.validate():
        video_title = form.videoTitle.data
        video_description = form.videoDescription.data

        # Get the selected images and durations from the form
        selected_images = json.loads(request.form['selected_images'])
        selected_audio_id = request.form['selectedAudio']
        resolution_choice = request.form['resolution']
        quality_choice = request.form['quality']

        # Map resolution and quality selections to actual values
        resolution_map = {'480': (640, 480), '720': (1280, 720), '1080': (1920, 1080), '2160': (3840, 2160)}
        quality_map = {'low': '500k', 'medium': '1000k', 'high': '2000k'}
        resolution = resolution_map.get(resolution_choice, (1280, 720))
        quality = quality_map.get(quality_choice, 'medium')

        try:
            image_clips = []
            for selection in selected_images:
                image_id = selection['id']
                duration = float(selection['duration'])
                # Fetch the image using the existing cursor
                cursor.execute('SELECT image_path FROM images WHERE image_id = %s AND user_id = %s', (image_id, user_id))
                image_record = cursor.fetchone()
                if image_record:
                    #image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_record['image_path'])
                    image_path = os.path.join(image_record['image_path'])
                    image_clip = ImageClip(image_path, duration=duration).resize(newsize=resolution)  # Set the size here
                    image_clips.append(image_clip)

            # Fetch and set the audio
            audio_clip = None
            if selected_audio_id:
                cursor.execute('SELECT audio_path FROM audio_library WHERE audio_id = %s', (selected_audio_id,))
                audio_record = cursor.fetchone()
                if audio_record:
                    audio_file_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_record['audio_path'])
                    audio_clip = AudioFileClip(audio_file_path)

            # Concatenate all image clips
            video_clip = concatenate_videoclips(image_clips, method='compose')

            # Set the audio to the video if audio is selected
            if audio_clip:
                video_clip.audio = audio_clip

            # Define directory for saving the video
            videos_folder = os.path.join(app.static_folder, 'videos')
            if not os.path.exists(videos_folder):
                os.makedirs(videos_folder)

            output_video_path = os.path.join('videos', secure_filename(f'video_{user_id}_{video_title}.mp4'))
            full_output_video_path = os.path.join(app.static_folder, output_video_path)
            
            # Write the video file without the 'size' argument
            video_clip.write_videofile(full_output_video_path, fps=24, codec='libx264', bitrate=quality, audio_codec='aac', preset='medium')
            video_path = f"videos/video_{user_id}_{video_title}.mp4"

            flash('Video created successfully!', 'success')
        except Exception as e:
            flash(f'Error creating video: {e}', 'danger')
            app.logger.error(f'Exception on /create [POST]: {e}', exc_info=True)
            video_path = None 
        finally:
            if cursor and not cursor.connection.closed:
                cursor.close()  # Ensure cursor is closed after the operation

        # Redirect to the same page to show the form and the result
        return render_template('home/create.html', form=form, images=images, audio_files=audio_files, video_path=video_path)
    
    # Close the cursor for the GET request
    cursor.close()
    # If it's a GET request or the form isn't validated, render the template normally
    return render_template('home/create.html', form=form, images=images, audio_files=audio_files, video_path=output_video_path)

@app.route('/download_video/<path:video_filename>')
def download_video(video_filename):
    #flash('Your download will begin shortly.', 'info')
    directory = os.path.join(app.static_folder, 'videos')
    response = send_from_directory(directory=directory, path=video_filename, as_attachment=True)
    response.headers["Content-Disposition"] = f"attachment; filename={video_filename}"
    return response

@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('jwt_token', None)
    # Redirect to login page
    return redirect(url_for('login'))

if __name__ =='__main__':
    app.run(debug=True)
