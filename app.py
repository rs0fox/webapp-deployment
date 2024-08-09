from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import boto3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure SQLite or MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # or use MySQL: 'mysql://username:password@localhost/dbname'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

# Route for registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            return redirect(url_for('download'))
        return 'Invalid credentials'
    return render_template('login.html')

# Route for downloading the game
@app.route('/download')
def download():
    if 'user_id' in session:
        # Generate the S3 download link
        s3 = boto3.client('s3')
        bucket_name = 'builddb'
        object_name = 'game/main.exe'
        download_url = s3.generate_presigned_url('get_object',
                                                 Params={'Bucket': bucket_name, 'Key': object_name},
                                                 ExpiresIn=3600)
        return render_template('download.html', link=download_url)
    return redirect(url_for('login'))

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
