from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
import json
from backend.models.database import get_db

bp = Blueprint('pods', __name__, url_prefix='/api/pods')

POD_TYPES = ['skill', 'company', 'health', 'baby_monitor', 'mental_health', 'post_placement']

@bp.route('/enroll', methods=['POST'])
def enroll_pod():
    # Allow optional JWT for quick demo: if no valid token, return a mock response
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except Exception:
        user_id = None

    data = request.json or {}
    pod_type = data.get('pod_type')

    if pod_type not in POD_TYPES:
        return jsonify({'error': 'Invalid pod type'}), 400

    # If unauthenticated, return a demo response (no DB writes)
    if user_id is None:
        return jsonify({'message': f'(demo) Successfully enrolled in {pod_type} pod', 'pod_id': None}), 201

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM pods WHERE user_id = ? AND pod_type = ?', (user_id, pod_type))
    existing = cursor.fetchone()

    if existing:
        conn.close()
        return jsonify({'message': 'Already enrolled in this pod'}), 200

    cursor.execute('''
        INSERT INTO pods (user_id, pod_type, progress, data)
        VALUES (?, ?, ?, ?)
    ''', (user_id, pod_type, 0, json.dumps({})))
    conn.commit()
    pod_id = cursor.lastrowid
    conn.close()

    return jsonify({
        'message': f'Successfully enrolled in {pod_type} pod',
        'pod_id': pod_id
    }), 201

@bp.route('/progress', methods=['GET'])
def get_progress():
    # Allow optional JWT so unauthenticated users can see demo data while testing UI
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except Exception:
        user_id = None

    if user_id is None:
        # Return sample/demo pod progress data
        demo = [
            {'id': None, 'user_id': None, 'pod_type': 'skill', 'progress': 40, 'badge_earned': 0, 'completed_at': None, 'data': '{}'},
            {'id': None, 'user_id': None, 'pod_type': 'company', 'progress': 60, 'badge_earned': 0, 'completed_at': None, 'data': '{}'},
            {'id': None, 'user_id': None, 'pod_type': 'health', 'progress': 20, 'badge_earned': 0, 'completed_at': None, 'data': '{}'}
        ]
        return jsonify(demo), 200

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM pods WHERE user_id = ?', (user_id,))
    pods = cursor.fetchall()
    conn.close()

    return jsonify([dict(row) for row in pods]), 200

@bp.route('/update', methods=['POST'])
def update_progress():
    # Support optional JWT for demo mode
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except Exception:
        user_id = None

    data = request.json or {}
    pod_type = data.get('pod_type')
    progress = data.get('progress', 0)
    pod_data = data.get('data', {})

    badge_earned = progress >= 100

    # If unauthenticated, return a mock success response without DB writes
    if user_id is None:
        message = 'Pod progress updated (demo)'
        if badge_earned and progress == 100:
            message = f'Congratulations! You earned the {pod_type.replace("_", " ").title()} Badge!'
        return jsonify({'message': message, 'progress': progress, 'badge_earned': bool(badge_earned)}), 200

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE pods 
        SET progress = ?, badge_earned = ?, data = ?
        WHERE user_id = ? AND pod_type = ?
    ''', (progress, badge_earned, json.dumps(pod_data), user_id, pod_type))

    if cursor.rowcount == 0:
        cursor.execute('''
            INSERT INTO pods (user_id, pod_type, progress, badge_earned, data)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, pod_type, progress, badge_earned, json.dumps(pod_data)))

    conn.commit()
    conn.close()

    message = 'Pod progress updated'
    if badge_earned and progress == 100:
        message = f'Congratulations! You earned the {pod_type.replace("_", " ").title()} Badge!'

    return jsonify({
        'message': message,
        'progress': progress,
        'badge_earned': badge_earned
    }), 200

@bp.route('/health/log', methods=['POST'])
@jwt_required()
def log_health():
    user_id = get_jwt_identity()
    data = request.json
    
    mood = data.get('mood')
    sleep = data.get('sleep')
    energy = data.get('energy')
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT data FROM pods WHERE user_id = ? AND pod_type = ?', (user_id, 'health'))
    row = cursor.fetchone()
    
    if row:
        health_data = json.loads(row[0]) if row[0] else {}
    else:
        health_data = {}
        cursor.execute('''
            INSERT INTO pods (user_id, pod_type, progress, data)
            VALUES (?, ?, ?, ?)
        ''', (user_id, 'health', 0, json.dumps(health_data)))
    
    if 'logs' not in health_data:
        health_data['logs'] = []
    
    from datetime import datetime
    health_data['logs'].append({
        'mood': mood,
        'sleep': sleep,
        'energy': energy,
        'timestamp': datetime.now().isoformat()
    })
    
    health_data['logs'] = health_data['logs'][-30:]
    
    cursor.execute('''
        UPDATE pods SET data = ? WHERE user_id = ? AND pod_type = ?
    ''', (json.dumps(health_data), user_id, 'health'))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Health data logged successfully'}), 200

@bp.route('/mental/journal', methods=['POST'])
@jwt_required()
def add_journal():
    user_id = get_jwt_identity()
    data = request.json
    entry = data.get('entry')
    emotion = data.get('emotion')
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT data FROM pods WHERE user_id = ? AND pod_type = ?', (user_id, 'mental_health'))
    row = cursor.fetchone()
    
    if row:
        mental_data = json.loads(row[0]) if row[0] else {}
    else:
        mental_data = {}
        cursor.execute('''
            INSERT INTO pods (user_id, pod_type, progress, data)
            VALUES (?, ?, ?, ?)
        ''', (user_id, 'mental_health', 0, json.dumps(mental_data)))
    
    if 'journal' not in mental_data:
        mental_data['journal'] = []
    
    from datetime import datetime
    mental_data['journal'].append({
        'entry': entry,
        'emotion': emotion,
        'timestamp': datetime.now().isoformat()
    })
    
    cursor.execute('''
        UPDATE pods SET data = ? WHERE user_id = ? AND pod_type = ?
    ''', (json.dumps(mental_data), user_id, 'mental_health'))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Journal entry saved'}), 200

@bp.route('/mental/journal', methods=['GET'])
@jwt_required()
def get_journal():
    user_id = get_jwt_identity()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT data FROM pods WHERE user_id = ? AND pod_type = ?', (user_id, 'mental_health'))
    row = cursor.fetchone()
    conn.close()
    
    if row and row[0]:
        mental_data = json.loads(row[0])
        return jsonify(mental_data.get('journal', [])), 200
    
    return jsonify([]), 200


@bp.route('/details/<pod_type>', methods=['GET'])
def pod_details(pod_type):
    """Return task list for a pod. If user has saved data, include completed tasks."""
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except Exception:
        user_id = None

    TASKS = {
        'skill': [
            {'id': 1, 'title': 'Complete Resume Module', 'desc': 'Revise and polish your resume', 'progress': 20},
            {'id': 2, 'title': 'Interview Prep', 'desc': 'Practice common interview questions', 'progress': 25},
            {'id': 3, 'title': 'Networking', 'desc': 'Attend a virtual networking session', 'progress': 15}
        ],
        'company': [
            {'id': 1, 'title': 'Onboard to Project', 'desc': 'Read project brief and setup environment', 'progress': 20},
            {'id': 2, 'title': 'Implement Feature', 'desc': 'Complete assigned feature', 'progress': 50},
            {'id': 3, 'title': 'Submit Project', 'desc': 'Finalize and submit for review', 'progress': 30}
        ],
        'health': [
            {'id': 1, 'title': 'Log Daily Wellness', 'desc': 'Submit mood and sleep data', 'progress': 10},
            {'id': 2, 'title': 'Follow Wellness Plan', 'desc': 'Complete daily wellness activity', 'progress': 20}
        ],
        'baby_monitor': [
            {'id': 1, 'title': 'Connect Device', 'desc': 'Ensure baby monitor is connected', 'progress': 10},
            {'id': 2, 'title': 'Review Alerts', 'desc': 'Check recent alerts and trends', 'progress': 20}
        ],
        'mental_health': [
            {'id': 1, 'title': 'Daily Journal', 'desc': 'Write a short journal entry', 'progress': 5},
            {'id': 2, 'title': 'Mindfulness Exercise', 'desc': 'Complete a 10-minute mindfulness', 'progress': 15}
        ],
        'post_placement': [
            {'id': 1, 'title': 'Set Career Goals', 'desc': 'Define short and mid-term goals', 'progress': 10},
            {'id': 2, 'title': 'Skill Checkpoint', 'desc': 'Complete a skills validation task', 'progress': 20}
        ]
    }

    tasks = TASKS.get(pod_type, [])

    completed = []
    if user_id is not None:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT data FROM pods WHERE user_id = ? AND pod_type = ?', (user_id, pod_type))
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            try:
                pdata = json.loads(row[0])
                completed = pdata.get('completed_tasks', [])
            except Exception:
                completed = []

    # mark tasks complete flag
    for t in tasks:
        t['completed'] = t['id'] in completed

    return jsonify({'pod_type': pod_type, 'tasks': tasks}), 200
