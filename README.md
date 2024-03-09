Set up a virtual env using the command
py -3 -m venv venv
Activate it
venv\Scripts\activate
Run
python -m pip install -r requirements.txt
Also install other modules not given in requirements.txt. 

Create a database

CREATE DATABASE loginapp;

-- Switch to 'loginapp' database; 
USE loginapp; 

-- Create 'account' table with id, username,email, password columns. 
CREATE TABLE accounts (
  id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  password VARCHAR(255) NOT NULL
); 

Delete image based on user id
DELETE FROM images WHERE user_id = 1;

CREATE TABLE IF NOT EXISTS images (
  image_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  image_name VARCHAR(255) NOT NULL,
  image_path VARCHAR(255) NOT NULL,
  image BLOB,
  metadata TEXT
);

CREATE TABLE IF NOT EXISTS audio_library (
  audio_id INT AUTO_INCREMENT PRIMARY KEY,
  audio_name VARCHAR(255) NOT NULL, -- Name of the audio file
  audio_blob MEDIUMBLOB NOT NULL, -- Storing the audio as binary data
  audio_path VARCHAR(255), -- Path to the audio file on the server, if applicable
  metadata TEXT, -- Any additional data you want to store about the audio file
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Timestamp of when the audio was uploaded
);


Make sure that the password, hsot and username you are running the program with is correct. In my case my mysql password is computing@123! and the username is root. This is the corresponding code for it in the python code. Modify according to your system.

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'yourMYSQL password'
app.config['MYSQL_DB'] = 'loginapp'

To run the code, execute the following comands in the current working directory which contains the main.py file:

Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
set FLASK_APP=main.py
set FLASK_DEBUG=1 
flask --app main.py run


Here is how you can see if an account  has been updated to the accounts table in the database
SELECT * FROM accounts;

To check if the images have been uploaded correctly (since the SELECT * FROM images WHERE user_id=1; comand prints nonsense as the image is stored as BLOB.)

SELECT COUNT(*) FROM images WHERE user_id=1;
SELECT image_id, LENGTH(image) AS image_size FROM images WHERE user_id=1;

If your images are not updating to the database, first insert an image manually to perform a check using a command dimilar to the following. Replace the image name with the image you are using. 
 
To run the program
$env:FLASK_APP="main.py"
$env:FLASK_DEBUG = "1" 
flask run
Command to run code without virtual
python -m flask --app main.py run

See user details using MySQL Commandline

Commands to see user image details:
1. Details of All Users:
SELECT * FROM accounts;

2. Number of Images Per User:
SELECT 
  accounts.username, 
  COUNT(images.image_id) AS number_of_images
FROM 
  accounts
JOIN 
  images ON accounts.id = images.user_id
GROUP BY 
  accounts.username;

3. Length of Image Paths Per User
SELECT 
  accounts.username, 
  images.image_path, 
  CHAR_LENGTH(images.image_path) AS path_length
FROM 
  accounts
JOIN 
  images ON accounts.id = images.user_id;

4. Comprehensive Information Per User
SELECT 
  accounts.id,
  accounts.username, 
  accounts.email,
  COUNT(images.image_id) AS number_of_images, 
  AVG(CHAR_LENGTH(images.image_path)) AS avg_path_length
FROM 
  accounts
LEFT JOIN 
  images ON accounts.id = images.user_id
GROUP BY 
  accounts.id;


5. Displaying Binary Data Size
SELECT 
  accounts.username, 
  images.image_id, 
  OCTET_LENGTH(images.image) AS image_size_in_bytes
FROM 
  accounts
JOIN 
  images ON accounts.id = images.user_id;
6. Display data for audio library
SELECT audio_id, audio_name, OCTET_LENGTH(audio_blob) as blob_length, audio_path, metadata, uploaded_at FROM audio_library;
