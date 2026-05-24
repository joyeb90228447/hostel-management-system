from flask import Flask, render_template, request, redirect, session
import mysql.connector

from reportlab.pdfgen import canvas
from flask import send_file

app = Flask(__name__)
app.secret_key = "hostel_secret_key"

# MySQL Connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root2006",   # yaha apna password likho
    database="hostel_db",
    port=3307
)

cursor = db.cursor()

# Home Page
@app.route('/')
def home():

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints")
    total_complaints = cursor.fetchone()[0]

    return render_template(
        'index.html',
        total_students=total_students,
        total_complaints=total_complaints
    )

# Registration
@app.route('/register', methods=['POST'])
def register():

    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    room = request.form['room']
    password = request.form['password']

    sql = """
    INSERT INTO students
    (name, email, phone, room_no, password)
    VALUES (%s, %s, %s, %s, %s)
    """

    values = (name, email, phone, room, password)

    cursor.execute(sql, values)
    db.commit()

    return "Student Registered Successfully"
# View Students

@app.route('/view')
def view_students():

    cursor.execute("SELECT * FROM students")

    students = cursor.fetchall()

    return render_template('view_students.html', students=students)
# Delete Student

@app.route('/delete/<int:id>')
def delete_student(id):

    sql = "DELETE FROM students WHERE id=%s"

    cursor.execute(sql, (id,))

    db.commit()

    return redirect('/view')
# Complaint Page

@app.route('/complaint')
def complaint_page():
    return render_template('complaint.html')


# Save Complaint

@app.route('/save_complaint', methods=['POST'])
def save_complaint():

    student_name = request.form['student_name']
    complaint = request.form['complaint']

    sql = """
    INSERT INTO complaints
    (student_name, complaint)
    VALUES (%s, %s)
    """

    values = (student_name, complaint)

    cursor.execute(sql, values)

    db.commit()

    return "Complaint Submitted Successfully"
# Edit Student Page

@app.route('/edit/<int:id>')
def edit_student(id):

    sql = "SELECT * FROM students WHERE id=%s"

    cursor.execute(sql, (id,))

    student = cursor.fetchone()

    return render_template(
        'edit_student.html',
        student=student
    )


# Update Student

@app.route('/update/<int:id>', methods=['POST'])
def update_student(id):

    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    room = request.form['room']

    sql = """
    UPDATE students
    SET name=%s,
        email=%s,
        phone=%s,
        room_no=%s
    WHERE id=%s
    """

    values = (name, email, phone, room, id)

    cursor.execute(sql, values)

    db.commit()

    return redirect('/view')
# Student Login Page

@app.route('/login')
def login_page():
    return render_template('login.html')


# Student Login

@app.route('/student_login', methods=['POST'])
def student_login():

    email = request.form['email']
    password = request.form['password']

    sql = """
    SELECT * FROM students
    WHERE email=%s AND password=%s
    """

    values = (email, password)

    cursor.execute(sql, values)

    student = cursor.fetchone()

    if student:

        session['student_name'] = student[1]

        return redirect(
    f'/profile/{student[2]}'
)

    else:

        return "Invalid Email or Password"
    # Search Student

@app.route('/search', methods=['POST'])
def search_student():

    keyword = request.form['keyword']

    sql = """
    SELECT * FROM students
    WHERE name LIKE %s
    """

    value = ("%" + keyword + "%",)

    cursor.execute(sql, value)

    students = cursor.fetchall()

    return render_template(
        'view_students.html',
        students=students
    )
# Fee Page

@app.route('/fees')
def fees_page():

    cursor.execute("SELECT * FROM fees")

    fees = cursor.fetchall()

    return render_template(
        'fees.html',
        fees=fees
    )


# Add Fee

@app.route('/add_fee', methods=['POST'])
def add_fee():

    student_name = request.form['student_name']

    amount = request.form['amount']

    status = request.form['status']

    sql = """
    INSERT INTO fees
    (student_name, amount, status)
    VALUES (%s, %s, %s)
    """

    values = (student_name, amount, status)

    cursor.execute(sql, values)

    db.commit()

    return redirect('/fees')
# =========================
# ADMIN LOGIN
# =========================

@app.route('/admin')
def admin_page():
    return render_template('admin_login.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin123':

            return redirect('/dashboard')

        else:

            return "Invalid Admin Login"

    return render_template('admin_login.html')


# =========================
# DASHBOARD
# =========================

@app.route('/dashboard')
def dashboard():

    cursor.execute(
        "SELECT COUNT(*) FROM students"
    )

    total_students = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM complaints"
    )

    total_complaints = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM rooms WHERE status='Available'"
    )

    available_rooms = cursor.fetchone()[0]

    return render_template(

        'dashboard.html',

        total_students=total_students,

        total_complaints=total_complaints,

        available_rooms=available_rooms

    )


# =========================
# ROOMS
# =========================

@app.route('/rooms')
def rooms():

    cursor.execute("SELECT * FROM rooms")

    rooms = cursor.fetchall()

    return render_template(
        'rooms.html',
        rooms=rooms
    )


@app.route('/add_room', methods=['POST'])
def add_room():

    room_no = request.form['room_no']
    capacity = request.form['capacity']
    occupied = request.form['occupied']

    if int(occupied) >= int(capacity):
        status = "Full"
    else:
        status = "Available"

    sql = """
    INSERT INTO rooms
    (room_no, capacity, occupied, status)
    VALUES (%s, %s, %s, %s)
    """

    values = (
        room_no,
        capacity,
        occupied,
        status
    )

    cursor.execute(sql, values)

    db.commit()

    return redirect('/rooms')


# =========================
# ATTENDANCE
# =========================

@app.route('/attendance')
def attendance():

    cursor.execute(
        "SELECT * FROM attendance"
    )

    attendance = cursor.fetchall()

    return render_template(
        'attendance.html',
        attendance=attendance
    )


@app.route('/add_attendance', methods=['POST'])
def add_attendance():

    student_name = request.form['student_name']
    date = request.form['date']
    status = request.form['status']

    sql = """
    INSERT INTO attendance
    (student_name, date, status)
    VALUES (%s, %s, %s)
    """

    values = (
        student_name,
        date,
        status
    )

    cursor.execute(sql, values)

    db.commit()

    return redirect('/attendance')


# =========================
# NOTICE BOARD
# =========================

@app.route('/notice')
def notice():

    cursor.execute("SELECT * FROM notices")

    notices = cursor.fetchall()

    return render_template(
        'notice.html',
        notices=notices
    )


@app.route('/add_notice', methods=['POST'])
def add_notice():

    title = request.form['title']
    message = request.form['message']

    sql = """
    INSERT INTO notices
    (title, message)
    VALUES (%s, %s)
    """

    values = (title, message)

    cursor.execute(sql, values)

    db.commit()

    return redirect('/notice')
# =========================
# STUDENT PROFILE
# =========================

@app.route('/profile/<email>')
def profile(email):

    sql = """
    SELECT * FROM students
    WHERE email=%s
    """

    cursor.execute(sql, (email,))

    student = cursor.fetchone()

    fee_sql = """
    SELECT * FROM fees
    WHERE student_name=%s
    """

    cursor.execute(
        fee_sql,
        (student[1],)
    )

    fees = cursor.fetchall()

    attendance_sql = """
    SELECT * FROM attendance
    WHERE student_name=%s
    """

    cursor.execute(
        attendance_sql,
        (student[1],)
    )

    attendance = cursor.fetchall()

    return render_template(
        'profile.html',
        student=student,
        fees=fees,
        attendance=attendance
    )
# =========================
# EXPORT PDF
# =========================

@app.route('/pdf')
def export_pdf():

    cursor.execute("SELECT * FROM students")

    students = cursor.fetchall()

    pdf_file = "students_report.pdf"

    c = canvas.Canvas(pdf_file)

    c.setFont("Helvetica-Bold", 18)

    c.drawString(
        180,
        800,
        "Hostel Student Report"
    )

    y = 750

    c.setFont("Helvetica", 12)

    for student in students:

        text = f"""
ID: {student[0]}
Name: {student[1]}
Email: {student[2]}
Phone: {student[3]}
Room: {student[4]}
"""

        c.drawString(50, y, text)

        y -= 60

        if y < 100:

            c.showPage()

            y = 750

    c.save()

    return send_file(
        pdf_file,
        as_attachment=True
    )
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)