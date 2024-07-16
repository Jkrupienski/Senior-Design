# app.py is the entry point for the flask application
from flask import Flask, render_template, jsonify, request, redirect, url_for  # import modules from Flask and others
from flask_sqlalchemy import SQLAlchemy  # import for db integration
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user  # login manager/user auth
from flask_bcrypt import Bcrypt  # import for password hashing
import pandas as pd  # import pandas lib for data manipulation and analysis
import sqlite3

app = Flask(__name__, static_folder='static', template_folder='templates')  # create Flask class instance for web application
app.config['SECRET_KEY'] = 'KJSDP2024BASNET'  # securely sign in to session cookie ** CHANGE THIS *****
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/traffic.db'  # URI for db
db = SQLAlchemy(app)  # init SQLAlc w flask app
login_manager = LoginManager(app)  # initialize login manager
bcrypt = Bcrypt(app)  # init for password hashing


class User(UserMixin, db.Model):  # def user class for db inherit from UserMixin for flask login integration
    # def cols for user table
    id = db.Column(db.Integer, primary_key=True)  # PK col
    username = db.Column(db.String(50), unique=True, nullable=False)  # user col must be unique and not null
    password = db.Column(db.String(50), nullable=False)  # password col not null
    name = db.Column(db.String(50), nullable=False)  # for future, print 'last name, first name'
    email = db.Column(db.String(50), nullable=False)  # last name first initial: 'arpinok'
    access = db.Column(db.Integer, nullable=False)  # 1 (engineer), 2 (admin), 3 (work)
    role = db.Column(db.String(50), nullable=False)  # role col, engineer, admin, worker ** CLARIFY LATER!! *****


@login_manager.user_loader
def load_user(user_id):  # def user loader callback func for flask login
    return User.query.get(int(user_id))  # query the user table by PK to load user


@app.route('/login', methods=['GET', 'POST'])  # route for user login; 'GET' request, retrieve data; 'POST' submit data
def login():
    if request.method == 'POST':  # process form data "POST"
        username = request.form['username']
        password = request.form['password']
        data = request.form  # get data from req
        user = User.query.filter_by(username=username).first()  # query user table to find user via username
        if user and bcrypt.check_password_hash(user.password, password):  # check if user exists and pass matches
            login_user(user)  # log user in using flask login
            return redirect(url_for('dashboard'))
        return 'Login Failed'
    return render_template('login.html')  # render login page for "GET"


@app.route('/logout')  # route for user logout
@login_required  # required the user to be logged in to access route
def logout():
    logout_user()  # logout using flask login
    return redirect(url_for('index'))  # redirect user to index pg ** OR ** other specified page **


@app.route('/data', methods=['GET'])  # route for protected data, allow only GET method
@login_required  # require user to be logged in to access route
def get_data():
    df = get_lane_counts()  # gather lane data from db
    data = {
        'lane_One': df['lane_One'].tolist(),
        'lane_Two': df['lane_Two'].tolist(),
        'lane_Three': df['lane_Three'].tolist(),
        'time': df['time'].tolist()
    }
    return jsonify(data)  # return data as json


@app.route('/public-data', methods=['GET'])  # public route for getting data only via GET
def public_data():
    data = {"message": "This is public data"}
    return jsonify(data)  # return data as json


def get_lane_counts(camera_id):
    conn = sqlite3.connect('database/traffic.db')  # connect to db
    table_name = "CAM01_HW_I90"  # or "CAM02_AVE_HUNT", way to change it depending on desired camera *****
    query = f"SELECT * FROM {table_name} ORDER BY date DESC, time DESC LIMIT 60"  # get last 60 entries, decending order
    df = pd.read_sql_query(query, conn)  # execute query and read the results into a pandas DataFrame
    conn.close()  # close db connection
    return df  # return dataframe containing lane counts


@app.route('/')
def index():
    return render_template('index.html')  # render 'index.html' template when URL accessed


@app.route('/dashboard')  # route for dashboard, required to be logged in by user
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/home')  # homepage route, possible showing of data before login ??? *****
def home():
    return render_template('home.html')


if __name__ == '__main__':
    app.run(debug=True)  # use line to execute web app in debug mode
