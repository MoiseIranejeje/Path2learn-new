import unittest
from app import app, db, User, School, Shortlist
from models import SchoolSuggestion, Review

class PortalTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

            # Create Users
            self.parent = User(username='parent1', email='parent@test.com', role='parent')
            self.parent.set_password('password')

            self.student = User(username='student1', email='student@test.com', role='student')
            self.student.set_password('password')

            self.admin = User(username='superadmin1', email='admin@test.com', role='superadmin')
            self.admin.set_password('password')

            # Create School
            self.school = School(
                name="Test Academy", province="Kigali", district="Gasabo", sector="Remera",
                education_program="National", gender_policy="Mixed", ownership="Private"
            )
            self.school_two = School(
                name="Second Academy", province="Southern", district="Huye", sector="Ngoma",
                education_program="Technical and Vocational Education and Training (TVET)",
                gender_policy="Girls Only", ownership="Public"
            )

            db.session.add_all([self.parent, self.student, self.admin, self.school, self.school_two])
            db.session.commit()

            self.student_id = self.student.id
            self.parent_id = self.parent.id
            self.admin_id = self.admin.id
            self.school_id = self.school.id
            self.school_two_id = self.school_two.id

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def test_linking_logic(self):
        with app.app_context():
            # Login as Parent and link to Student
            self.login('parent1', 'password')
            response = self.app.post('/profile/link', data={
                'target_email': 'student@test.com'
            }, follow_redirects=True)

            # Check DB
            student = db.session.get(User, self.student_id)
            self.assertEqual(student.parent_id, self.parent_id)
            self.assertIn(b'Successfully linked', response.data)

    def test_shortlist_flow(self):
        with app.app_context():
            # 1. Link accounts manually for test setup
            student = db.session.get(User, self.student_id)
            student.parent_id = self.parent_id
            db.session.commit()

            # 2. Student logs in and adds to shortlist
            self.login('student1', 'password')
            self.app.post(f'/student/shortlist/add/{self.school_id}', follow_redirects=True)

            shortlist = Shortlist.query.filter_by(student_id=self.student_id).first()
            self.assertIsNotNone(shortlist)
            self.assertEqual(shortlist.parent_status, 'pending')

            # Logout student
            self.logout()

            # 3. Parent logs in and approves
            self.login('parent1', 'password')

            response = self.app.post(f'/parent/shortlist/update/{shortlist.id}', data={
                'action': 'approved',
                'comment': 'Looks good!'
            }, follow_redirects=True)

            # Reload shortlist
            shortlist = db.session.get(Shortlist, shortlist.id)
            self.assertEqual(shortlist.parent_status, 'approved')
            self.assertEqual(shortlist.parent_comment, 'Looks good!')

    def test_homepage_renders_with_empty_school_state(self):
        with app.app_context():
            Shortlist.query.delete()
            Review.query.delete()
            School.query.delete()
            db.session.commit()

        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Find the right secondary school in Rwanda', response.data)
        self.assertIn(b'Schools coming soon', response.data)

    def test_homepage_shows_live_metrics_and_school_cards(self):
        with app.app_context():
            review = Review(
                rating=5,
                comment='Excellent environment',
                reviewer_name='Parent Reviewer',
                status='approved',
                school_id=self.school_id
            )
            db.session.add(review)
            db.session.commit()

        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Academy', response.data)
        self.assertIn(b'Top rated schools', response.data)
        self.assertIn(b'Approved reviews', response.data)

    def test_school_detail_shows_redesigned_sections_and_reviews(self):
        with app.app_context():
            self.school.description = 'A strong school with academic and extracurricular opportunities.'
            self.school.extracurriculars = 'Debate Club, Robotics, Football'
            self.school.combinations = 'MEG, PCM'
            self.school.tags = 'STEM, Boarding'
            self.school.boarding_policy = 'Boarding School'
            self.school.min_aggregate = 12
            self.school.phone = '+250700000000'
            self.school.website = 'https://example.com'
            review = Review(
                rating=4,
                comment='Very supportive teachers.',
                reviewer_name='Alumni Reviewer',
                status='approved',
                school_id=self.school_id
            )
            db.session.add(review)
            db.session.commit()

        response = self.app.get(f'/school/{self.school_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'About this school', response.data)
        self.assertIn(b'Academic details', response.data)
        self.assertIn(b'Reviews and community feedback', response.data)
        self.assertIn(b'Very supportive teachers.', response.data)

    def test_compare_page_supports_get_selection_and_unavailable_values(self):
        response = self.app.get(f'/compare?s1={self.school_id}&s2={self.school_two_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Compare schools with real profile data', response.data)
        self.assertIn(b'Admissions &amp; Fit', response.data)
        self.assertIn(b'Unavailable', response.data)

    def test_compare_page_shows_real_data_and_review_counts(self):
        with app.app_context():
            school_one = db.session.get(School, self.school_id)
            school_two = db.session.get(School, self.school_two_id)

            school_one.photos = 'https://example.com/school-one.jpg'
            school_one.boarding_policy = 'Boarding School'
            school_one.min_aggregate = 15
            school_one.combinations = 'PCM, MEG'
            school_one.extracurriculars = 'Robotics, Debate Club'
            school_one.tags = 'STEM, Boarding'
            school_one.fees_breakdown = 'Moderate annual fees'
            school_one.website = 'https://school-one.example.com'

            school_two.boarding_policy = 'Day School'
            school_two.min_aggregate = 8
            school_two.phone = '+250711111111'

            db.session.add_all([
                Review(rating=5, comment='Excellent.', reviewer_name='Reviewer One', status='approved', school_id=self.school_id),
                Review(rating=4, comment='Very good.', reviewer_name='Reviewer Two', status='approved', school_id=self.school_id),
                Review(rating=3, comment='Okay.', reviewer_name='Reviewer Three', status='approved', school_id=self.school_two_id),
            ])
            db.session.commit()

        response = self.app.post('/compare', data={
            'school1': self.school_id,
            'school2': self.school_two_id,
            'submit': 'Compare Schools'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Second Academy', response.data)
        self.assertIn(b'Moderate annual fees', response.data)
        self.assertIn(b'Approved review count', response.data)
        self.assertIn(b'Better fit', response.data)
        self.assertIn(b'Best overall choice', response.data)

    def test_download_template_includes_new_school_fields(self):
        response = self.app.get('/admin/download-template')
        self.assertEqual(response.status_code, 302)

        self.login('superadmin1', 'password')
        response = self.app.get('/admin/download-template')
        self.assertEqual(response.status_code, 200)

        content = response.data.decode('utf-8')
        self.assertIn('Smart Tags', content)
        self.assertIn('Minimum Aggregate Cutoff', content)
        self.assertIn('Subject Combinations', content)
        self.assertIn('Fees Breakdown', content)
        self.assertIn('Performance History', content)

if __name__ == '__main__':
    unittest.main()
