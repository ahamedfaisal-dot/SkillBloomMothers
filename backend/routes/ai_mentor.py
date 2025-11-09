from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.database import get_db
from datetime import datetime
import os
import google.generativeai as genai

bp = Blueprint('ai_mentor', __name__, url_prefix='/api/ai')

# Configure the generative AI client if an API key is present. The actual
# API key must be provided via the GEMINI_API_KEY environment variable and
# must NOT be committed to source control. .env is already listed in .gitignore.
try:
    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        genai.configure(api_key=api_key)
        # model selection - keep this configurable in case environments differ
        model = genai.GenerativeModel(os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash-exp'))
    else:
        model = None
except Exception:
    # If the google generative SDK isn't available or configuration fails,
    # keep model as None and fall back to canned responses below.
    model = None

RESPONSES = {
    'resume': [
        "Highlight your key achievements and add measurable outcomes.",
        "Use action verbs and quantify your impact with numbers.",
        "Tailor your resume to each job description and emphasize relevant skills.",
        "Include a strong summary that showcases your unique value proposition."
    ],
    'anxious': [
        "That's completely natural. Start small and celebrate every progress.",
        "Remember, many mothers successfully return to work. You're not alone in this journey.",
        "Focus on your strengths and the valuable skills you've developed during your break.",
        "Take it one day at a time. Progress, not perfection, is what matters."
    ],
    'skills': [
        "Consider online courses in your field to refresh your knowledge.",
        "Practice with small projects to build confidence in your skills.",
        "Join professional communities to stay updated with industry trends.",
        "Your life experience is valuable - don't underestimate transferable skills!"
    ],
    'interview': [
        "Practice common interview questions and prepare your answers in advance.",
        "Research the company thoroughly and prepare thoughtful questions to ask.",
        "Be honest about your career gap - frame it as a period of personal growth.",
        "Prepare specific examples that demonstrate your skills and achievements."
    ],
    'balance': [
        "Work-life balance is achievable with proper planning and boundaries.",
        "Communicate your needs clearly with your employer from the start.",
        "Remember that it's okay to ask for flexible arrangements.",
        "Prioritize self-care - you can't pour from an empty cup."
    ],
    'confidence': [
        "Your experiences as a mother have given you unique skills employers value.",
        "Set small, achievable goals to build momentum and confidence.",
        "Surround yourself with supportive people who believe in you.",
        "Remember: impostor syndrome affects everyone. You deserve to be here."
    ],
    'default': [
        "I'm here to support you in your career re-entry journey.",
        "Every challenge is an opportunity to grow. You've got this!",
        "Your unique perspective and experience are valuable assets.",
        "Remember to be kind to yourself during this transition."
    ]
}

CAREER_RECOMMENDATIONS = {
    'analytical': ['Data Analyst', 'QA Engineer', 'Project Manager', 'Business Analyst', 'Financial Analyst'],
    'creative': ['UI Designer', 'Content Strategist', 'Product Designer', 'Marketing Manager', 'Brand Manager'],
    'empathetic': ['Customer Success', 'HR Associate', 'Social Worker', 'Healthcare Coordinator', 'Counselor'],
    'collaborative': ['Team Lead', 'Scrum Master', 'Account Manager', 'Community Manager', 'Operations Manager'],
    'organizational': ['Project Coordinator', 'Office Manager', 'Operations Specialist', 'Event Planner', 'Executive Assistant']
}

@bp.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    user_id = get_jwt_identity()
    data = request.json
    
    if not data or 'query' not in data:
        return jsonify({'error': 'Missing query in request'}), 422
        
    query = data.get('query', '').strip()
    if not query:
        return jsonify({'error': 'Empty query'}), 422
    
    try:
        from backend.models.database import get_user_by_id
        user = get_user_by_id(user_id)
        
        # If user profile isn't found, create a basic one to avoid errors
        if not user:
            user = {'name': 'User', 'personality': 'Not yet assessed', 'skills': [], 'career_gap': 0}
        
        context = f"""You are an AI career mentor for SkillBloom, a platform helping mothers return to work after a career break.
        
User Profile:
- Name: {user.get('name', 'User')}
- Personality Type: {user.get('personality', 'Not yet assessed')}
- Skills: {', '.join(user.get('skills', [])) if isinstance(user.get('skills'), list) else 'Not yet assessed'}
- Career Gap: {user.get('career_gap', 0)} years

Be empathetic, encouraging, and provide practical career advice. Focus on:
- Building confidence for career re-entry
- Addressing work-life balance concerns
- Highlighting transferable skills from motherhood
- Providing actionable career guidance

User Question: {query}

Respond in a warm, supportive tone in 2-3 sentences."""

        if model:
            response_obj = model.generate_content(context)
            response = response_obj.text
        else:
            response = get_ai_mentor_response(context, query)
        
    except Exception as e:
        response = get_ai_mentor_response("", query)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ai_logs (user_id, query, response)
        VALUES (?, ?, ?)
    ''', (user_id, query, response))
    conn.commit()
    conn.close()
    
    return jsonify({
        'response': response,
        'timestamp': datetime.now().isoformat()
    }), 200

@bp.route('/recommendation', methods=['POST'])
@jwt_required()
def recommend_roles():
    user_id = get_jwt_identity()
    data = request.json
    
    from backend.models.database import get_user_by_id
    user = get_user_by_id(user_id)
    
    personality = data.get('personality') or user.get('personality', '')
    skills = data.get('skills', [])
    
    if not personality:
        roles = CAREER_RECOMMENDATIONS.get('collaborative', CAREER_RECOMMENDATIONS['collaborative'])
        recommendations = []
        for role in roles[:3]:
            recommendations.append({
                'role': role,
                'match_score': 75,
                'reason': 'Complete your assessment for personalized recommendations'
            })
        return jsonify({
            'personality': 'General',
            'recommendations': recommendations
        }), 200
    
    try:
        if model:
            prompt = f"""Based on the following profile, recommend 3 specific job roles for a mother returning to work:

Personality Type: {personality}
Skills/Experience: {', '.join(skills) if skills else 'General professional experience'}
Career Gap: {user.get('career_gap', 0)} years

For each role, provide:
1. Job title
2. Match percentage (realistic score)
3. Brief reason why this role suits them

Format as JSON array with 3 items, each having: role, match_score (number), reason"""

            response = model.generate_content(prompt)
            response_text = response.text
            
            import json
            import re
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                recommendations = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")
        else:
            raise ValueError("Model not configured")
            
    except Exception as e:
        roles = CAREER_RECOMMENDATIONS.get(personality.lower(), CAREER_RECOMMENDATIONS.get('collaborative', []))
        recommendations = []
        for i, role in enumerate(roles[:3]):
            match_score = 70 + (len(skills) * 5) + (i * 2)
            if match_score > 95:
                match_score = 95
            recommendations.append({
                'role': role,
                'match_score': match_score,
                'reason': f'Your {personality} personality is well-suited for this role'
            })
    
    return jsonify({
        'personality': personality,
        'recommendations': recommendations
    }), 200

@bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    user_id = get_jwt_identity()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM ai_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT 50
    ''', (user_id,))
    logs = cursor.fetchall()
    conn.close()
    
    return jsonify([dict(row) for row in logs]), 200


def get_ai_mentor_response(context: str, question: str) -> str:
    """Return an AI-generated mentor response.

    This helper uses the configured generative model when an API key is
    present. If the model call fails (or SDK missing), it falls back to a
    friendly canned response from RESPONSES.
    """
    prompt = f"{context}\nUser Question: {question}\nPlease respond in 2-3 concise, supportive sentences."

    # Try calling the generative model if configured
    if model is not None:
        try:
            response_obj = model.generate_content(prompt)
            text = getattr(response_obj, 'text', None) or str(response_obj)
            if text and text.strip():
                return text.strip()
        except Exception:
            # Fall through to canned responses on any failure
            pass

    # Fallback: choose category-based canned responses when possible
    # Try to find a matching keyword in the topic/context
    lc = (context or '').lower() + ' ' + (question or '').lower()
    for key in RESPONSES:
        if key in lc:
            # return the first canned suggestion
            return RESPONSES[key][0]

    # Default fallback
    return RESPONSES['default'][0]