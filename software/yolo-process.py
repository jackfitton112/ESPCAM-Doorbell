import time, json, base64, os, cv2, threading, queue
import numpy as np
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

def loadFromEnv():

    #load the .env file using the dotenv library
    if load_dotenv() == False:
        assert False, "Error loading .env file"


    #declare the global variables to be used in the script
    global MQTT_BROKER
    global MQTT_PORT
    global MOTION_EYE_URL
    global MQTT_USER
    global MQTT_PASS

    MQTT_BROKER = os.getenv("MQTT_BROKER") 
    MQTT_PORT = int(os.getenv("MQTT_PORT")) #Must be type cast to int for lib
    MOTION_EYE_URL = os.getenv("MOTION_EYE_URL")
    MQTT_USER = os.getenv("MQTT_USER")
    MQTT_PASS = os.getenv("MQTT_PASS")

    #check if the variables are set
    if (MQTT_BROKER == None or MQTT_PORT == None or MOTION_EYE_URL == None or 
        MQTT_USER == None or MQTT_PASS == None):
  
        assert False, "Error loading .env variables"

    return True

loadFromEnv()

# MQTT settings
MQTT_KEEPALIVE = 60
MQTT_TOPIC = "home/doorbell/motion"
MQTT_PUB_TOPIC = "home/doorbell/yolo"

# Script settings
image_process_queue = queue.Queue()
mqtt_publish_queue = queue.Queue()

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

    def save_image(img, filename):
        #create a temp directory if it doesn't exist
        if not os.path.exists("./tmp"):
            os.makedirs("./tmp")

        file_path = "./tmp/" + filename

        with open(file_path, "wb") as f:
            f.write(img)

        return file_path
        
    def remove_tmp_dir():
        #delete all files in temp directory
        for file in os.listdir("./tmp"):
            os.remove("./tmp/" + file)
        
        #delete temp directory
        os.rmdir("./tmp")

    while True:           

        # if no message in queue, wait
        if image_process_queue.empty():
            time.sleep(1)
            continue

        # get the decoded message from queue
        msg = image_process_queue.get()

        # convert json to dict
        msg = json.loads(msg)

        #message contains time, camera name, and image  (image is base64 encoded)
        if not("time" in msg and "camera" in msg and "image" in msg):
            continue

        img_time = msg["time"] #time image was taken (in unix time)
        img_camera = msg["camera"] #camera name
        img_data = base64.b64decode(msg["image"]) #decode image from base64 string to bytes


        #make temp directory if it doesn't exist
        if not os.path.exists("./tmp"):
            os.makedirs("./tmp")

        #save image to temp file
        img_file = img_camera + "-" + img_time + ".jpg"

        #send image to yolo
        output = yolo(save_image(img_data, img_file))

        output_img = output["image"] #file path of image
        output_detected = output["detected"] # list of what has been detected

        #outimg needs to be json serializable
        output_img = output_img.decode("utf-8")

        #publish message
        mqtt_publish_queue.put({"time": img_time, "camera": img_camera, "image": output_img, "detected": output_detected})

        #remove temp directory
        remove_tmp_dir()

def publish():

    while True:

        # if no message in queue, wait
        if mqtt_publish_queue.empty():
            time.sleep(1)
            continue

        # get message from queue
        msg = mqtt_publish_queue.get()

        # publish message
        client.publish(MQTT_PUB_TOPIC, json.dumps(msg))

        #remove item from queue
        mqtt_publish_queue.task_done()

    

def on_connect(client, userdata, flags, rc):
    #if successful rc = 0
    if rc == 0:
        pass
    else:
        print("Connection failed")

def on_message(client, userdata, msg):
    #print("got message")
    if msg.topic == "home/doorbell/motion":
        #decode message
        msg = msg.payload.decode("utf-8")
        #add message to queue
        image_process_queue.put(msg)

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


#TODO: remove threading and use asyncio instead
