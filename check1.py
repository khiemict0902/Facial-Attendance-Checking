import cv2,requests
from ultralytics import YOLO
from deepface import DeepFace

# Load the YOLOv8 model
model = YOLO('./pc1.pt')

# Path to DeepFace database
db_path = "./db2"

list_checked = []
list_subjects = ['math','it']

def check_att(name):
    if name in list_checked:
        return 
    else:
        list_checked.append(name)
        url = "http://127.0.0.1:5000/checking"
        checkings = {"id": f'{name}',
                     "subject": 1,
                     "class": 1}
        requests.post(url, json=checkings)

# Initialize the webcam
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 960)

frame_reg = 30
frame_count = 0


while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # YOLOv8 detection
    results = model(frame)

    # Verify if detections are made
    if results and len(results[0].boxes) > 0:
        for r in results:
            for box, conf in zip(r.boxes.xyxy, r.boxes.conf):
                # Convert box to integer coordinates
                x1, y1, x2, y2 = map(int, box)

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                # Only proceed if the confidence is above a threshold (e.g., 0.5)
                if frame_count % frame_reg ==0 and conf > 0.8:
                    # print(f"Bounding Box: {(x1, y1, x2, y2)}, Confidence: {conf}")

                    # Crop the detected face
                    face = frame[y1:y2, x1:x2]

                    try:
                        # Use DeepFace for recognition
                        predictions = DeepFace.find(face, db_path=db_path, enforce_detection=False, model_name='Facenet512',anti_spoofing=False,threshold=0.4,detector_backend='skip')
                        print(predictions)
                        # Access the first DataFrame if results are found
                        if predictions and not predictions[0].empty:
                            # Extract and format the label
                            name = predictions[0]['identity'][0].split('/')[-2]  # Assuming db_path is like ./db/person1/img1.jpg
                            print(f"Recognized: {name}")
                            check_att(name)

                            # Draw bounding box and label
                            cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

                    except Exception as e:
                        print(f"DeepFace error: {e}")

    # Display the frame
    cv2.imshow('Webcam Face Recognition', frame)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    frame_count+=1
    
cap.release()
cv2.destroyAllWindows()

