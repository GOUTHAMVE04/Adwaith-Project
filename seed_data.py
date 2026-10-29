import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'college.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

def init_database():
    print("[1/3] Removing existing database (if any) and loading schema...")
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except PermissionError:
            print("Note: college.db is locked. Overwriting contents instead.")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    with open(SCHEMA_PATH, 'r') as f:
        conn.executescript(f.read())
    conn.commit()

    print("[2/3] Seeding users, profiles, subjects, timetable, attendance, marks, and notices...")
    cursor = conn.cursor()

    # Default Passwords
    admin_pw = generate_password_hash("admin123")
    faculty_pw = generate_password_hash("faculty123")
    student_pw = generate_password_hash("student123")
    parent_pw = generate_password_hash("parent123")

    # 1. Insert Users
    users_data = [
        ('admin', admin_pw, 'admin', 'Principal / Admin Office', 'admin@college.edu'),
        ('prof_smith', faculty_pw, 'faculty', 'Dr. John Smith', 'smith@college.edu'),
        ('prof_anjali', faculty_pw, 'faculty', 'Prof. Anjali Nair', 'anjali@college.edu'),
        ('adwaith', student_pw, 'student', 'Adwaith R.', 'adwaith@student.college.edu'),
        ('sneha', student_pw, 'student', 'Sneha Patel', 'sneha@student.college.edu'),
        ('rahul', student_pw, 'student', 'Rahul Kumar', 'rahul@student.college.edu'),
        ('parent_adwaith', parent_pw, 'parent', 'Mr. Radhakrishnan (Parent of Adwaith)', 'radhakrishnan@gmail.com')
    ]
    cursor.executemany(
        "INSERT INTO users (username, password_hash, role, full_name, email) VALUES (?, ?, ?, ?, ?)",
        users_data
    )

    # Map usernames to user_id
    cursor.execute("SELECT username, id FROM users")
    user_map = {row[0]: row[1] for row in cursor.fetchall()}

    # 2. Insert Faculty Profiles
    faculty_data = [
        ('FAC-101', 'Dr. John Smith', 'Electronics & Communication', 'Associate Professor', user_map['prof_smith']),
        ('FAC-102', 'Prof. Anjali Nair', 'Electronics & Communication', 'Assistant Professor', user_map['prof_anjali'])
    ]
    cursor.executemany(
        "INSERT INTO faculty (employee_id, name, department, designation, user_id) VALUES (?, ?, ?, ?, ?)",
        faculty_data
    )
    cursor.execute("SELECT employee_id, id FROM faculty")
    faculty_map = {row[0]: row[1] for row in cursor.fetchall()}

    # 3. Insert Student Profiles
    students_data = [
        ('ECE2101', 'Adwaith R.', 'Electronics & Communication', 7, user_map['adwaith']),
        ('ECE2102', 'Sneha Patel', 'Electronics & Communication', 7, user_map['sneha']),
        ('ECE2103', 'Rahul Kumar', 'Electronics & Communication', 7, user_map['rahul'])
    ]
    cursor.executemany(
        "INSERT INTO students (roll_no, name, department, semester, user_id) VALUES (?, ?, ?, ?, ?)",
        students_data
    )
    cursor.execute("SELECT roll_no, id FROM students")
    student_map = {row[0]: row[1] for row in cursor.fetchall()}

    # 4. Link Parent to Student (parent_adwaith -> Adwaith R.)
    cursor.execute(
        "INSERT INTO parent_student (parent_user_id, student_id) VALUES (?, ?)",
        (user_map['parent_adwaith'], student_map['ECE2101'])
    )

    # 5. Insert Subjects
    subjects_data = [
        ('ECT423', 'Computer Networks', 'Electronics & Communication', 7, faculty_map['FAC-101']),
        ('ECT401', 'Wireless Communication', 'Electronics & Communication', 7, faculty_map['FAC-102']),
        ('ECT413', 'Optical Communication', 'Electronics & Communication', 7, faculty_map['FAC-101']),
        ('ECT433', 'DSP Algorithms & Architecture', 'Electronics & Communication', 7, faculty_map['FAC-102'])
    ]
    cursor.executemany(
        "INSERT INTO subjects (subject_code, subject_name, department, semester, faculty_id) VALUES (?, ?, ?, ?, ?)",
        subjects_data
    )
    cursor.execute("SELECT subject_code, id FROM subjects")
    subject_map = {row[0]: row[1] for row in cursor.fetchall()}

    # 6. Insert Timetable
    timetable_data = [
        (subject_map['ECT423'], faculty_map['FAC-101'], 'Monday', '09:00 AM - 10:00 AM', 'LH-201'),
        (subject_map['ECT401'], faculty_map['FAC-102'], 'Monday', '10:00 AM - 11:00 AM', 'LH-201'),
        (subject_map['ECT413'], faculty_map['FAC-101'], 'Tuesday', '09:00 AM - 10:00 AM', 'LH-202'),
        (subject_map['ECT423'], faculty_map['FAC-101'], 'Tuesday', '11:15 AM - 12:15 PM', 'Networks Lab'),
        (subject_map['ECT433'], faculty_map['FAC-102'], 'Wednesday', '09:00 AM - 10:00 AM', 'DSP Lab'),
        (subject_map['ECT401'], faculty_map['FAC-102'], 'Wednesday', '10:00 AM - 11:00 AM', 'LH-201'),
        (subject_map['ECT423'], faculty_map['FAC-101'], 'Thursday', '01:30 PM - 02:30 PM', 'LH-201'),
        (subject_map['ECT413'], faculty_map['FAC-101'], 'Friday', '10:00 AM - 11:00 AM', 'LH-202'),
        (subject_map['ECT433'], faculty_map['FAC-102'], 'Friday', '11:15 AM - 12:15 PM', 'LH-201')
    ]
    cursor.executemany(
        "INSERT INTO timetable (subject_id, faculty_id, day_of_week, time_slot, classroom) VALUES (?, ?, ?, ?, ?)",
        timetable_data
    )

    # 7. Insert Attendance Records
    dates = ['2026-10-05', '2026-10-07', '2026-10-12', '2026-10-14', '2026-10-19', '2026-10-21']
    # Attendance for ECT423 (Computer Networks)
    attendance_records = [
        # Adwaith (Attended 5 of 6 = ~83%)
        (student_map['ECE2101'], subject_map['ECT423'], dates[0], 'Present'),
        (student_map['ECE2101'], subject_map['ECT423'], dates[1], 'Present'),
        (student_map['ECE2101'], subject_map['ECT423'], dates[2], 'Absent'),
        (student_map['ECE2101'], subject_map['ECT423'], dates[3], 'Present'),
        (student_map['ECE2101'], subject_map['ECT423'], dates[4], 'Present'),
        (student_map['ECE2101'], subject_map['ECT423'], dates[5], 'Present'),
        # Sneha (Attended 6 of 6 = 100%)
        (student_map['ECE2102'], subject_map['ECT423'], dates[0], 'Present'),
        (student_map['ECE2102'], subject_map['ECT423'], dates[1], 'Present'),
        (student_map['ECE2102'], subject_map['ECT423'], dates[2], 'Present'),
        (student_map['ECE2102'], subject_map['ECT423'], dates[3], 'Present'),
        (student_map['ECE2102'], subject_map['ECT423'], dates[4], 'Present'),
        (student_map['ECE2102'], subject_map['ECT423'], dates[5], 'Present'),
        # Rahul (Attended 4 of 6 = ~67%)
        (student_map['ECE2103'], subject_map['ECT423'], dates[0], 'Present'),
        (student_map['ECE2103'], subject_map['ECT423'], dates[1], 'Absent'),
        (student_map['ECE2103'], subject_map['ECT423'], dates[2], 'Present'),
        (student_map['ECE2103'], subject_map['ECT423'], dates[3], 'Absent'),
        (student_map['ECE2103'], subject_map['ECT423'], dates[4], 'Present'),
        (student_map['ECE2103'], subject_map['ECT423'], dates[5], 'Present'),
        # ECT401 Attendance
        (student_map['ECE2101'], subject_map['ECT401'], dates[0], 'Present'),
        (student_map['ECE2101'], subject_map['ECT401'], dates[1], 'Present'),
        (student_map['ECE2101'], subject_map['ECT401'], dates[2], 'Present'),
        (student_map['ECE2102'], subject_map['ECT401'], dates[0], 'Present'),
        (student_map['ECE2102'], subject_map['ECT401'], dates[1], 'Present'),
        (student_map['ECE2102'], subject_map['ECT401'], dates[2], 'Present'),
        (student_map['ECE2103'], subject_map['ECT401'], dates[0], 'Absent'),
        (student_map['ECE2103'], subject_map['ECT401'], dates[1], 'Present'),
        (student_map['ECE2103'], subject_map['ECT401'], dates[2], 'Present')
    ]
    cursor.executemany(
        "INSERT INTO attendance (student_id, subject_id, date, status) VALUES (?, ?, ?, ?)",
        attendance_records
    )

    # 8. Insert Marks
    marks_data = [
        # ECT423 (Computer Networks)
        (student_map['ECE2101'], subject_map['ECT423'], 'Series Test 1', 50.0, 46.5),
        (student_map['ECE2101'], subject_map['ECT423'], 'Series Test 2', 50.0, 48.0),
        (student_map['ECE2101'], subject_map['ECT423'], 'Assignment 1', 20.0, 19.0),

        (student_map['ECE2102'], subject_map['ECT423'], 'Series Test 1', 50.0, 44.0),
        (student_map['ECE2102'], subject_map['ECT423'], 'Series Test 2', 50.0, 47.0),
        (student_map['ECE2102'], subject_map['ECT423'], 'Assignment 1', 20.0, 18.5),

        (student_map['ECE2103'], subject_map['ECT423'], 'Series Test 1', 50.0, 35.0),
        (student_map['ECE2103'], subject_map['ECT423'], 'Series Test 2', 50.0, 38.0),
        (student_map['ECE2103'], subject_map['ECT423'], 'Assignment 1', 20.0, 15.0),

        # ECT401 (Wireless Communication)
        (student_map['ECE2101'], subject_map['ECT401'], 'Series Test 1', 50.0, 43.0),
        (student_map['ECE2101'], subject_map['ECT401'], 'Series Test 2', 50.0, 45.0),
        (student_map['ECE2101'], subject_map['ECT401'], 'Assignment 1', 20.0, 18.0)
    ]
    cursor.executemany(
        "INSERT INTO marks (student_id, subject_id, assessment_name, max_marks, marks_obtained) VALUES (?, ?, ?, ?, ?)",
        marks_data
    )

    # 9. Insert Notices
    notices_data = [
        ('ECT423 Computer Networks Project Submission & Viva', 
         'All S7 ECE students are requested to complete and demonstrate their client-server networking projects on or before Friday. Viva will focus on socket communication, HTTP, and database access.', 
         'Exam', user_map['prof_smith']),
        ('S7 Internal Assessment Exam Schedule Released', 
         'Series Exam 2 for Seventh Semester ECE will commence from next Monday. Timetable is available on the departmental portal.', 
         'Academic', user_map['admin']),
        ('College LAN Maintenance & IP Reconfiguration Notice', 
         'Central server maintenance is scheduled for Saturday evening. Static IP assignments for department labs will be updated.', 
         'General', user_map['admin'])
    ]
    cursor.executemany(
        "INSERT INTO notices (title, message, category, created_by_user_id) VALUES (?, ?, ?, ?)",
        notices_data
    )

    conn.commit()
    conn.close()
    print("[3/3] Database seeded successfully into 'college.db'!")

if __name__ == '__main__':
    init_database()

