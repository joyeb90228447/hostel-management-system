import mysql.connector

# Directly connecting using your production live parameters
db = mysql.connector.connect(
    host="yamanote.proxy.rlwy.net",
    user="root",
    password="LbfrGLXkJqOesqWowVbdPpPEWbehgMYq",
    database="railway",
    port=41887
)

cursor = db.cursor()

print("Force clean existing data maps...")
cursor.execute("DROP TABLE IF EXISTS attendance;")
cursor.execute("DROP TABLE IF EXISTS notices;")
cursor.execute("DROP TABLE IF EXISTS fees;")
cursor.execute("DROP TABLE IF EXISTS complaints;")
cursor.execute("DROP TABLE IF EXISTS students;")
cursor.execute("DROP TABLE IF EXISTS rooms;")

print("Building modern schemas...")

cursor.execute("""
CREATE TABLE rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_no VARCHAR(50) UNIQUE NOT NULL,
    capacity INT NOT NULL,
    occupied INT DEFAULT 0,
    status VARCHAR(50) DEFAULT 'Available'
)
""")

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

cursor.execute("""
CREATE TABLE complaints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_name VARCHAR(100) NOT NULL,
    complaint TEXT NOT NULL,
    date_raised TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# 🔥 FIXED DYNAMIC ENGINE STRUCTURE
cursor.execute("""
CREATE TABLE fees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_name VARCHAR(100) NOT NULL,
    total_amount INT NOT NULL DEFAULT 0,
    paid_amount INT NOT NULL DEFAULT 0,
    remaining_amount INT NOT NULL DEFAULT 0,
    status VARCHAR(50) DEFAULT 'Pending'
)
""")

cursor.execute("""
CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_name VARCHAR(100) NOT NULL,
    date VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL
)
""")

cursor.execute("""
CREATE TABLE notices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    date_posted TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

db.commit()

# Insert an initial sample room to prevent empty tables view
cursor.execute("INSERT INTO rooms (room_no, capacity, occupied, status) VALUES ('101', 4, 0, 'Available')")
db.commit()

cursor.close()
db.close()
print("🎉 SUCCESS: All cloud tables recreated with custom calculation columns!")