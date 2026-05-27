from flask import Flask, render_template, request, redirect, session, send_file
import mysql.connector
from reportlab.pdfgen import canvas
import os

app = Flask(__name__)
app.secret_key = "hostel_secret_key"

# ==========================================
# DATABASE RECONNECTION AUTOMATION ENGINE
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

# Initial boot connection setup
db = mysql.connector.connect(
    host=os.getenv("MYSQLHOST"),
    user=os.getenv("MYSQLUSER"),
    password=os.getenv("MYSQLPASSWORD"),
    database=os.getenv("MYSQLDATABASE"),
    port=int(os.getenv("MYSQLPORT"))
)
cursor = db.cursor(buffered=True)


# ==========================================
# CENTRAL PORTAL GATEWAY (APP OPEN SCREEN)
# ==========================================
@app.route('/')
def gateway_portal():
    return render_template('gateway.html')


# ==========================================
# AUTHENTICATION ENGINE
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
            return render_template('login.html', error="Invalid Student Credentials. Please try again.")
            
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
            return "Invalid Admin Login <br><a href='/admin'>Try Again</a>"

    return render_template('admin_login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ==========================================
# ADMINISTRATIVE ECOSYSTEM (SECURED)
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
# ADMIN-ONLY STUDENT REGISTRATION & VIEW
# ==========================================
@app.route('/register_student_page')
def register_student_page():
    if not session.get('admin_logged_in'):
        return redirect('/admin')
    return render_template('register_student.html')


@app.route('/register', methods=['POST'])
def register():
    if not session.get('admin_logged_in'):
        return redirect('/admin')

    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    room = request.form['room'].strip()
    password = request.form['password']

    local_cursor = check_db()
    
    # Check if room exists and has vacant beds before inserting student
    local_cursor.execute("SELECT capacity, occupied FROM rooms WHERE room_no = %s", (room,))
    room_data = local_cursor.fetchone()
    
    if not room_data:
        return "<h3>Error: Allocated Room Number does not exist in inventory system.</h3><br><a href='/register_student_page'>Go Back</a>"
        
    capacity = room_data[0]
    occupied = room_data[1]
    
    if occupied >= capacity:
        return "<h3>Error: Target Room is already Full! Cannot allocate more students.</h3><br><a href='/register_student_page'>Go Back</a>"

    # Step A: Save student data safely
    sql = "INSERT INTO students (name, email, phone, room_no, password) VALUES (%s, %s, %s, %s, %s)"
    local_cursor.execute(sql, (name, email, phone, room, password))
    
    # Step B: AUTOMATIC ROOM CAPACITY MINUS LOGIC (+1 Occupied)
    new_occupied = occupied + 1
    new_status = "Full" if new_occupied >= capacity else "Available"
    
    update_room_sql = "UPDATE rooms SET occupied = %s, status = %s WHERE room_no = %s"
    local_cursor.execute(update_room_sql, (new_occupied, new_status, room))
        
    db.commit()
    return redirect('/view')


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
    new_room = request.form['room'].strip()

    local_cursor = check_db()

    # Get current room information before update for logic calibration
    local_cursor.execute("SELECT room_no FROM students WHERE id=%s", (id,))
    old_room_data = local_cursor.fetchone()
    
    if old_room_data:
        old_room = old_room_data[0]
        
        # If the room number has changed, shift inventory counters automatically
        if old_room != new_room:
            # 1. De-allocate from old room (-1 Occupied)
            local_cursor.execute("SELECT capacity, occupied FROM rooms WHERE room_no = %s", (old_room,))
            old_rd = local_cursor.fetchone()
            if old_rd:
                dec_occupied = max(0, old_rd[1] - 1)
                local_cursor.execute("UPDATE rooms SET occupied=%s, status='Available' WHERE room_no=%s", (dec_occupied, old_room))
            
            # 2. Allocate to new room (+1 Occupied)
            local_cursor.execute("SELECT capacity, occupied FROM rooms WHERE room_no = %s", (new_room,))
            new_rd = local_cursor.fetchone()
            if new_rd:
                inc_occupied = new_rd[1] + 1
                new_stat = "Full" if inc_occupied >= new_rd[0] else "Available"
                local_cursor.execute("UPDATE rooms SET occupied=%s, status=%s WHERE room_no=%s", (inc_occupied, new_stat, new_room))

    sql = "UPDATE students SET name=%s, email=%s, phone=%s, room_no=%s WHERE id=%s"
    local_cursor.execute(sql, (name, email, phone, new_room, id))
    db.commit()
    return redirect('/view')


@app.route('/delete/<int:id>')
def delete_student(id):
    if not session.get('admin_logged_in'):
        return redirect('/admin')

    local_cursor = check_db()
    
    # Automated clean-up counter decrement before student profile drop
    local_cursor.execute("SELECT room_no FROM students WHERE id=%s", (id,))
    student_room = local_cursor.fetchone()
    if student_room:
        room = student_room[0]
        local_cursor.execute("SELECT occupied FROM rooms WHERE room_no = %s", (room,))
        rm_occ = local_cursor.fetchone()
        if rm_occ:
            new_occ = max(0, rm_occ[0] - 1)
            local_cursor.execute("UPDATE rooms SET occupied=%s, status='Available' WHERE room_no=%s", (new_occ, room))

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
# INVENTORY CONTROL MODULE
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
    local_cursor.execute("INSERT INTO rooms (room_no, capacity, occupied, status) VALUES (%s, %s, %s, %s)", (room_no, capacity, occupied, status))
    db.commit()
    return redirect('/rooms')


# ==========================================
# COMPLAINTS MODULE
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
    return "Complaint Submitted Successfully! <br><a href='/complaint'>Submit Another</a>"


# ==========================================
# FEES MANAGEMENT
# ==========================================
@app.route('/fees')
def fees_page():
    if not session.get('admin_logged_in'):
        return redirect('/admin')

    local_cursor = check_db()
    local_cursor.execute("SELECT * FROM fees")
    return render_template('fees.html', fees=local_cursor.fetchall())


@app.route('/add_fee', methods=['POST'])
def add_fee():
    if not session.get('admin_logged_in'):
        return redirect('/admin')

    student_name = request.form['student_name']
    total_amount = int(request.form['total_amount'])
    paid_amount = int(request.form['paid_amount'])
    
    # 🧠 Dynamic Logic Math Engine
    remaining_amount = total_amount - paid_amount
    
    # Auto-assign Status based on math results
    if remaining_amount <= 0:
        status = "Paid"
        remaining_amount = 0
    elif paid_amount > 0 and remaining_amount > 0:
        status = "Partial"
    else:
        status = "Pending"

    local_cursor = check_db()
    sql = "INSERT INTO fees (student_name, total_amount, paid_amount, remaining_amount, status) VALUES (%s, %s, %s, %s, %s)"
    local_cursor.execute(sql, (student_name, total_amount, paid_amount, remaining_amount, status))
    db.commit()
    return redirect('/fees')


# ==========================================
# ATTENDANCE PROTOCOLS
# ==========================================
@app.route('/attendance')
def attendance():
    if not session.get('admin_logged_in'):
        return redirect('/admin')

    local_cursor = check_db()
    local_cursor.execute("SELECT * FROM attendance")
    return render_template('attendance.html', attendance=local_cursor.fetchall())


@app.route('/add_attendance', methods=['POST'])
def add_attendance():
    if not session.get('admin_logged_in'):
        return redirect('/admin')

    student_name = request.form['student_name']
    date = request.form['date']
    status = request.form['status']

    local_cursor = check_db()
    local_cursor.execute("INSERT INTO attendance (student_name, date, status) VALUES (%s, %s, %s)", (student_name, date, status))
    db.commit()
    return redirect('/attendance')


# ==========================================
# COMMUNICATIONS SYSTEM (NOTICES)
# ==========================================
@app.route('/notice')
def notice():
    if not session.get('admin_logged_in'):
        return redirect('/admin')

    local_cursor = check_db()
    local_cursor.execute("SELECT * FROM notices")
    return render_template('notice.html', notices=local_cursor.fetchall())


@app.route('/add_notice', methods=['POST'])
def add_notice():
    if not session.get('admin_logged_in'):
        return redirect('/admin')

    title = request.form['title']
    message = request.form['message']

    local_cursor = check_db()
    local_cursor.execute("INSERT INTO notices (title, message) VALUES (%s, %s)", (title, message))
    db.commit()
    return redirect('/notice')


# ==========================================
# DATACLUSTER USER PROFILES
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
    return render_template('profile.html', student=student, fees=fees_data, attendance=local_cursor.fetchall())


# ==========================================
# EXPORT DATA TO PDF
# ==========================================
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


# ==========================================
# EMERGENCY CLOUD RE-INDEX MATRIX (TEMPORARY)
# ==========================================
@app.route('/force_db_sync_2026')
def force_db_sync_2026():
    local_cursor = check_db()
    try:
        # Step A: Drop conflicting old instances safely
        local_cursor.execute("DROP TABLE IF EXISTS attendance;")
        local_cursor.execute("DROP TABLE IF EXISTS notices;")
        local_cursor.execute("DROP TABLE IF EXISTS fees;")
        local_cursor.execute("DROP TABLE IF EXISTS complaints;")
        local_cursor.execute("DROP TABLE IF EXISTS students;")
        local_cursor.execute("DROP TABLE IF EXISTS rooms;")
        
        # Step B: Build synchronized table structures
        local_cursor.execute("""
        CREATE TABLE rooms (
            id INT AUTO_INCREMENT PRIMARY KEY,
            room_no VARCHAR(50) UNIQUE NOT NULL,
            capacity INT NOT NULL,
            occupied INT DEFAULT 0,
            status VARCHAR(50) DEFAULT 'Available'
        )
        """)

        local_cursor.execute("""
        CREATE TABLE students (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            phone VARCHAR(20),
            room_no VARCHAR(50),
            password VARCHAR(255) NOT NULL
        )
        """)

        local_cursor.execute("""
        CREATE TABLE fees (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_name VARCHAR(100) NOT NULL,
            total_amount INT NOT NULL DEFAULT 0,
            paid_amount INT NOT NULL DEFAULT 0,
            remaining_amount INT NOT NULL DEFAULT 0,
            status VARCHAR(50) DEFAULT 'Pending'
        )
        """)

        local_cursor.execute("""
        CREATE TABLE attendance (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_name VARCHAR(100) NOT NULL,
            date VARCHAR(50) NOT NULL,
            status VARCHAR(50) NOT NULL
        )
        """)

        local_cursor.execute("""
        CREATE TABLE complaints (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_name VARCHAR(100) NOT NULL,
            complaint TEXT NOT NULL,
            date_raised TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        local_cursor.execute("""
        CREATE TABLE notices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            message TEXT NOT NULL,
            date_posted TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Insert base allocation parameters
        local_cursor.execute("INSERT INTO rooms (room_no, capacity, occupied, status) VALUES ('101', 4, 0, 'Available')")
        
        db.commit()
        return "<h1>🎉 SUCCESS: Cloud Cluster Database Recreated Flawlessly!</h1>"
    except Exception as e:
        return f"<h1>Structural Error: {str(e)}</h1>"


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)