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
