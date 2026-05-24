import mysql.connector

# Apne Railway credentials yahan daalein
db = mysql.connector.connect(
    host="yamanote.proxy.rlwy.net",  # Apna actual host daalein
    user="root",
    password="LbfrGLXkJqOesqWowVbdPpPEWbehgMYq", # Apna password daalein
    database="railway",
    port=41887 # Apna actual port daalein
)

cursor = db.cursor()

# 1. Rooms Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_number VARCHAR(10) UNIQUE NOT NULL,
    capacity INT NOT NULL,
    available_beds INT NOT NULL
)
""")
print("Rooms table checked/created.")

# 2. Students Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    contact VARCHAR(15),
    room_id INT,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL
)
""")
print("Students table checked/created.")

# 3. Fees Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS fees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    amount DECIMAL(10,2) NOT NULL,
    payment_status VARCHAR(50) DEFAULT 'Pending',
    payment_date DATE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
)
""")
print("Fees table checked/created.")

# 4. Complaints Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS complaints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    description TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'Pending',
    date_raised TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
)
""")
print("Complaints table checked/created.")

db.commit()
cursor.close()
db.close()

print("🎉 Saari tables successfully create ho gayi hain!")