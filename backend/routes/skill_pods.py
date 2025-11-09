from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
import json
from backend.models.database import get_db
from backend.routes.ai_mentor import get_ai_mentor_response

bp = Blueprint('skill_pods', __name__, url_prefix='/api/skill-pods')

SKILL_PATHS = {
    'fullstack': {
        'title': 'Full Stack Development',
        'description': 'Learn web development from front-end to back-end',
        'skills': ['HTML/CSS', 'JavaScript', 'Python/Flask', 'Database Design', 'API Development'],
        'mentor_topics': ['coding challenges', 'project architecture', 'debugging tips', 'best practices'],
        'assessment_topics': ['frontend', 'backend', 'database', 'api_design', 'system_design']
    },
    'ml_engineer': {
        'title': 'Machine Learning Engineer',
        'description': 'Master AI and machine learning technologies',
        'skills': ['Python', 'Mathematics', 'Machine Learning', 'Deep Learning', 'Data Processing'],
        'mentor_topics': ['ml algorithms', 'model training', 'data preprocessing', 'model deployment'],
        'assessment_topics': ['python', 'math_stats', 'ml_concepts', 'deep_learning', 'data_analysis']
    },
    'vlsi': {
        'title': 'VLSI Engineer',
        'description': 'Learn chip design and verification',
        'skills': ['Digital Design', 'Verilog', 'ASIC Design', 'Verification', 'Physical Design'],
        'mentor_topics': ['circuit design', 'verification methods', 'timing analysis', 'power optimization'],
        'assessment_topics': ['digital_design', 'hdl', 'verification', 'physical_design', 'timing']
    },
    'data_science': {
        'title': 'Data Scientist',
        'description': 'Learn data analysis and visualization',
        'skills': ['Python', 'Statistics', 'Data Analysis', 'Visualization', 'Big Data'],
        'mentor_topics': ['data analysis', 'statistical methods', 'visualization techniques', 'big data tools'],
        'assessment_topics': ['python', 'statistics', 'data_analysis', 'visualization', 'big_data']
    },
    'cloud_engineer': {
        'title': 'Cloud Engineer',
        'description': 'Master cloud platforms and DevOps',
        'skills': ['AWS/Azure', 'Docker', 'Kubernetes', 'CI/CD', 'Infrastructure as Code'],
        'mentor_topics': ['cloud architecture', 'container orchestration', 'devops practices', 'security'],
        'assessment_topics': ['cloud_platforms', 'containers', 'devops', 'security', 'infrastructure']
    }
}

@bp.route('/paths', methods=['GET'])
def get_skill_paths():
    """Get all available skill paths"""
    return jsonify({
        'paths': [
            {
                'id': path_id,
                'title': info['title'],
                'description': info['description'],
                'skills': info['skills']
            }
            for path_id, info in SKILL_PATHS.items()
        ]
    })

@bp.route('/enroll', methods=['POST'])
@jwt_required()
def enroll_skill_path():
    """Enroll in a specific skill path"""
    user_id = get_jwt_identity()
    data = request.json
    path_id = data.get('path_id')
    
    if path_id not in SKILL_PATHS:
        return jsonify({'error': 'Invalid skill path'}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if already enrolled
    cursor.execute('''
        SELECT id FROM skill_enrollments 
        WHERE user_id = ? AND path_id = ?
    ''', (user_id, path_id))
    
    if cursor.fetchone():
        conn.close()
        return jsonify({'message': 'Already enrolled in this skill path'}), 200
        
    # Enroll user
    cursor.execute('''
        INSERT INTO skill_enrollments (user_id, path_id, progress, completed_skills)
        VALUES (?, ?, 0, ?)
    ''', (user_id, path_id, json.dumps([])))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'message': f'Successfully enrolled in {SKILL_PATHS[path_id]["title"]}'
    }), 201

@bp.route('/progress/<path_id>', methods=['GET'])
@jwt_required()
def get_progress(path_id):
    """Get user's progress in a skill path"""
    user_id = get_jwt_identity()
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT progress, completed_skills, assessment_results
        FROM skill_enrollments
        WHERE user_id = ? AND path_id = ?
    ''', (user_id, path_id))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'error': 'Not enrolled in this skill path'}), 404
        
    return jsonify({
        'progress': row[0],
        'completed_skills': json.loads(row[1] or '[]'),
        'assessment_results': json.loads(row[2] or '{}')
    })

@bp.route('/mentor/<path_id>', methods=['POST'])
@jwt_required()
def get_mentor_guidance(path_id):
    """Get AI mentor guidance for a specific topic"""
    if path_id not in SKILL_PATHS:
        return jsonify({'error': 'Invalid skill path'}), 400
        
    data = request.json
    topic = data.get('topic')
    question = data.get('question')
    
    if not topic or not question:
        return jsonify({'error': 'Topic and question are required'}), 400
        
    # Get mentor response using AI
    context = f"As a mentor for {SKILL_PATHS[path_id]['title']}, focusing on {topic}"
    response = get_ai_mentor_response(context, question)
    
    return jsonify({'response': response})

@bp.route('/assessment/<path_id>', methods=['POST'])
@jwt_required()
def submit_assessment(path_id):
    """Submit an assessment for a skill path"""
    if path_id not in SKILL_PATHS:
        return jsonify({'error': 'Invalid skill path'}), 400
        
    user_id = get_jwt_identity()
    data = request.json
    topic = data.get('topic')
    answers = data.get('answers')
    
    if not topic or not answers:
        return jsonify({'error': 'Topic and answers are required'}), 400
        
    if topic not in SKILL_PATHS[path_id]['assessment_topics']:
        return jsonify({'error': 'Invalid assessment topic'}), 400
        
    # Calculate score (simplified for demo)
    score = len([a for a in answers if a.get('correct', False)]) / len(answers) * 100
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get current assessment results
    cursor.execute('''
        SELECT assessment_results FROM skill_enrollments
        WHERE user_id = ? AND path_id = ?
    ''', (user_id, path_id))
    
    row = cursor.fetchone()
    if not row:
        return jsonify({'error': 'Not enrolled in this skill path'}), 404
        
    results = json.loads(row[0] or '{}')
    results[topic] = {
        'score': score,
        'completed_at': datetime.now().isoformat()
    }
    
    # Update assessment results and progress
    cursor.execute('''
        UPDATE skill_enrollments
        SET assessment_results = ?,
            progress = ?
        WHERE user_id = ? AND path_id = ?
    ''', (
        json.dumps(results),
        calculate_overall_progress(results, SKILL_PATHS[path_id]['assessment_topics']),
        user_id,
        path_id
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'topic': topic,
        'score': score,
        'message': get_score_feedback(score)
    })

def calculate_overall_progress(results, total_topics):
    """Calculate overall progress based on completed assessments"""
    if not results:
        return 0
    completed = len(results.keys())
    return (completed / len(total_topics)) * 100

def get_score_feedback(score):
    """Get feedback message based on assessment score"""
    if score >= 90:
        return "Excellent! You've mastered this topic! 🎉"
    elif score >= 70:
        return "Good job! You're showing strong understanding! 👍"
    elif score >= 50:
        return "You're making progress! Keep practicing! 💪"
    else:
        return "Keep learning! Review the material and try again! 📚"