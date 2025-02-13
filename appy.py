from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import requests
from ultralytics import YOLO
from deepface import DeepFace
import cv2
from datetime import datetime
import numpy as np
import base64
from flask_sqlalchemy import SQLAlchemy
import threading

# Flask app initialization
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:hai2652003@localhost/student_usth"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")  # Enable SocketIO with CORS

# Global variables
selected_subject = None
recognition_active = False
selected_class = None
model = YOLO('./pc1.pt')
db_path = "./db2"
list_checked = []
stop_event = threading.Event()
frame_counter = 0  # Counter to track frames


class Student(db.Model):
    __tablename__ = 'STUDENT'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(255), nullable=False, unique=True)
    student_name = db.Column(db.String(255), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('CLASS.id'), nullable=False)

    # Relationships
    class_ = db.relationship('Class', backref=db.backref('students', lazy=True))

    def __repr__(self):
        return f'<Student {self.student_name}>'


# Database models
class Class(db.Model):
    __tablename__ = 'CLASS'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_name = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<Class {self.class_name}>'


class Subject(db.Model):
    __tablename__ = 'SUBJECT'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subject_name = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<Subject {self.subject_name}>'


class SubjectClass(db.Model):
    __tablename__ = 'SUBJECT_CLASS'
    class_id = db.Column(db.Integer, db.ForeignKey('CLASS.id'), primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('SUBJECT.id'), primary_key=True)

    # Relationships
    class_ = db.relationship('Class', backref=db.backref('subject_classes', lazy=True))
    subject = db.relationship('Subject', backref=db.backref('subject_classes', lazy=True))

    def __repr__(self):
        return f'<SubjectClass {self.class_id} {self.subject_id}>'


# Utility function to check attendance
def check_att(name, s, c):
    """Send attendance to the server and notify clients via WebSocket."""
    if name not in list_checked:
        list_checked.append(name)
        print(f"Attendance checked for: {name}, {s}, {c}")
        url = "http://127.0.0.1:5000/checking"

        st = Student.query.filter(Student.student_id == name).first()
        st_name = st.student_name
        if not st:
            print("no st")
        
        try:
            requests.post(url, json={"id": name, "subject": s, "class": c})
        except requests.RequestException as e:
            print(f"Error sending attendance: {e}")
        
        dt = str(datetime.now())
        dt = dt[:19:]
        # Emit the name to all connected clients
        socketio.emit('attendance_checked', {'name': name, 'subject': s, 'class': c, 'dt':dt, 'st':st_name})


@app.route('/')
def index():
    """Render the homepage."""
    try:
        classes = Class.query.all()
        subjects = Subject.query.all()
    except Exception as e:
        print(f"Error fetching data from the database: {e}")
        classes, subjects = [], []
    return render_template('checking_web.html', classes=classes, subjects=subjects)


@app.route('/select_subject', methods=['POST'])
def select_subject():
    """Handle subject selection."""
    global selected_subject, recognition_active, selected_class
    data = request.get_json()
    selected_subject = data.get('subject')
    selected_class = data.get('class')
    recognition_active = True
    stop_event.clear()  # Ensure the stop event is reset
    return jsonify({"message": "Recognition started", "subject": selected_subject, "class": selected_class})


@app.route('/process_frame', methods=['POST'])
def process_frame():
    """Process incoming webcam frame."""
    global recognition_active, selected_subject, selected_class, frame_counter

    if not recognition_active:
        return jsonify({"message": "Recognition stopped"})

    try:
        data = request.get_json()
        frame_data = base64.b64decode(data['frame'].split(',')[1])
        frame = np.frombuffer(frame_data, dtype=np.uint8)
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
    
        frame_counter += 1

        if frame_counter % 20 == 0:  # Process every 20th frame
            results = model(frame)
            if results and len(results[0].boxes) > 0:
                for r in results:
                    for box, conf in zip(r.boxes.xyxy, r.boxes.conf):
                        if conf > 0.8:
                            x1, y1, x2, y2 = map(int, box)
                            face = frame[y1:y2, x1:x2]

                            try:
                                predictions = DeepFace.find(
                                    face, db_path=db_path, enforce_detection=False,
                                    model_name='Facenet512', detector_backend='skip', threshold=0.36
                                )
                                if predictions and not predictions[0].empty:
                                    name = predictions[0]['identity'][0].split('\\')[-2]
                                    check_att(name, selected_subject, selected_class)
                                    print(f"Recognized: {name}")
                            except Exception as e:
                                print(f"Error during face recognition: {e}")
    except Exception as e:
        print(f"Error processing frame: {e}")

    return jsonify({"message": "Frame processed"})


@app.route('/stop_recognition', methods=['POST'])
def stop_recognition():
    """Stop the recognition process."""
    global recognition_active
    recognition_active = False
    stop_event.set()  # Signal threads to stop
    list_checked.clear()
    return jsonify({"message": "Recognition stopped"})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Initialize the database tables
    socketio.run(app, debug=True, port=5555)
