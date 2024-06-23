from flask import Flask, render_template, jsonify  # import modules from Flask and others
import sqlite3
import pandas as pd  # import pandas lib for data manipulation and analysis

app = Flask(__name__)  # create Flask class instance for web application

def get_lane_counts():
    conn = sqlite3.connect('lane_counts.db')  # connect to db
    query = "SELECT * FROM lane_counts ORDER BY date DESC, time DESC LIMIT 60"  # get last 60 entries by date and time decending order
    df = pd.read_sql_query(query, conn)  # execute query and read the results into a pandas DataFrame
    conn.close()  # close db connection
    return df  # return dataframe containing lane counts

@app.route('/')
def index():
    return render_template('index.html')  # render 'index.html' template when URL accessed

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
