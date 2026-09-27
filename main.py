import cv2
import numpy as np
from ultralytics import YOLO
import easyocr
import datetime
import sqlite3

conn = sqlite3.connect("DataBase.db")
cursor = conn.cursor()
cursor.execute("""create table if not exists info (Id integer primary key AUTOINCREMENT , Type text , Plate_Number text , Screenshot text , Date text , Confidence real)""")
conn.commit()

classes = {0:"person",1:"bicycle",2:"car",3:"motorcycle",5:"bus",7:"truck"}

close_threshold = 5.0
medium_threshold = 15.0
alpha = 0.2

def classify(distance):
    if distance < close_threshold:
        return (0,0,255) , "Close"
    elif distance < medium_threshold:
        return (0,165,255) , "Medium"
    else:
        return (0,255,0) , "far"

reader = easyocr.Reader(['en'])
detection = YOLO('yolo26n.pt')
depth = YOLO('yolo26n-depth.pt')

cam = cv2.VideoCapture(0)

state = {}
timers = {}
smooth = {}

while True:
    ret , frame = cam.read()
    if not ret:
        break
    h,w = frame.shape[:2]
    det = detection.track(frame,persist=True,tracker='bytetrack.yaml',classes=list(classes),verbose=False)[0]
    dep = depth(frame,verbose=False)[0].depth.data.cpu().numpy()
    if dep.shape[:2] != (h,w):
        dep = cv2.resize(dep,(w,h),interpolation=cv2.INTER_NEAREST)
    for box in det.boxes:
        x1,y1,x2,y2 = map(int,box.xyxy[0])
        x1,y1,x2,y2 = max(x1,0),max(y1,0),min(x2,w),min(y2,h)
        class_id = int(box.cls[0])
        track_id = int(box.id[0]) if box.id is not None else None
        if track_id is None:
            continue
        if track_id not in state:
            state[track_id] = {
                "Type": classes[class_id],
                "Plate_Number": "Unknown",
                "Screenshot": "No",
                "Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Saved": False
            }
        bw,bh = x2-x1 , y2-y1
        crop = dep[y1 + bh // 4:y2 - bh // 4, x1 + bw // 4:x2 - bw // 4]
        valid = crop[np.isfinite(crop) & (crop>0)]
        if valid.size == 0:
            continue
        dist = float(np.median(valid))
        dist = alpha * dist + (1-alpha) * smooth.get(track_id,dist)
        smooth[track_id] = dist
        color , status = classify(dist)
        tag = f"{track_id}"
        label = f"{tag} {classes[class_id]} - {status} {dist:.1f}M"
        cv2.rectangle(frame,(x1,y1),(x2,y2),color,3)
        cv2.putText(frame,label,(x1,y1-10),cv2.FONT_HERSHEY_SIMPLEX,0.6,color,3)
        if class_id in (1, 2, 3, 5, 7) and status == "Close":
            if track_id not in timers:
                timers[track_id] = datetime.datetime.now().timestamp()
            duration = (datetime.datetime.now().timestamp()- timers[track_id])
            if duration >= 5:
                if not state[track_id]["Saved"]:
                    Vehicle_crop = frame[y1:y2, x1:x2]
                    ocr = reader.readtext(Vehicle_crop)
                    if ocr:
                        state[track_id]["Plate_Number"] = ocr[0][1]
                    filename = f"full_{track_id}.jpg"
                    cv2.imwrite(f"full_{track_id}.jpg", frame)
                    state[track_id]["Screenshot"] = filename
                    conf = float(box.conf[0])
                    cursor.execute("""
                        INSERT INTO info
                        (Type, Plate_Number, Screenshot, Date, Confidence)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        state[track_id]["Type"],
                        state[track_id]["Plate_Number"],
                        state[track_id]["Screenshot"],
                        state[track_id]["Date"],
                        conf
                    ))
                    conn.commit()
                    state[track_id]["Saved"] = True
        else:
            timers.pop(track_id, None)
    cv2.imshow("Webcam",frame)
    if cv2.waitKey(1) & 0xff == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()