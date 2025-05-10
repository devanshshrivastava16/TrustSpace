import json
import os
import time
from datetime import datetime
import uuid
import random

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
def create_property(property_data):
    """Create a new property"""
    try:
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        # Load existing properties
        properties = get_properties()
        
        # Validate required fields
        required_fields = ['id', 'owner_id', 'title', 'location', 'property_type', 'price_per_day', 'capacity']
        for field in required_fields:
            if field not in property_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Set default values
        property_data['status'] = 'pending'
        property_data['verified'] = False
        property_data['blockchain_registered'] = False
        property_data['created_at'] = datetime.now().isoformat()
        property_data['updated_at'] = datetime.now().isoformat()
        
        # Add property to list
        properties.append(property_data)
        
        # Save to file
        with open('data/properties.json', 'w') as f:
            json.dump(properties, f, indent=4)
        
        return property_data
    except Exception as e:
        print(f"Error creating property: {str(e)}")
        raise

def get_properties(filters=None):
    """Get properties with optional filters"""
    properties = load_data(PROPERTIES_FILE)
    
    if not filters:
        return properties
    
    filtered_properties = []
    for prop in properties:
        matches = True
        
        # Apply filters
        for key, value in filters.items():
            if key == 'price_min':
                if prop['price_per_day'] < value:
                    matches = False
            elif key == 'price_max':
                if prop['price_per_day'] > value:
                    matches = False
            elif key in prop and prop[key] != value:
                matches = False
        
        if matches:
            filtered_properties.append(prop)
    
    return filtered_properties

def update_property(property_id, property_data):
    """Update an existing property"""
    properties = load_data(PROPERTIES_FILE)
    
    for i, prop in enumerate(properties):
        if prop['id'] == property_id:
            # Preserve existing fields that shouldn't be updated
            existing_data = {
                'id': prop['id'],
                'owner_id': prop['owner_id'],
                'created_at': prop['created_at']
            }
            
            # Update with new data
            properties[i] = {**existing_data, **property_data}
            save_data(properties, PROPERTIES_FILE)
            return True
    
    return False

# Booking Management Functions
def create_booking(booking_data):
    """Create a new booking"""
    bookings = load_data(BOOKINGS_FILE)
    
    # Validate required fields
    required_fields = ['id', 'property_id', 'guest_id', 'owner_id', 'check_in', 'check_out', 'status']
    if not all(field in booking_data for field in required_fields):
        return False
    
    # Add default fields if not provided
    booking_data.setdefault('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    booking_data.setdefault('payment_status', 'pending')
    
    bookings.append(booking_data)
    save_data(bookings, BOOKINGS_FILE)
    return True

def get_bookings(filters=None):
    """Get bookings with optional filters"""
    bookings = load_data(BOOKINGS_FILE)
    
    if not filters:
        return bookings
    
    filtered_bookings = []
    for booking in bookings:
        matches = True
        
        # Apply filters
        for key, value in filters.items():
            if key in booking and booking[key] != value:
                matches = False
        
        if matches:
            filtered_bookings.append(booking)
    
    return filtered_bookings

def update_booking_status(booking_id, new_status):
    """Update booking status"""
    bookings = load_data(BOOKINGS_FILE)
    
    for i, booking in enumerate(bookings):
        if booking['id'] == booking_id:
            booking['status'] = new_status
            save_data(bookings, BOOKINGS_FILE)
            return True
    
    return False

# Review Management Functions
def create_review(review_data):
    """Create a new review"""
    reviews = load_data(REVIEWS_FILE)
    
    # Validate required fields
    required_fields = ['id', 'property_id', 'user_id', 'rating', 'comment']
    if not all(field in review_data for field in required_fields):
        return False
    
    # Add default fields if not provided
    review_data.setdefault('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    review_data.setdefault('verified', False)
    
    reviews.append(review_data)
    save_data(reviews, REVIEWS_FILE)
    return True

def get_reviews(filters=None):
    """Get reviews with optional filters"""
    reviews = load_data(REVIEWS_FILE)
    
    if not filters:
        return reviews
    
    filtered_reviews = []
    for review in reviews:
        matches = True
        
        # Apply filters
        for key, value in filters.items():
            if key in review and review[key] != value:
                matches = False
        
        if matches:
            filtered_reviews.append(review)
    
    return filtered_reviews

def generate_sample_properties():
    """Generate 50 sample properties in Jaipur"""
    # Sample property types and their descriptions
    property_types = {
        "House": "Beautiful traditional Rajasthani house with modern amenities",
        "Apartment": "Modern apartment with city views",
        "Villa": "Luxury villa with private garden",
        "Garden": "Spacious garden venue perfect for events",
        "Hall": "Elegant banquet hall with traditional decor",
        "Event Space": "Versatile event space with modern facilities"
    }
    
    # Sample locations in Jaipur
    locations = [
        "Malviya Nagar", "C-Scheme", "Bani Park", "Vaishali Nagar", "Raja Park",
        "Sitapura", "Jawahar Circle", "Civil Lines", "Mansarovar", "Pratap Nagar",
        "Vidyadhar Nagar", "Sector 3", "Sector 4", "Sector 5", "Sector 6",
        "Sector 7", "Sector 8", "Sector 9", "Sector 10", "Sector 11"
    ]
    
    # Sample property names
    property_names = [
        "Royal Heritage Villa", "Pink City Palace", "Jaipur Royal Estate",
        "Rajasthani Royal Villa", "Pink Pearl Apartment", "Heritage Garden Estate",
        "Royal Palace Villa", "Pink City Mansion", "Rajasthani Royal Palace",
        "Pink Pearl Villa", "Heritage Palace Estate", "Royal Garden Villa",
        "Pink City Estate", "Rajasthani Pearl Villa", "Heritage Royal Palace",
        "Royal Pearl Villa", "Pink Palace Estate", "Rajasthani Heritage Villa",
        "Pink Pearl Palace", "Heritage Royal Estate", "Royal Palace Garden",
        "Pink City Pearl", "Rajasthani Palace Estate", "Heritage Pearl Villa",
        "Royal Garden Palace", "Pink Estate Villa", "Rajasthani Royal Garden",
        "Pink Palace Villa", "Heritage Estate Palace", "Royal Pearl Estate",
        "Pink City Garden", "Rajasthani Pearl Palace", "Heritage Palace Villa",
        "Royal Estate Palace", "Pink Pearl Garden", "Rajasthani Heritage Palace",
        "Pink Palace Pearl", "Heritage Royal Garden", "Royal Garden Pearl",
        "Pink Estate Palace", "Rajasthani Palace Villa", "Heritage Pearl Palace",
        "Royal Estate Garden", "Pink City Pearl", "Rajasthani Royal Estate",
        "Pink Palace Garden", "Heritage Estate Villa", "Royal Pearl Garden"
    ]
    
    # Generate 50 properties
    properties = []
    for i in range(50):
        property_type = random.choice(list(property_types.keys()))
        location = random.choice(locations)
        name = random.choice(property_names)
        
        # Generate random price between 1000 and 10000
        price = random.randint(1000, 10000)
        
        # Generate random capacity based on property type
        if property_type in ["House", "Apartment"]:
            capacity = random.randint(4, 8)
        elif property_type in ["Villa"]:
            capacity = random.randint(8, 15)
        else:
            capacity = random.randint(20, 100)
        
        property_data = {
            'id': str(uuid.uuid4()),
            'owner_id': 'sample_owner_id',  # This should be replaced with a real owner ID
            'title': f"{name} in {location}",
            'location': location,
            'property_type': property_type,
            'price_per_day': price,
            'capacity': capacity,
            'description': f"{property_types[property_type]} located in the heart of {location}. Perfect for your stay in the Pink City.",
            'images': [],  # No images for sample data
            'verified': random.choice([True, False]),
            'blockchain_registered': random.choice([True, False]),
            'status': 'active',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        properties.append(property_data)
    
    return properties

def initialize_sample_data():
    """Initialize the database with sample data"""
    # Create data directory if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Generate sample properties
    properties = generate_sample_properties()
    
    # Save properties to database
    save_data(properties, PROPERTIES_FILE)
    
    # Create empty users file if it doesn't exist
    if not os.path.exists(USERS_FILE):
        save_data([], USERS_FILE)
    
    # Create empty bookings file if it doesn't exist
    if not os.path.exists(BOOKINGS_FILE):
        save_data([], BOOKINGS_FILE)
    
    # Create empty reviews file if it doesn't exist
    if not os.path.exists(REVIEWS_FILE):
        save_data([], REVIEWS_FILE)
    
    return True 