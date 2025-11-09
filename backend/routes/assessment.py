from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
from backend.models.database import get_db, update_user_profile

bp = Blueprint('assessment', __name__, url_prefix='/api/assessment')

PERSONALITY_QUESTIONS = [
    {"id": 1, "question": "I enjoy solving logical problems", "type": "analytical"},
    {"id": 2, "question": "I like working in teams", "type": "collaborative"},
    {"id": 3, "question": "I'm confident managing multiple tasks", "type": "organizational"},
    {"id": 4, "question": "I prefer creative solutions over standard ones", "type": "creative"},
    {"id": 5, "question": "I'm empathetic and understand others' emotions", "type": "empathetic"},
    {"id": 6, "question": "I enjoy learning new technologies", "type": "analytical"},
    {"id": 7, "question": "I like helping others succeed", "type": "empathetic"},
    {"id": 8, "question": "I'm detail-oriented in my work", "type": "organizational"},
    {"id": 9, "question": "I thrive in dynamic environments", "type": "creative"},
    {"id": 10, "question": "I'm comfortable with data and numbers", "type": "analytical"},
    {"id": 11, "question": "I build relationships easily", "type": "collaborative"},
    {"id": 12, "question": "I'm good at planning and prioritizing", "type": "organizational"},
    {"id": 13, "question": "I enjoy brainstorming new ideas", "type": "creative"},
    {"id": 14, "question": "I listen actively to understand perspectives", "type": "empathetic"},
    {"id": 15, "question": "I work well under pressure", "type": "organizational"}
]

SKILL_TESTS = {
    "tech": [
        {"id": 1, "question": "What does OOP stand for?", "options": ["Object Oriented Programming", "Only One Program", "Output Operation Process", "Open Online Platform"], "correct": 0},
        {"id": 2, "question": "What is the time complexity of binary search?", "options": ["O(n)", "O(log n)", "O(n^2)", "O(1)"], "correct": 1},
        {"id": 3, "question": "Which language is commonly used for AI model training?", "options": ["Java", "Python", "C++", "Ruby"], "correct": 1},
        {"id": 4, "question": "What does HTML stand for?", "options": ["Hyper Text Markup Language", "High Tech Modern Language", "Home Tool Markup Language", "Hyperlinks and Text Markup Language"], "correct": 0},
        {"id": 5, "question": "Which data structure uses LIFO?", "options": ["Queue", "Stack", "Array", "Tree"], "correct": 1},
        {"id": 6, "question": "What is Git used for?", "options": ["Database Management", "Version Control", "UI Design", "Testing"], "correct": 1},
        {"id": 7, "question": "What does API stand for?", "options": ["Application Programming Interface", "Advanced Program Integration", "Automated Process Implementation", "Application Process Interface"], "correct": 0},
        {"id": 8, "question": "Which is a NoSQL database?", "options": ["MySQL", "PostgreSQL", "MongoDB", "Oracle"], "correct": 2},
        {"id": 9, "question": "What is CSS used for?", "options": ["Programming logic", "Styling web pages", "Database queries", "Server management"], "correct": 1},
        {"id": 10, "question": "What does REST stand for in API design?", "options": ["Representational State Transfer", "Remote Execution State Transfer", "Rapid Execution Service Tool", "Reliable Endpoint Service Transfer"], "correct": 0}
    ],
    "design": [
        {"id": 1, "question": "What is the purpose of a wireframe?", "options": ["Final design", "Layout structure", "Color palette", "Animation"], "correct": 1},
        {"id": 2, "question": "What does UI stand for?", "options": ["User Interface", "Universal Integration", "Uniform Interaction", "User Integration"], "correct": 0},
        {"id": 3, "question": "Which tool is commonly used for prototyping?", "options": ["Excel", "Figma", "Word", "PowerPoint"], "correct": 1},
        {"id": 4, "question": "What is UX focused on?", "options": ["Visual design", "User experience", "Code quality", "Marketing"], "correct": 1},
        {"id": 5, "question": "What is a design system?", "options": ["A collection of reusable components", "A type of software", "A design tool", "A coding framework"], "correct": 0},
        {"id": 6, "question": "What does responsive design mean?", "options": ["Fast loading", "Adapts to screen sizes", "Has animations", "Uses bright colors"], "correct": 1},
        {"id": 7, "question": "What is the rule of thirds in design?", "options": ["Use three colors", "Composition guideline", "Three fonts maximum", "Three pages minimum"], "correct": 1},
        {"id": 8, "question": "What is white space in design?", "options": ["Background color", "Empty space around elements", "Paper color", "Header area"], "correct": 1},
        {"id": 9, "question": "What is A/B testing?", "options": ["Testing two versions", "Alphabetical testing", "After/Before testing", "Automated testing"], "correct": 0},
        {"id": 10, "question": "What is a persona in UX?", "options": ["Designer name", "User archetype", "Color scheme", "Font style"], "correct": 1}
    ],
    "hr": [
        {"id": 1, "question": "What does HR stand for?", "options": ["High Ranking", "Human Resources", "Hiring Requirements", "Human Relations"], "correct": 1},
        {"id": 2, "question": "What is onboarding?", "options": ["Hiring process", "Integrating new employees", "Board meeting", "Training program"], "correct": 1},
        {"id": 3, "question": "What is KPI?", "options": ["Key Performance Indicator", "Knowledge Process Integration", "Key Process Improvement", "Known Performance Index"], "correct": 0},
        {"id": 4, "question": "What is employee retention?", "options": ["Hiring new staff", "Keeping employees", "Training programs", "Performance reviews"], "correct": 1},
        {"id": 5, "question": "What is a competency framework?", "options": ["Skill requirements", "Software tool", "Org chart", "Budget plan"], "correct": 0},
        {"id": 6, "question": "What is workforce planning?", "options": ["Daily schedules", "Strategic staffing", "Office layout", "Team building"], "correct": 1},
        {"id": 7, "question": "What is employer branding?", "options": ["Company logo", "Reputation as employer", "Product branding", "Office design"], "correct": 1},
        {"id": 8, "question": "What is talent acquisition?", "options": ["Training", "Recruiting top talent", "Performance review", "Salary negotiation"], "correct": 1},
        {"id": 9, "question": "What is succession planning?", "options": ["Exit interviews", "Preparing future leaders", "Retirement plans", "Promotion ceremony"], "correct": 1},
        {"id": 10, "question": "What is employee engagement?", "options": ["Marriage proposal", "Commitment and motivation", "Contract signing", "Team meeting"], "correct": 1}
    ]
}

@bp.route('/personality/questions', methods=['GET'])
def get_personality_questions():
    return jsonify(PERSONALITY_QUESTIONS), 200

@bp.route('/skill/questions/<category>', methods=['GET'])
def get_skill_questions(category):
    if category not in SKILL_TESTS:
        return jsonify({'error': 'Invalid category'}), 400
    return jsonify(SKILL_TESTS[category]), 200

@bp.route('/personality/submit', methods=['POST'])
@jwt_required()
def submit_personality():
    user_id = get_jwt_identity()
    data = request.json
    
    if not data or 'answers' not in data:
        return jsonify({'error': 'Missing answers data'}), 422
        
    answers = data.get('answers', [])
    # Accept partial submissions (allow user to submit answered questions)
    if not answers or len(answers) == 0:
        return jsonify({'error': 'No answers provided'}), 422
    
    type_counts = {'analytical': 0, 'creative': 0, 'empathetic': 0, 'collaborative': 0, 'organizational': 0}
    
    for answer in answers:
        if not isinstance(answer, dict) or 'question_id' not in answer or 'rating' not in answer:
            return jsonify({'error': 'Invalid answer format'}), 422
            
        question_id = answer.get('question_id')
        rating = answer.get('rating', 0)
        
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({'error': f'Invalid rating value for question {question_id}'}), 422
        
        question = next((q for q in PERSONALITY_QUESTIONS if q['id'] == question_id), None)
        if not question:
            return jsonify({'error': f'Invalid question id: {question_id}'}), 422
            
        type_counts[question['type']] += rating
    
    # Determine personality type and score based on provided answers
    personality_type = max(type_counts, key=type_counts.get)
    # Normalize score by number of answered questions (each rating is up to 5)
    total_possible = len(answers) * 5
    score = (sum(type_counts.values()) / total_possible) * 100 if total_possible > 0 else 0
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO assessments (user_id, test_type, answers, score, personality_type)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, 'personality', json.dumps(answers), score, personality_type))
    conn.commit()
    conn.close()
    
    update_user_profile(user_id, personality=personality_type)
    
    return jsonify({
        'personality_type': personality_type,
        'score': round(score, 2),
        'breakdown': type_counts
    }), 200

@bp.route('/skill/submit', methods=['POST'])
@jwt_required()
def submit_skill():
    user_id = get_jwt_identity()
    data = request.json
    
    if not data:
        return jsonify({'error': 'Missing request data'}), 422
        
    category = data.get('category')
    if not category:
        return jsonify({'error': 'Missing category'}), 422
        
    if category not in SKILL_TESTS:
        return jsonify({'error': 'Invalid category'}), 422
        
    answers = data.get('answers', [])
    if not answers:
        return jsonify({'error': 'Missing answers'}), 422
        
    if len(answers) != len(SKILL_TESTS[category]):
        return jsonify({'error': 'Invalid number of answers'}), 422
    
    questions = SKILL_TESTS[category]
    correct_count = 0
    
    for answer in answers:
        if not isinstance(answer, dict) or 'question_id' not in answer or 'selected_option' not in answer:
            return jsonify({'error': 'Invalid answer format'}), 422
            
        question_id = answer.get('question_id')
        selected_option = answer.get('selected_option')
        
        if not isinstance(selected_option, int) or selected_option < 0 or selected_option >= len(questions[0]['options']):
            return jsonify({'error': f'Invalid option selected for question {question_id}'}), 422
        
        question = next((q for q in questions if q['id'] == question_id), None)
        if not question:
            return jsonify({'error': f'Invalid question id: {question_id}'}), 422
            
        if question['correct'] == selected_option:
            correct_count += 1
    
    score = (correct_count / len(questions)) * 100
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO assessments (user_id, test_type, answers, score, skill_category)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, 'skill', json.dumps(answers), score, category))
    conn.commit()
    conn.close()
    
    return jsonify({
        'category': category,
        'score': round(score, 2),
        'correct': correct_count,
        'total': len(questions),
        'message': f'You scored {round(score, 2)}% in {category}!'
    }), 200

@bp.route('/results', methods=['GET'])
@jwt_required()
def get_results():
    user_id = get_jwt_identity()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM assessments WHERE user_id = ? ORDER BY created_at DESC
    ''', (user_id,))
    results = cursor.fetchall()
    conn.close()
    
    return jsonify([dict(row) for row in results]), 200


@bp.route('/recommend', methods=['POST'])
@jwt_required()
def recommend():
    """Return career role recommendations and suggested pods based on personality and skill results.
    Expects JSON: { personality_type: str, skill: {category: str, score: number} }
    """
    user_id = get_jwt_identity()
    data = request.json
    
    if not data:
        return jsonify({'error': 'Missing request data'}), 422
        
    personality = data.get('personality_type')
    if not personality:
        return jsonify({'error': 'Missing personality type'}), 422
        
    # allow unknown personality strings (don't block recommendations)
    if personality and not isinstance(personality, str):
        return jsonify({'error': 'Invalid personality type'}), 422
        
    skill = data.get('skill')
    if not skill:
        return jsonify({'error': 'Missing skill data'}), 422
        
    category = skill.get('category')
    if not category or category not in SKILL_TESTS:
        return jsonify({'error': 'Invalid skill category'}), 422
        
    score = skill.get('score')
    if not isinstance(score, (int, float)) or score < 0 or score > 100:
        return jsonify({'error': 'Invalid skill score'}), 422

    # Simple rule-based recommendations
    recs = []

    # Tech-focused recommendations
    if category == 'tech' or (personality == 'analytical'):
        recs.extend([
            {'role': 'Fullstack Developer', 'pods': ['skill', 'company', 'post_placement']},
            {'role': 'Backend Engineer', 'pods': ['skill', 'company']},
            {'role': 'Data Analyst', 'pods': ['skill', 'post_placement']},
            {'role': 'Design Verification Engineer', 'pods': ['skill', 'company']}
        ])

    # Design-focused recommendations
    if category == 'design' or (personality == 'creative'):
        recs.extend([
            {'role': 'UI/UX Designer', 'pods': ['skill', 'company']},
            {'role': 'Product Designer', 'pods': ['skill', 'post_placement']}
        ])

    # HR / collaborative roles
    if personality == 'empathetic' or category == 'hr':
        recs.extend([
            {'role': 'People Operations Specialist', 'pods': ['skill', 'post_placement']},
            {'role': 'Learning & Development Coordinator', 'pods': ['skill', 'company']}
        ])

    # Ensure uniqueness and limit to 8 suggestions
    seen = set()
    final = []
    for r in recs:
        if r['role'] not in seen:
            final.append(r)
            seen.add(r['role'])
        if len(final) >= 8:
            break

    # If nothing matched, fallback suggestions
    if not final:
        final = [
            {'role': 'Fullstack Developer', 'pods': ['skill', 'company', 'post_placement']},
            {'role': 'UI/UX Designer', 'pods': ['skill', 'company']},
            {'role': 'Project Coordinator', 'pods': ['skill', 'post_placement']}
        ]

    return jsonify({'recommendations': final}), 200
