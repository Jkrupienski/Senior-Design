from flask import Flask, render_template, jsonify, request, redirect, url_for, Response, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from io import BytesIO
import pandas as pd
import sqlite3
import cv2
import datetime
import math
import threading
import numpy as np
from collections import deque

# initialize flask application, declare static folder and templates folder
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'KJSDP2024BASNET'  # for session management

login_manager = LoginManager(app)  # initialize login manager for user sessions
login_manager.login_view = 'login'

car_counts = {  # dict to keep car counts for diff cameras
    'CAM01_HW_I90': [0, 0, 0],  # three lanes, add/take away if needed
    'CAM02_AVE_HUNT': [0, 0, 0],  # may move these into a camera table in traffic.db
    'CAM03_NH_RABOUT': [0, 0, 0]
}

cameras = ['CAM01_HW_I90', 'CAM02_AVE_HUNT', 'CAM03_NH_RABOUT', 'https://www.youtube.com/watch?v=1fiF7B6VkCk']

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
        return jsonify({'error': 'Camera ID is required'}), 400  # error msg

    conn = sqlite3.connect('database/traffic.db')
    cursor = conn.cursor()

    # ensure the table name is safe by using double quotes
    query = f'SELECT lane_One, lane_Two, lane_Three, date, time, dotw FROM {camera_id} WHERE 1=1'
    params = []  # list to hold query parameters

    # create query, add to it depending on search parameters
    if start_date and end_date:  # searching via start and end dates
        query += ' AND date BETWEEN ? AND ?'  # add date range filter
        params.extend([start_date, end_date])  # add dates to query
    if start_time and end_time:  # searching via time
        query += ' AND time BETWEEN ? AND ?'  # add time range
        params.extend([start_time, end_time])  # add times to query
    if day_of_week:  # searching via dotw
        query += ' AND dotw = ?'  # create query, start by adding dotw filter
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
    global cameras  # current camera options
    return render_template('dashboard.html', cameras=cameras)  # render dashboard with camera options


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


def insert_lane_counts(camera_id, lane_counts, averages):  # insert lane count into db
    conn = sqlite3.connect('database/traffic.db')
    cursor = conn.cursor()
    current_time = datetime.datetime.now()  # gather current time and dotw for lane count storage
    DOTW = current_time.strftime('%A')
    try:  # add individual lane data to db with date and time ** problem later when not 3 lanes, method edits needed
        cursor.execute(f'''INSERT INTO {camera_id} (lane_One, lane_Two, lane_Three, date, time, DOTW, lane_One_Avg, lane_Two_Avg, lane_Three_Avg) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (lane_counts[0], lane_counts[1], lane_counts[2], current_time.date(),
                current_time.strftime('%H:%M:%S'), DOTW, round(averages[0], 2), round(averages[1], 2), round(averages[2], 2)))
        conn.commit()  # commit changes
    except sqlite3.IntegrityError:  # info already exists for time
        print(f"Data for time {current_time.strftime('%H:%M:%S')} already exists in {camera_id}.")
    finally:
        conn.close()


def save_counts(camera_id, count, last_minute, lane_speeds):  # save count end of each min, clear count start of new min
    while True:
        now = datetime.datetime.now()  # get current time
        seconds_to_wait = 59 - now.second  # calc sec left to wait until next min
        threading.Event().wait(seconds_to_wait)  # wait until 59 seconds
        now = datetime.datetime.now()  # update to the new time
        if now.second == 59:  # if seconds == 59
            average_speeds = calculate_average_speeds(lane_speeds)  # calc average speeds
            insert_lane_counts(camera_id, count, average_speeds)  # insert lane count into db
            last_minute = now.minute  # update last min
        threading.Event().wait(1)  # ensure to start in the new minute
        count[:] = [0, 0, 0]  # reset each lane's count


def weighted_moving_average(values, weights):
    weighted_avg = np.dot(values, weights) / np.sum(weights)
    return weighted_avg


def average_speeds():
    return jsonify(average_speeds)


def calculate_average_speeds(lane_speeds):
    while True:
        now = datetime.datetime.now()
        seconds_to_wait = 59 - now.second
        threading.Event().wait(seconds_to_wait)
        now = datetime.datetime.now()
        if now.second == 59:
            average_speeds = {}
            for lane, speeds in lane_speeds.items():
                # Filter out unrealistic values
                filtered_speeds = [speed for speed in speeds if 30 <= speed <= 100]
                if filtered_speeds:
                    average_speeds[lane] = (sum(filtered_speeds) / len(filtered_speeds))
                else:
                    average_speeds[lane] = 0  # Handle empty lists
                lane_speeds[lane] = []  # Reset the lane speed list to an empty list
            print("AVERAGE SPEEDS PRINTING")
            print(average_speeds)
            return average_speeds


# ========================================================================================================
# ========================================================================================================
def gen(camera_id):  # generator function to serve the video feed frames  ** MAIN VEHICLE DETECTION LOGIC

    src_points = np.float32([
        [100, 300],
        [500, 300],
        [100, 700],
        [500, 700]
    ])
    dst_points = np.float32([
        [0, 0],
        [2000, 0],
        [0, 2000],
        [2000, 2000]
    ])

    homography_matrix, _ = cv2.findHomography(src_points, dst_points)

    prev_centroids = {}
    car_ids = {}
    car_speeds = {}
    car_trails = {}
    next_car_id = 0
    meters_per_mile = 1609.34
    smoothing_frames = 10
    trail_fade_time = 5
    decay_factor = 0.9

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
    lane_speeds = {i: [] for i in range(len(lanes))}  # dict to store speeds for each lane
    last_minute = datetime.datetime.now().minute  # current min gathered to be used as previous minute reference
    conn = sqlite3.connect('database/traffic.db')
    cursor = conn.cursor()

    # start new thread to save lane counts every min
    threading.Thread(target=save_counts, args=(camera_id, count, last_minute, lane_speeds), daemon=True).start()

    frame_skip = 2
    frame_count = 0

    while True:
        ret, frame = cap.read()  # read frame from video
        if not ret:  # if no frames
            break
        frame_count += 1
        if frame_count % frame_skip != 0:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # convert to greyscale
        cars = car_cascade.detectMultiScale(gray, 1.1, 1)  # detect cars in the frame

        new_cent = [calc_cent(x, y, w, h) for (x, y, w, h) in cars]  # calc centroids for detected cars
        # decay prev tracked centroids
        tracked_cent = [(cent, age * decay_factor) for (cent, age) in tracked_cent if age * decay_factor > 0.1]

        for (x, y, w, h), centroid in zip(cars, new_cent):  # iterate over each detected car and its centroid
            # draw a circle at the centroid of the car on the frame for visualization
            cv2.circle(frame, (centroid[0], centroid[1]), 5, (0, 255, 0), -1)  # draw circle onto centroid

            coords = [cent for (cent, age) in tracked_cent]  # create a list of coordinates from the tracked centroids

            if check_multiple(centroid, coords):  # check if new centroid is not too close to existing centroids
                for lane_num, (start_x, width) in enumerate(lanes):  # iterate each lane w starting x coord and width
                    # check if centroid is within the rectangle bounds of the lane
                    if (Y - rectangle_thickness) <= centroid[1] <= (Y + rectangle_thickness) \
                            and start_x <= centroid[0] <= start_x + width:
                        current_time = datetime.datetime.now()  # get current time
                        # create dict of current centroids with their bounding boxes
                        current_centroids = {centroid: (x, y, w, h) for (x, y, w, h), centroid in zip(cars, new_cent)}

                        for centroid in list(prev_centroids.keys()):  # iterate over prev cent to find the closest one
                            min_dist = float('inf')
                            closest_centroid = None
                            # iterate over current centroids to find min distance to a previous centroid
                            for curr_centroid in current_centroids.keys():
                                dist = np.linalg.norm(np.array(centroid) - np.array(curr_centroid))  # calc dist
                                if dist < min_dist and dist < 50:  # find closest centroid
                                    min_dist = dist  # update min dist
                                    closest_centroid = curr_centroid  # update closest cent to be current cent

                            if closest_centroid is not None and centroid in prev_centroids:  # if close cent found
                                points = np.array([[list(centroid)], [list(closest_centroid)]], dtype='float32')
                                # apply homography transformation to points
                                points_transformed = cv2.perspectiveTransform(points, homography_matrix)
                                # calc the real-world distance between points
                                real_world_distance = np.linalg.norm(points_transformed[0] - points_transformed[1])
                                # calc time elapsed for movement
                                time_elapsed = (current_time - prev_centroids[centroid][1]).total_seconds()
                                if time_elapsed == 0:
                                    time_elapsed = 1
                                speed_m_per_s = real_world_distance / time_elapsed
                                speed_mph = speed_m_per_s * 3600 / meters_per_mile  # convert the speed to miles per hr

                                if speed_mph > 100:  # filter out unrealistic speeds
                                    speed_mph = 0
                                speed_mph = round(speed_mph, 2)

                                if centroid not in car_ids:  # assign a new car ID if it doesn't exist
                                    car_ids[centroid] = next_car_id
                                    next_car_id += 1
                                    # init deque for speed smoothing
                                    car_speeds[car_ids[centroid]] = deque(maxlen=smoothing_frames)

                                car_speeds[car_ids[centroid]].append(speed_mph)  # append the calc speed to the deque

                                weights = np.linspace(1, 0.1, len(car_speeds[car_ids[centroid]]))  # calc avg of speeds
                                avg_speed_mph = round(weighted_moving_average(np.array(car_speeds[car_ids[centroid]]),
                                                                        weights), 2)

                                # update the closest centroid with the new data
                                prev_centroids[closest_centroid] = (closest_centroid, current_time)
                                car_ids[closest_centroid] = car_ids.pop(centroid)

                                # check if centroid should be displayed and add its speed to the lane speeds
                                if (Y - rectangle_thickness) <= centroid[1] <= (Y + rectangle_thickness) and start_x <= \
                                        centroid[0] <= start_x + width:
                                    if not np.isnan(avg_speed_mph):
                                        cv2.putText(frame, f'{int(avg_speed_mph)} mph',  # display speed on the frame
                                                    (closest_centroid[0], closest_centroid[1] - 10),
                                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                                        lane_speeds[lane_num].append(avg_speed_mph)  # add speed to list of lane speeds
                                        print(avg_speed_mph)  # print speed for debugging

                        for centroid in new_cent:  # add new cent to prev centroids for tracking
                            if centroid not in prev_centroids:
                                prev_centroids[centroid] = (centroid, current_time)
                                car_ids[centroid] = next_car_id
                                next_car_id += 1
                                car_trails[car_ids[centroid]] = deque(maxlen=50)
                                car_speeds[car_ids[centroid]] = deque(maxlen=smoothing_frames)

                        count[lane_num] += 1  # increment the count for the lane
                        tracked_cent.append((centroid, 1))  # add centroid to tracked list
                        break  # exit loop after processing this lane

        for start_x, width in lanes:  # draw rectangle for the lanes
            cv2.rectangle(frame, (start_x, Y - rectangle_thickness), (start_x + width, Y + rectangle_thickness), (150, 0, 0), 2)

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
# ========================================================================================================
# ========================================================================================================


@app.route('/add_camera', methods=['POST'])
@login_required
def add_camera():
    global cameras
    global car_counts

    if current_user.role not in ['Admin', 'Manager']:
        flash('You do not have permission to add a camera.', 'danger')
        return redirect(url_for('profile'))

    camera_id = request.form.get('camera_id')
    if not camera_id:
        flash('Camera ID  required.', 'danger')
        return redirect(url_for('profile'))

    conn = sqlite3.connect('database/traffic.db')
    cursor = conn.cursor()
    try:
        # Create a new table for the camera with three lanes
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS "{camera_id}" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lane_One INTEGER DEFAULT 0,
                lane_Two INTEGER DEFAULT 0,
                lane_Three INTEGER DEFAULT 0,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                DOTW TEXT NOT NULL,
                lane_One_Avg INTEGER DEFAULT 0,
                lane_Two_Avg INTEGER DEFAULT 0, 
                lane_Three_Avg INTEGER DEFAULT 0
            )''')

        conn.commit()


        car_counts[camera_id] = [0, 0, 0]
        cameras.append(camera_id)
        flash('Camera added successfully.', 'success')
    except sqlite3.Error as e:
        flash(f'An error occurred: {e}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('profile'))


@app.route('/avg_speeds', methods=['GET'])
@login_required
def get_average_speeds():
    camera_id = 'CAM01_HW_I90'
    #camera_id = request.args.get('camera_id')
    if not camera_id:
        return jsonify({'error': 'Camera ID is required'}), 400

    conn = sqlite3.connect('database/traffic.db')
    cursor = conn.cursor()
    cursor.execute(f'SELECT lane_One_Avg, lane_Two_Avg, lane_Three_Avg FROM {camera_id} ORDER BY date DESC, time DESC LIMIT 1')
    row = cursor.fetchone()
    conn.close()

    if row:
        data = {
            'lane_One': row[0],
            'lane_Two': row[1],
            'lane_Three': row[2]
        }
        return jsonify(data)
    else:
        return jsonify({'lane_One': 0, 'lane_Two': 0, 'lane_Three': 0})


@app.route('/download_excel', methods=['GET'])
@login_required
def download_excel():  # save an excel file with the data obtained from the specific parameters
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
    query = f'SELECT lane_One, lane_Two, lane_Three, date, time, dotw, lane_One_Avg, lane_Two_Avg, lane_Three_Avg FROM {camera_id} WHERE 1=1'
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
        'Date': [row[4] for row in rows],
        'Time': [row[5] for row in rows],
        'Day of the Week': [row[5] for row in rows],
        'Lane One Volume': [row[0] for row in rows],
        'Lane Two Volume': [row[1] for row in rows],
        'Lane Three Volume': [row[2] for row in rows],
        'Lane One Average Speed' : [row[6] for row in rows],
        'Lane Two Average Speed': [row[7] for row in rows],
        'Lane Three Average Speed': [row[8] for row in rows]
    }

    df = pd.DataFrame(data)
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Traffic Data')
    writer.close()
    output.seek(0)

    return Response(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    headers={"Content-Disposition": f"attachment;filename={camera_id}.xlsx"})


if __name__ == '__main__':
    app.run(debug=True)
