import cv2

haar_cascade = 'cars.xml'
video = 'Alibi ALI-IPU3030RV IP Camera Highway Surveillance (online-video-cutter.com).mp4'

cap = cv2.VideoCapture(video)
car_cascade = cv2.CascadeClassifier(haar_cascade)


while True:
    ret, frames = cap.read()

    gray = cv2.cvtColor(frames, cv2.COLOR_BGR2GRAY)

    cars = car_cascade.detectMultiScale(gray, 1.1,1)
    X1 = 150
    X2 = 850
    Y = 500
    # (X1, Y), (X2, Y)
    cv2.line(frames, (X1, Y), (X2, Y), (150,0,0))
    cv2.line
    for (x, y, w, h) in cars:
        cv2.rectangle(frames, (x, y), (x + w, y + h), (0, 0, 255), 2)

    cv2.putText(frames, 'Cars Detected Onscreen: ' + str(len(cars)), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2,cv2.LINE_AA)
    # Display frames in a window
    cv2.imshow('video', frames)

    if cv2.waitKey(33) == 27:
        break

cv2.destroyAllWindows()