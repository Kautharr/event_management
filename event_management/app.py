from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Mock database for users and event requests
users = {
    'cso': {'password_hash': generate_password_hash('password'), 'role': 'cso'},
    'janet': {'password_hash': generate_password_hash('password'), 'role': 'senior_cso'},
    'Finance': {'password_hash': generate_password_hash('1234'), 'role': 'fm'},
    'Admin': {'password_hash': generate_password_hash('2345'), 'role': 'am'}
}
clients = {}
requests = []

class EventRequest:
    def __init__(self, client_username, event_name, event_date, budget, details):
        self.id = str(uuid.uuid4())
        self.client_username = client_username
        self.event_name = event_name
        self.event_date = event_date
        self.budget = budget
        self.details = details
        self.status = "Pending"
        self.stage = "CSO Review"
        self.submitted_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    role = session.get('role')
    return redirect(url_for(f"{role}_dashboard"))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username) or clients.get(username)

        if user and check_password_hash(user['password_hash'], password):
            session['username'] = username
            session['role'] = user['role']
            flash('Login successful!', 'success')
            return redirect(url_for(f"{user['role']}_dashboard"))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users or username in clients:
            flash('Username already exists.', 'danger')
        else:
            clients[username] = {'password_hash': generate_password_hash(password), 'role': 'client'}
            flash('Account created successfully. Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/client_dashboard')
def client_dashboard():
    if 'username' not in session or session.get('role') != 'client':
        flash("Access denied!", "danger")
        return redirect(url_for("login"))
    client_requests = [req for req in requests if req.client_username == session['username']]
    return render_template('client_dashboard.html', requests=client_requests)

@app.route('/forward_to_am/<request_id>', methods=['POST'])
def forward_to_am(request_id):
    if 'username' not in session or session.get('role') != 'fm':
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    # Find the request by ID and update its stage to "AM Approval"
    for request in requests:
        if request.id == request_id:
            request.stage = "AM Approval"
            request.status = "Under Review by AM"
            flash("Request forwarded to Administration Manager.", "success")
            break
    else:
        flash("Request not found.", "danger")

    return redirect(url_for('fm_dashboard'))

@app.route('/submit_request', methods=['POST'])
def submit_request():
    if 'username' not in session or session.get('role') not in ['client', 'cso']:
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    event_name = request.form['event_name']
    event_date = request.form['event_date']
    budget = float(request.form['budget'])
    details = request.form['details']
    
    if session.get('role') == 'cso':
        client_username = request.form['client_username']
    else:
        client_username = session['username']

    new_request = EventRequest(client_username=client_username, event_name=event_name,
                               event_date=event_date, budget=budget, details=details)
    requests.append(new_request)
    flash("Event request submitted successfully.", "success")
    
    if session.get('role') == 'client':
        return redirect(url_for('client_dashboard'))
    return redirect(url_for('cso_dashboard'))

@app.route('/approve_request/<request_id>', methods=['POST'])
def approve_request(request_id):
    if 'username' not in session or session.get('role') != 'am':
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    # Find the request by ID and update its status to "Approved"
    for request in requests:
        if request.id == request_id:
            request.stage = "Approved"
            request.status = "Approved by AM"
            flash("Request has been approved.", "success")
            break
    else:
        flash("Request not found.", "danger")

    return redirect(url_for('am_dashboard'))

@app.route('/reject_request_am/<request_id>', methods=['POST'])
def reject_request_am(request_id):
    if 'username' not in session or session.get('role') != 'am':
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    # Find the request by ID and update its status to "Rejected by AM"
    for request in requests:
        if request.id == request_id:
            request.stage = "Rejected"
            request.status = "Rejected by AM"
            flash("Request has been rejected by Administration Manager.", "success")
            break
    else:
        flash("Request not found.", "danger")

    return redirect(url_for('am_dashboard'))

@app.route('/cso_dashboard', methods=['GET', 'POST'])
def cso_dashboard():
    if 'username' not in session or session.get('role') != 'cso':
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    if request.method == 'POST':
        # Form submission for creating a new request by CSO
        event_name = request.form['event_name']
        event_date = request.form['event_date']
        budget = float(request.form['budget'])
        details = request.form['details']
        client_username = request.form['client_username']

        new_request = EventRequest(client_username=client_username, event_name=event_name,
                                   event_date=event_date, budget=budget, details=details)
        requests.append(new_request)
        flash("Event request submitted to Senior CSO.", "success")
    
    # Display all requests on the CSO dashboard
    return render_template('cso_dashboard.html', requests=requests)

@app.route('/forward_to_fm/<request_id>', methods=['POST'])
def forward_to_fm(request_id):
    if 'username' not in session or session.get('role') != 'senior_cso':
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    # Find the request by ID and update its stage
    for request in requests:
        if request.id == request_id:
            request.stage = "FM Review"
            request.status = "In Progress"
            flash("Request forwarded to Financial Manager.", "success")
            break
    else:
        flash("Request not found.", "danger")

    return redirect(url_for('senior_cso_dashboard'))

@app.route('/reject_request/<request_id>', methods=['POST'])
def reject_request(request_id):
    if 'username' not in session or session.get('role') != 'senior_cso':
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    # Find the request by ID and update its status to "Rejected"
    for request in requests:
        if request.id == request_id:
            request.stage = "Rejected"
            request.status = "Rejected"
            flash("Request has been rejected.", "success")
            break
    else:
        flash("Request not found.", "danger")

    return redirect(url_for('senior_cso_dashboard'))

@app.route('/senior_cso_dashboard')
def senior_cso_dashboard():
    if 'username' not in session or session.get('role') != 'senior_cso':
        flash("Access denied!", "danger")
        return redirect(url_for("login"))
    pending_requests = [req for req in requests if req.stage == "CSO Review"]
    return render_template('senior_cso_dashboard.html', requests=pending_requests)

@app.route('/fm_dashboard')
def fm_dashboard():
    if 'username' not in session or session.get('role') != 'fm':
        flash("Access denied!", "danger")
        return redirect(url_for("login"))
    requests_for_review = [req for req in requests if req.stage == "FM Review"]
    return render_template('fm_dashboard.html', requests=requests_for_review)

@app.route('/am_dashboard')
def am_dashboard():
    if 'username' not in session or session.get('role') != 'am':
        flash("Access denied!", "danger")
        return redirect(url_for("login"))
    final_requests = [req for req in requests if req.stage == "AM Approval"]
    return render_template('am_dashboard.html', requests=final_requests)

if __name__ == '__main__':
    app.run(debug=True)