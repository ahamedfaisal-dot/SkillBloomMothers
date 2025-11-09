from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from backend.models.database import create_user, get_user_by_email, verify_password

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')
    
    if not name or not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400
    
    user_id = create_user(name, email, password, role)
    
    if user_id is None:
        return jsonify({'error': 'Email already exists'}), 409
    
    access_token = create_access_token(identity=user_id)
    
    return jsonify({
        'message': 'User created successfully',
        'user_id': user_id,
        'access_token': access_token
    }), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Missing email or password'}), 400
    
    user = get_user_by_email(email)
    
    if not user or not verify_password(user['password'], password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    access_token = create_access_token(identity=user['id'])
    
    return jsonify({
        'message': 'Login successful',
        'user_id': user['id'],
        'name': user['name'],
        'role': user['role'],
        'access_token': access_token
    }), 200

@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    from backend.models.database import get_user_by_id
    user_id = get_jwt_identity()
    user = get_user_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user.pop('password', None)
    return jsonify(user), 200
