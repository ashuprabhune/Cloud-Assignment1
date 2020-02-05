from flask import Flask, render_template, request, redirect, url_for, session
from flask import send_from_directory, send_file
from werkzeug.utils import secure_filename
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import os


UPLOAD_FOLDER = '/home/ubuntu/flaskapp/user_files'
ALLOWED_EXTENSIONS = set(['txt'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'secretKey'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'flask'
app.config['MYSQL_PASSWORD'] = 'flask'
app.config['MYSQL_DB'] = 'cloudDB'

mysql = MySQL(app)


@app.route('/', methods=['GET', 'POST'])
def login():
	welcome_message=''
	if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
		username = request.form['username']
        	password = request.form['password']
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM user_details WHERE username = %s AND password = %s', (username, password))
		user_details = cursor.fetchone()
		if user_details:
			session['loggedin'] = True
			session['id'] = user_details['id']
			session['username'] = user_details['username']
			session['lastname'] = user_details['lastname']
			session['email_id'] = user_details['email']
			if user_details['file_path'] == 'null': 
				session['file_path'] = None
				session['wc'] = None;
			else:
				session['file_path'] = user_details['file_path']
				session['wc'] = user_details['count']
			welcome_message = 'Welcome' + user_details['username']
			return redirect(url_for('home'))
		else:
			welcome_message = 'Invalid credentials !!!'
	return render_template('index.html', welcome_message=welcome_message)

@app.route('/logout')
def logout():
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   session.pop('file_path',None)
   session.pop('wc', None)
   return redirect(url_for('login'))
			 
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'lastname' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
	lastname = request.form['lastname']
        email = request.form['email']
	print(username)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user_details WHERE username = %s', [username])
        account = cursor.fetchone()
        if account:
            msg = 'User already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Enter valid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO user_details VALUES (NULL, %s, %s, %s,NULL,NULL,%s)', (username, password, email,lastname))
            mysql.connection.commit()
            msg = 'User successfully registered. Pleas Login to continue!'
    elif request.method == 'POST':
        msg  = 'Please fill  the form!'
    return render_template('register.html', msg=msg)

@app.route('/home')
def home():
    if 'loggedin' in session:
	num_words = 0
	if session['file_path'] == None:
		return render_template('no_file.html',username=session['username'], lastname=session['lastname'], emailid=session['email_id'])
        return render_template('home.html', username=session['username'], lastname=session['lastname'], emailid=session['email_id'], num_words=session['wc'], file_path=session['file_path'])
    return redirect(url_for('login'))

@app.route('/success', methods = ['POST'])
def success():
    if request.method == 'POST':
	f = request.files['file-upload']
	file_count = f
	filename = f.filename
	f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	session['wc'] = word(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	session['file_path'] = filename
	cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	sql = 'UPDATE user_details set file_path = %s, count = %s where username = %s'
	val = (filename , session['wc'],  session['username'])
	cursor.execute(sql,val)
	mysql.connection.commit()
    return redirect(url_for('home'))

	
def word(file_count):
	f = open(file_count)
	num_words = 0
	for line in f:
		words = line.split()
		print(words)
		num_words += len(words)
	return num_words 

@app.route('/download/<path:filename>', methods=['GET', 'POST'])
def download(filename):
	return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), attachment_filename=filename,as_attachment=True)
