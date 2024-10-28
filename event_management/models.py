from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

# Dictionary to store users and clients
users = {}
clients = {}

# List to store all event requests
requests = []

class User:
    """A class representing a user in the system, including roles."""
    
    def __init__(self, username, password, role):
        self.username = username
        self.password_hash = generate_password_hash(password)
        self.role = role

    def check_password(self, password):
        """Verify the user's password."""
        return check_password_hash(self.password_hash, password)

    @classmethod
    def add_user(cls, username, password, role):
        """Add a user to the system."""
        if username in users or username in clients:
            raise ValueError("Username already exists.")
        
        user = cls(username, password, role)
        if role == 'client':
            clients[username] = user
        else:
            users[username] = user
        return user


class EventRequest:
    """A class representing an event request submitted by a client."""

    def __init__(self, client_username, event_name, event_date, budget, details):
        self.id = str(uuid.uuid4())  # Unique tracking ID
        self.client_username = client_username
        self.event_name = event_name
        self.event_date = event_date
        self.budget = budget
        self.details = details
        self.status = "Pending"      # Status can be 'Pending', 'Reviewed', 'Approved', 'Rejected'
        self.stage = "CSO Review"    # Workflow stage
        self.submitted_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def forward_to_fm(self):
        """Forward the request to the Financial Manager."""
        self.stage = "FM Review"
        self.status = "In Progress"

    def forward_to_am(self):
        """Forward the request to the Administration Manager."""
        self.stage = "AM Approval"
        self.status = "Budget Approved"

    def approve(self):
        """Approve the request at the final stage."""
        self.status = "Approved"
        self.stage = "Approved by Admin"

    def reject(self):
        """Reject the request."""
        self.status = "Rejected"
        self.stage = "Rejected"

    @classmethod
    def add_request(cls, client_username, event_name, event_date, budget, details):
        """Add a new event request to the system."""
        event_request = cls(client_username, event_name, event_date, budget, details)
        requests.append(event_request)
        return event_request