from flask import Flask, render_template, jsonify, request, redirect, url_for, Response, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from io import BytesIO
import pandas as pd
import sqlite3
import cv2
import datetime
import math
import threading

# initialize flask application, declare static folder and templates folder
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'KJSDP2024BASNET'  # for session management

login_manager = LoginManager(app)  # initialize login manager for user sessions
login_manager.login_view = 'login'

car_counts = {  # dict to keep car counts for diff cameras
    'CAM01_HW_I90': [0, 0, 0],  # three lanes, add/take away if needed
    'CAM02_AVE_HUNT': [0, 0, 0]  # may move these into a camera table in traffic.db
}

min_dist = 40  # declare global var for min dist btwn centroids and decay factor for tracked centroids
decay_factor = 0.9

'''
order of code (top to bottom):
user class and login manager
app routes: '/' (root route) >> '/login' >> '/logout' >> '/profile' >> '/change_password' >> '/search' > ...
            ... > '/cleanup' >> '/data' >> '/dashboard' >> '/submit_counts' >> '/reset_counts' >> '/video_feed'
functions in /video_feed route: calc_cent, insert_lane_counts, save_counts
'''


class User(UserMixin):  # USER CLASS to maintain user information
    def __init__(self, id, username, password, name, email, access, role):
        self.id = id
        self.username = username
        self.password = password
        self.name = name
        self.email = email
        self.access = access
        self.role = role


@login_manager.user_loader  # LOAD USER from db via user id for User class
def load_user(user_id):  # ** used every time request is made by user
    conn = sqlite3.connect('database/traffic.db')  # connect db
    cursor = conn.cursor()  # open db
    cursor.execute('SELECT * FROM USERS WHERE id = ?', (user_id,))  # get user by their id
    user = cursor.fetchone()  # fetch results
    conn.close()  # close db

    if user:  # if valid user, gather user's info, current user
        return User(id=user[0], username=user[1], password=user[2], name=user[3], email=user[4], access=user[5],
                    role=user[6])
    return None


@app.route('/')  # ROOT PAGE ROUTE, LOGIN
def home():
    return redirect(url_for('login'))  # redirect to log in pg


@app.route('/login', methods=['GET', 'POST'])  # LOGIN ROUTE
def login():
    if request.method == 'POST':
        username = request.form['username']  # get username from form
        password = request.form['password']  # get password from form

        conn = sqlite3.connect('database/traffic.db')
        cursor = conn.cursor()
        # search db for user w same login info
        cursor.execute('SELECT * FROM USERS WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()  # fetch results
        conn.close()

        if user:  # if user is found w info
            user_obj = User(id=user[0], username=user[1], password=user[2], name=user[3], email=user[4],
                            access=user[5], role=user[6])
            login_user(user_obj)  # login user object made above ^
            return redirect(url_for('search'))  # redirect to search page
        else:
            return render_template('login.html', error='Incorrect login. Please try again.')  # incorrect login msg
    return render_template('login.html')  # render login pg


@app.route('/logout')  # LOGOUT ROUTE
@login_required  # must be logged in to access route
def logout():
    logout_user()  # log user out
    return redirect(url_for('login'))  # redirect to login page


@app.route('/profile')  # USER PROFILE ROUTE
@login_required
def profile():
    return render_template('profile.html')  # render user profile page


@app.route('/change_password', methods=['POST'])  # CHANGE PASSWORD ROUTE
@login_required
def change_password():
    old_password = request.form.get('old_password')  # get old password from user input
    new_password = request.form.get('new_password')  # get desired new password

    conn = sqlite3.connect('database/traffic.db')
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM USERS WHERE id = ?', (current_user.id,))  # gather user's current password
    stored_password = cursor.fetchone()[0]

    if stored_password == old_password:  # if current password matches user input of current password
        # update db w new password
        cursor.execute('UPDATE USERS SET password = ? WHERE id = ?', (new_password, current_user.id))
        conn.commit()  # commit changes to db
        flash('Password updated successfully.', 'success')  # flash success msg (success green in styles)
    else:
        flash('Old password is incorrect.', 'danger')  # flash error, current password v. user input do not match
    conn.close()
    return redirect(url_for('profile'))  # redirect to profile page


@app.route('/search')
def search():
    return render_template('search.html')  # render search page


@app.route('/cleanup', methods=['POST'])
def cleanup():  # delete records where lane data for all lanes are zero
    camera_id = request.args.get('camera_id')  # get cam id
    conn = sqlite3.connect('database/traffic.db')
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM {camera_id} WHERE lane_One = 0 AND lane_Two = 0 AND lane_Three = 0')
    conn.commit()
    # fetch remaining data after cleanup
    cursor.execute(f'SELECT date, time, lane_One, lane_Two, lane_Three FROM {camera_id}')
    rows = cursor.fetchall()
    conn.close()

    # prepare data for response
    data = {
        'date': [row[0] for row in rows],
        'time': [row[1] for row in rows],
        'lane_One': [row[2] for row in rows],
        'lane_Two': [row[3] for row in rows],
        'lane_Three': [row[4] for row in rows]
    }
    return jsonify(data)  # return cleaned up data as JSON


@app.route('/data', methods=['GET'])  # GET DATA FROM DB ROUTE
@login_required
def get_data():
    camera_id = request.args.get('camera_id')  # get following data from request
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    day_of_week = request.args.get('day_of_week')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    lane = request.args.get('lane')
    volume_min = request.args.get('volume_min')
    volume_max = request.args.get('volume_max')

    if not camera_id:  # if not valid cam id
        return jsonify({'error': 'Camera ID is required'})  # error msg

    conn = sqlite3.connect('database/traffic.db')
    cursor = conn.cursor()
    query = f'SELECT lane_One, lane_Two, lane_Three, date, time, dotw FROM {camera_id} WHERE 1=1'  # select data from table
    params = []  # list to hold query parameters

    # create query, add to it depending on search parameters
    if start_date and end_date:  # searching via start and end dates
        query += ' AND date BETWEEN ? AND ?'  # add date range filter
        params.extend([start_date, end_date])  # add dates to query
    if start_time and end_time:  # searching via time
        query += ' AND time BETWEEN ? AND ?'  # add time range
        params.extend([start_time, end_time])  # add times to query
    if day_of_week:  # searching via dotw
        query += ' AND DOTW = ?'  # create query, start by adding dotw filter
        params.append(day_of_week)  # add dotw to parameters
    if lane:  # search via specific lane volume
        query += f' AND {lane} IS NOT NULL'  # and lane has data
        if volume_min and volume_max:  # min and max as a parameter
            query += f' AND {lane} BETWEEN ? AND ?'  # find data in range
            params.extend([volume_min, volume_max])  # add to query
        elif volume_min:  # only min, same logic
            query += f' AND {lane} >= ?'
            params.append(volume_min)
        elif volume_max:  # only max, same logic
            query += f' AND {lane} <= ?'
            params.append(volume_max)
    else:  # did not search specifically by lane therefore search volume for all lanes
        if volume_min or volume_max:
            flash('Volume data needs a specific lane to be specified.', 'error')
            return redirect(url_for('search'))

    query += ' ORDER BY date DESC, time DESC'  # most recent data listed first

    cursor.execute(query, params)  # execute query with parameters
    df = cursor.fetchall()  # fetch results
    conn.close()
    data = {  # extract lane data, date, time, dotw based on search parameters
        'lane_One': [row[0] for row in df],
        'lane_Two': [row[1] for row in df],
        'lane_Three': [row[2] for row in df],
        'date': [row[3] for row in df],
        'time': [row[4] for row in df],
        'dotw': [row[5] for row in df]
    }
    return jsonify(data)  # return data as json


@app.route('/dashboard')  # VIDEO DASHBOARD ROUTE
@login_required
def dashboard():
    cameras = ['CAM01_HW_I90', 'CAM02_AVE_HUNT']  # current camera options
    return render_template('dashboard.html', cameras=cameras)  # render dashboard with camera options


@app.route('/submit_counts', methods=['POST'])  # SUBMIT COUNTS when user leaves dashboard or every minute
@login_required
def submit_counts():
    camera_id = request.json.get('camera_id')  # get cam id that is being used
    global car_counts  # access global car count
    insert_lane_counts(camera_id, car_counts[camera_id])  # insert lane count into db
    return jsonify({'status': 'success'})  # return success status


@app.route('/reset_counts', methods=['POST'])  # RESET COUNTS at the start of every minute
@login_required
def reset_counts():
    global car_counts  # access global car count
    for key in car_counts:  # reset car count for each camera
        car_counts[key] = [0, 0, 0]
    return jsonify({'status': 'success'})  # return success status


@app.route('/video_feed')  # VIDEO FEED ROUTE display video footage
def video_feed():
    camera_id = request.args.get('camera_id')  # get cam id from req
    if not camera_id:  # if no camera selected
        camera_id = 'CAM01_HW_I90'  # default camera ** (CHANGE LATER TO BLANK BOX W MSG?) **
    return Response(gen(camera_id), mimetype='multipart/x-mixed-replace; boundary=frame')  # return vid feed


def calc_cent(x, y, w, h):  # calc center of rectangle for centroid
    return x + w // 2, y + h // 2


def check_multiple(new, centroids):  # check if cents are too close to be separate cars, avoids multiple counts per car
    for cent in centroids:
        if math.sqrt((cent[0] - new[0]) ** 2 + (cent[1] - new[1]) ** 2) < min_dist:  # min_dist can be altered at top
            return False  # false if centroids are too close to each other
    return True  # no close centroids found


def insert_lane_counts(camera_id, lane_counts):  # insert lane count into db
    conn = sqlite3.connect('database/traffic.db')
    cursor = conn.cursor()
    current_time = datetime.datetime.now()  # gather current time and dotw for lane count storage
    DOTW = current_time.strftime('%A')
    try:  # add individual lane data to db with date and time ** problem later when not 3 lanes, method edits needed
        cursor.execute(f'''INSERT INTO {camera_id} (lane_One, lane_Two, lane_Three, date, time, DOTW) 
        VALUES (?, ?, ?, ?, ?, ?)''', (lane_counts[0], lane_counts[1], lane_counts[2],
                                       current_time.date(), current_time.strftime('%H:%M:%S'), DOTW))
        conn.commit()  # commit changes
    except sqlite3.IntegrityError:  # info already exists for time
        print(f"Data for time {current_time.strftime('%H:%M:%S')} already exists in {camera_id}.")
    finally:
        conn.close()


def gen(camera_id):  # generator function to serve the video feed frames
    global car_counts  # access global car count
    video = f'{camera_id}.mp4'  # make a video file ext. w the name of the camera id
    cap = cv2.VideoCapture(video)  # create a video capture for the video
    car_cascade = cv2.CascadeClassifier('cars.xml')  # load haar cascade for car detection

    # define lane detection coords *** change validation method to be thru camera db later    <---- DEFINE LANE COORDS
    lanes = [(275, 200), (476, 174), (650, 200)]  # lane detection boxes
    rectangle_thickness = 10  # rectangle thickness
    Y = 500  # rectangle height
    count = [0, 0, 0]  # init count
    tracked_cent = []  # init list of tracked centroids
    last_minute = datetime.datetime.now().minute  # current min gathered to be used as previous minute reference
    conn = sqlite3.connect('database/traffic.db')
    cursor = conn.cursor()

    def save_counts():  # save lane count end of every minute and clear count at start of new minute
        nonlocal last_minute  # use last_minute variable for last min
        while True:
            now = datetime.datetime.now()  # get current time
            seconds_to_wait = 59 - now.second  # calc sec left to wait until next min
            threading.Event().wait(seconds_to_wait)  # wait until 59 seconds
            now = datetime.datetime.now()  # update to the new time
            if now.second == 59:  # if seconds == 59
                insert_lane_counts(camera_id, count)  # insert lane count into db
                last_minute = now.minute  # update last min
            threading.Event().wait(1)  # ensure to start in the new minute
            count[:] = [0, 0, 0]  # reset each lane's count
    threading.Thread(target=save_counts, daemon=True).start()  # start new thread to save lane counts every min

    while True:
        ret, frame = cap.read()  # read frame from video
        if not ret:  # if no frames
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # convert to greyscale
        cars = car_cascade.detectMultiScale(gray, 1.1, 1)  # detect cars in the frame

        new_cent = [calc_cent(x, y, w, h) for (x, y, w, h) in cars]  # calc centroids for detected cars
        # decay prev. tracked centroids
        tracked_cent = [(cent, age * decay_factor) for (cent, age) in tracked_cent if age * decay_factor > 0.1]

        for centroid in new_cent:  # for new detected centroid
            cv2.circle(frame, (centroid[0], centroid[1]), 5, (0, 255, 0), -1)  # calc centroid based off bounding box
            coords = [cent for (cent, age) in tracked_cent]  # apply decay to tracked centroids
            if check_multiple(centroid, coords):  # check if multiple centroids on same vehicle
                # list of tuple, tuple represents lane and has starting x-coords and width of lane
                for lane_num, (start_x, width) in enumerate(lanes):  # check if cent is within lane's rectangle bounds
                    if (Y - rectangle_thickness) <= centroid[1] <= (Y + rectangle_thickness) \
                            and start_x <= centroid[0] <= start_x + width:
                        count[lane_num] += 1  # add one to total lane count
                        tracked_cent.append((centroid, 1))  # add centroid to tracked list, so it won't be counted again
                        break

        for start_x, width in lanes:  # draw rectangle for the lanes
            cv2.rectangle(frame, (start_x, Y - rectangle_thickness), (start_x + width, Y + rectangle_thickness), (150, 0, 0), 2)

        for lane_num, total in enumerate(count):  # DISPLAY LANE COUNT end up taking away when live graph works
            cv2.putText(frame, f'Lane {lane_num + 1} Count: {total}', (10, 30 + lane_num * 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # gather and display current date and time
        cv2.putText(frame, current_time, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, camera_id, (10, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        _, jpeg = cv2.imencode('.jpg', frame)  # encode frame as a jpeg (FOR WEBSITE DISPLAYING)
        frame = jpeg.tobytes()  # convert frame to bytes
        # yields data in increments, allows frame by frame video streaming to the user
        yield (b'--frame\r\n'  # specify boundary for content
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')  # content type and frame w data in bytes
    cap.release()
    conn.close()


@app.route('/download_excel', methods=['GET'])
@login_required
def download_excel(): # Save an excel file with the data obtained from the specific parameters
    camera_id = request.args.get('camera_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    day_of_week = request.args.get('day_of_week')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    lane = request.args.get('lane')
    volume_min = request.args.get('volume_min')
    volume_max = request.args.get('volume_max')

    if not camera_id:
        return jsonify({'error': 'Camera ID is required'}), 400

    conn = sqlite3.connect('database/traffic.db')
    cursor = conn.cursor()
    query = f'SELECT lane_One, lane_Two, lane_Three, date, time, dotw FROM {camera_id} WHERE 1=1'
    params = []

    if start_date and end_date:
        query += ' AND date BETWEEN ? AND ?'
        params.extend([start_date, end_date])
    if start_time and end_time:
        query += ' AND time BETWEEN ? AND ?'
        params.extend([start_time, end_time])
    if day_of_week:
        query += ' AND dotw = ?'
        params.append(day_of_week)
    if lane:
        query += f' AND {lane} IS NOT NULL'
        if volume_min and volume_max:
            query += f' AND {lane} BETWEEN ? AND ?'
            params.extend([volume_min, volume_max])
        elif volume_min:
            query += f' AND {lane} >= ?'
            params.append(volume_min)
        elif volume_max:
            query += f' AND {lane} <= ?'
            params.append(volume_max)
    else:
        if volume_min or volume_max:
            flash('Volume data needs a specific lane to be specified.', 'error')
            return redirect(url_for('search'))

    query += ' ORDER BY date DESC, time DESC'
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    data = {
        'Date': [row[3] for row in rows],
        'Time': [row[4] for row in rows],
        'Day of the Week': [row[5] for row in rows],
        'Lane One Volume': [row[0] for row in rows],
        'Lane Two Volume': [row[1] for row in rows],
        'Lane Three Volume': [row[2] for row in rows]
    }

    df = pd.DataFrame(data)
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Traffic Data')
    writer.close()
    output.seek(0)

    return Response(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    headers={"Content-Disposition": "attachment;filename=traffic_data.xlsx"})

if __name__ == '__main__':
    app.run(debug=True)
