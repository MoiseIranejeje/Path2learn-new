import unittest
from app import app, db, School, smart_search
from sqlalchemy import text

class SmartSearchTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

            # Create test schools
            # min_aggregate here represents the CUT-OFF (Highest acceptable aggregate)
            # Lower score = Better student.

            # School A: Very strict. Cutoff 12.
            s1 = School(name="Elite Academy", province="Kigali", district="Gasabo", sector="Remera",
                        education_program="National", gender_policy="Mixed", ownership="Private",
                        min_aggregate=12)

            # School B: Moderate. Cutoff 25.
            s2 = School(name="Community High", province="Kigali", district="Kicukiro", sector="Niboye",
                        education_program="National", gender_policy="Mixed", ownership="Public",
                        min_aggregate=25)

            # School C: Open. No Cutoff (0).
            s3 = School(name="Open School", province="Kigali", district="Nyarugenge", sector="Nyamirambo",
                        education_program="National", gender_policy="Mixed", ownership="Private",
                        min_aggregate=0)

            db.session.add_all([s1, s2, s3])
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_aggregate_logic_good_student(self):
        """Student with Aggregate 10 (Excellent) should see ALL schools."""
        with app.app_context():
            response = self.app.post('/smart-search', data={
                'aggregate_score': '10',
                'province': 'Kigali' # To limit scope
            })
            data = response.get_data(as_text=True)

            # 10 is <= 12. Elite Academy should be there.
            self.assertIn("Elite Academy", data)
            # 10 is <= 25. Community High should be there.
            self.assertIn("Community High", data)
            # Open School (0) should be there.
            self.assertIn("Open School", data)

    def test_aggregate_logic_average_student(self):
        """Student with Aggregate 20 (Average) should see B and C, but NOT A."""
        with app.app_context():
            response = self.app.post('/smart-search', data={
                'aggregate_score': '20',
                'province': 'Kigali'
            })
            data = response.get_data(as_text=True)

            # 20 is > 12. Elite Academy should NOT be there.
            self.assertNotIn("Elite Academy", data)
            # 20 is <= 25. Community High should be there.
            self.assertIn("Community High", data)
            # Open School should be there.
            self.assertIn("Open School", data)

    def test_aggregate_logic_poor_student(self):
        """Student with Aggregate 30 (Poor) should see ONLY C."""
        with app.app_context():
            response = self.app.post('/smart-search', data={
                'aggregate_score': '30',
                'province': 'Kigali'
            })
            data = response.get_data(as_text=True)

            self.assertNotIn("Elite Academy", data)
            self.assertNotIn("Community High", data)
            self.assertIn("Open School", data)

if __name__ == '__main__':
    unittest.main()
