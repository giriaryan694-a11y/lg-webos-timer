#!/usr/bin/env python3
import os
import time
import json
import logging
import threading
import secrets
from functools import wraps
from flask import Flask, request, session, redirect, url_for, render_template_string, jsonify
from pywebostv.connection import WebOSClient
from pywebostv.controls import SystemControl

# ==========================================
# CONFIGURATION & LOGGING
# ==========================================
logging.basicConfig(
    filename='server.log', 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
app.secret_key = secrets.token_hex(32) # Secure session key

AUTH_FILE = "auth.txt"
CONFIG_FILE = "tv_config.json"
KEY_FILE = ".tv_key.json"

# Global State for the Background Timer
timer_state = {
    "is_running": False,
    "target_time": 0,
    "ip": ""
}

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def load_auth():
    if not os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, 'w') as f:
            f.write("admin:admin123\n") # Default creds
        logging.info("Created default auth.txt (admin:admin123)")
    
    with open(AUTH_FILE, 'r') as f:
        line = f.readline().strip()
        if ':' in line:
            return line.split(':', 1)
    return ("admin", "admin123")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"ip": ""}

def save_config(ip):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({"ip": ip}, f)
    timer_state["ip"] = ip

timer_state["ip"] = load_config().get("ip", "")

# ==========================================
# SECURITY DECORATORS (Auth & CSRF)
# ==========================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def verify_csrf(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == "POST":
            token = session.get('csrf_token')
            if not token or token != request.form.get('csrf_token') and token != request.headers.get('X-CSRFToken'):
                logging.warning(f"CSRF attempt blocked from {request.remote_addr}")
                return jsonify({"error": "CSRF token missing or invalid"}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def csrf_protect():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)

# ==========================================
# TV CONTROL & BACKGROUND THREAD
# ==========================================
def authenticate_tv(ip):
    """Only performs the handshake to get the pairing token."""
    logging.info(f"Attempting to authenticate TV at {ip}")
    try:
        store = {}
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, 'r') as f:
                store = json.load(f)
        
        client = WebOSClient(ip, secure=True)
        try:
            client.connect()
        except:
            client = WebOSClient(ip, secure=False)
            client.connect()
            
        for status in client.register(store):
            if status == WebOSClient.REGISTERED:
                with open(KEY_FILE, 'w') as f:
                    json.dump(store, f)
                logging.info("TV Authenticated Successfully.")
                return True
        return False
    except Exception as e:
        logging.error(f"Failed to authenticate TV: {e}")
        return False

def power_off_tv(ip):
    """Authenticates (silently if token exists) and sends power off."""
    logging.info(f"Attempting to power off TV at {ip}")
    try:
        store = {}
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, 'r') as f:
                store = json.load(f)
        
        client = WebOSClient(ip, secure=True)
        try:
            client.connect()
        except:
            client = WebOSClient(ip, secure=False)
            client.connect()
            
        for status in client.register(store):
            if status == WebOSClient.REGISTERED:
                with open(KEY_FILE, 'w') as f:
                    json.dump(store, f)
                    
        system = SystemControl(client)
        system.power_off()
        logging.info("TV Powered Off Successfully.")
        return True
    except Exception as e:
        logging.error(f"Failed to turn off TV: {e}")
        return False

def background_timer_worker():
    while True:
        if timer_state["is_running"]:
            if time.time() >= timer_state["target_time"]:
                logging.info("Timer finished! Triggering shutdown.")
                power_off_tv(timer_state["ip"])
                timer_state["is_running"] = False
        time.sleep(1)

# Start the background thread
threading.Thread(target=background_timer_worker, daemon=True).start()

# ==========================================
# HTML TEMPLATES (Modern UI)
# ==========================================
BASE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LG Timer WebUI</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style> body { background-color: #0f172a; color: #f8fafc; } </style>
</head>
<body class="min-h-screen flex items-center justify-center p-4">
    {% block content %}{% endblock %}
</body>
</html>
"""

LOGIN_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="w-full max-w-md bg-gray-800 rounded-xl shadow-2xl p-8 border border-gray-700">
    <h2 class="text-3xl font-bold text-center mb-2 text-blue-400">TV Timer Login</h2>
    <p class="text-center text-gray-500 text-xs mb-6 tracking-widest">Made By Aryan Giri | giriaryan694-a11y</p>
    {% if error %}<p class="text-red-500 text-center mb-4">{{ error }}</p>{% endif %}
    <form method="POST" action="/login" class="space-y-6">
        <input type="hidden" name="csrf_token" value="{{ session.csrf_token }}">
        <div>
            <label class="block text-sm font-medium text-gray-400">Username</label>
            <input type="text" name="username" class="mt-1 w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" required>
        </div>
        <div>
            <label class="block text-sm font-medium text-gray-400">Password</label>
            <input type="password" name="password" class="mt-1 w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" required>
        </div>
        <button type="submit" class="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg transition duration-200">Login</button>
    </form>
</div>
""")

DASHBOARD_HTML = BASE_HTML.replace('{% block content %}{% endblock %}', """
<div class="w-full max-w-md bg-gray-800 rounded-xl shadow-2xl p-6 border border-gray-700">
    <div class="flex justify-between items-center mb-2">
        <h2 class="text-2xl font-bold text-blue-400">Timer Dashboard</h2>
        <a href="/logout" class="text-sm text-gray-400 hover:text-white">Logout</a>
    </div>
    <p class="text-gray-500 text-xs mb-6 tracking-widest border-b border-gray-700 pb-2">Made By Aryan Giri | giriaryan694-a11y</p>

    <div class="mb-6 bg-gray-900 p-4 rounded-lg border border-gray-700">
        <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Target TV IP</label>
        <div class="flex space-x-2">
            <input type="text" id="tv_ip" value="{{ ip }}" placeholder="192.168.x.x" class="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:ring-1 focus:ring-blue-500 outline-none text-sm">
            <button onclick="saveIp()" class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm font-medium transition">Save</button>
        </div>
    </div>

    <div class="text-center mb-8">
        <div id="countdown" class="text-5xl font-mono font-light text-white mb-2 tracking-widest">00:00:00</div>
        <div id="status_text" class="text-sm font-medium text-gray-400">Status: Stopped</div>
    </div>

    <div id="controls" class="space-y-4">
        <div class="flex space-x-2 justify-center">
            <input type="number" id="input_h" min="0" max="23" placeholder="HH" class="w-16 text-center text-xl py-2 bg-gray-900 border border-gray-700 rounded-xl focus:border-blue-500 outline-none">
            <span class="text-xl py-2 text-gray-500">:</span>
            <input type="number" id="input_m" min="0" max="59" placeholder="MM" class="w-16 text-center text-xl py-2 bg-gray-900 border border-gray-700 rounded-xl focus:border-blue-500 outline-none">
            <span class="text-xl py-2 text-gray-500">:</span>
            <input type="number" id="input_s" min="0" max="59" placeholder="SS" class="w-16 text-center text-xl py-2 bg-gray-900 border border-gray-700 rounded-xl focus:border-blue-500 outline-none">
        </div>
        
        <div class="flex space-x-4 mt-6">
            <button onclick="startTimer()" class="flex-1 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl shadow-lg shadow-blue-900/50 transition">Start Timer</button>
            <button onclick="stopTimer()" class="flex-1 py-3 bg-red-600 hover:bg-red-500 text-white font-bold rounded-xl shadow-lg shadow-red-900/50 transition">Cancel</button>
        </div>

        <div class="flex space-x-2 mt-4 pt-4 border-t border-gray-700">
            <button onclick="authTV()" class="flex-1 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition">🔑 Auth TV</button>
            <button onclick="testTV()" class="flex-1 py-2 bg-orange-600 hover:bg-orange-500 text-white text-sm font-medium rounded-lg transition">⚡ Test Shutdown</button>
        </div>
    </div>
</div>

<script>
    const csrfToken = "{{ session.csrf_token }}";
    
    function updateDisplay() {
        fetch('/api/status')
            .then(res => res.json())
            .then(data => {
                if (data.is_running) {
                    let remaining = Math.max(0, Math.floor(data.target_time - (Date.now() / 1000)));
                    let h = Math.floor(remaining / 3600).toString().padStart(2, '0');
                    let m = Math.floor((remaining % 3600) / 60).toString().padStart(2, '0');
                    let s = (remaining % 60).toString().padStart(2, '0');
                    document.getElementById('countdown').innerText = `${h}:${m}:${s}`;
                    document.getElementById('status_text').innerText = "Status: Running";
                    document.getElementById('status_text').className = "text-sm font-medium text-green-400";
                } else {
                    document.getElementById('countdown').innerText = "00:00:00";
                    document.getElementById('status_text').innerText = "Status: Stopped";
                    document.getElementById('status_text').className = "text-sm font-medium text-gray-400";
                }
            });
    }

    function saveIp() {
        let ip = document.getElementById('tv_ip').value;
        fetch('/api/settings', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrfToken},
            body: `ip=${ip}`
        }).then(() => alert('IP Saved!'));
    }

    function startTimer() {
        let h = parseInt(document.getElementById('input_h').value) || 0;
        let m = parseInt(document.getElementById('input_m').value) || 0;
        let s = parseInt(document.getElementById('input_s').value) || 0;
        let total_sec = (h * 3600) + (m * 60) + s;
        if(total_sec <= 0) return alert("Enter a valid time.");
        
        fetch('/api/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrfToken},
            body: `seconds=${total_sec}`
        }).then(updateDisplay);
    }

    function stopTimer() {
        fetch('/api/stop', {
            method: 'POST',
            headers: {'X-CSRFToken': csrfToken}
        }).then(updateDisplay);
    }

    function authTV() {
        alert("Check your TV screen right after clicking OK! Accept the prompt if it appears.");
        fetch('/api/auth', {
            method: 'POST',
            headers: {'X-CSRFToken': csrfToken}
        })
        .then(res => res.json())
        .then(data => alert(data.message || data.error));
    }

    function testTV() {
        if(confirm("Are you sure you want to test the shutdown command right now?")) {
            fetch('/api/test', {
                method: 'POST',
                headers: {'X-CSRFToken': csrfToken}
            })
            .then(res => res.json())
            .then(data => alert(data.message || data.error));
        }
    }

    setInterval(updateDisplay, 1000);
    updateDisplay();
</script>
""")

# ==========================================
# ROUTES
# ==========================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        valid_user, valid_pass = load_auth()
        if request.form['username'] == valid_user and request.form['password'] == valid_pass:
            session['logged_in'] = True
            logging.info(f"Successful login from {request.remote_addr}")
            return redirect(url_for('index'))
        else:
            error = "Invalid Credentials. Try again."
            logging.warning(f"Failed login attempt from {request.remote_addr}")
    return render_template_string(LOGIN_HTML, error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template_string(DASHBOARD_HTML, ip=timer_state["ip"])

# --- API ENDPOINTS ---
@app.route('/api/status', methods=['GET'])
@login_required
def get_status():
    return jsonify(timer_state)

@app.route('/api/start', methods=['POST'])
@login_required
@verify_csrf
def start_timer():
    seconds = int(request.form.get('seconds', 0))
    if seconds > 0:
        timer_state["target_time"] = time.time() + seconds
        timer_state["is_running"] = True
        logging.info(f"Timer started for {seconds} seconds by UI.")
        return jsonify({"status": "started"})
    return jsonify({"error": "Invalid time"}), 400

@app.route('/api/stop', methods=['POST'])
@login_required
@verify_csrf
def stop_timer():
    timer_state["is_running"] = False
    logging.info("Timer stopped by UI.")
    return jsonify({"status": "stopped"})

@app.route('/api/settings', methods=['POST'])
@login_required
@verify_csrf
def update_settings():
    ip = request.form.get('ip', '')
    save_config(ip)
    logging.info(f"TV IP updated to {ip}")
    return jsonify({"status": "saved"})

@app.route('/api/auth', methods=['POST'])
@login_required
@verify_csrf
def auth_tv_api():
    if not timer_state["ip"]:
        return jsonify({"error": "Please save an IP address first."}), 400
    success = authenticate_tv(timer_state["ip"])
    if success:
        return jsonify({"message": "Successfully authenticated and saved token!"})
    return jsonify({"error": "Failed. Is TV on? Did you click Accept?"}), 500

@app.route('/api/test', methods=['POST'])
@login_required
@verify_csrf
def test_shutdown_api():
    if not timer_state["ip"]:
        return jsonify({"error": "Please save an IP address first."}), 400
    success = power_off_tv(timer_state["ip"])
    if success:
        return jsonify({"message": "Shutdown command sent!"})
    return jsonify({"error": "Failed to shut down. Did you Authenticate first?"}), 500


if __name__ == '__main__':
    logging.info("Starting LG Timer WebUI Server...")
    print("[*] Server running on http://0.0.0.0:5000")
    print("[*] Default login is admin:admin123 (check auth.txt)")
    # Run securely accessible on local network
    app.run(host='0.0.0.0', port=5000, debug=False)
