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
        endpoints = ['/admin/students', '/admin/faculty', '/admin/subjects', '/admin/timetable', '/admin/notices', '/admin/reports', '/admin/fees']
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

        # Test attendance, marks, timetable, notices, fees, materials, assignments pages
        endpoints = ['/faculty/attendance', '/faculty/marks', '/faculty/timetable', '/faculty/notices', '/faculty/fees', '/faculty/materials', '/faculty/assignments']
        for ep in endpoints:
            r = self.client.get(ep)
            self.assertEqual(r.status_code, 200, f"Faculty endpoint {ep} failed with {r.status_code}")

        self.client.get('/logout')

    def test_05_student_workflow(self):
        # Login as Adwaith
        res = self.client.post('/login', data={'username': 'adwaith', 'password': 'student123'}, follow_redirects=True)
        self.assertIn(b'Adwaith Krishna R', res.data)

        # Test Student pages
        endpoints = [
            '/student/dashboard',
            '/student/attendance',
            '/student/marks',
            '/student/timetable',
            '/student/notices',
            '/student/fees',
            '/student/materials',
            '/student/assignments',
            '/student/courses',
            '/student/faculties',
            '/student/analysis',
            '/student/lab',
            '/student/quiz',
            '/student/videos',
            '/student/university_exam'
        ]
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
        self.assertIn(b'Adwaith Krishna R', res.data)

        # Test Parent pages
        endpoints = ['/parent/attendance', '/parent/marks', '/parent/notices']
        for ep in endpoints:
            r = self.client.get(ep)
            self.assertEqual(r.status_code, 200, f"Parent endpoint {ep} failed with {r.status_code}")

        self.client.get('/logout')

if __name__ == '__main__':
    unittest.main()

