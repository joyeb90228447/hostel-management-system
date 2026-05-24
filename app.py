from flask import Flask, render_template, request, redirect, session, send_file
import mysql.connector
from reportlab.pdfgen import canvas
import os

app = Flask(__name__)
app.secret_key = "hostel_secret_key"

# Database connection using environment variables
db = mysql.connector.connect(
    host=os.getenv("MYSQLHOST"),
    user=os.getenv("MYSQLUSER"),
    password=os.getenv("MYSQLPASSWORD"),
    database=os.getenv("MYSQLDATABASE"),
    port=int(os.getenv("MYSQLPORT"))
)

cursor = db.cursor(buffered=True)

# ==========================================
# HOME PAGE
# ==========================================
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

# ==========================================
# STUDENT REGISTRATION & MANAGEMENT
# ==========================================
@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    room = request.form['room']
    password = request.form['password']

    sql = """
    INSERT INTO students (name, email, phone, room_no, password)
    VALUES (%s, %s, %s, %s, %s)
    """
    values = (name, email, phone, room, password)
    cursor.execute(sql, values)
    db.commit()  # Fixed: Commits are now active to save data permanently

    return "Student Registered Successfully! <br><a href='/'>Go Home</a>"

@app.route('/view')
def view_students():
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    return render_template('view_students.html', students=students)

@app.route('/edit/<int:id>')
def edit_student(id):
    sql = "SELECT * FROM students WHERE id=%s"
    cursor.execute(sql, (id,))
    student = cursor.fetchone()
    return render_template('edit_student.html', student=student)

@app.route('/update/<int:id>', methods=['POST'])
def update_student(id):
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    room = request.form['room']

    sql = """
    UPDATE students
    SET name=%s, email=%s, phone=%s, room_no=%s
    WHERE id=%s
    """
    values = (name, email, phone, room, id)
    cursor.execute(sql, values)
    db.commit()
    return redirect('/view')

@app.route('/delete/<int:id>')
def delete_student(id):
    sql = "DELETE FROM students WHERE id=%s"
    cursor.execute(sql, (id,))
    db.commit()
    return redirect('/view')

@app.route('/search', methods=['POST'])
def search_student():
    keyword = request.form['keyword']
    sql = "SELECT * FROM students WHERE name LIKE %s"
    value = ("%" + keyword + "%",)
    cursor.execute(sql, value)
    students = cursor.fetchall()
    return render_template('view_students.html', students=students)

# ==========================================
# AUTHENTICATION (STUDENT & ADMIN)
# ==========================================
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        sql = "SELECT * FROM students WHERE email=%s AND password=%s"
        cursor.execute(sql, (email, password))
        student = cursor.fetchone()

        if student:
            session['student_name'] = student[1]
            return redirect(f'/profile/{student[2]}')
        else:
            return "Invalid Email or Password"
            
    return render_template('login.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin123':
            return redirect('/dashboard')
        else:
            return "Invalid Admin Login"

    # Updated Admin Login Route with Session Tracking
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True  # Creates login session token
            return redirect('/dashboard')
        else:
            return "Invalid Admin Login"

    return render_template('admin_login.html')

# Secured Dashboard Route
@app.route('/dashboard')
def dashboard():
    # Session Guard: Protects dashboard from unauthorized URL inputs
    if not session.get('admin_logged_in'):
        return redirect('/admin')

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints")
    total_complaints = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM rooms WHERE status='Available'")
    available_rooms = cursor.fetchone()[0]

    return render_template(
        'dashboard.html',
        total_students=total_students,
        total_complaints=total_complaints,
        available_rooms=available_rooms
    )

    sql = "INSERT INTO rooms (room_no, capacity, occupied, status) VALUES (%s, %s, %s, %s)"
    values = (room_no, capacity, occupied, status)
    cursor.execute(sql, values)
    db.commit()
    return redirect('/rooms')

# ==========================================
# COMPLAINTS SYSTEM
# ==========================================
@app.route('/complaint')
def complaint_page():
    return render_template('complaint.html')

@app.route('/save_complaint', methods=['POST'])
def save_complaint():
    student_name = request.form['student_name']
    complaint = request.form['complaint']

    sql = "INSERT INTO complaints (student_name, complaint) VALUES (%s, %s)"
    values = (student_name, complaint)
    cursor.execute(sql, values)
    db.commit()

    return "Complaint Submitted Successfully! <br><a href='/'>Go Home</a>"

# ==========================================
# FEES MANAGEMENT
# ==========================================
@app.route('/fees')
def fees_page():
    cursor.execute("SELECT * FROM fees")
    fees_data = cursor.fetchall()
    return render_template('fees.html', fees=fees_data)

@app.route('/add_fee', methods=['POST'])
def add_fee():
    student_name = request.form['student_name']
    amount = request.form['amount']
    status = request.form['status']

    sql = "INSERT INTO fees (student_name, amount, status) VALUES (%s, %s, %s)"
    values = (student_name, amount, status)
    cursor.execute(sql, values)
    db.commit()
    return redirect('/fees')

# ==========================================
# ATTENDANCE SYSTEM
# ==========================================
@app.route('/attendance')
def attendance():
    cursor.execute("SELECT * FROM attendance")
    attendance_data = cursor.fetchall()
    return render_template('attendance.html', attendance=attendance_data)

@app.route('/add_attendance', methods=['POST'])
def add_attendance():
    student_name = request.form['student_name']
    date = request.form['date']
    status = request.form['status']

    sql = "INSERT INTO attendance (student_name, date, status) VALUES (%s, %s, %s)"
    values = (student_name, date, status)
    cursor.execute(sql, values)
    db.commit()
    return redirect('/attendance')

# ==========================================
# NOTICE BOARD SYSTEM
# ==========================================
@app.route('/notice')
def notice():
    cursor.execute("SELECT * FROM notices")
    notices_data = cursor.fetchall()
    return render_template('notice.html', notices=notices_data)

@app.route('/add_notice', methods=['POST'])
def add_notice():
    title = request.form['title']
    message = request.form['message']

    sql = "INSERT INTO notices (title, message) VALUES (%s, %s)"
    values = (title, message)
    cursor.execute(sql, values)
    db.commit()
    return redirect('/notice')

# ==========================================
# STUDENT PROFILE PROFILE VISUALIZATION
# ==========================================
@app.route('/profile/<email>')
def profile(email):
    sql = "SELECT * FROM students WHERE email=%s"
    cursor.execute(sql, (email,))
    student = cursor.fetchone()

    if not student:
        return "Student profile not found."

    fee_sql = "SELECT * FROM fees WHERE student_name=%s"
    cursor.execute(fee_sql, (student[1],))
    fees_data = cursor.fetchall()

    attendance_sql = "SELECT * FROM attendance WHERE student_name=%s"
    cursor.execute(attendance_sql, (student[1],))
    attendance_data = cursor.fetchall()

    return render_template(
        'profile.html',
        student=student,
        fees=fees_data,
        attendance=attendance_data
    )

# ==========================================
# EXPORT DATA TO PDF
# ==========================================
@app.route('/pdf')
def export_pdf():
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    pdf_file = "students_report.pdf"
    c = canvas.Canvas(pdf_file)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(180, 800, "Hostel Student Report")

    y = 750
    c.setFont("Helvetica", 12)
    for student in students:
        text = f"ID: {student[0]} | Name: {student[1]} | Email: {student[2]} | Phone: {student[3]} | Room: {student[4]}"
        c.drawString(50, y, text)
        y -= 30
        if y < 100:
            c.showPage()
            y = 750

    c.save()
    return send_file(pdf_file, as_attachment=True)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)