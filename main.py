import cv2
import math
import datetime

haar_cascade = 'cars.xml'  # video path and video to process
video = 'Alibi ALI-IPU3030RV IP Camera Highway Surveillance (online-video-cutter.com).mp4'
cap = cv2.VideoCapture(video)  # video capture object
car_cascade = cv2.CascadeClassifier(haar_cascade)  # car detection classifier

# set start pos and widths for lanes, order of lanes: [1, 2, 3], coords in form (start_x, width)
lanes = [(275, 200), (476, 174), (650, 200)]
rectangle_thickness = 10  # set thickness of detection zone
Y = 500  # pos of line on vertically

count = [0, 0, 0]  # display counter for each lane
tracked_cent = []  # track detected centroids
decay_factor = 0.9  # decay impact of old centroids  (*****)
min_dist = 40  # min distance between each centroid to verify singular car

last_hour = datetime.datetime.now().hour  # get current hour value to compare for count reset


def print_lanes():  # display lanes onto screen
    for start_x, width in lanes:  # coordinates (top left, bottom right)
        cv2.rectangle(frames, (start_x, Y - rectangle_thickness), (start_x + width, Y + rectangle_thickness), (150, 0, 0), 2)


def calc_cent(x, y, w, h):  # take in parameters for calculating centroid
    return x + w // 2, y + h // 2


def check_multiple(new, centroids):  # check if multiple centroids per car (aka check if centroids detected too close
    for cent in centroids:  # using euclidean dist formula, find dist btwn centroids
        if math.sqrt((cent[0] - new[0])**2 + (cent[1] - new[1])**2) < min_dist:
            return False  # if centroids detected closer than min allowed distance, return false
    return True  # no close detected centroids, more confidently a single vehicle


while True:
    ret, frames = cap.read()  # read a frame from the video
    # if not ret:  # if no more frames, end video
        # break
    gray = cv2.cvtColor(frames, cv2.COLOR_BGR2GRAY)  # convert to grayscale
    cars = car_cascade.detectMultiScale(gray, 1.1, 1)  # detect cars

    print_lanes()  # display lanes

    new_cent = [calc_cent(x, y, w, h) for (x, y, w, h) in cars]  # each detected car, calc centroid

    # set a decay factor to centroids to release them from the list if they are old
    tracked_cent = [(cent, age * decay_factor) for (cent, age) in tracked_cent if age * decay_factor > 0.1]

    current_time = datetime.datetime.now()  # receive current time
    if current_time.hour != last_hour:  # if hour has changed
        count = [0, 0, 0]  # reset lane at start of new hour
        last_hour = current_time.hour  # store new current hour value

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
        cv2.putText(frames, f'Lane {lane_num+1} Count: {total}', (10, 30 + lane_num * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    # display date and time at bottom of screen
    cv2.putText(frames, current_time.strftime('%Y-%m-%d %H:%M:%S'), (10, frames.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.imshow('video', frames)  # display frames

    if cv2.waitKey(33) == 27:  # exit if user presses 'esc'
        break

cv2.destroyAllWindows()
cap.release()
