import paho.mqtt.client as mqtt
import time
import json
import base64
import os
import cv2
import numpy as np
import datetime
import threading
import queue


# MQTT settings
MQTT_BROKER = ""
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60
MQTT_TOPIC = "home/doorbell/motion"
MQTT_PUB_TOPIC = "home/doorbell/yolo"

# Script settings
q = queue.Queue()
publishq = queue.Queue()

def image_process():

    def get_output_layers(net):
    
        layer_names = net.getLayerNames()
        try:
            output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
        except:
            output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

        return output_layers

    def draw_prediction(COLORS, classes, img, class_id, confidence, x, y, x_plus_w, y_plus_h):

        label = str(classes[class_id] + " " + str(round(confidence*100, 2))+ "%")

        color = COLORS[class_id]

        cv2.rectangle(img, (x,y), (x_plus_w,y_plus_h), color, 2)

        cv2.putText(img, label, (x-10,y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    def yolo(filepath):  

        image = cv2.imread(filepath)

        Width = image.shape[1]
        Height = image.shape[0]
        scale = 0.00392

        classes = None

        with open("yolov3.txt", 'r') as f:
            classes = [line.strip() for line in f.readlines()]

        COLORS = np.random.uniform(0, 255, size=(len(classes), 3))

        net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")

        blob = cv2.dnn.blobFromImage(image, scale, (416,416), (0,0,0), True, crop=False)

        net.setInput(blob)

        outs = net.forward(get_output_layers(net))

        class_ids = []
        confidences = []
        boxes = []
        conf_threshold = 0.5
        nms_threshold = 0.4


        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5:
                    center_x = int(detection[0] * Width)
                    center_y = int(detection[1] * Height)
                    w = int(detection[2] * Width)
                    h = int(detection[3] * Height)
                    x = center_x - w / 2
                    y = center_y - h / 2
                    class_ids.append(class_id)
                    confidences.append(float(confidence))
                    boxes.append([x, y, w, h])


        indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

        detected_things = []

        for i in indices:
            
            try:
                box = boxes[i]
            except:
                i = i[0]
                box = boxes[i]
            
            x = box[0]
            y = box[1]
            w = box[2]
            h = box[3]
            draw_prediction(COLORS, classes, image, class_ids[i], confidences[i], round(x), round(y), round(x+w), round(y+h))
            try:
                detected_things.append(classes[class_ids[i]])
            except:
                pass

        filepath = filepath.replace(".jpg", "-yolo.jpg")
        
        cv2.imwrite(filepath, image)

        with open(filepath, "rb") as f:
            img = f.read()

        img = base64.b64encode(img)

        #return base64 encoded image and what has been detected
        output = {"image": img, "detected": detected_things}

        return output
        


        


    while True:           

        # if no message in queue, wait
        if q.empty():
            time.sleep(1)
            #print("no message")
            continue

        # get message from queue
        msg = q.get()
        #print("got message")

        # decode message
        msg = msg.decode("utf-8")

        # convert to json
        msg = json.loads(msg)

        #message contains time, camera name, and image  (image is base64 encoded)
        try:
            img_time = str(round(msg["time"],0))
            img_camera = msg["camera"]
            img_data = msg["image"]
        except:
            continue

        #decode image
        img_data = base64.b64decode(img_data)

        #make temp directory if it doesn't exist
        if not os.path.exists("./tmp"):
            os.makedirs("./tmp")

        #save image to temp file
        img_file = "./tmp/" + img_camera + "-" + img_time + ".jpg"

        #send image to yolo
        with open(img_file, "wb") as f:
            f.write(img_data)

        output = yolo(img_file)

        outimg = output["image"]
        outdetect = output["detected"]

        #outimg needs to be json serializable
        outimg = outimg.decode("utf-8")

        #publish message
        publishq.put({"time": img_time, "camera": img_camera, "image": outimg, "detected": outdetect})

        #delete all files in temp directory
        for file in os.listdir("./tmp"):
            os.remove("./tmp/" + file)
        
        #delete temp directory
        os.rmdir("./tmp")


def publish():

    while True:

        # if no message in queue, wait
        if publishq.empty():
            time.sleep(1)
            continue

        # get message from queue
        msg = publishq.get()

        # publish message
        client.publish(MQTT_PUB_TOPIC, json.dumps(msg))

def on_connect(client, userdata, flags, rc):
    #if successful, rc = 0
    if rc == 0:
        pass
    else:
        print("Connection failed")

def on_message(client, userdata, msg):
    #print("got message")
    if msg.topic == "home/doorbell/motion":
        print("got message from doorbell")
        q.put(msg.payload)

#set up MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
client.subscribe(MQTT_TOPIC)



#start the thread
threading.Thread(target=image_process).start()
threading.Thread(target=publish).start()

#start loop but non-blocking
client.loop_start()
