from flask import Flask, jsonify, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:hai2652003@localhost/student_database_new'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Student(db.Model):
    __tablename__ = "STUDENT"
    
    student_id = db.Column(db.String(255), primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    class_name = db.Column(db.String(255), db.ForeignKey("CLASS.class_name"), nullable=False)
    
    faces = db.relationship('Face', backref='student', lazy=True)
    attendance_records = db.relationship('AttendanceRecord', backref='student', lazy=True)
    attendance_summaries = db.relationship('AttendanceSummary', backref='student', lazy=True)

class Class(db.Model):
    __tablename__ = "CLASS"
    
    class_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_name = db.Column(db.String(255), unique=True, nullable=False)
    
    students = db.relationship('Student', backref='class', lazy=True)
    attendance_records = db.relationship('AttendanceRecord', backref='class', lazy=True)
    attendance_summaries = db.relationship('AttendanceSummary', backref='class', lazy=True)
    subjects = db.relationship('SubjectClass', backref='class', lazy=True)

class Subject(db.Model):
    __tablename__ = "SUBJECT"
    
    subject_id = db.Column(db.String(255), primary_key=True, unique=True, nullable=False)
    subject_name = db.Column(db.String(255), nullable=False)
    
    attendance_records = db.relationship('AttendanceRecord', backref='subject', lazy=True)
    attendance_summaries = db.relationship('AttendanceSummary', backref='subject', lazy=True)
    classes = db.relationship('SubjectClass', backref='subject', lazy=True)

class Face(db.Model):
    __tablename__ = "FACE"
    
    face_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(255), db.ForeignKey("STUDENT.student_id"), nullable=False)
    url = db.Column(db.Text, nullable=False)

class AttendanceRecord(db.Model):
    __tablename__ = "ATTENDANCE_RECORD"
    
    attendance_record_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_name = db.Column(db.String(255), db.ForeignKey("CLASS.class_name"), nullable=False)
    subject_id = db.Column(db.String(255), db.ForeignKey("SUBJECT.subject_id"), nullable=False)
    student_id = db.Column(db.String(255), db.ForeignKey("STUDENT.student_id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(255), nullable=False)
    def __init__(self, student_id, subject_id, class_name ,date ,status ):
        self.student_id = student_id
        self.subject_id = subject_id
        self.class_name = class_name
        self.date = date
        self.status = status

class AttendanceSummary(db.Model):
    __tablename__ = "ATTENDANCE_SUMMARY"
    
    attendance_summary_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_name = db.Column(db.String(255), db.ForeignKey("CLASS.class_name"), nullable=False)
    subject_id = db.Column(db.String(255), db.ForeignKey("SUBJECT.subject_id"), nullable=False)
    student_id = db.Column(db.String(255), db.ForeignKey("STUDENT.student_id"), nullable=False)
    total_absent = db.Column(db.Integer, nullable=False)
    total_present = db.Column(db.Integer, nullable=False)

    

class SubjectClass(db.Model):
    __tablename__ = 'subject_class'

    class_name = db.Column(db.String(255), db.ForeignKey('CLASS.class_name'), primary_key=True, nullable=False)
    subject_id = db.Column(db.String(255), db.ForeignKey('SUBJECT.subject_id'), primary_key=True, nullable=False)

    class_rel = db.relationship('Class', back_populates='subjects')
    subject_rel = db.relationship('Subject', back_populates='classes')



@app.route('/status/<student_id>', methods=['GET'])
def get_attendance_status(student_id):
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        return jsonify({"message": "Student not found."}), 404

    query = db.session.query(
        AttendanceRecord.attendance_record_id,
        AttendanceRecord.class_name,
        AttendanceRecord.student_id,
        AttendanceRecord.subject_id,
        Subject.subject_name,
        AttendanceRecord.date,
        AttendanceRecord.status
    ).join(Subject, AttendanceRecord.subject_id == Subject.subject_id).filter(
        AttendanceRecord.student_id == student_id
    )

    attendance_records = query.all()
    if not attendance_records:
        return jsonify({"student_name": student.name, "message": "No attendance records found for student."}), 404

    records = []
    for record in attendance_records:
        records.append({
            "attendance_record_id": record.attendance_record_id,
            "class_name": record.class_name,
            "student_id": record.student_id,
            "subject_id": record.subject_id,
            "subject_name": record.subject_name,
            "date": record.date.strftime('%Y-%m-%d %H:%M:%S'),
            "status": record.status
        })

    return jsonify({"student_name": student.name, "attendance_records": records})


@app.route('/')
def home():
    subjects = Subject.query.all()
    subjectClasses = SubjectClass.query.all()
    return render_template('home.html', subjects = subjects, subjectClasses = subjectClasses)

@app.route('/subject')
def subject():
    subjects = Subject.query.all()
    return render_template('subject_list.html', subjects = subjects)

@app.route('/class')
def classes():
    classes = Class.query.all()
    return render_template('class_list.html', classes = classes)


@app.route('/check_attendance')
def check_attendance():
    return render_template('check_attendance.html')

@app.route('/student_list/<subject_id>/<class_name>')
def student_list(subject_id, class_name):

    subject = Subject.query.filter_by(subject_id=subject_id).first()
    students = Student.query.filter_by(class_name = class_name).all()
    attendance_dates = db.session.query(AttendanceRecord.date).distinct().order_by(AttendanceRecord.date).all()
    attendanceRecords = AttendanceRecord.query.filter_by(subject_id = subject_id, class_name = class_name).all()
    attendanceSummaries = AttendanceSummary.query.filter_by(subject_id = subject_id, class_name = class_name).all()
    return render_template('student_list.html', students = students, subject = subject, attendanceRecords =attendanceRecords, attendanceSummaries = attendanceSummaries, attendance_dates = attendance_dates, className = class_name)

@app.route('/subject/add_subject', methods = ['POST', 'GET'])  
def add_subject():
    if request.method == 'POST':
        subject_id = request.form['subject_id']
        subject_name = request.form['subject_name']
        new_subject = Subject(subject_id, subject_name)

        try:
            db.session.add(new_subject)
            db.session.commit()
            return redirect('/subject/add_subject')
        except:
            return redirect('/subject/add_subject')

    else:
        return render_template('add_subject.html')

@app.route('/class/add_class', methods = ['POST', 'GET'])
def add_class():
    if request.method == 'POST':
        class_name = request.form['class_name']
        new_class = Class(class_name)

        try:
            db.session.add(new_class)
            db.session.commit()
            return redirect('/class/add_class')
        except:
            return redirect('/class/add_class')

    else:
        return render_template('add_class.html')

@app.route('/student_list/<subject_id>/<class_name>/add_student', methods = ['POST', 'GET'])
def add_student(subject_id, class_name):
    if request.method == 'POST':
        student_id = request.form['student_id']
        student_name = request.form['student_name']
        date_of_birth = request.form['date_of_birth']
        class_name = class_name
        new_student = Student(student_id, student_name, date_of_birth, class_name)

        try:
            db.session.add(new_student)
            db.session.commit()
            return redirect('/student_list/<subject_id>/<class_name>/add_student')
        except:
            return redirect('/student_list/<subject_id>/<class_name>/add_student')

    else:
        subject = Subject.query.filter_by(subject_id=subject_id).first()
        return render_template('add_student.html', subject = subject, className = class_name)

@app.route('/checking', methods=['POST'])
def checking():
    data = request.json
    s_id = data.get('id')
    print(s_id)

    st = Student.query.filter(Student.student_id==s_id).first()
    if not st:
        return "No student"

    s_subject = data.get('subject')
    s_class = data.get('class')
    date = "2024-01-02"

    new_record = AttendanceRecord(s_id,s_subject,s_class,date,"Present")
    try:
        db.session.add(new_record)
        db.session.commit()
        print("Success")
        return "Success"
    except:
        print("False")

        return "False"
    
@app.route('/smt')
def home2():
    return render_template('attendance.html')


if __name__ == '__main__':
    app.run(debug=True)
