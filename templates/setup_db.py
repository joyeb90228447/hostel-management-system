import mysql.connector

# Connecting to your Railway instance
db = mysql.connector.connect(
    host="yamanote.proxy.rlwy.net",
    user="root",
    password="LbfrGLXkJqOesqWowVbdPpPEWbehgMYq",
    database="railway",
    port=41887
)

cursor = db.cursor()

print("Dropping old tables to clean up structural mismatches...")
# Drop existing tables to clear conflicting columns safely
cursor.execute("DROP TABLE IF EXISTS attendance;")
cursor.execute("DROP TABLE IF EXISTS notices;")
cursor.execute("DROP TABLE IF EXISTS fees;")
cursor.execute("DROP TABLE IF EXISTS complaints;")
cursor.execute("DROP TABLE IF EXISTS students;")
cursor.execute("DROP TABLE IF EXISTS rooms;")

print("Creating fresh, synchronized tables...")

# 1. Rooms Table (Now contains 'status' and 'occupied'!)
cursor.execute("""
CREATE TABLE rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_no VARCHAR(50) UNIQUE NOT NULL,
    capacity INT NOT NULL,
    occupied INT DEFAULT 0,
    status VARCHAR(50) DEFAULT 'Available'
)
""")
print("- Rooms table created successfully.")

# 2. Students Table
cursor.execute("""
CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    room_no VARCHAR(50),
    password VARCHAR(255) NOT NULL
)
""")
print("- Students table created successfully.")

# 3. Complaints Table
cursor.execute("""
CREATE TABLE complaints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_name VARCHAR(100) NOT NULL,
    complaint TEXT NOT NULL,
    date_raised TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
print("- Complaints table created successfully.")

# 4. Fees Table
cursor.execute("""
CREATE TABLE fees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_name VARCHAR(100) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'Pending'
)
""")
print("- Fees table created successfully.")

# 5. Attendance Table
cursor.execute("""
CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_name VARCHAR(100) NOT NULL,
    date VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL
)
""")
print("- Attendance table created successfully.")

# 6. Notices Table
cursor.execute("""
CREATE TABLE notices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    date_posted TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
print("- Notices table created successfully.")

db.commit()
cursor.close()
db.close()

print("\n🎉 SUCCESS: All database tables match your app perfectly now!")