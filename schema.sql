-- College Educational Management System
-- Database Schema for SQLite

-- Enable Foreign Keys
PRAGMA foreign_keys = ON;

-- 1. Users Table (Stores authentication credentials and roles)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT CHECK(role IN ('admin', 'faculty', 'student', 'parent')) NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Students Table (Academic profile of students)
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    semester INTEGER NOT NULL,
    user_id INTEGER UNIQUE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. Faculty Table (Academic staff profile)
CREATE TABLE IF NOT EXISTS faculty (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    designation TEXT NOT NULL,
    user_id INTEGER UNIQUE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 4. Parent-Student Mapping (Enforces access control so parents only see their student)
CREATE TABLE IF NOT EXISTS parent_student (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_user_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    FOREIGN KEY (parent_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    UNIQUE (parent_user_id, student_id)
);

-- 5. Subjects Table (Courses taught in college)
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_code TEXT UNIQUE NOT NULL,
    subject_name TEXT NOT NULL,
    department TEXT NOT NULL,
    semester INTEGER NOT NULL,
    faculty_id INTEGER,
    FOREIGN KEY (faculty_id) REFERENCES faculty(id) ON DELETE SET NULL
);

-- 6. Attendance Table (Daily student attendance per subject)
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    date DATE NOT NULL,
    status TEXT CHECK(status IN ('Present', 'Absent')) NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    UNIQUE (student_id, subject_id, date)
);

-- 7. Marks Table (Internal exams, assignments, semester results)
CREATE TABLE IF NOT EXISTS marks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    assessment_name TEXT NOT NULL, -- e.g. 'Series Test 1', 'Series Test 2', 'Assignment', 'End Semester'
    max_marks REAL NOT NULL,
    marks_obtained REAL NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    UNIQUE (student_id, subject_id, assessment_name)
);

-- 8. Timetable Table (Weekly schedule)
CREATE TABLE IF NOT EXISTS timetable (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    faculty_id INTEGER NOT NULL,
    day_of_week TEXT CHECK(day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday')) NOT NULL,
    time_slot TEXT NOT NULL, -- e.g. '09:00 AM - 10:00 AM'
    classroom TEXT NOT NULL,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (faculty_id) REFERENCES faculty(id) ON DELETE CASCADE
);

-- 9. Notices Table (Broadcast communications from Admin/Faculty)
CREATE TABLE IF NOT EXISTS notices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    category TEXT CHECK(category IN ('General', 'Academic', 'Exam', 'Urgent')) DEFAULT 'General',
    created_by_user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE CASCADE
);

