import os
from functools import wraps
from datetime import date, datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db, close_db, query_db, execute_db

app = Flask(__name__)
# In production, use a random byte string; for local academic testing, a fixed secret is fine
app.secret_key = os.environ.get('SECRET_KEY', 'college_management_secret_key_ect423')

# Register database teardown
app.teardown_appcontext(close_db)

# ---------------------------------------------------------
# AUTHENTICATION & ACCESS CONTROL DECORATORS
# ---------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first.', 'warning')
                return redirect(url_for('login'))
            user_role = session.get('role')
            if user_role not in allowed_roles:
                flash(f'Access denied! Your role ({user_role}) does not have permission for this section.', 'danger')
                return redirect(url_for(f"{user_role}_dashboard"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ---------------------------------------------------------
# CONTEXT PROCESSOR (Inject common variables into templates)
# ---------------------------------------------------------
@app.context_processor
def inject_user():
    return {
        'current_user': {
            'id': session.get('user_id'),
            'username': session.get('username'),
            'role': session.get('role'),
            'full_name': session.get('full_name')
        },
        'today_date': date.today().strftime('%Y-%m-%d')
    }

# ---------------------------------------------------------
# UNIVERSAL ROUTES
# ---------------------------------------------------------
@app.route('/')
def index():
    if 'user_id' in session:
        role = session.get('role')
        return redirect(url_for(f"{role}_dashboard"))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for(f"{session.get('role')}_dashboard"))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Both username and password are required.', 'danger')
            return render_template('login.html')

        user = query_db('SELECT * FROM users WHERE username = ?', (username,), one=True)

        if user and check_password_hash(user['password_hash'], password):
            # Session assignment (Stateful session over stateless HTTP)
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            flash(f"Welcome back, {user['full_name']}! Logged in as {user['role'].capitalize()}.", 'success')
            return redirect(url_for(f"{user['role']}_dashboard"))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = query_db('SELECT * FROM users WHERE id = ?', (session['user_id'],), one=True)
    if request.method == 'POST':
        current_pw = request.form.get('current_password', '')
        new_pw = request.form.get('new_password', '')
        confirm_pw = request.form.get('confirm_password', '')

        if not check_password_hash(user['password_hash'], current_pw):
            flash('Incorrect current password.', 'danger')
        elif len(new_pw) < 6:
            flash('New password must be at least 6 characters.', 'warning')
        elif new_pw != confirm_pw:
            flash('New passwords do not match.', 'danger')
        else:
            new_hash = generate_password_hash(new_pw)
            execute_db('UPDATE users SET password_hash = ? WHERE id = ?', (new_hash, session['user_id']))
            flash('Password updated successfully!', 'success')
            return redirect(url_for('profile'))

    return render_template('profile.html', user=user)

# ---------------------------------------------------------
# STUDENT ROUTES
# ---------------------------------------------------------
@app.route('/student/dashboard')
@role_required('student')
def student_dashboard():
    student = query_db('SELECT * FROM students WHERE user_id = ?', (session['user_id'],), one=True)
    if not student:
        flash('Student record not found.', 'danger')
        return redirect(url_for('logout'))

    # Calculate overall attendance percentage
    att_stats = query_db('''
        SELECT 
            COUNT(*) as total_classes,
            SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as attended_classes
        FROM attendance
        WHERE student_id = ?
    ''', (student['id'],), one=True)

    total_classes = att_stats['total_classes'] or 0
    attended = att_stats['attended_classes'] or 0
    attendance_pct = round((attended / total_classes * 100), 1) if total_classes > 0 else 0.0

    # Recent marks
    recent_marks = query_db('''
        SELECT m.*, s.subject_name, s.subject_code
        FROM marks m
        JOIN subjects s ON m.subject_id = s.id
        WHERE m.student_id = ?
        ORDER BY m.id DESC LIMIT 5
    ''', (student['id'],))

    # Recent notices
    notices = query_db('''
        SELECT n.*, u.full_name as author
        FROM notices n
        JOIN users u ON n.created_by_user_id = u.id
        ORDER BY n.created_at DESC LIMIT 4
    ''')

    # Today's timetable
    today_name = datetime.now().strftime('%A')
    today_timetable = query_db('''
        SELECT t.*, s.subject_name, s.subject_code, f.name as faculty_name
        FROM timetable t
        JOIN subjects s ON t.subject_id = s.id
        JOIN faculty f ON t.faculty_id = f.id
        WHERE s.department = ? AND s.semester = ? AND t.day_of_week = ?
        ORDER BY t.time_slot ASC
    ''', (student['department'], student['semester'], today_name))

    return render_template('student/dashboard.html', 
                           student=student, 
                           attendance_pct=attendance_pct,
                           total_classes=total_classes,
                           attended=attended,
                           recent_marks=recent_marks,
                           notices=notices,
                           today_timetable=today_timetable,
                           today_name=today_name)

@app.route('/student/attendance')
@role_required('student')
def student_attendance():
    student = query_db('SELECT * FROM students WHERE user_id = ?', (session['user_id'],), one=True)
    # Subject-wise attendance breakdown
    subject_attendance = query_db('''
        SELECT 
            s.subject_code,
            s.subject_name,
            COUNT(a.id) as total_conducted,
            SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as attended
        FROM subjects s
        LEFT JOIN attendance a ON s.id = a.subject_id AND a.student_id = ?
        WHERE s.department = ? AND s.semester = ?
        GROUP BY s.id
    ''', (student['id'], student['department'], student['semester']))

    # Date-wise detailed logs
    attendance_logs = query_db('''
        SELECT a.date, a.status, s.subject_code, s.subject_name
        FROM attendance a
        JOIN subjects s ON a.subject_id = s.id
        WHERE a.student_id = ?
        ORDER BY a.date DESC
    ''', (student['id'],))

    return render_template('student/attendance.html', 
                           student=student,
                           subject_attendance=subject_attendance,
                           attendance_logs=attendance_logs)

@app.route('/student/marks')
@role_required('student')
def student_marks():
    student = query_db('SELECT * FROM students WHERE user_id = ?', (session['user_id'],), one=True)
    marks_list = query_db('''
        SELECT m.*, s.subject_code, s.subject_name
        FROM marks m
        JOIN subjects s ON m.subject_id = s.id
        WHERE m.student_id = ?
        ORDER BY s.subject_code, m.assessment_name
    ''', (student['id'],))
    return render_template('student/marks.html', student=student, marks=marks_list)

@app.route('/student/timetable')
@role_required('student')
def student_timetable():
    student = query_db('SELECT * FROM students WHERE user_id = ?', (session['user_id'],), one=True)
    timetable = query_db('''
        SELECT t.*, s.subject_code, s.subject_name, f.name as faculty_name
        FROM timetable t
        JOIN subjects s ON t.subject_id = s.id
        JOIN faculty f ON t.faculty_id = f.id
        WHERE s.department = ? AND s.semester = ?
        ORDER BY 
            CASE t.day_of_week
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
            END, t.time_slot
    ''', (student['department'], student['semester']))
    return render_template('student/timetable.html', student=student, timetable=timetable)

@app.route('/student/notices')
@role_required('student')
def student_notices():
    notices = query_db('''
        SELECT n.*, u.full_name as author, u.role as author_role
        FROM notices n
        JOIN users u ON n.created_by_user_id = u.id
        ORDER BY n.created_at DESC
    ''')
    return render_template('student/notices.html', notices=notices)

# ---------------------------------------------------------
# FACULTY ROUTES
# ---------------------------------------------------------
@app.route('/faculty/dashboard')
@role_required('faculty')
def faculty_dashboard():
    faculty = query_db('SELECT * FROM faculty WHERE user_id = ?', (session['user_id'],), one=True)
    if not faculty:
        flash('Faculty profile not found.', 'danger')
        return redirect(url_for('logout'))

    assigned_subjects = query_db('SELECT * FROM subjects WHERE faculty_id = ?', (faculty['id'],))
    recent_notices = query_db('''
        SELECT n.*, u.full_name as author
        FROM notices n
        JOIN users u ON n.created_by_user_id = u.id
        ORDER BY n.created_at DESC LIMIT 3
    ''')

    return render_template('faculty/dashboard.html', 
                           faculty=faculty, 
                           assigned_subjects=assigned_subjects,
                           notices=recent_notices)

@app.route('/faculty/attendance', methods=['GET', 'POST'])
@role_required('faculty')
def faculty_attendance():
    faculty = query_db('SELECT * FROM faculty WHERE user_id = ?', (session['user_id'],), one=True)
    assigned_subjects = query_db('SELECT * FROM subjects WHERE faculty_id = ?', (faculty['id'],))

    selected_subject_id = request.args.get('subject_id', type=int)
    if not selected_subject_id and assigned_subjects:
        selected_subject_id = assigned_subjects[0]['id']

    selected_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))

    selected_subject = query_db('SELECT * FROM subjects WHERE id = ? AND faculty_id = ?', 
                                (selected_subject_id, faculty['id']), one=True)

    students = []
    if selected_subject:
        # Fetch students belonging to the subject's department and semester
        students = query_db('''
            SELECT s.*, 
                   COALESCE(a.status, 'Present') as current_status
            FROM students s
            LEFT JOIN attendance a 
                ON s.id = a.student_id 
                AND a.subject_id = ? 
                AND a.date = ?
            WHERE s.department = ? AND s.semester = ?
            ORDER BY s.roll_no ASC
        ''', (selected_subject_id, selected_date, selected_subject['department'], selected_subject['semester']))

    if request.method == 'POST':
        sub_id = request.form.get('subject_id', type=int)
        att_date = request.form.get('date')

        # Verify faculty teaches this subject
        subj_check = query_db('SELECT id FROM subjects WHERE id = ? AND faculty_id = ?', (sub_id, faculty['id']), one=True)
        if not subj_check:
            flash('Unauthorized subject selection.', 'danger')
            return redirect(url_for('faculty_attendance'))

        # Fetch students for this subject to record attendance
        dept_sem = query_db('SELECT department, semester FROM subjects WHERE id = ?', (sub_id,), one=True)
        class_students = query_db('SELECT id FROM students WHERE department = ? AND semester = ?', 
                                  (dept_sem['department'], dept_sem['semester']))

        for st in class_students:
            status = request.form.get(f"status_{st['id']}", 'Absent')
            # UPSERT using SQLite INSERT OR REPLACE
            execute_db('''
                INSERT OR REPLACE INTO attendance (student_id, subject_id, date, status)
                VALUES (?, ?, ?, ?)
            ''', (st['id'], sub_id, att_date, status))

        flash(f"Attendance recorded successfully for {len(class_students)} students on {att_date}!", 'success')
        return redirect(url_for('faculty_attendance', subject_id=sub_id, date=att_date))

    return render_template('faculty/attendance.html', 
                           faculty=faculty,
                           assigned_subjects=assigned_subjects,
                           selected_subject=selected_subject,
                           selected_date=selected_date,
                           students=students)

@app.route('/faculty/marks', methods=['GET', 'POST'])
@role_required('faculty')
def faculty_marks():
    faculty = query_db('SELECT * FROM faculty WHERE user_id = ?', (session['user_id'],), one=True)
    assigned_subjects = query_db('SELECT * FROM subjects WHERE faculty_id = ?', (faculty['id'],))

    selected_subject_id = request.args.get('subject_id', type=int)
    if not selected_subject_id and assigned_subjects:
        selected_subject_id = assigned_subjects[0]['id']

    selected_assessment = request.args.get('assessment', 'Series Test 1')

    selected_subject = query_db('SELECT * FROM subjects WHERE id = ? AND faculty_id = ?', 
                                (selected_subject_id, faculty['id']), one=True)

    students = []
    if selected_subject:
        students = query_db('''
            SELECT s.*, 
                   m.marks_obtained, 
                   m.max_marks
            FROM students s
            LEFT JOIN marks m 
                ON s.id = m.student_id 
                AND m.subject_id = ? 
                AND m.assessment_name = ?
            WHERE s.department = ? AND s.semester = ?
            ORDER BY s.roll_no ASC
        ''', (selected_subject_id, selected_assessment, selected_subject['department'], selected_subject['semester']))

    if request.method == 'POST':
        sub_id = request.form.get('subject_id', type=int)
        assessment = request.form.get('assessment')
        max_marks = float(request.form.get('max_marks', 50.0))

        dept_sem = query_db('SELECT department, semester FROM subjects WHERE id = ?', (sub_id,), one=True)
        class_students = query_db('SELECT id FROM students WHERE department = ? AND semester = ?', 
                                  (dept_sem['department'], dept_sem['semester']))

        for st in class_students:
            marks_val = request.form.get(f"marks_{st['id']}")
            if marks_val is not None and marks_val.strip() != '':
                try:
                    obtained = float(marks_val)
                    if 0 <= obtained <= max_marks:
                        execute_db('''
                            INSERT OR REPLACE INTO marks (student_id, subject_id, assessment_name, max_marks, marks_obtained)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (st['id'], sub_id, assessment, max_marks, obtained))
                except ValueError:
                    pass

        flash(f"Marks for '{assessment}' updated successfully!", 'success')
        return redirect(url_for('faculty_marks', subject_id=sub_id, assessment=assessment))

    return render_template('faculty/marks.html', 
                           faculty=faculty,
                           assigned_subjects=assigned_subjects,
                           selected_subject=selected_subject,
                           selected_assessment=selected_assessment,
                           students=students)

@app.route('/faculty/timetable')
@role_required('faculty')
def faculty_timetable():
    faculty = query_db('SELECT * FROM faculty WHERE user_id = ?', (session['user_id'],), one=True)
    timetable = query_db('''
        SELECT t.*, s.subject_code, s.subject_name
        FROM timetable t
        JOIN subjects s ON t.subject_id = s.id
        WHERE t.faculty_id = ?
        ORDER BY 
            CASE t.day_of_week
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
            END, t.time_slot
    ''', (faculty['id'],))
    return render_template('faculty/timetable.html', faculty=faculty, timetable=timetable)

@app.route('/faculty/notices', methods=['GET', 'POST'])
@role_required('faculty')
def faculty_notices():
    faculty = query_db('SELECT * FROM faculty WHERE user_id = ?', (session['user_id'],), one=True)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        message = request.form.get('message', '').strip()
        category = request.form.get('category', 'Academic')

        if not title or not message:
            flash('Title and notice content cannot be empty.', 'danger')
        else:
            execute_db('''
                INSERT INTO notices (title, message, category, created_by_user_id)
                VALUES (?, ?, ?, ?)
            ''', (title, message, category, session['user_id']))
            flash('Academic notice posted successfully!', 'success')
            return redirect(url_for('faculty_notices'))

    notices = query_db('''
        SELECT n.*, u.full_name as author
        FROM notices n
        JOIN users u ON n.created_by_user_id = u.id
        ORDER BY n.created_at DESC
    ''')
    return render_template('faculty/notices.html', notices=notices)

# ---------------------------------------------------------
# PARENT ROUTES (Strict Linkage Enforcement)
# ---------------------------------------------------------
@app.route('/parent/dashboard')
@role_required('parent')
def parent_dashboard():
    # Enforce database-level relationship
    student = query_db('''
        SELECT s.*, u.email as student_email
        FROM students s
        JOIN parent_student ps ON s.id = ps.student_id
        JOIN users u ON s.user_id = u.id
        WHERE ps.parent_user_id = ?
    ''', (session['user_id'],), one=True)

    if not student:
        flash('No student linked to this parent account. Please contact college admin.', 'warning')
        return render_template('parent/dashboard.html', student=None)

    # Attendance summary
    att_stats = query_db('''
        SELECT 
            COUNT(*) as total_classes,
            SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as attended_classes
        FROM attendance
        WHERE student_id = ?
    ''', (student['id'],), one=True)

    total_classes = att_stats['total_classes'] or 0
    attended = att_stats['attended_classes'] or 0
    attendance_pct = round((attended / total_classes * 100), 1) if total_classes > 0 else 0.0

    # Recent marks
    recent_marks = query_db('''
        SELECT m.*, s.subject_name, s.subject_code
        FROM marks m
        JOIN subjects s ON m.subject_id = s.id
        WHERE m.student_id = ?
        ORDER BY m.id DESC LIMIT 5
    ''', (student['id'],))

    notices = query_db('''
        SELECT n.*, u.full_name as author
        FROM notices n
        JOIN users u ON n.created_by_user_id = u.id
        ORDER BY n.created_at DESC LIMIT 3
    ''')

    return render_template('parent/dashboard.html', 
                           student=student, 
                           attendance_pct=attendance_pct,
                           total_classes=total_classes,
                           attended=attended,
                           recent_marks=recent_marks,
                           notices=notices)

@app.route('/parent/attendance')
@role_required('parent')
def parent_attendance():
    student = query_db('''
        SELECT s.* FROM students s
        JOIN parent_student ps ON s.id = ps.student_id
        WHERE ps.parent_user_id = ?
    ''', (session['user_id'],), one=True)

    if not student:
        flash('No linked student found.', 'warning')
        return redirect(url_for('parent_dashboard'))

    subject_attendance = query_db('''
        SELECT 
            s.subject_code,
            s.subject_name,
            COUNT(a.id) as total_conducted,
            SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as attended
        FROM subjects s
        LEFT JOIN attendance a ON s.id = a.subject_id AND a.student_id = ?
        WHERE s.department = ? AND s.semester = ?
        GROUP BY s.id
    ''', (student['id'], student['department'], student['semester']))

    attendance_logs = query_db('''
        SELECT a.date, a.status, s.subject_code, s.subject_name
        FROM attendance a
        JOIN subjects s ON a.subject_id = s.id
        WHERE a.student_id = ?
        ORDER BY a.date DESC
    ''', (student['id'],))

    return render_template('parent/attendance.html', 
                           student=student,
                           subject_attendance=subject_attendance,
                           attendance_logs=attendance_logs)

@app.route('/parent/marks')
@role_required('parent')
def parent_marks():
    student = query_db('''
        SELECT s.* FROM students s
        JOIN parent_student ps ON s.id = ps.student_id
        WHERE ps.parent_user_id = ?
    ''', (session['user_id'],), one=True)

    if not student:
        flash('No linked student found.', 'warning')
        return redirect(url_for('parent_dashboard'))

    marks_list = query_db('''
        SELECT m.*, s.subject_code, s.subject_name
        FROM marks m
        JOIN subjects s ON m.subject_id = s.id
        WHERE m.student_id = ?
        ORDER BY s.subject_code, m.assessment_name
    ''', (student['id'],))

    return render_template('parent/marks.html', student=student, marks=marks_list)

@app.route('/parent/notices')
@role_required('parent')
def parent_notices():
    notices = query_db('''
        SELECT n.*, u.full_name as author
        FROM notices n
        JOIN users u ON n.created_by_user_id = u.id
        ORDER BY n.created_at DESC
    ''')
    return render_template('parent/notices.html', notices=notices)

# ---------------------------------------------------------
# ADMINISTRATOR ROUTES
# ---------------------------------------------------------
@app.route('/admin/dashboard')
@role_required('admin')
def admin_dashboard():
    stats = {
        'total_students': query_db('SELECT COUNT(*) as count FROM students', one=True)['count'],
        'total_faculty': query_db('SELECT COUNT(*) as count FROM faculty', one=True)['count'],
        'total_subjects': query_db('SELECT COUNT(*) as count FROM subjects', one=True)['count'],
        'total_notices': query_db('SELECT COUNT(*) as count FROM notices', one=True)['count']
    }
    recent_notices = query_db('''
        SELECT n.*, u.full_name as author
        FROM notices n
        JOIN users u ON n.created_by_user_id = u.id
        ORDER BY n.created_at DESC LIMIT 3
    ''')
    return render_template('admin/dashboard.html', stats=stats, notices=recent_notices)

@app.route('/admin/students', methods=['GET', 'POST'])
@role_required('admin')
def admin_students():
    if request.method == 'POST':
        roll_no = request.form.get('roll_no', '').strip().upper()
        name = request.form.get('name', '').strip()
        department = request.form.get('department', '').strip()
        semester = request.form.get('semester', type=int)
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()
        email = request.form.get('email', '').strip()

        if not (roll_no and name and department and semester and username and password):
            flash('All student and account fields are required.', 'danger')
        else:
            try:
                pw_hash = generate_password_hash(password)
                user_id = execute_db('''
                    INSERT INTO users (username, password_hash, role, full_name, email)
                    VALUES (?, ?, 'student', ?, ?)
                ''', (username, pw_hash, name, email))

                execute_db('''
                    INSERT INTO students (roll_no, name, department, semester, user_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (roll_no, name, department, semester, user_id))

                flash(f"Student '{name}' ({roll_no}) registered successfully!", 'success')
            except Exception as e:
                flash(f"Error registering student: {str(e)}", 'danger')

        return redirect(url_for('admin_students'))

    students = query_db('''
        SELECT s.*, u.username, u.email
        FROM students s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.department, s.semester, s.roll_no
    ''')
    return render_template('admin/students.html', students=students)

@app.route('/admin/students/delete/<int:student_id>', methods=['POST'])
@role_required('admin')
def admin_delete_student(student_id):
    student = query_db('SELECT user_id FROM students WHERE id = ?', (student_id,), one=True)
    if student:
        # Cascade delete removes student profile, attendance, and marks
        execute_db('DELETE FROM users WHERE id = ?', (student['user_id'],))
        flash('Student record deleted successfully.', 'info')
    return redirect(url_for('admin_students'))

@app.route('/admin/faculty', methods=['GET', 'POST'])
@role_required('admin')
def admin_faculty():
    if request.method == 'POST':
        emp_id = request.form.get('employee_id', '').strip().upper()
        name = request.form.get('name', '').strip()
        department = request.form.get('department', '').strip()
        designation = request.form.get('designation', '').strip()
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()
        email = request.form.get('email', '').strip()

        if not (emp_id and name and department and designation and username and password):
            flash('All faculty fields are required.', 'danger')
        else:
            try:
                pw_hash = generate_password_hash(password)
                user_id = execute_db('''
                    INSERT INTO users (username, password_hash, role, full_name, email)
                    VALUES (?, ?, 'faculty', ?, ?)
                ''', (username, pw_hash, name, email))

                execute_db('''
                    INSERT INTO faculty (employee_id, name, department, designation, user_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (emp_id, name, department, designation, user_id))

                flash(f"Faculty '{name}' added successfully!", 'success')
            except Exception as e:
                flash(f"Error adding faculty: {str(e)}", 'danger')

        return redirect(url_for('admin_faculty'))

    faculty_list = query_db('''
        SELECT f.*, u.username, u.email,
               (SELECT COUNT(*) FROM subjects WHERE faculty_id = f.id) as subject_count
        FROM faculty f
        JOIN users u ON f.user_id = u.id
        ORDER BY f.department, f.name
    ''')
    return render_template('admin/faculty.html', faculty_list=faculty_list)

@app.route('/admin/faculty/delete/<int:faculty_id>', methods=['POST'])
@role_required('admin')
def admin_delete_faculty(faculty_id):
    faculty = query_db('SELECT user_id FROM faculty WHERE id = ?', (faculty_id,), one=True)
    if faculty:
        execute_db('DELETE FROM users WHERE id = ?', (faculty['user_id'],))
        flash('Faculty member removed successfully.', 'info')
    return redirect(url_for('admin_faculty'))

@app.route('/admin/subjects', methods=['GET', 'POST'])
@role_required('admin')
def admin_subjects():
    if request.method == 'POST':
        code = request.form.get('subject_code', '').strip().upper()
        name = request.form.get('subject_name', '').strip()
        dept = request.form.get('department', '').strip()
        sem = request.form.get('semester', type=int)
        fac_id = request.form.get('faculty_id', type=int) or None

        if not (code and name and dept and sem):
            flash('Subject code, name, department, and semester are required.', 'danger')
        else:
            try:
                execute_db('''
                    INSERT INTO subjects (subject_code, subject_name, department, semester, faculty_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (code, name, dept, sem, fac_id))
                flash(f"Subject '{code}: {name}' created successfully!", 'success')
            except Exception as e:
                flash(f"Error creating subject: {str(e)}", 'danger')

        return redirect(url_for('admin_subjects'))

    subjects = query_db('''
        SELECT s.*, f.name as faculty_name
        FROM subjects s
        LEFT JOIN faculty f ON s.faculty_id = f.id
        ORDER BY s.department, s.semester, s.subject_code
    ''')
    faculty_list = query_db('SELECT id, name, department FROM faculty ORDER BY name')
    return render_template('admin/subjects.html', subjects=subjects, faculty_list=faculty_list)

@app.route('/admin/timetable', methods=['GET', 'POST'])
@role_required('admin')
def admin_timetable():
    if request.method == 'POST':
        subj_id = request.form.get('subject_id', type=int)
        fac_id = request.form.get('faculty_id', type=int)
        day = request.form.get('day_of_week')
        slot = request.form.get('time_slot')
        classroom = request.form.get('classroom', '').strip()

        if not (subj_id and fac_id and day and slot and classroom):
            flash('All timetable slot fields are required.', 'danger')
        else:
            execute_db('''
                INSERT INTO timetable (subject_id, faculty_id, day_of_week, time_slot, classroom)
                VALUES (?, ?, ?, ?, ?)
            ''', (subj_id, fac_id, day, slot, classroom))
            flash('Timetable slot scheduled successfully!', 'success')

        return redirect(url_for('admin_timetable'))

    timetable_slots = query_db('''
        SELECT t.*, s.subject_code, s.subject_name, s.department, s.semester, f.name as faculty_name
        FROM timetable t
        JOIN subjects s ON t.subject_id = s.id
        JOIN faculty f ON t.faculty_id = f.id
        ORDER BY 
            CASE t.day_of_week
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
            END, t.time_slot
    ''')
    subjects = query_db('SELECT id, subject_code, subject_name, semester FROM subjects ORDER BY subject_code')
    faculty_list = query_db('SELECT id, name FROM faculty ORDER BY name')
    return render_template('admin/timetable.html', 
                           timetable_slots=timetable_slots, 
                           subjects=subjects, 
                           faculty_list=faculty_list)

@app.route('/admin/timetable/delete/<int:slot_id>', methods=['POST'])
@role_required('admin')
def admin_delete_timetable(slot_id):
    execute_db('DELETE FROM timetable WHERE id = ?', (slot_id,))
    flash('Timetable slot removed.', 'info')
    return redirect(url_for('admin_timetable'))

@app.route('/admin/notices', methods=['GET', 'POST'])
@role_required('admin')
def admin_notices():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        message = request.form.get('message', '').strip()
        category = request.form.get('category', 'General')

        if not title or not message:
            flash('Title and notice text are required.', 'danger')
        else:
            execute_db('''
                INSERT INTO notices (title, message, category, created_by_user_id)
                VALUES (?, ?, ?, ?)
            ''', (title, message, category, session['user_id']))
            flash('College-wide notice published successfully!', 'success')
            return redirect(url_for('admin_notices'))

    notices = query_db('''
        SELECT n.*, u.full_name as author
        FROM notices n
        JOIN users u ON n.created_by_user_id = u.id
        ORDER BY n.created_at DESC
    ''')
    return render_template('admin/notices.html', notices=notices)

@app.route('/admin/notices/delete/<int:notice_id>', methods=['POST'])
@role_required('admin')
def admin_delete_notice(notice_id):
    execute_db('DELETE FROM notices WHERE id = ?', (notice_id,))
    flash('Notice deleted.', 'info')
    return redirect(url_for('admin_notices'))

@app.route('/admin/reports')
@role_required('admin')
def admin_reports():
    # 1. Department Summary
    dept_summary = query_db('''
        SELECT department, COUNT(*) as student_count
        FROM students
        GROUP BY department
    ''')

    # 2. Attendance Shortage Alerts (< 75%)
    attendance_report = query_db('''
        SELECT 
            s.roll_no,
            s.name,
            s.department,
            s.semester,
            COUNT(a.id) as total_conducted,
            SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as attended,
            ROUND(CAST(SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS FLOAT) / 
                  NULLIF(COUNT(a.id), 0) * 100, 1) as percentage
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id
        GROUP BY s.id
        ORDER BY percentage ASC
    ''')

    # 3. Marks Summary
    marks_report = query_db('''
        SELECT 
            sub.subject_code,
            sub.subject_name,
            m.assessment_name,
            ROUND(AVG(m.marks_obtained), 1) as avg_marks,
            MAX(m.marks_obtained) as highest_marks,
            MIN(m.marks_obtained) as lowest_marks,
            m.max_marks
        FROM marks m
        JOIN subjects sub ON m.subject_id = sub.id
        GROUP BY sub.id, m.assessment_name
    ''')

    return render_template('admin/reports.html', 
                           dept_summary=dept_summary,
                           attendance_report=attendance_report,
                           marks_report=marks_report)

# ---------------------------------------------------------
# ERROR HANDLERS (Friendly & Informative)
# ---------------------------------------------------------
@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

# ---------------------------------------------------------
# MAIN RUNNER (Binds to 0.0.0.0 for LAN Multi-Client Access)
# ---------------------------------------------------------
if __name__ == '__main__':
    # Binding to '0.0.0.0' allows external devices on the same Wi-Fi / LAN to connect
    print("================================================================")
    print("  EDUCATIONAL MANAGEMENT SYSTEM - COMPUTER NETWORKS SERVER")
    print("  Course: ECT423 Computer Networks Project")
    print("  Listening on: http://127.0.0.1:5000 (Local Machine)")
    print("  Accessible over LAN at: http://<Your-IP-Address>:5000")
    print("================================================================")
    app.run(host='0.0.0.0', port=5000, debug=True)

