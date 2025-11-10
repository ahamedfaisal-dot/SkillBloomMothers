from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.database import get_db
import random
from datetime import datetime, timedelta

bp = Blueprint('baby_monitor', __name__, url_prefix='/api/baby')

MOTION_STATES = ['Sleeping', 'Moving', 'Awake', 'Restless']
SLEEP_STATES = ['Deep Sleep', 'Light Sleep', 'Awake', 'REM Sleep']

def generate_mock_data():
    temperature = round(random.uniform(36.5, 37.5), 1)
    motion = random.choice(MOTION_STATES)
    sleep_status = random.choice(SLEEP_STATES)
    
    alert = None
    if temperature > 37.3 or motion == 'Restless':
        if random.random() > 0.7:
            alert = "Unusual activity detected"
    
    return {
        'temperature': temperature,
        'motion': motion,
        'sleep_status': sleep_status,
        'alert': alert,
        'timestamp': datetime.now().isoformat()
    }

@bp.route('/current', methods=['GET'])
@jwt_required()
def get_current_data():
    user_id = get_jwt_identity()
    
    data = generate_mock_data()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO baby_monitor_data (user_id, temperature, motion, sleep_status)
        VALUES (?, ?, ?, ?)
    ''', (user_id, data['temperature'], data['motion'], data['sleep_status']))
    conn.commit()
    conn.close()
    
    return jsonify(data), 200

@bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    user_id = get_jwt_identity()
    limit = request.args.get('limit', 50, type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM baby_monitor_data 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (user_id, limit))
    history = cursor.fetchall()
    conn.close()
    
    return jsonify([dict(row) for row in history]), 200

@bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    user_id = get_jwt_identity()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT temperature, motion, sleep_status, timestamp 
        FROM baby_monitor_data 
        WHERE user_id = ? AND timestamp >= datetime('now', '-24 hours')
        ORDER BY timestamp DESC
    ''', (user_id,))
    recent_data = cursor.fetchall()
    conn.close()
    
    if not recent_data:
        for i in range(20):
            data = generate_mock_data()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO baby_monitor_data (user_id, temperature, motion, sleep_status)
                VALUES (?, ?, ?, ?)
            ''', (user_id, data['temperature'], data['motion'], data['sleep_status']))
            conn.commit()
            conn.close()
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT temperature, motion, sleep_status, timestamp 
            FROM baby_monitor_data 
            WHERE user_id = ?
            ORDER BY timestamp DESC LIMIT 20
        ''', (user_id,))
        recent_data = cursor.fetchall()
        conn.close()
    
    temps = [row[0] for row in recent_data]
    avg_temp = sum(temps) / len(temps) if temps else 37.0
    
    motion_counts = {}
    for row in recent_data:
        motion = row[1]
        motion_counts[motion] = motion_counts.get(motion, 0) + 1
    
    return jsonify({
        'average_temperature': round(avg_temp, 1),
        'motion_distribution': motion_counts,
        'total_readings': len(recent_data),
        'last_updated': datetime.now().isoformat()
    }), 200


@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, user_id, name, weight, height, camera_url, created_at, updated_at FROM baby_profiles WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({}), 200
    return jsonify(dict(row)), 200


@bp.route('/profile', methods=['POST'])
@jwt_required()
def save_profile():
    user_id = get_jwt_identity()
    body = request.get_json() or {}
    name = body.get('name')
    weight = body.get('weight')
    height = body.get('height')
    camera_url = body.get('camera_url')

    conn = get_db()
    cursor = conn.cursor()
    # check if exists
    cursor.execute('SELECT id FROM baby_profiles WHERE user_id = ?', (user_id,))
    existing = cursor.fetchone()
    try:
        if existing:
            cursor.execute('''
                UPDATE baby_profiles
                SET name = ?, weight = ?, height = ?, camera_url = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (name, weight, height, camera_url, user_id))
        else:
            cursor.execute('''
                INSERT INTO baby_profiles (user_id, name, weight, height, camera_url)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, name, weight, height, camera_url))
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500
    conn.close()
    return jsonify({'status': 'saved'}), 200
