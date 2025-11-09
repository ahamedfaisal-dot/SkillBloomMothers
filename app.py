from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
import os

if 'GEMINI_API_KEY' not in os.environ:
    os.environ['GEMINI_API_KEY'] = 'AIzaSyAVWCNsilXM76wNf1Mb41jhp0kqrO8SyZU'

from backend.models.database import init_db
from backend.routes import auth, assessment, pods, ai_mentor, baby_monitor

app = Flask(__name__, static_folder='static', template_folder='templates')

app.config['JWT_SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'skillbloom-secret-key-2025')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

CORS(app)
jwt = JWTManager(app)

# Friendly JWT error handlers to return JSON messages instead of default HTML/empty 422 responses
@jwt.unauthorized_loader
def unauthorized_callback(reason):
    # Called when no JWT is present in the request
    return jsonify({'error': 'Authorization header missing or not provided', 'reason': reason}), 401

@jwt.invalid_token_loader
def invalid_token_callback(reason):
    # Called when a token is provided but invalid (malformed/signature)
    return jsonify({'error': 'Invalid token', 'reason': reason}), 422

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token has expired'}), 401

@jwt.needs_fresh_token_loader
def needs_fresh_token_callback():
    return jsonify({'error': 'Fresh token required'}), 401

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token has been revoked'}), 401

init_db()

app.register_blueprint(auth.bp)
app.register_blueprint(assessment.bp)
app.register_blueprint(pods.bp)
app.register_blueprint(ai_mentor.bp)
app.register_blueprint(baby_monitor.bp)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/assessment')
def assessment_page():
    return render_template('assessment.html')

@app.route('/pods')
def pods_page():
    return render_template('pods.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    return render_template('signup.html')

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'message': 'SkillBloom API is running'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
