from flask import Flask, render_template, request, redirect, url_for , jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import not_
from datetime import datetime
import psycopg2 
  
app = Flask(__name__) 
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:password@localhost/student_usth"
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


class Face(db.Model):
    __tablename__ = 'FACE'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('STUDENT.id'), nullable=False)
    url = db.Column(db.Text, nullable=False)

    # Relationships
    student = db.relationship('Student', backref=db.backref('faces', lazy=True))

    def __repr__(self):
        return f'<Face {self.url}>'


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

    def __init__(self, student_id, subject_id, class_name ,date ,status ):
        self.student_id = student_id
        self.subject_id = subject_id
        self.class_id = class_name
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


#subjects and classes of subjects
# @app.route('/')
# def home():
#     classes = Class.query.all()
#     subjects = Subject.query.all()
#     subjectClasses = SubjectClass.query.all()
#     return render_template('home.html', subjects = subjects, subjectClasses = subjectClasses, classes=classes)

#subject list
@app.route('/')
def subject():
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
        db.session.delete(class_to_delete)
        db.session.commit()
        return redirect('/')
    except:
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
            return 'There was an issue updating your task'

    else:
        return render_template('edit_subject.html', subject_to_edit=subject_to_edit)

#delete subject
@app.route('/subject/delete/<id>')
def delete_subject(id):
    subject_to_delete = Subject.query.get_or_404(id)

    try:
        db.session.delete(subject_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'There was a problem deleting that subject'


#class list
@app.route('/class')
def classes():
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
            return 'There was an issue updating your task'

    else:
        return render_template('edit_class.html', class_to_edit=class_to_edit)

#delete class
@app.route('/class/delete/<id>')
def delete_class(id):
    class_to_delete = Class.query.get_or_404(id)

    try:
        db.session.delete(class_to_delete)
        db.session.commit()
        return redirect('/class')
    except:
        return 'There was a problem deleting that subject'
    
#student list of a class
@app.route('/<int:class_id>/student_list')
def class_student_list(class_id):
    classes = Class.query.filter_by(id = class_id).first()
    students = Student.query.filter_by(class_id = class_id).order_by(Student.id).all()
    return render_template('class_student_list.html', students = students, classes = classes)

#add student
@app.route('/<class_id>/student_list/add_student', methods = ['POST', 'GET'])
def add_student(class_id):
    if request.method == 'POST':
        student_id = request.form['student_id']
        student_name = request.form['student_name']
        date_of_birth = request.form['date_of_birth']
        class_id = class_id
        new_student = Student(student_id = student_id, student_name = student_name, date_of_birth = date_of_birth, class_id =class_id)

        try:
            db.session.add(new_student)
            db.session.commit()
            return redirect(f'/{class_id}/student_list')
        except:
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
        Face.query.filter_by(student_id=id).delete()
        db.session.delete(student_to_delete)
        db.session.commit()
        return redirect(f'/{class_id}/student_list')
    except:
        return 'There was a problem deleting that subject'


#student list of a class in a subject
@app.route('/<int:subject_id>/<int:class_id>/student_list')
def subject_student_list(subject_id, class_id):

    classes = Class.query.filter_by(id = class_id).first()
    subject = Subject.query.filter_by(id = subject_id).first()
    students = Student.query.filter_by(class_id = class_id).order_by(Student.id).all()
    attendance_dates = db.session.query(AttendanceRecord.date).distinct().order_by(AttendanceRecord.date).all()
    dates = [date[0] for date in attendance_dates]
    attendanceRecords = AttendanceRecord.query.filter_by(subject_id = subject_id, class_id = class_id).all()
    attendanceSummaries = AttendanceSummary.query.filter_by(subject_id = subject_id, class_id = class_id).all()
    return render_template('subject_student_list.html', students = students, subject = subject, attendanceRecords =attendanceRecords, attendanceSummaries = attendanceSummaries, dates = dates, classes = classes)


#check attendance
@app.route('/check_attendance')
def check_attendance():
    return render_template('check_attendance.html')

@app.route('/status/<student_id>', methods=['GET'])
def get_attendance_status(student_id):
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
     .filter(AttendanceRecord.student_id == student.id)

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
            "date": record.date.strftime('%Y-%m-%d'),
            "status": record.status
        })

    return jsonify({"student_name": student.student_name, "attendance_records": records})

#api
@app.route('/checking', methods=['POST'])
def checking():
    data = request.json
    s_id = data.get('id')
    print(s_id)

    st = Student.query.filter(Student.student_id==s_id).first()
    if not st:
        return "No student"

    s_subject = data.get('subject')
    sj = Subject.query.filter(Subject.subject_name==s_subject).first()
    if not sj:
        return "No subject"
    
    s_class = data.get('class')
    sc = Class.query.filter(Class.class_name==s_class).first()

    if not sc:
        return "No class"
    
    dt = str(datetime.now())
    date = dt[:10:]

    new_record = AttendanceRecord(int(st.id),int(sj.id),int(sc.id),date,"Present")
    print(new_record.student_id)
    try:
        db.session.add(new_record)
        db.session.commit()
        print("Success")
        return "Success"
    except:
        print("False")

        return "False"
    

if __name__ == '__main__':
    app.run(debug=True)





