from flask import Flask, render_template, request, redirect, url_for 
from flask_sqlalchemy import SQLAlchemy
import psycopg2 
  
app = Flask(__name__) 
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:hai2652003@localhost/student_attendance_db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
db = SQLAlchemy(app)

class Student2(db.Model):
    id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    date_of_birth = db.Column(db.Date)
    class_id = db.Column(db.Integer, nullable=True)

    
    def __init__(self, id, name, date_of_birth):
        self.id = id
        self.name = name
        self.date_of_birth = date_of_birth
        # self.class_id = class_id

# class Class(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     class_name = db.Column(db.String(255))
#     subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))

# class Subject(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     subject_name = db.Column(db.String(255))

# class SubjectClass(db.Model):
#     class_id = db.Column(db.Integer, db.ForeignKey('class.id'), primary_key=True)
#     subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), primary_key=True)

# class Face(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     student_id = db.Column(db.String(255), db.ForeignKey('student.id'), nullable=False)
#     url = db.Column(db.String(255))

# class AttendanceRecord(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
#     subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
#     student_id = db.Column(db.String(255), db.ForeignKey('student.id'), nullable=False)
#     date = db.Column(db.TIMESTAMP)
#     status = db.Column(db.String(255))

# class AttendanceSummary(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     student_id = db.Column(db.String(255), db.ForeignKey('student.id'), nullable=False)
#     class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
#     subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
#     total_present = db.Column(db.Integer, default=0)
#     total_absent = db.Column(db.Integer, default=0)


@app.route('/add_student', methods = ['POST', 'GET'])
def add_student():
    if request.method == 'POST':
        student_id = request.form['student_id']
        student_name = request.form['student_name']
        date_of_birth = request.form['date_of_birth']
        # class_id = request.form['class_id']
        new_student = Student2(student_id, student_name, date_of_birth)

        try:
            db.session.add(new_student)
            db.session.commit()
            return redirect('/add_student')
        except:
            return redirect('/add_student')

    else:
        return render_template('add_student.html')

@app.route('/student_list', methods = ['POST', 'GET'])
def student_list():
    students = Student2.query.all()
    return render_template('student_list.html', students = students)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)