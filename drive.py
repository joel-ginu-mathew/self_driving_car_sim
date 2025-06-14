import eventlet.wsgi
import socketio
import eventlet
import numpy as np
from flask import Flask
from keras.models import load_model
import tensorflow as tf
import base64
from io import BytesIO
from PIL import Image
import cv2


sio = socketio.Server()

app=Flask(__name__) #'__main__'

speed_limit = 10

def img_preprocessing(img):
    img = img[60:135,:,:]
    img = cv2.cvtColor(img,cv2.COLOR_RGB2YUV)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    img = cv2.resize(img, (200,66))
    img = img/255
    return img

@sio.on('connect')
def connect(sid, environ):
    print('Connected')
    send_control(0, 0)

def send_control(steering_angle,throttle):
    sio.emit('steer',data = {
        'steering_angle': steering_angle.__str__(),
        'throttle': throttle.__str__()
    })

@sio.on('telemetry')
def telemetry(sid,data):
    speed = float(data['speed'])
    image = Image.open(BytesIO(base64.b64decode(data['image'])))
    image = np.asarray(image)
    image = img_preprocessing(image)
    image = np.array([image])
    steering_angle = float(model.predict(image))
    throttle = 1.0 - speed/speed_limit
    print('{} {} {}'.format(steering_angle,throttle,speed))
    send_control(steering_angle,throttle)

# Define custom mse if necessary
def mse(y_true, y_pred):
    return tf.reduce_mean(tf.square(y_true - y_pred))

if __name__== '__main__':
    model = load_model('model/model.h5', custom_objects={'mse': mse})
    app = socketio.Middleware(sio,app)
    eventlet.wsgi.server(eventlet.listen(('',4567)),app)

