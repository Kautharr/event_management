import unittest
from app import app, event_requests
from datetime import datetime

class TestEventRequestSubmission(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        app.config['TESTING'] = True

    def setUp(self):
        event_requests.clear()

    def login_as_cso(self):
        """Helper function to log in as CSO by posting to the login route."""
        return self.client.post('/login', data={'username': 'sarah', 'password': 'cso'}, follow_redirects=True)

    def test_event_request_submission_successful(self):
        """Test successful event request submission by CSO with all fields."""
        # log in as CSO
        response = self.login_as_cso()
        self.assertIn(b'Login successful!', response.data)

        request_data = {
            'record_number': '0001',
            'client_name': 'Kauthar Ahmed',
            'event_type': 'Workshop',
            'start_date': '2024-11-04',
            'end_date': '2024-11-09',
            'budget': '5000',
            'details': 'Detailed event description.'
        }

        # submit event request
        response = self.client.post('/submit_request', data=request_data, follow_redirects=True)

        # check for successful submission
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"submitted successfully", response.data)  # check flash message

        # check if the event request was saved correctly
        self.assertEqual(len(event_requests), 1)
        saved_request = event_requests[0]
        self.assertEqual(saved_request['record_number'], '0001')
        self.assertEqual(saved_request['client_name'], 'Kauthar Ahmed')
        self.assertEqual(saved_request['event_type'], 'Workshop')
        self.assertEqual(saved_request['start_date'], '2024-11-04')
        self.assertEqual(saved_request['end_date'], '2024-11-09')
        self.assertEqual(saved_request['budget'], '5000')
        self.assertEqual(saved_request['status'], 'Pending Approval by Senior CSO')

    def test_event_request_submission_incomplete(self):
        """Test that CSO cannot submit an event request with missing required fields."""
        # log in as CSO
        response = self.login_as_cso()
        self.assertIn(b'Login successful!', response.data)

        # define incomplete event request data (missing client_name and budget)
        request_data = {
            'record_number': '0002',
            'event_type': 'Seminar',
            'start_date': '2024-12-01',
            'end_date': '2024-12-05',
            'details': 'Incomplete event request without client name and budget.'
        }

        # submit incomplete event request
        response = self.client.post('/submit_request', data=request_data, follow_redirects=True)

        # check for unsuccessful submission
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please fill in all required fields.", response.data)  # Check flash message

        # ensure no event request was added
        self.assertEqual(len(event_requests), 0)

if __name__ == '__main__':
    unittest.main()