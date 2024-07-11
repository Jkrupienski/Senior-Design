from flask import Flask, render_template, jsonify, request, redirect, url_for  # import modules from Flask and others
from flask_sqlalchemy import SQLAlchemy  # import for db integration
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user  # login manager/user auth
from flask_bcrypt import Bcrypt  # import for password hashing
import pandas as pd  # import pandas lib for data manipulation and analysis
import sqlite3

app = Flask(__name__)  # create Flask class instance for web application
app.config['SECRET_KEY'] = 'KJSDP2024BASNET'  # securely sign in to session cookie ** CHANGE THIS *****
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/traffic.db'  # URI for db
db = SQLAlchemy(app)  # init SQLAlc w flask app
login_manager = LoginManager(app)  # initialize login manager
bcrypt = Bcrypt(app)  # init for password hashing


class User(UserMixin, db.Model):  # def user class for db inherit from UserMixin for flask login integration
    # def cols for user table
    id = db.Column(db.Integer, primary_key=True)  # PK col
    username = db.Column(db.String(150), unique=True, nullable=False)  # user col must be unique and not null
    password = db.Column(db.String(150), nullable=False)  # password col not null
    role = db.Column(db.String(50), nullable=False)  # role col, admin, worker ** CLARIFY LATER!! *****

@login_manager.user_loader
def load_user(user_id):  # def user loader callback func for flask login
    return User.query.get(int(user_id))  # query the user table by PK to load user


@app.route('/login', methods=['POST'])  # route for user login, only allow POST method
def login():
    data = request.get_json()  # get json data from req
    user = User.query.filter_by(username=data['username']).first()  # query user table to find user via username
    if user and bcrypt.check_password_hash(user.password, data['password']):  # check if user exists and pass matches
        login_user(user)  # log user in using flask login
        return jsonify({"status": "success", "role": user.role})  # return login success and user role
    return jsonify({"status": "failure"})  # login failure


@app.route('/logout')  # route for user logout
@login_required  # required the user to be logged in to access route
def logout():
    logout_user()  # logout using flask login
    return redirect(url_for('index'))  # redirect user to index pg ** OR ** other specified page **


@app.route('/data', methods=['GET'])  # route for protected data, allow only GET method
@login_required  # require user to be logged in to access route
def get_data():
    data = {"message": "This is protected data"}  # PLACEHOLDER for actual data fetching logic  **************
    return jsonify(data)  # return data as json


@app.route('/public-data', methods=['GET'])  # public route for getting data only via GET
def public_data():
    data = {"message": "This is public data"}
    return jsonify(data)  # return data as json


def get_lane_counts(camera_id):
    conn = sqlite3.connect('database/traffic.db')  # connect to db
    table_name = "CAM01_HW_I90"  # or "CAM02_AVE_HUNT", find way to change it depending on desired camera ***** (overall issue needing to be addressed)
    query = f"SELECT * FROM {table_name} ORDER BY date DESC, time DESC LIMIT 60"  # get last 60 entries by date and time decending order
    df = pd.read_sql_query(query, conn)  # execute query and read the results into a pandas DataFrame
    conn.close()  # close db connection
    return df  # return dataframe containing lane counts


@app.route('/')
def index():
    return render_template('index_flask.html')  # render 'index.html' template when URL accessed


@app.route('/data')
def data():
    df = get_lane_counts()  # get lane counts from db
    data = {
        'lane_One': df['lane_One'].tolist(),  # convert 'lane_One' col of df to a list
        'lane_Two': df['lane_Two'].tolist(),  # same as above
        'lane_Three': df['lane_Three'].tolist(),  # same as above
        'time': df['time'].tolist()  # convert 'time' column of df to list
    }
    return jsonify(data)  # return data as json file


if __name__ == '__main__':
    app.run(debug=True)  # use line to execute web app in debug mode
