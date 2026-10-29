import unittest
from app import app
from database import get_db

class CollegeManagementTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_01_login_page_renders(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'College Portal Login', response.data)

    def test_02_invalid_login(self):
        response = self.client.post('/login', data={
            'username': 'fakeuser',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertIn(b'Invalid username or password', response.data)

    def test_03_admin_workflow(self):
        # 1. Login as Admin
        res = self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        self.assertIn(b'Administration Management Console', res.data)

        # 2. Check Admin endpoints
        endpoints = ['/admin/students', '/admin/faculty', '/admin/subjects', '/admin/timetable', '/admin/notices', '/admin/reports']
        for ep in endpoints:
            r = self.client.get(ep)
            self.assertEqual(r.status_code, 200, f"Endpoint {ep} failed with {r.status_code}")

        # 3. Logout
        r_logout = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'logged out successfully', r_logout.data)

    def test_04_faculty_workflow(self):
        # Login as Dr. John Smith
        res = self.client.post('/login', data={'username': 'prof_smith', 'password': 'faculty123'}, follow_redirects=True)
        self.assertIn(b'Faculty Portal: Dr. John Smith', res.data)

        # Test attendance & marks pages
        r_att = self.client.get('/faculty/attendance')
        self.assertEqual(r_att.status_code, 200)

        r_marks = self.client.get('/faculty/marks')
        self.assertEqual(r_marks.status_code, 200)

        r_tt = self.client.get('/faculty/timetable')
        self.assertEqual(r_tt.status_code, 200)

        r_notices = self.client.get('/faculty/notices')
        self.assertEqual(r_notices.status_code, 200)

        self.client.get('/logout')

    def test_05_student_workflow(self):
        # Login as Adwaith
        res = self.client.post('/login', data={'username': 'adwaith', 'password': 'student123'}, follow_redirects=True)
        self.assertIn(b'Welcome, Adwaith R.!', res.data)

        # Test Student pages
        endpoints = ['/student/attendance', '/student/marks', '/student/timetable', '/student/notices']
        for ep in endpoints:
            r = self.client.get(ep)
            self.assertEqual(r.status_code, 200, f"Student endpoint {ep} failed with {r.status_code}")

        # Security check: Student should NOT be able to access /admin/dashboard
        r_unauth = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertIn(b'Access denied', r_unauth.data)

        self.client.get('/logout')

    def test_06_parent_workflow(self):
        # Login as Parent
        res = self.client.post('/login', data={'username': 'parent_adwaith', 'password': 'parent123'}, follow_redirects=True)
        self.assertIn(b'Parent Portal', res.data)
        self.assertIn(b'Adwaith R.', res.data)

        # Test Parent pages
        endpoints = ['/parent/attendance', '/parent/marks', '/parent/notices']
        for ep in endpoints:
            r = self.client.get(ep)
            self.assertEqual(r.status_code, 200, f"Parent endpoint {ep} failed with {r.status_code}")

        self.client.get('/logout')

if __name__ == '__main__':
    unittest.main()

