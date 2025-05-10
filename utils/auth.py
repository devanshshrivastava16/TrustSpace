import json
import hashlib
import os
import uuid
from datetime import datetime, timedelta
import jwt

# Secret key for JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Load users from JSON file."""
    try:
        with open('data/users.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Create empty users file if it doesn't exist
        os.makedirs('data', exist_ok=True)
        with open('data/users.json', 'w') as f:
            json.dump([], f)
        return []

def save_users(users):
    """Save users to JSON file."""
    with open('data/users.json', 'w') as f:
        json.dump(users, f, indent=4)

def register_user(email, password, full_name, user_type):
    """Register a new user."""
    users = load_users()
    
    # Check if user already exists
    if any(user['email'] == email for user in users):
        return False, "Email already registered"
    
    # Create new user
    new_user = {
        "id": str(uuid.uuid4()),
        "email": email,
        "password_hash": hash_password(password),
        "full_name": full_name,
        "user_type": user_type,  # "renter" or "owner"
        "kyc_verified": False,
        "created_at": datetime.now().isoformat(),
        "wallet_address": None,
        "profile_image": None,
        "kyc_documents": []
    }
    
    users.append(new_user)
    save_users(users)
    return True, "User registered successfully"

def verify_user(email, password):
    """Verify user credentials."""
    users = load_users()
    password_hash = hash_password(password)
    
    for user in users:
        if user['email'] == email and user['password_hash'] == password_hash:
            # Generate JWT token
            expiration = datetime.now() + timedelta(hours=24)
            payload = {
                "user_id": user["id"],
                "email": user["email"],
                "exp": expiration.timestamp()
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
            return True, token, user
    
    return False, None, None

def verify_token(token):
    """Verify a JWT token and return user_id if valid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return True, payload["user_id"], payload
    except jwt.ExpiredSignatureError:
        return False, None, "Token expired"
    except jwt.InvalidTokenError:
        return False, None, "Invalid token"

def update_kyc_status(user_id, verified=True):
    """Update KYC verification status for a user."""
    users = load_users()
    
    for user in users:
        if user['id'] == user_id:
            user['kyc_verified'] = verified
            save_users(users)
            return True
    
    return False

def upload_kyc_document(user_id, document_type, file_path):
    """Store KYC document information."""
    users = load_users()
    
    for user in users:
        if user['id'] == user_id:
            if 'kyc_documents' not in user:
                user['kyc_documents'] = []
                
            user['kyc_documents'].append({
                "type": document_type,
                "file_path": file_path,
                "uploaded_at": datetime.now().isoformat(),
                "verified": False
            })
            
            save_users(users)
            return True
    
    return False

def update_user_role(user_id, new_role):
    """Update user's role"""
    users = load_users()
    for user in users:
        if user['id'] == user_id:
            user['user_type'] = new_role
            break
    save_users(users)
    return True

def update_user_profile(user_id, profile_data):
    """Update user's profile information"""
    users = load_users()
    for user in users:
        if user['id'] == user_id:
            user.update(profile_data)
            break
    save_users(users)
    return True

def update_user_wallet(user_id, wallet_address):
    """Update user's wallet address"""
    users = load_users()
    for user in users:
        if user['id'] == user_id:
            user['wallet_address'] = wallet_address
            break
    save_users(users)
    return True

def get_user_data(user_id):
    """Get user data by ID"""
    users = load_users()
    for user in users:
        if user['id'] == user_id:
            return user
    return None 