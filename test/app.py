from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/aboutUs')
def display_table():
    data = [
        {'name': 'Alice', 'age': 22},
        {'name': 'Bob', 'age': 19},
        {'name': 'Charlie', 'age': 25},
        {'name': 'David', 'age': 24},
        {'name': 'Eve', 'age': 21}
    ]
    
    return render_template('aboutUs.html', students=data)

@app.route('/SignalAndSystem')
def SignalAndSystem():
    data = [
        {'index': 1, 'name': 'Alice', 'id': 1, 'state': 'present'},
        {'index': 2, 'name': 'Bob', 'id': 2, 'state': 'absent'},
        {'index': 3, 'name': 'Charlie', 'id': 3, 'state': 'present'},
        {'index': 4, 'name': 'Diana', 'id': 4, 'state': 'present'},
        {'index': 5, 'name': 'Eve', 'id': 5, 'state': 'absent'},
        {'index': 6, 'name': 'Frank', 'id': 6, 'state': 'present'},
        {'index': 7, 'name': 'Grace', 'id': 7, 'state': 'absent'},
        {'index': 8, 'name': 'Hank', 'id': 8, 'state': 'present'},
        {'index': 9, 'name': 'Ivy', 'id': 9, 'state': 'absent'},
        {'index': 10, 'name': 'Jack', 'id': 10, 'state': 'present'},
    ]    
    return render_template('SignalAndSystem.html', students=data)



if __name__ == '__main__':
    app.run(debug=True)