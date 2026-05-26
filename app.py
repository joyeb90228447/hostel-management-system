from flask import Flask, render_template, request, redirect, session, send_file
import mysql.connector
from reportlab.pdfgen import canvas
import os

app = Flask(__name__)
app.secret_key = "hostel_secret_key"

# ==========================================
# CENTRALIZED AUTOMATED RECONNECTION POOL
# ==========================================
def check_db():
    global db, cursor
    try:
        db.ping(reconnect=True, attempts=3, delay=2)
    except Exception:
        db = mysql.connector.connect(
            host=os.getenv("MYSQLHOST"),
            user=os.getenv("MYSQLUSER"),
            password=os.getenv("MYSQLPASSWORD"),
            database=os.getenv("MYSQLDATABASE"),
            port=int(os.getenv("MYSQLPORT"))
        )
        cursor = db.cursor(buffered=True)
    return cursor

# Connection instantiation on core runtime load
db = mysql.connector.connect(
    host=os.getenv("MYSQLHOST"),
    user=os.getenv("MYSQLUSER"),
    password=os.getenv("MYSQLPASSWORD"),
    database=os.getenv("MYSQLDATABASE"),
    port=int(os.getenv("MYSQLPORT"))
)
cursor = db.cursor(buffered=True)


# ==========================================
# GUEST PLATFORM ENVIRONMENT
# ==========================================
@app.route('/')
def home():
    local_cursor = check_db()
    local_cursor.execute("SELECT COUNT(*) FROM students")
    total_students = local_cursor.fetchone()[0]

    local_cursor.execute("SELECT COUNT(*) FROM complaints")
    total_complaints = local_cursor.fetchone()[0]

    return render_template(
        'index.html',
        total_students=total_students,
        total_complaints=total_complaints
    )


# ==========================================
# AUTHENTICATION LOGISTICS TERMINAL
# ==========================================
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        local_cursor = check_db()
        sql = "SELECT * FROM students WHERE email=%s AND password=%s"
        local_cursor.execute(sql, (email, password))
        student = local_cursor.fetchone()

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
            session['admin_logged_in'] = True
            return redirect('/dashboard')
        else:
            return "Invalid Admin Login"

    return render_template('admin_login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ==========================================
# ADMINISTRATIVE CONTROL MATRIX (SECURE)
# ==========================================
@app.route('/dashboard')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect('/admin')

    local_cursor = check_db()
    local_cursor.execute("SELECT COUNT(*) FROM students")
    total_students = local_cursor.fetchone()[0]

    local_cursor.execute("SELECT COUNT(*) FROM complaints")
    total_complaints = local_cursor.fetchone()[0]

    local_cursor.execute("SELECT COUNT(*) FROM rooms WHERE status='Available'")
    available_rooms = local_cursor.fetchone()[0]

    return render_template(
        'dashboard.html',
        total_students=total_students,
        total_complaints=total_complaints,
        available_rooms=available_rooms
    )


# ==========================================
# CONTROL PANEL SUB-SYSTEMS
# ==========================================
@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    room = request.form['room']
    password = request.form['password']

    local_cursor = check_db()
    sql = "INSERT INTO students (name, email, phone, room_no, password) VALUES (%s, %s, %s, %s, %s)"
    local_cursor.execute(sql, (name, email, phone, room, password))
    db.commit()

    return "Student Registered Successfully! <br><a href='/'>Go Home</a>"


@app.route('/view')
def view_students():
    if not session.get('admin_logged_in'):
        return redirect('/admin')
        
    local_cursor = check_db()
    local_cursor.execute("SELECT * FROM students")
    students = local_cursor.fetchall()
    return render_template('view_students.html', students=students)


@app.route('/edit/<int:id>')
def edit_student(id):
    if not session.get('admin_logged_in'):
        return redirect('/admin')

    local_cursor = check_db()
    local_cursor.execute("SELECT * FROM students WHERE id=%s", (id,))
    student = local_cursor.fetchone()
    return render_template('edit_student.html', student=student)


@app.route('/update/<int:id>', methods=['POST'])
def update_student(id):
    if not session.get('admin_logged_in'):
        return redirect('/admin')

    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    room = request.form['room']

    local_cursor = check_db()
    sql = "UPDATE students SET name=%s, email=%s, phone=%s, room_no=%s WHERE id=%s"
    local_cursor.execute(sql, (name, email, phone, room, id))
    db.commit()
    return redirect('/view')


@app.route('/delete/<int:id>')
def delete_student(id):
    if not session.get('admin_logged_in'):
        return redirect('/admin')

    local_cursor = check_db()
    local_cursor.execute("DELETE FROM students WHERE id=%s", (id,))
    db.commit()
    return redirect('/view')


@app.route('/search', methods=['POST'])
def search_student():
    if not session.get('admin_logged_in'):
        return redirect('/admin')

    keyword = request.form['keyword']
    local_cursor = check_db()
    local_cursor.execute("SELECT * FROM students WHERE name LIKE %s", ("%" + keyword + "%",))
    students = local_cursor.fetchall()
    return render_template('view_students.html', students=students)


# ==========================================
# INVENTORY CONTROL LOGISTICS
# ==========================================
@app.route('/rooms')
def rooms():
    if not session.get('admin_logged_in'):
        return redirect('/admin')
        
    local_cursor = check_db()
    local_cursor.execute("SELECT * FROM rooms")
    rooms_data = local_cursor.fetchall()
    return render_template('rooms.html', rooms=rooms_data)


@app.route('/add_room', methods=['POST'])
def add_room():
    if not session.get('admin_logged_in'):
        return redirect('/admin')

    room_no = request.form['room_no']
    capacity = request.form['capacity']
    occupied = request.form['occupied']
    status = "Full" if int(occupied) >= int(capacity) else "Available"

    local_cursor = check_db()
    sql = "INSERT INTO rooms (room_no, capacity, occupied, status) VALUES (%s, %s, %s, %s)"
    local_cursor.execute(sql, (room_no, capacity, occupied, status))
    db.commit()
    return redirect('/rooms')


# ==========================================
# COMPLAINTS MATRIX OPERATIONS
# ==========================================
@app.route('/complaint')
def complaint_page():
    return render_template('complaint.html')


@app.route('/save_complaint', methods=['POST'])
def save_complaint():
    student_name = request.form['student_name']
    complaint = request.form['complaint']

    local_cursor = check_db()
    sql = "INSERT INTO complaints (student_name, complaint) VALUES (%s, %s)"
    local_cursor.execute(sql, (student_name, complaint))
    db.commit()
    return "Complaint Submitted Successfully! <br><a href='/'>Go Home</a>"


# ==========================================
# ECONOMIC MANAGEMENT LEDGER
# ==========================================
@app.route('/fees')
def fees_page():
    if not session.get('admin_logged_in'):
        return redirect('/admin')

    local_cursor = check_db()
    local_cursor.execute("SELECT * FROM fees")
    fees_data = local_cursor.fetchall()
    return render_template('fees.html', fees=fees_data)


@app.route('/add_fee', methods=['POST'])
def add_fee():
    if not session.get('admin_logged_in'):
        return redirect('/admin')

    student_name = request.form['student_name']
    amount = request.form['amount']
    status = request.form['status']

    local_cursor = check_db()
    sql = "INSERT INTO fees (student_name, amount, status) VALUES (%s, %s, %s)"
    local_cursor.execute(sql, (student_name, amount, status))
    db.commit()
    return redirect('/fees')


# ==========================================
# SECURITY TRACKER SYSTEM (ATTENDANCE)
# ==========================================
@app.route('/attendance')
def attendance():
    if not session.get('admin_logged_in'):
        return redirect('/admin')

    local_cursor = check_db()
    local_cursor.execute("SELECT * FROM attendance")
    attendance_data = local_cursor.fetchall()
    return render_template('attendance.html', attendance=attendance_data)


@app.route('/add_attendance', methods=['POST'])
def add_attendance():
    if not session.get('admin_logged_in'):
        return redirect('/admin')

    student_name = request.form['student_name']
    date = request.form['date']
    status = request.form['status']

    local_cursor = check_db()
    sql = "INSERT INTO attendance (student_name, date, status) VALUES (%s, %s, %s)"
    local_cursor.execute(sql, (student_name, date, status))
    db.commit()
    return redirect('/attendance')


# ==========================================
# PUBLIC NETWORK ANNOUNCEMENT SYSTEM
# ==========================================
@app.route('/notice')
def notice():
    if not session.get('admin_logged_in'):
        return redirect('/admin')

    local_cursor = check_db()
    local_cursor.execute("SELECT * FROM notices")
    notices_data = local_cursor.fetchall()
    return render_template('notice.html', notices=notices_data)


@app.route('/add_notice', methods=['POST'])
def add_notice():
    if not session.get('admin_logged_in'):
        return redirect('/admin')

    title = request.form['title']
    message = request.form['message']

    local_cursor = check_db()
    sql = "INSERT INTO notices (title, message) VALUES (%s, %s)"
    local_cursor.execute(sql, (title, message))
    db.commit()
    return redirect('/notice')


# ==========================================
# DATA CLUSTER ENDPOINTS (PROFILES & REPORT)
# ==========================================
@app.route('/profile/<email>')
def profile(email):
    local_cursor = check_db()
    local_cursor.execute("SELECT * FROM students WHERE email=%s", (email,))
    student = local_cursor.fetchone()

    if not student:
        return "Student profile not found."

    local_cursor.execute("SELECT * FROM fees WHERE student_name=%s", (student[1],))
    fees_data = local_cursor.fetchall()

    local_cursor.execute("SELECT * FROM attendance WHERE student_name=%s", (student[1],))
    attendance_data = local_cursor.fetchall()

    return render_template(
        'profile.html',
        student=student,
        fees=fees_data,
        attendance=attendance_data
    )


@app.route('/pdf')
def export_pdf():
    if not session.get('admin_logged_in'):
        return redirect('/admin')

    local_cursor = check_db()
    local_cursor.execute("SELECT * FROM students")
    students = local_cursor.fetchall()

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