import os
import uuid
from flask import Flask, render_template, request, redirect, url_for , jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import not_
from deepface import DeepFace
from datetime import datetime
import psycopg2 
from werkzeug.utils import secure_filename
  
UPLOAD_FOLDER = './db2'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__) 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:hai2652003@localhost/student_usth"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
db = SQLAlchemy(app)

class Class(db.Model):
    __tablename__ = 'CLASS'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_name = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<Class {self.class_name}>'


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


class Subject(db.Model):
    __tablename__ = 'SUBJECT'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subject_name = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<Subject {self.subject_name}>'

class AttendanceRecord(db.Model):
    __tablename__ = 'ATTENDANCE_RECORD'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('STUDENT.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('CLASS.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('SUBJECT.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(255), nullable=False)

    # Relationships
    student = db.relationship('Student', backref=db.backref('attendance_records', lazy=True))
    class_ = db.relationship('Class', backref=db.backref('attendance_records', lazy=True))
    subject = db.relationship('Subject', backref=db.backref('attendance_records', lazy=True))

    def __init__(self, student_id, subject_id, class_id ,date ,status ):
        self.student_id = student_id
        self.subject_id = subject_id
        self.class_id = class_id
        self.date = date
        self.status = status

    
    def __repr__(self):
        return f'<AttendanceRecord {self.student_id} {self.status}>'


class AttendanceSummary(db.Model):
    __tablename__ = 'ATTENDANCE_SUMMARY'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_id = db.Column(db.Integer, db.ForeignKey('CLASS.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('SUBJECT.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('STUDENT.id'), nullable=False)
    total_absent = db.Column(db.Integer, nullable=False)
    total_present = db.Column(db.Integer, nullable=False)

    # Relationships
    class_ = db.relationship('Class', backref=db.backref('attendance_summaries', lazy=True))
    subject = db.relationship('Subject', backref=db.backref('attendance_summaries', lazy=True))
    student = db.relationship('Student', backref=db.backref('attendance_summaries', lazy=True))
    
    def __repr__(self):
        return f'<AttendanceSummary {self.student_id}>'


class SubjectClass(db.Model):
    __tablename__ = 'SUBJECT_CLASS'
    class_id = db.Column(db.Integer, db.ForeignKey('CLASS.id'), primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('SUBJECT.id'), primary_key=True)

    # Relationships
    class_ = db.relationship('Class', backref=db.backref('subject_classes', lazy=True))
    subject = db.relationship('Subject', backref=db.backref('subject_classes', lazy=True))

    def __repr__(self):
        return f'<SubjectClass {self.class_id} {self.subject_id}>'

#subject list
@app.route('/')
def home():
    classes = Class.query.all()
    subjects = Subject.query.order_by(Subject.id).all()
    subjectClasses = SubjectClass.query.all()
    return render_template('subject_list.html', subjects = subjects,subjectClasses = subjectClasses, classes=classes)

#add subject
@app.route('/subject/add_subject', methods = ['POST', 'GET'])  
def add_subject():
    if request.method == 'POST':
        subject_name = request.form['subject_name']
        new_subject = Subject(subject_name=subject_name) 

        try:
            db.session.add(new_subject)
            db.session.commit()
            return redirect('/')
        except:
            db.session.rollback()
            return 'There was an issue adding subject'

    else:
        return render_template('add_subject.html')
    
#add subject_class
@app.route('/subject/<int:subject_id>/add_class', methods=['POST', 'GET'])
def add_subject_class(subject_id):
    if request.method == 'POST':
        class_id = request.form.get('class_id')
        new_subject_class = SubjectClass(subject_id=subject_id, class_id=class_id)
        try:
            db.session.add(new_subject_class)
            db.session.commit() 
            return redirect('/')
        except:
            db.session.rollback()
            return 'There was an issue adding class'

    else:
        subjectClasses = SubjectClass.query.filter_by(subject_id=subject_id).all()
        subject = Subject.query.filter_by(id=subject_id).first()
        linked_class_ids = [sc.class_id for sc in subjectClasses]
        unlinked_classes = Class.query.filter(not_(Class.id.in_(linked_class_ids))).order_by(Class.id).all()
        linked_classes = Class.query.filter((Class.id.in_(linked_class_ids))).order_by(Class.id).all()
        return render_template('add_subject-class.html', subject=subject, unlinked_classes=unlinked_classes, linked_classes=linked_classes)


@app.route('/<int:subject_id>/delete/<int:id>')
def delete_subject_class(subject_id, id):
    class_to_delete = SubjectClass.query.filter_by(subject_id=subject_id, class_id=id).first()

    try:
        AttendanceSummary.query.filter_by(subject_id=subject_id, class_id=id).delete()
        AttendanceRecord.query.filter_by(subject_id=subject_id, class_id=id).delete()
        db.session.delete(class_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        db.session.rollback()
        return 'There was a problem deleting that subject'

#edit subject
@app.route('/subject/<id>/edit', methods=['GET', 'POST']) 
def update_subject(id):
    subject_to_edit = Subject.query.get_or_404(id)

    if request.method == 'POST':
        subject_to_edit.subject_name = request.form['subject_name']

        try:
            db.session.commit()
            return redirect('/')
        except:
            db.session.rollback()
            return 'There was an issue updating your task'

    else:
        return render_template('edit_subject.html', subject_to_edit=subject_to_edit)

#delete subject
@app.route('/subject/delete/<id>')
def delete_subject(id):
    subject_to_delete = Subject.query.get_or_404(id)

    try:
        AttendanceSummary.query.filter_by(subject_id=id).delete()
        AttendanceRecord.query.filter_by(subject_id=id).delete()
        SubjectClass.query.filter_by(subject_id=id).delete()
        db.session.delete(subject_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        db.session.rollback()
        return 'There was a problem deleting that subject'


#class list
@app.route('/class')
def classes_list():
    classes = Class.query.order_by(Class.id).all()
    return render_template('class_list.html', classes = classes)

#add class
@app.route('/class/add_class', methods = ['POST', 'GET'])
def add_class():
    if request.method == 'POST':
        class_name = request.form['class_name']
        new_class = Class(class_name=class_name)

        try:
            db.session.add(new_class)
            db.session.commit() 
            return redirect('/class')
        except:
            db.session.rollback()
            return 'There was an issue adding class'

    else:
        return render_template('add_class.html')

#edit class
@app.route('/class/<id>/edit', methods=['GET', 'POST'])     
def update_class(id):
    class_to_edit = Class.query.get_or_404(id)

    if request.method == 'POST':
        class_to_edit.class_name = request.form['class_name']

        try:
            db.session.commit()
            return redirect('/class')
        except:
            db.session.rollback()
            return 'There was an issue updating your task'

    else:
        return render_template('edit_class.html', class_to_edit=class_to_edit)

#delete class
@app.route('/class/delete/<id>')
def delete_class(id):
    class_to_delete = Class.query.get_or_404(id)

    try:
        AttendanceSummary.query.filter_by(class_id=id).delete()
        AttendanceRecord.query.filter_by(class_id=id).delete()
        SubjectClass.query.filter_by(class_id=id).delete()
        Student.query.filter_by(class_id=id).delete()
        db.session.delete(class_to_delete)
        db.session.commit()
        return redirect('/class')
    except:
        db.session.rollback()
        return 'There was a problem deleting that subject'
    
#student list of a class
@app.route('/<int:class_id>/student_list')
def class_student_list(class_id):
    classes = Class.query.filter_by(id = class_id).first()
    students = Student.query.filter_by(class_id = class_id).order_by(Student.student_id).all()
    return render_template('class_student_list.html', students = students, classes = classes)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#add student
@app.route('/<class_id>/student_list/add_student', methods = ['POST', 'GET'])
def add_student(class_id):
    if request.method == 'POST':
        student_id = request.form['student_id']
        student_name = request.form['student_name']
        date_of_birth = request.form['date_of_birth']
        student_images = request.files.getlist('student_images[]')

        student_folder = os.path.join(UPLOAD_FOLDER, secure_filename(student_id))
        if not os.path.exists(student_folder):
            os.makedirs(student_folder)

        uploaded_files = []

        try:
            for student_image in student_images:
                if not allowed_file(student_image.filename):
                    return f"Invalid file type for {student_image.filename}", 400

                filename = f"{uuid.uuid4().hex}_{secure_filename(student_image.filename)}"
                image_path = os.path.join(student_folder, filename)
                student_image.save(image_path)
                uploaded_files.append(image_path)
        
            DeepFace.find(img_path='./db2/BA12-010/Marmik_0.jpg',db_path=UPLOAD_FOLDER,enforce_detection=False, model_name='Facenet512',detector_backend='skip',threshold=0.36)
            new_student = Student(student_id = student_id, student_name = student_name, date_of_birth = date_of_birth, class_id = class_id)
            db.session.add(new_student)
            db.session.commit()
            return redirect(f'/{class_id}/student_list')
        except:
            db.session.rollback()
            return 'There was an issue adding student'

    else:
        classes = Class.query.filter_by(id=class_id).first()
        return render_template('add_student.html', classes = classes)
    

#edit student
@app.route('/<class_id>/student_list/<id>/edit', methods=['GET', 'POST']) 
def update_student(class_id, id):
    student_to_edit = Student.query.get_or_404(id)

    if request.method == 'POST':
        student_to_edit.student_id = request.form['student_id']
        student_to_edit.student_name = request.form['student_name']
        student_to_edit.date_of_birth = request.form['date_of_birth']

        try:
            db.session.commit()
            return redirect(f'/{class_id}/student_list')
        except:
            db.session.rollback()
            return 'There was an issue updating your task'

    else:
        return render_template('edit_student.html', student_to_edit=student_to_edit, class_id=class_id)

#delete student
@app.route('/<int:class_id>/student_list/delete/<id>')
def delete_student(class_id, id):
    student_to_delete = Student.query.get_or_404(id)

    try:
        AttendanceSummary.query.filter_by(student_id=id).delete()
        AttendanceRecord.query.filter_by(student_id=id).delete()
        db.session.delete(student_to_delete)
        db.session.commit()
        return redirect(f'/{class_id}/student_list')
    except:
        db.session.rollback()
        return 'There was a problem deleting that subject'


#student list of a class in a subject
@app.route('/<int:subject_id>/<int:class_id>/student_list')
def subject_student_list(subject_id, class_id):

    classes = Class.query.filter_by(id = class_id).first()
    subject = Subject.query.filter_by(id = subject_id).first()
    students = Student.query.filter_by(class_id = class_id).order_by(Student.student_id).all()
    attendanceRecords = AttendanceRecord.query.filter_by(subject_id = subject_id, class_id = class_id).all()
    attendanceSummaries = AttendanceSummary.query.filter_by(subject_id = subject_id, class_id = class_id).all()
    attendance_dates = [attendanceRecord.date for attendanceRecord in attendanceRecords]
    dates = [datetime.strptime(str(date), '%Y-%m-%d').strftime('%d-%m-%Y') for date in attendance_dates]
    dates = list(set(dates))
    return render_template('subject_student_list.html', students = students, subject = subject, attendanceRecords =attendanceRecords, attendanceSummaries = attendanceSummaries, dates = dates, classes = classes)


#edit status
@app.route('/<subject_id>/<class_id>/<student_id>/<id>/edit', methods=['GET', 'POST'])     
def update_status(subject_id, class_id, student_id,id):
    record_to_edit = AttendanceRecord.query.get_or_404(id)

    if request.method == 'POST':
        record_to_edit.status = request.form['record_status']

        try:
            db.session.commit()
            return redirect(f'/{subject_id}/{class_id}/student_list')
        except:
            db.session.rollback()
            return 'There was an issue updating your task'

    else:
        student = Student.query.filter_by(id = student_id).first()
        return render_template('edit_status.html', record_to_edit=record_to_edit, student = student, subject_id= subject_id, class_id = class_id)

#check attendance
@app.route('/check_attendance')
def check_attendance():
    subjects = Subject.query.all()
    return render_template('check_attendance.html', subjects = subjects)

@app.route('/status/<subject_id>/<student_id>', methods=['GET'])
def get_attendance_status(subject_id,student_id):
    # Retrieve student information
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        return jsonify({"message": "Student not found."}), 404

    # Query attendance records with related class and subject information
    query = db.session.query(
        AttendanceRecord.id,
        Class.class_name,
        AttendanceRecord.student_id,
        AttendanceRecord.subject_id,
        Subject.subject_name,
        AttendanceRecord.date,
        AttendanceRecord.status
    ).join(Class, AttendanceRecord.class_id == Class.id) \
     .join(Subject, AttendanceRecord.subject_id == Subject.id) \
     .filter(AttendanceRecord.student_id == student.id, AttendanceRecord.subject_id ==subject_id)

    attendance_records = query.all()
    if not attendance_records:
        return jsonify({"student_name": student.student_name, "message": "No attendance records found for student."}), 404

    # Format attendance records
    records = []
    for record in attendance_records:
        records.append({
            "attendance_record_id": record.id,
            "class_name": record.class_name,
            "student_id": record.student_id,
            "subject_name": record.subject_name,
            "date": record.date.strftime('%d-%m-%Y'),
            "status": record.status
        })

    return jsonify({"student_name": student.student_name, "attendance_records": records})


#api
@app.route('/checking', methods=['POST'])
def checking():
    data = request.json
    s_id = data.get('id')
    print(s_id)

    # Get student by ID
    st = Student.query.filter(Student.student_id == s_id).first()
    if not st:
        return "No student"

    # Get subject by name
    s_subject = data.get('subject')
    sj = Subject.query.filter(Subject.subject_name == s_subject).first()
    if not sj:
        return "No subject"
    
    # Get class by name
    s_class = data.get('class')
    sc = Class.query.filter(Class.class_name == s_class).first()
    if not sc:
        return "No class"
    
    # Get current date
    dt = str(datetime.now())
    date = dt[:10:]  # YYYY-MM-DD

    # Check if the attendance record already exists
    existing_record = AttendanceRecord.query.filter(
        AttendanceRecord.student_id == st.id,
        AttendanceRecord.subject_id == sj.id,
        AttendanceRecord.class_id == sc.id,
        AttendanceRecord.date == date
    ).first()

    if existing_record:
        # If record exists, update the status
        existing_record.status = "Present"
        try:
            db.session.commit()
            print("Updated existing record")
            return "Updated existing record"
        except Exception as e:
            print(f"Error updating record: {e}")
            return "Failed to update record"
    else:
        # If no record exists, create a new one
        new_record = AttendanceRecord(int(st.id), int(sj.id), int(sc.id), date, "Present")
        try:
            db.session.add(new_record)
            db.session.commit()
            print("Inserted new record")
            return "Inserted new record"
        except Exception as e:
            print(f"Error inserting record: {e}")
            return "Failed to insert record"

    

if __name__ == '__main__':
    app.run(debug=True)





