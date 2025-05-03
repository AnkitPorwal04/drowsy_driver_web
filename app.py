from flask import Flask, render_template, Response
import cv2
import torch
import numpy as np
from PIL import Image
import vlc
import random

app = Flask(__name__)

# Load YOLOv5 model
torch.hub._validate_not_a_forked_repo=lambda a,b,c: True
model = torch.hub.load('ultralytics/yolov5', 'custom', path='yolov5/runs/train/exp9/weights/last.pt', force_reload=True)

# Initialize video capture
cap = cv2.VideoCapture(0)

# Counter variable
counter = 0

# Function to perform drowsiness detection
def detect_drowsiness(frame):
    global counter

    # Convert frame to RGB
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Perform object detection with YOLOv5
    results = model(frame)
    
    # Process detection results
    if len(results.xywh[0]) > 0:
        dconf = results.xywh[0][0][4]
        dclass = results.xywh[0][0][5]

        if dconf.item() > 0.75 and dclass.item() == 1.0:
            filechoice = random.choice([1, 2])
            p = vlc.MediaPlayer(f"file:///{filechoice}.wav")
            p.play()
            counter += 1

    return frame

# Generator function to capture frames from webcam
def generate_frames():
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        else:
            flip_frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(flip_frame, cv2.COLOR_BGR2RGB)
            frame = detect_drowsiness(rgb_frame)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame/r/n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Video feed route
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Reset counter route
@app.route('/reset_counter')
def reset_counter():
    global counter
    counter = 0
    return 'Counter reset successfully.'

if __name__ == '__main__':
    app.run(debug=True)
