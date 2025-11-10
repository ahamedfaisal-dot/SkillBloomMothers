import sqlite3
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE_NAME = 'skillbloom.db'

def get_db():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            career_gap INTEGER DEFAULT 0,
            skills TEXT,
            personality TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            test_type TEXT NOT NULL,
            answers TEXT,
            score REAL,
            personality_type TEXT,
            skill_category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            pod_type TEXT NOT NULL,
            progress INTEGER DEFAULT 0,
            badge_earned BOOLEAN DEFAULT 0,
            completed_at TIMESTAMP,
            data TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Add skill_enrollments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skill_enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            path_id TEXT NOT NULL,
            progress INTEGER DEFAULT 0,
            completed_skills TEXT,  -- JSON array of completed skill IDs
            assessment_results TEXT,  -- JSON object with assessment scores
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            query TEXT NOT NULL,
            response TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS baby_monitor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            temperature REAL,
            motion TEXT,
            sleep_status TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Profiles for baby monitor (per-user settings)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS baby_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT,
            weight REAL,
            height REAL,
            camera_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

def create_user(name, email, password, role='user'):
    conn = get_db()
    cursor = conn.cursor()
    hashed_password = generate_password_hash(password)
    
    try:
        cursor.execute('''
            INSERT INTO users (name, email, password, role)
            VALUES (?, ?, ?, ?)
        ''', (name, email, hashed_password, role))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def get_user_by_email(email):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_id(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def verify_password(stored_password, provided_password):
    return check_password_hash(stored_password, provided_password)

def update_user_profile(user_id, skills=None, personality=None, career_gap=None):
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        updates = []
        params = []
        
        if skills is not None:
            updates.append("skills = ?")
            params.append(json.dumps(skills) if isinstance(skills, list) else skills)
        if personality is not None:
            updates.append("personality = ?")
            params.append(personality)
        if career_gap is not None:
            updates.append("career_gap = ?")
            params.append(career_gap)
        
        if updates:
            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            
        # Ensure user exists after update
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return False
            
        return True
    except Exception as e:
        print(f"Error updating user profile: {str(e)}")
        return False
    finally:
        conn.close()

def save_ai_chat(user_id, query, response):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO ai_logs (user_id, query, response)
            VALUES (?, ?, ?)
        ''', (user_id, query, response))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving AI chat: {str(e)}")
        return False
    finally:
        conn.close()

def save_assessment(user_id, test_type, answers, score, personality_type=None, skill_category=None):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO assessments (
                user_id, test_type, answers, score, 
                personality_type, skill_category
            )
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, test_type, json.dumps(answers), score, 
              personality_type, skill_category))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving assessment: {str(e)}")
        return False
    finally:
        conn.close()
