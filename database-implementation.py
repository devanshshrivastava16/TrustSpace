# utils/database.py
import json
import os
import time
from datetime import datetime
import uuid

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# JSON file paths
USERS_FILE = 'data/users.json'
PROPERTIES_FILE = 'data/properties.json'
BOOKINGS_FILE = 'data/bookings.json'
REVIEWS_FILE = 'data/reviews.json'

def load_data(file_path):
    """Load data from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Create empty file if it doesn't exist
        with open(file_path, 'w') as f:
            json.dump([], f)
        return []

def save_data(data, file_path):
    """Save data to a JSON file with file locking mechanism."""
    max_retries = 5
    retry_delay = 0.5
    
    for attempt in range(max_retries):
        try:
            # Create a temp file
            temp_file = f"{file_path}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=4)
            
            # Rename temp file to target file (atomic operation)
            os.replace(temp_file, file_path)
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                print(f"Failed to save data to {file_path}: {e}")
                return False

# Property Management Functions
def create_property(owner_id, property_data):
    """Create a new property listing."""
    properties = load_data(PROPERTIES_FILE)
    
    new_property = {
        "id": str(uuid.uuid4()),
        "owner_id": owner_id,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "active",
        "verified": False,
        "blockchain_registered": False,
        "contract_address": None,
        **property_data
    }
    
    properties.append(new_property)
    save_data(properties, PROPERTIES_FILE)
    return new_property

def get_properties(filters=None):
    """Get properties with optional filtering."""
    properties = load_data(PROPERTIES_FILE)
    
    if not filters:
        return properties
    
    filtered_properties = properties
    
    # Apply filters
    if 'owner_id' in filters:
        filtered_properties = [p for p in filtered_properties if p['owner_id'] == filters['owner_id']]
    
    if 'status' in filters:
        filtered_properties = [p for p in filtered_properties if p['status'] == filters['status']]
        
    if 'verified' in filters:
        filtered_properties = [p for p in filtered_properties if p['verified'] == filters['verified']]
    
    if 'price_min' in filters and 'price_max' in filters:
        filtered_properties = [p for p in filtered_properties 
                               if float(p['price_per_day']) >= filters['price_min'] 
                               and float(p['price_per_day']) <= filters['price_max']]
    
    if 'location' in filters:
        filtered_properties = [p for p in filtered_properties 
                               if filters['location'].lower() in p['location'].lower()]
    
    if 'property_type' in filters:
        filtered_properties = [p for p in filtered_properties 
                               if p['property_type'] == filters['property_type']]
    
    return filtered_properties

def update_property(property_id, updated_data):
    """Update a property listing."""
    properties = load_data(PROPERTIES_FILE)
    
    for i, prop in enumerate(properties):
        if prop['id'] == property_id:
            # Update the property
            properties[i].update(updated_data)
            properties[i]['updated_at'] = datetime.now().isoformat()
            save_data(properties, PROPERTIES_FILE)
            return properties[i]
    
    return None

# Booking Management Functions
def create_booking(booking_data):
    """Create a new booking."""
    bookings = load_data(BOOKINGS_FILE)
    
    new_booking = {
        "id": str(uuid.uuid4()),
        "created_at": datetime.now().isoformat(),
        "status": "pending",  # pending, confirmed, completed, cancelled
        "payment_status": "pending",
        "contract_address": None,
        "transaction_hash": None,
        **booking_data
    }
    
    bookings.append(new_booking)
    save_data(bookings, BOOKINGS_FILE)
    return new_booking

def get_bookings(filters=None):
    """Get bookings with optional filtering."""
    bookings = load_data(BOOKINGS_FILE)
    
    if not filters:
        return bookings
    
    filtered_bookings = bookings
    
    if 'renter_id' in filters:
        filtered_bookings = [b for b in filtered_bookings if b['renter_id'] == filters['renter_id']]
    
    if 'property_id' in filters:
        filtered_bookings = [b for b in filtered_bookings if b['property_id'] == filters['property_id']]
    
    if 'status' in filters:
        filtered_bookings = [b for b in filtered_bookings if b['status'] == filters['status']]
    
    if 'owner_id' in filters:
        properties = load_data(PROPERTIES_FILE)
        property_ids = [p['id'] for p in properties if p['owner_id'] == filters['owner_id']]
        filtered_bookings = [b for b in filtered_bookings if b['property_id'] in property_ids]
    
    return filtered_bookings

def update_booking(booking_id, updated_data):
    """Update a booking."""
    bookings = load_data(BOOKINGS_FILE)
    
    for i, booking in enumerate(bookings):
        if booking['id'] == booking_id:
            # Update the booking
            bookings[i].update(updated_data)
            save_data(bookings, BOOKINGS_FILE)
            return bookings[i]
    
    return None

# Review Management Functions
def create_review(review_data):
    """Create a new review."""
    reviews = load_data(REVIEWS_FILE)
    
    new_review = {
        "id": str(uuid.uuid4()),
        "created_at": datetime.now().isoformat(),
        "blockchain_registered": False,
        "transaction_hash": None,
        **review_data
    }
    
    reviews.append(new_review)
    save_data(reviews, REVIEWS_FILE)
    return new_review

def get_reviews(property_id=None, user_id=None):
    """Get reviews for a property or by a user."""
    reviews = load_data(REVIEWS_FILE)
    
    if property_id:
        return [r for r in reviews if r['property_id'] == property_id]
    
    if user_id:
        return [r for r in reviews if r['reviewer_id'] == user_id]
    
    return reviews
