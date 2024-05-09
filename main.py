import cv2  # import openCV lib

haar_cascade = 'cars.xml'  # video path and video to process
video = 'Alibi ALI-IPU3030RV IP Camera Highway Surveillance (online-video-cutter.com).mp4'

cap = cv2.VideoCapture(video)  # video capture object
car_cascade = cv2.CascadeClassifier(haar_cascade)  # car detection classifier

X1, X2, Y = 150, 850, 500  # (X1, Y), (X2, Y)
count = 0  # initial car counter
count_cent = []  # tracked centroid count


def calc_cent(x, y, w, h):  # take in parameters for calculation
    return (x + w // 2, y + h // 2)  # return tuple w coordinates of center

while True:
    ret, frames = cap.read()  # read a single frame from the video
    if not ret:
        break
    gray = cv2.cvtColor(frames, cv2.COLOR_BGR2GRAY)  # convert frames to grayscale
    cars = car_cascade.detectMultiScale(gray, 1.1, 1)  # detect cars

    cv2.line(frames, (X1, Y), (X2, Y), (150, 0, 0), 2)  # draw blue line across frame

    new_cent = [calc_cent(x, y, w, h) for (x, y, w, h) in cars]

    for centroid in new_cent:  # for each centroid in list
        x, y = centroid  # store specific data for centroid via tuple
        cv2.circle(frames, (x, y), 5, (0, 0, 255), -1)  # filled circle
        #  verify if there are multiple centroids in one spot, if so, only count for one (??!!!!!)  *******
        if centroid not in count_cent:  # check if centroid crossed line
            if Y - 5 <= y <= Y + 5 and X1 <= x <= X2:  # small margin around y line
                count += 1
                count_cent.append(centroid)  # add centroid to tracked car list

    cv2.putText(frames, 'Oncoming Car Counter: ' + str(count), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2,
                cv2.LINE_AA)
    # cv2.putText(frames, 'Oncoming Car Counter: ' + str(len(cars)), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0),
    # 2, cv2.LINE_AA)
    cv2.imshow('video', frames)  # display processed frames in window

    if cv2.waitKey(33) == 27:  # press 'esc' to quit
        break
'''
    for (x, y, w, h) in cars:
        cv2.rectangle(frames, (x, y), (x + w, y + h), (0, 0, 255), 2)  # flag rectangle on detected car
        count = count + 1
'''

cv2.destroyAllWindows()