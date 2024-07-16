import cv2
import math
import datetime
import sqlite3

video = 'CAM01_HW_I90.mp4'
title = video.rsplit('.', 1)[0]  # extract title w out file extension, this will be specific db table name

haar_cascade = 'cars.xml'  # video path and video to process
cap = cv2.VideoCapture(video)  # video capture object
car_cascade = cv2.CascadeClassifier(haar_cascade)  # car detection classifier

# set start pos and widths for lanes, order of lanes: [1, 2, 3], coords in form (start_x, width)
lanes = [(275, 200), (476, 174), (650, 200)]
rectangle_thickness = 10  # set thickness of detection zone
Y = 500  # pos of line on vertically

count = [0, 0, 0]  # display counter for each lane
tracked_cent = []  # track detected centroids
decay_factor = 0.9  # decay impact of old centroids
min_dist = 40  # min distance between each centroid to verify singular car

last_minute = datetime.datetime.now().minute  # current min to compare for count reset
#last_hour = datetime.datetime.now().hour  # get current hour value to compare for count reset

conn = sqlite3.connect('database/traffic.db')  # create connection to DB
cursor = conn.cursor()  # assign cursor obj
# create table for camera if it does not exist already ***
new_table = f'''
    CREATE TABLE IF NOT EXISTS {title} (
    lane_One INTEGER,
    lane_Two INTEGER,
    lane_Three INTEGER,
    date TEXT,
    time TEXT,
    DOTW TEXT
 )
'''
cursor.execute(new_table)
conn.commit()
print(f"{title} is live collecting data.")


def insert_lane_counts(table_name, lane_counts):  # insert lane counts into database
    current_time = datetime.datetime.now()
    DOTW = current_time.strftime('%A')  # get day of the week as a string
    cursor.execute(f'''
    INSERT INTO {table_name} (lane_One, lane_Two, lane_Three, date, time, DOTW)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (lane_counts[0], lane_counts[1], lane_counts[2], current_time.date(), current_time.time().strftime('%H:%M:%S'), DOTW))
    conn.commit()


def print_lanes():  # display lanes onto screen
    for start_x, width in lanes:  # coordinates (top left, bottom right)
        cv2.rectangle(frames, (start_x, Y - rectangle_thickness), (start_x + width, Y + rectangle_thickness),
                      (150, 0, 0), 2)


def calc_cent(x, y, w, h):  # take in parameters for calculating centroid
    return x + w // 2, y + h // 2


def check_multiple(new, centroids):  # check if multiple centroids per car (aka check if centroids detected too close
    for cent in centroids:  # using euclidean dist formula, find dist btwn centroids
        if math.sqrt((cent[0] - new[0]) ** 2 + (cent[1] - new[1]) ** 2) < min_dist:
            return False  # if centroids detected closer than min allowed distance, return false
    return True  # no close detected centroids, more confidently a single vehicle


while True:
    ret, frames = cap.read()  # read a frame from the video
    if not ret:  # if no more frames, end video
        break
    gray = cv2.cvtColor(frames, cv2.COLOR_BGR2GRAY)  # convert to grayscale
    cars = car_cascade.detectMultiScale(gray, 1.1, 1)  # detect cars

    print_lanes()  # display lanes

    new_cent = [calc_cent(x, y, w, h) for (x, y, w, h) in cars]  # each detected car, calc centroid

    # set a decay factor to centroids to release them from the list if they are old
    tracked_cent = [(cent, age * decay_factor) for (cent, age) in tracked_cent if age * decay_factor > 0.1]

    current_time = datetime.datetime.now()  # receive current time
    if current_time.minute != last_minute:  # if it is a new minute
        insert_lane_counts(title, count)  # insert lane counts for previous min into database  <-------- STORE LANE DATA INTO SPECIFIC CAMERA TABLE ****
        count = [0, 0, 0]  # reset the count for each lane
        last_minute = current_time.minute  # update last minute

    for centroid in new_cent:
        cv2.circle(frames, (centroid[0], centroid[1]), 5, (0, 255, 0), -1)  # display centroid on detected car

        coords = [cent for (cent, age) in tracked_cent]  # get coords only of tracked centroids
        if check_multiple(centroid, coords):  # check if current centroids have any x,y close to each other
            # calc lane centroid is in + if within bounds of lane's rectangle
            for lane_num, (start_x, width) in enumerate(lanes):  # loop over each lane
                if (Y - rectangle_thickness) <= centroid[1] <= (Y + rectangle_thickness) and start_x <= centroid[0] <= start_x + width:
                    # if centroid in bounds of rectangle
                    count[lane_num] += 1  # increment lane count
                    tracked_cent.append((centroid, 1))  # add centroid to tracked cars, set age for decay
                    break  # stop before possibly count centroid in multiple lanes

    for lane_num, total in enumerate(count):  # continuously check and display counts for each lane #
        cv2.putText(frames, f'Lane {lane_num + 1} Count: {total}', (10, 30 + lane_num * 20), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0, 0, 255), 2)
    # display date and time at bottom of screen
    cv2.putText(frames, current_time.strftime('%Y-%m-%d %H:%M:%S'), (10, frames.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.imshow('video', frames)  # display frames

    if cv2.waitKey(33) == 27:  # exit if user presses 'esc'
        break

if any(count):  # if any remaining count when closed or stream ends
    insert_lane_counts(title, count)  # add to database (other than that, saves data top of every minute)

cv2.destroyAllWindows()
cap.release()
conn.close()  # close the database connection
