from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = "supersecretkey"

# actors
users = {
    'sarah': {'password_hash': generate_password_hash('cso'), 'role': 'cso'},
    'sam': {'password_hash': generate_password_hash('cso'), 'role': 'cso'},
    'judy': {'password_hash': generate_password_hash('cso'), 'role': 'cso'},
    'carine': {'password_hash': generate_password_hash('cso'), 'role': 'cso'},
    'janet': {'password_hash': generate_password_hash('janet'), 'role': 'senior_cso'},
    'alice': {'password_hash': generate_password_hash('alice'), 'role': 'fm'},
    'mike': {'password_hash': generate_password_hash('mike'), 'role': 'am'}
}

# event requests storage
event_requests = []

class EventRequest:
    def __init__(self, record_number, client_name, event_type, start_date, end_date, attendees, preferences, budget):
        self.id = str(uuid.uuid4())
        self.record_number = record_number
        self.client_name = client_name
        self.event_type = event_type
        self.start_date = start_date
        self.end_date = end_date
        self.attendees = attendees
        self.preferences = preferences
        self.budget = budget
        self.status = "Pending"
        self.stage = "CSO Review"
        self.submitted_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for(f"{session['role']}_dashboard"))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username) 

        if user and check_password_hash(user['password_hash'], password):
            session['username'] = username
            session['role'] = user['role']
            flash('Login successful!', 'success')
            
            # redirect based on user role
            if user['role'] == 'cso':
                return redirect(url_for('cso_dashboard'))
            elif user['role'] == 'senior_cso':
                return redirect(url_for('senior_cso_dashboard'))
            elif user['role'] == 'fm':
                return redirect(url_for('fm_dashboard'))
            elif user['role'] == 'am':
                return redirect(url_for('am_dashboard'))
            else:
                flash('Access denied!', 'danger')
                return redirect(url_for('login'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/submit_request', methods=['POST'])
def submit_request():
    if 'username' not in session or session.get('role') != 'cso':
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    # Retrieve form data
    record_number = request.form.get('record_number')
    client_name = request.form.get('client_name')
    event_type = request.form.get('event_type')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    budget = request.form.get('budget')
    details = request.form.get('details')

    # Check for missing fields
    if not record_number or not client_name or not event_type or not start_date or not end_date or not budget:
        flash("Please fill in all required fields.", "danger")
        return redirect(url_for('cso_dashboard'))

    # If all fields are provided, proceed with submission
    status = "Pending Approval by Senior CSO"
    event_requests.append({
        'record_number': record_number,
        'client_name': client_name,
        'event_type': event_type,
        'start_date': start_date,
        'end_date': end_date,
        'budget': budget,
        'details': details,
        'status': status,
    })

    flash(f"Event request '{client_name} - {event_type}' submitted successfully.", "success")
    return redirect(url_for('cso_dashboard'))

    

    

@app.route('/cso_dashboard', methods=['GET', 'POST'])
def cso_dashboard():
    if 'username' not in session or session.get('role') != 'cso':
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    if request.method == 'POST':
        # collect data from the form submission
        record_number = request.form['record_number']
        client_name = request.form['client_name']
        event_type = request.form['event_type']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        attendees = request.form['attendees']
        preferences = request.form.getlist('preferences')
        budget = request.form['budget']

        # new EventRequest object
        new_request = EventRequest(
            record_number=record_number,
            client_name=client_name,
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
            attendees=attendees,
            preferences=preferences,
            budget=budget
        )
        event_requests.append(new_request)
        flash("Event request recorded successfully.", "success")
    
    return render_template('cso_dashboard.html', records=event_requests)

@app.route('/senior_cso_dashboard')
def senior_cso_dashboard():
    if 'username' not in session or session.get('role') != 'senior_cso':
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    # Pass all requests to the template
    return render_template('senior_cso_dashboard.html', requests=event_requests)

from datetime import datetime

@app.route('/approve_request/<record_number>', methods=['POST'])
def approve_request(record_number):
    if 'username' not in session or session.get('role') != 'senior_cso':
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    # Retrieve meeting_time from the form
    meeting_time = request.form.get('meeting_time')
    
    # Find the request by record_number and update its status and meeting_time
    for req in event_requests:  # Change 'request' to 'req' to avoid conflict
        if req['record_number'] == record_number:
            req['status'] = "Meeting Arranged"
            req['meeting_time'] = meeting_time
            flash("Meeting arranged successfully.", "success")
            break
    else:
        flash("Request not found.", "danger")

    return redirect(url_for('senior_cso_dashboard'))


@app.route('/reject_request/<record_number>', methods=['POST'])
def reject_request(record_number):
    if 'username' not in session or session.get('role') != 'senior_cso':
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    # Find the request by record_number and update its status to "Rejected"
    for request in event_requests:
        if request['record_number'] == record_number:
            request['status'] = "Rejected"
            flash("Request rejected.", "success")
            break
    else:
        flash("Request not found.", "danger")

    return redirect(url_for('senior_cso_dashboard'))

@app.route('/fm_dashboard')
def fm_dashboard():
    if 'username' not in session or session.get('role') != 'fm':
        flash("Access denied!", "danger")
        return redirect(url_for("login"))
    return render_template('fm_dashboard.html', records=event_requests)

@app.route('/am_dashboard')
def am_dashboard():
    if 'username' not in session or session.get('role') != 'am':
        flash("Access denied!", "danger")
        return redirect(url_for("login"))
    return render_template('am_dashboard.html', records=event_requests)

if __name__ == '__main__':
    app.run(debug=True)