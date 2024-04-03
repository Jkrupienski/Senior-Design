from PIL import Image
import cv2
import numpy as np
import requests

# Downloading and resizing the image from the URL
image_url = 'https://a57.foxnews.com/media.foxbusiness.com/BrightCove/854081161001/201805/2879/931/524/854081161001_5782482890001_5782477388001-vs.jpg'
response = requests.get(image_url, stream=True)
image = Image.open(response.raw)
image = image.resize((450, 250))


# Convert the image to a Numpy array
image_arr = np.array(image)

# Show the converted Numpy array as an image
cv2.imshow("Converted Image to Numpy Array", image_arr)
cv2.waitKey(0)
cv2.destroyAllWindows()

# Convert the image to grayscale
grey = cv2.cvtColor(image_arr, cv2.COLOR_BGR2GRAY)

# Show the grayscale image
cv2.imshow("Grayscale Image", grey)
cv2.waitKey(0)
cv2.destroyAllWindows()

# Apply Gaussian blur to the grayscale image
blur = cv2.GaussianBlur(grey, (5, 5), 0)

# Show the blurred image
cv2.imshow("Blurred Image", blur)
cv2.waitKey(0)
cv2.destroyAllWindows()

# Apply dilation to the blurred image
dilated = cv2.dilate(blur, np.ones((3, 3)))

# Show the dilated image
cv2.imshow("Dilated Image", dilated)
cv2.waitKey(0)
cv2.destroyAllWindows()

# Apply morphological closing to the dilated image
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
closing = cv2.morphologyEx(dilated, cv2.MORPH_CLOSE, kernel)

# Show the morphologically closed image
cv2.imshow("Morphologically Closed Image", closing)
cv2.waitKey(0)
cv2.destroyAllWindows()

# Use CascadeClassifier for car detection
car_cascade_src = 'cars.xml'
car_cascade = cv2.CascadeClassifier(car_cascade_src)
cars = car_cascade.detectMultiScale(closing, 1.1, 1)

# Draw rectangles around each detected car and count
cnt = 0
for (x, y, w, h) in cars:
    cv2.rectangle(image_arr, (x, y), (x + w, y + h), (255, 0, 0), 2)
    cnt += 1

# Print the total number of detected cars and buses
print(cnt, " cars found")

# Convert the annotated image to PIL Image format and display it
annotated_image = Image.fromarray(image_arr)
annotated_image.show()

# Close the window when a key is pressed
cv2.waitKey(0)
cv2.destroyAllWindows()