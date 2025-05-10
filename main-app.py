# app.py
import streamlit as st
import os
import json
from datetime import datetime, timedelta
import time
import uuid
import base64
from PIL import Image
import io

# Import utility modules
from utils.auth import (
    register_user, verify_user, verify_token, update_kyc_status, 
    update_user_role, update_user_profile, update_user_wallet, get_user_data
)
from utils.database import (
    load_data, save_data, create_property, get_properties, 
    update_property, create_booking, get_bookings, update_booking_status,
    create_review, get_reviews, initialize_sample_data
)
from blockchain.web3_utils import (
    create_wallet, get_wallet_balance, send_transaction,
    create_rental_agreement, process_escrow_payment,
    release_escrow_payment, submit_review_to_blockchain
)
from utils.video_stream import (
    setup_webrtc_component, capture_verification_image,
    start_live_verification_session, complete_verification_session,
    get_verification_session, verify_property_images
)

# Page configuration
st.set_page_config(
    page_title="P2P Property Rental Platform",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'auth_token' not in st.session_state:
    st.session_state.auth_token = None
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'selected_property' not in st.session_state:
    st.session_state.selected_property = None
if 'verification_session' not in st.session_state:
    st.session_state.verification_session = None

# Function to change page
def change_page(page):
    st.session_state.page = page

# Check authentication
def check_auth():
    if not st.session_state.user or not st.session_state.auth_token:
        return False
    
    valid, user_id, payload = verify_token(st.session_state.auth_token)
    if valid and user_id == st.session_state.user['id']:
        return True
    return False

# Logout function
def logout():
    st.session_state.user = None
    st.session_state.auth_token = None
    st.session_state.page = 'home'

# Page layouts
def render_home():
    st.title("🏠 P2P Property Rental Platform")
    st.subheader("Rent Luxury Properties with Trust and Security")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Welcome to our Decentralized Property Rental Platform
        
        Our platform allows you to securely rent or list luxury properties for events and functions.
        We ensure trust and transparency through:
        
        - **Live Video Verification**: See the property in real-time before booking
        - **Blockchain Security**: Secure payments and verifiable reviews
        - **Identity Verification**: Know who you're dealing with
        """)
        
        if st.button("List Your Property", type="primary", key="list_property_button"):
            st.session_state.page = 'login'
        if st.button("Find a Property", key="find_property_button"):
            st.session_state.page = 'login'
    
    with col2:
        st.image("https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800&auto=format&fit=crop", 
                 caption="Secure & Verified Property Rentals")

def render_login():
    st.title("Sign In / Register")
    
    tab1, tab2 = st.tabs(["Sign In", "Register"])
    
    with tab1:
        email = st.text_input("Email Address", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Sign In", type="primary", key="sign_in_button"):
            if email and password:
                success, token, user = verify_user(email, password)
                if success:
                    st.session_state.auth_token = token
                    st.session_state.user = user
                    st.success("Login successful!")
                    st.session_state.page = 'dashboard'
                else:
                    st.error("Invalid email or password")
            else:
                st.warning("Please enter both email and password")
    
    with tab2:
        full_name = st.text_input("Full Name", key="reg_name")
        email = st.text_input("Email Address", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
        
        user_type = st.selectbox("Account Type", ["Renter", "Property Owner"], key="reg_type")
        
        if st.button("Register", key="register_button"):
            if password != confirm_password:
                st.error("Passwords don't match")
            elif not (full_name and email and password):
                st.warning("Please fill in all fields")
            else:
                # Convert user type to lowercase for consistency
                user_type = user_type.lower().replace(" ", "_")
                success, message = register_user(email, password, full_name, user_type)
                if success:
                    st.success("Registration successful! Please sign in.")
                    st.session_state.page = 'login'
                else:
                    st.error(message)

def render_dashboard():
    """Render user dashboard"""
    if not check_auth():
        st.warning("Please login to access the dashboard")
        st.session_state.page = 'login'
        return
    
    st.title("Dashboard")
    
    # Get user data
    user_data = get_user_data(st.session_state.user['id'])
    
    if user_data:
        # Show role-specific tabs
        if user_data['user_type'] == 'property_owner':
            tab1, tab2, tab3 = st.tabs(["My Properties", "Add New Property", "Bookings"])
            
            with tab1:
                st.markdown("### My Properties")
                properties = get_properties({'owner_id': st.session_state.user['id']})
                
                if not properties:
                    st.info("You haven't listed any properties yet.")
                    if st.button("Add Your First Property", type="primary", key="add_first_property_button"):
                        st.session_state.page = 'add_property'
                else:
                    for prop in properties:
                        col1, col2, col3 = st.columns([2, 3, 1])
                        
                        with col1:
                            if 'images' in prop and prop['images']:
                                st.image(prop['images'][0], width=200)
                            else:
                                st.image("https://via.placeholder.com/200x150?text=No+Image", width=200)
                        
                        with col2:
                            st.markdown(f"### {prop['title']}")
                            st.markdown(f"**Location:** {prop['location']}")
                            st.markdown(f"**Type:** {prop['property_type']}")
                            st.markdown(f"**Price:** ₹{prop['price_per_day']}/day")
                            st.markdown(f"**Capacity:** {prop['capacity']} people")
                            st.markdown(f"**Status:** {prop['status']}")
                            
                            if prop['blockchain_registered']:
                                st.success("✓ Blockchain Registered")
                            if prop['verified']:
                                st.success("✓ Property Verified")
                        
                        with col3:
                            if st.button("Edit", key=f"edit_property_{prop['id']}"):
                                st.session_state.selected_property = prop['id']
                                st.session_state.page = 'edit_property'
            
            with tab2:
                st.markdown("### Add New Property")
                st.markdown("""
                List your property on our platform and start earning!
                
                Fill out the property details below and our team will review your listing.
                """)
                if st.button("Add Property", type="primary", key="add_new_property_button"):
                    st.session_state.page = 'add_property'
            
            with tab3:
                st.markdown("### Property Bookings")
                bookings = get_bookings({'property_owner_id': st.session_state.user['id']})
                
                if not bookings:
                    st.info("No bookings yet.")
                else:
                    for booking in bookings:
                        st.markdown(f"**Property:** {booking['property_title']}")
                        st.markdown(f"**Guest:** {booking['guest_name']}")
                        st.markdown(f"**Check-in:** {booking['check_in']}")
                        st.markdown(f"**Check-out:** {booking['check_out']}")
                        st.markdown(f"**Status:** {booking['status']}")
                        
                        if booking['status'] == 'pending':
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Accept", key=f"accept_booking_{booking['id']}"):
                                    update_booking_status(booking['id'], 'confirmed')
                                    st.success("Booking accepted!")
                            with col2:
                                if st.button("Reject", key=f"reject_booking_{booking['id']}"):
                                    update_booking_status(booking['id'], 'rejected')
                                    st.success("Booking rejected!")
        
        else:  # Renter role
            tab1, tab2, tab3 = st.tabs(["Find Properties", "My Bookings", "My Reviews"])
            
            with tab1:
                st.markdown("### Find Properties")
                # Search filters
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    location = st.text_input("Location (e.g., Malviya Nagar, C-Scheme)")
                
                with col2:
                    property_type = st.selectbox("Property Type", [
                        "All Types", "House", "Apartment", "Villa", "Garden", "Hall", "Event Space"
                    ])
                
                with col3:
                    price_range = st.slider("Price Range (₹/day)", 0, 10000, (1000, 5000))
                
                # Build filters
                filters = {}
                if location:
                    filters['location'] = location
                if property_type != "All Types":
                    filters['property_type'] = property_type
                
                filters['price_min'] = price_range[0]
                filters['price_max'] = price_range[1]
                filters['status'] = 'active'
                
                # Search button
                if st.button("Search", type="primary", key="search_properties_button"):
                    properties = get_properties(filters)
                    
                    if not properties:
                        st.info("No properties found matching your criteria. Try adjusting your search filters.")
                    else:
                        st.write(f"Found {len(properties)} properties")
                        
                        for prop in properties:
                            col1, col2, col3 = st.columns([2, 3, 1])
                            
                            with col1:
                                if 'images' in prop and prop['images']:
                                    st.image(prop['images'][0], width=200)
                                else:
                                    st.image("https://via.placeholder.com/200x150?text=No+Image", width=200)
                            
                            with col2:
                                st.markdown(f"### {prop['title']}")
                                st.markdown(f"**Location:** {prop['location']}")
                                st.markdown(f"**Type:** {prop['property_type']}")
                                st.markdown(f"**Price:** ₹{prop['price_per_day']}/day")
                                st.markdown(f"**Capacity:** {prop['capacity']} people")
                                
                                if prop['blockchain_registered']:
                                    st.success("✓ Blockchain Verified")
                                if prop['verified']:
                                    st.success("✓ Property Verified")
                            
                            with col3:
                                if st.button("View Details", key=f"view_{prop['id']}"):
                                    st.session_state.selected_property = prop['id']
                                    st.session_state.page = 'property_detail'
            
            with tab2:
                st.markdown("### My Bookings")
                bookings = get_bookings({'guest_id': st.session_state.user['id']})
                
                if not bookings:
                    st.info("You haven't made any bookings yet.")
                else:
                    for booking in bookings:
                        st.markdown(f"**Property:** {booking['property_title']}")
                        st.markdown(f"**Check-in:** {booking['check_in']}")
                        st.markdown(f"**Check-out:** {booking['check_out']}")
                        st.markdown(f"**Status:** {booking['status']}")
            
            with tab3:
                st.markdown("### My Reviews")
                reviews = get_reviews({'user_id': st.session_state.user['id']})
                
                if not reviews:
                    st.info("You haven't written any reviews yet.")
                else:
                    for review in reviews:
                        st.markdown(f"**Property:** {review['property_title']}")
                        st.markdown(f"**Rating:** {review['rating']}/5")
                        st.markdown(f"**Comment:** {review['comment']}")
    else:
        st.error("User not found!")

def render_wallet():
    st.subheader("Blockchain Wallet")
    
    # Check if user has a wallet
    if not st.session_state.user.get('wallet_address'):
        st.warning("You don't have a blockchain wallet yet.")
        
        if st.button("Create Wallet", type="primary", key="create_wallet_button"):
            # Create new wallet
            wallet = create_wallet()
            
            # Update user record
            users = load_data('data/users.json')
            for user in users:
                if user['id'] == st.session_state.user['id']:
                    user['wallet_address'] = wallet['address']
                    user['wallet_private_key'] = wallet['private_key']  # In a real app, encrypt this!
                    break
            
            save_data(users, 'data/users.json')
            
            # Update session state
            st.session_state.user['wallet_address'] = wallet['address']
            st.session_state.user['wallet_private_key'] = wallet['private_key']
            
            st.success(f"Wallet created successfully!")
            st.session_state.page = 'dashboard'
    else:
        # Display wallet info
        wallet_address = st.session_state.user['wallet_address']
        balance = get_wallet_balance(wallet_address)
        
        st.markdown(f"### Your Wallet")
        st.markdown(f"**Address:** `{wallet_address}`")
        st.markdown(f"**Balance:** {balance} ETH")
        
        # Transfer funds section
        st.markdown("### Transfer Funds")
        
        col1, col2 = st.columns(2)
        
        with col1:
            recipient = st.text_input("Recipient Address")
            amount = st.number_input("Amount (ETH)", min_value=0.001, step=0.01)
        
        with col2:
            st.markdown("##### Transaction Information")
            st.markdown("- Network: EduChain")
            st.markdown("- Gas Fee: Estimated automatically")
            
            if st.button("Send Transaction", type="primary", key="send_transaction_button"):
                if recipient and amount > 0:
                    private_key = st.session_state.user['wallet_private_key']
                    result = send_transaction(private_key, recipient, amount)
                    
                    if result['success']:
                        st.success(f"Transaction sent successfully!")
                        st.markdown(f"Transaction Hash: `{result['transaction_hash']}`")
                    else:
                        st.error(f"Transaction failed: {result.get('error', 'Unknown error')}")
                else:
                    st.warning("Please enter recipient address and amount")
        
        # Transaction history
        st.markdown("### Transaction History")
        st.info("Transaction history will appear here")  # In a real app, fetch from blockchain

def render_profile():
    """Render user profile page"""
    if not check_auth():
        st.warning("Please login to access your profile")
        st.session_state.page = 'login'
        return
    
    st.title("My Profile")
    
    # Get user data
    user_data = get_user_data(st.session_state.user['id'])
    
    if user_data:
        # Role switching
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### Account Information")
            st.markdown(f"**Email:** {user_data['email']}")
            st.markdown(f"**Role:** {user_data['user_type']}")
            st.markdown(f"**KYC Status:** {'Verified' if user_data['kyc_verified'] else 'Not Verified'}")
            
            if user_data['wallet_address']:
                st.markdown(f"**Wallet Address:** {user_data['wallet_address']}")
                st.markdown(f"**Wallet Balance:** {get_wallet_balance(user_data['wallet_address'])} ETH")
            else:
                st.markdown("**Wallet:** Not Connected")
        
        with col2:
            # Role switching button
            if user_data['user_type'] == 'renter':
                if st.button("Switch to Property Owner", key="switch_to_owner"):
                    update_user_role(st.session_state.user['id'], 'owner')
                    st.success("Successfully switched to Property Owner role!")
                    st.session_state.page = 'dashboard'
            else:
                if st.button("Switch to Renter", key="switch_to_renter"):
                    update_user_role(st.session_state.user['id'], 'renter')
                    st.success("Successfully switched to Renter role!")
                    st.session_state.page = 'dashboard'
        
        # Profile update form
        st.markdown("### Update Profile")
        with st.form("update_profile_form"):
            new_name = st.text_input("Name", value=user_data.get('full_name', ''))
            new_phone = st.text_input("Phone", value=user_data.get('phone', ''))
            new_address = st.text_area("Address", value=user_data.get('address', ''))
            
            if st.form_submit_button("Update Profile", key="update_profile_button"):
                update_user_profile(st.session_state.user['id'], {
                    'full_name': new_name,
                    'phone': new_phone,
                    'address': new_address
                })
                st.success("Profile updated successfully!")
        
        # KYC verification section
        if not user_data['kyc_verified']:
            st.markdown("### KYC Verification")
            if st.button("Start KYC Verification", key="start_kyc_button"):
                st.session_state.page = 'kyc_verification'
        
        # Wallet management section
        st.markdown("### Wallet Management")
        if not user_data['wallet_address']:
            if st.button("Create Wallet", key="create_wallet_button"):
                wallet_address = create_wallet()
                if wallet_address:
                    update_user_wallet(st.session_state.user['id'], wallet_address)
                    st.success("Wallet created successfully!")
        else:
            st.markdown("#### Send Transaction")
            with st.form("send_transaction_form"):
                recipient = st.text_input("Recipient Address")
                amount = st.number_input("Amount (ETH)", min_value=0.0, step=0.001)
                
                if st.form_submit_button("Send", key="send_transaction_button"):
                    if send_transaction(user_data['wallet_address'], recipient, amount):
                        st.success("Transaction sent successfully!")
                    else:
                        st.error("Failed to send transaction. Please try again.")
    else:
        st.error("User not found!")

def render_kyc_verification():
    if not check_auth():
        st.warning("Please login to access KYC verification")
        st.session_state.page = 'login'
        return
    
    st.title("Identity Verification")
    
    st.markdown("""
    To ensure trust and security on our platform, we require identity verification.
    Please follow these steps:
    
    1. Upload your government-issued ID
    2. Complete a live video verification
    3. Submit additional documents if requested
    """)
    
    # ID Upload
    st.subheader("Upload ID Document")
    uploaded_file = st.file_uploader("Upload Government ID", type=['jpg', 'jpeg', 'png', 'pdf'])
    
    if uploaded_file:
        # Process uploaded file
        file_type = uploaded_file.type
        if file_type == 'application/pdf':
            # Handle PDF
            st.success("PDF document uploaded successfully")
        else:
            # Handle image
            image = Image.open(uploaded_file)
            st.success("Image uploaded successfully")
    
    # Live Verification
    st.subheader("Live Video Verification")
    if st.button("Start Live Verification", key="start_live_verification_button"):
        st.session_state.verification_session = start_live_verification_session()
        st.session_state.page = 'live_verification'
    
    # Submit for Review
    if st.button("Submit for Review", type="primary", key="submit_kyc_button"):
        if update_kyc_status(st.session_state.user['id'], 'pending'):
            st.success("Your verification documents have been submitted for review")
            time.sleep(2)
            st.session_state.page = 'dashboard'
        else:
            st.error("Failed to submit verification documents")

def render_property_detail():
    if not check_auth():
        st.warning("Please login to view property details")
        st.session_state.page = 'login'
        return
    
    if 'selected_property' not in st.session_state:
        st.warning("No property selected")
        st.session_state.page = 'dashboard'
        return
    
    # Get property details
    properties = get_properties({'id': st.session_state.selected_property})
    if not properties:
        st.error("Property not found")
        st.session_state.page = 'dashboard'
        return
    
    property = properties[0]
    
    # Display property details
    st.title(property['title'])
    
    # Image gallery
    if 'images' in property and property['images']:
        st.image(property['images'][0], use_column_width=True)
        
        # Thumbnail gallery
        cols = st.columns(4)
        for i, img in enumerate(property['images'][1:5]):
            with cols[i]:
                st.image(img, use_column_width=True)
    
    # Property information
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"### Property Details")
        st.markdown(f"**Location:** {property['location']}")
        st.markdown(f"**Type:** {property['property_type']}")
        st.markdown(f"**Price:** ${property['price_per_day']}/day")
        st.markdown(f"**Capacity:** {property.get('capacity', 'N/A')} people")
        st.markdown(f"**Description:** {property.get('description', 'No description available')}")
        
        if property['verified']:
            st.success("✓ Property Verified")
        if property['blockchain_registered']:
            st.success("✓ Blockchain Registered")
    
    with col2:
        # Booking form
        st.markdown("### Book This Property")
        
        start_date = st.date_input("Check-in Date", min_value=datetime.now().date())
        end_date = st.date_input("Check-out Date", min_value=start_date + timedelta(days=1))
        
        # Calculate total price
        days = (end_date - start_date).days
        total_price = days * property['price_per_day']
        
        st.markdown(f"**Total Price:** ${total_price} for {days} days")
        
        if st.button("Request Booking", type="primary", key="request_booking_button"):
            # Create booking
            booking_data = {
                'id': str(uuid.uuid4()),
                'property_id': property['id'],
                'guest_id': st.session_state.user['id'],
                'owner_id': property['owner_id'],
                'check_in': start_date.strftime('%Y-%m-%d'),
                'check_out': end_date.strftime('%Y-%m-%d'),
                'total_price': total_price,
                'status': 'pending',
                'payment_status': 'pending'
            }
            
            if create_booking(booking_data):
                st.success("Booking request sent successfully!")
                time.sleep(2)
                st.session_state.page = 'dashboard'
            else:
                st.error("Failed to create booking request")
    
    # Property reviews
    st.markdown("### Reviews")
    reviews = get_reviews({'property_id': property['id']})
    
    if not reviews:
        st.info("No reviews yet. Be the first to review this property!")
    else:
        for review in reviews:
            st.markdown(f"**Rating:** {review['rating']}/5")
            st.markdown(f"**Comment:** {review['comment']}")
            st.markdown(f"**Date:** {review['created_at']}")
            st.markdown("---")
    
    # Add review button (only for users who have booked and stayed)
    if st.session_state.user['id'] != property['owner_id']:
        user_bookings = get_bookings({
            'guest_id': st.session_state.user['id'],
            'property_id': property['id'],
            'status': 'completed'
        })
        
        if user_bookings:
            if st.button("Write a Review", key="write_review_button"):
                st.session_state.page = 'write_review'
                st.session_state.selected_property = property['id']

def render_add_property():
    if not check_auth():
        st.warning("Please login to add a property")
        st.session_state.page = 'login'
        return
    
    st.title("Add New Property")
    
    # Property details form
    with st.form("add_property_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Property Title", placeholder="e.g., Luxury Villa in Malviya Nagar")
            location = st.text_input("Location", placeholder="e.g., Malviya Nagar, Jaipur")
            property_type = st.selectbox("Property Type", [
                "House", "Apartment", "Villa", "Garden", "Hall", "Event Space"
            ])
            price_per_day = st.number_input("Price per Day (₹)", min_value=1000, value=5000)
            capacity = st.number_input("Maximum Capacity", min_value=1, value=4)
        
        with col2:
            description = st.text_area("Description", placeholder="Describe your property...")
            amenities = st.multiselect("Amenities", [
                "Parking", "Swimming Pool", "Gym", "Security", "WiFi",
                "Air Conditioning", "Kitchen", "Laundry", "Elevator"
            ])
            rules = st.text_area("House Rules", placeholder="List your house rules...")
        
        # Image upload
        st.subheader("Property Images")
        uploaded_files = st.file_uploader(
            "Upload Property Images (Max 5)",
            type=['jpg', 'jpeg', 'png'],
            accept_multiple_files=True
        )
        
        images = []
        if uploaded_files:
            for file in uploaded_files[:5]:  # Limit to 5 images
                image = Image.open(file)
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                images.append(f"data:image/png;base64,{img_str}")
        
        # Submit button
        submitted = st.form_submit_button("Add Property", type="primary", key="add_property_button")
        
        if submitted:
            if not (title and location and price_per_day):
                st.warning("Please fill in all required fields")
            else:
                # Create property
                property_data = {
                    'id': str(uuid.uuid4()),
                    'owner_id': st.session_state.user['id'],
                    'title': title,
                    'location': location,
                    'property_type': property_type,
                    'price_per_day': price_per_day,
                    'capacity': capacity,
                    'description': description,
                    'amenities': amenities,
                    'rules': rules,
                    'images': images,
                    'verified': False,
                    'blockchain_registered': False,
                    'status': 'active',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                if create_property(property_data):
                    st.success("Property added successfully! It will be reviewed by our team.")
                    time.sleep(2)
                    st.session_state.page = 'dashboard'
                else:
                    st.error("Failed to add property. Please try again.")
    
    # Add a back button
    if st.button("Back to Dashboard", key="back_to_dashboard_button"):
        st.session_state.page = 'dashboard'

def render_live_verification():
    if not check_auth():
        st.warning("Please login to access live verification")
        st.session_state.page = 'login'
        return
    
    st.title("Live Property Verification")
    
    # Get verification session
    session = get_verification_session(st.session_state.verification_session)
    if not session:
        st.error("Invalid verification session")
        st.session_state.page = 'dashboard'
        return
    
    # Display verification instructions
    st.markdown("""
    ### Verification Instructions
    
    1. Ensure you are in a well-lit area
    2. Position yourself in front of the camera
    3. Hold your ID document clearly visible
    4. Follow the on-screen prompts
    """)
    
    # WebRTC component for video stream
    setup_webrtc_component()
    
    # Verification controls
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Capture Image", type="primary", key="capture_image_button"):
            image = capture_verification_image()
            if image:
                st.success("Image captured successfully")
                st.image(image, use_column_width=True)
    
    with col2:
        if st.button("Complete Verification", key="complete_verification_button"):
            if complete_verification_session(session['id']):
                st.success("Verification completed successfully!")
                time.sleep(2)
                st.session_state.page = 'dashboard'
            else:
                st.error("Failed to complete verification")

def render_write_review():
    if not check_auth():
        st.warning("Please login to write a review")
        st.session_state.page = 'login'
        return
    
    if 'selected_property' not in st.session_state:
        st.warning("No property selected")
        st.session_state.page = 'dashboard'
        return
    
    # Get property details
    properties = get_properties({'id': st.session_state.selected_property})
    if not properties:
        st.error("Property not found")
        st.session_state.page = 'dashboard'
        return
    
    property = properties[0]
    
    st.title(f"Write a Review for {property['title']}")
    
    # Review form
    with st.form("review_form"):
        rating = st.slider("Rating", 1, 5, 5)
        comment = st.text_area("Your Review", height=150)
        
        if st.form_submit_button("Submit Review", key="submit_review_button"):
            if not comment:
                st.warning("Please provide a review comment")
            else:
                # Create review
                review_data = {
                    'id': str(uuid.uuid4()),
                    'property_id': property['id'],
                    'user_id': st.session_state.user['id'],
                    'rating': rating,
                    'comment': comment,
                    'verified': False
                }
                
                if create_review(review_data):
                    st.success("Review submitted successfully!")
                    time.sleep(2)
                    st.session_state.page = 'property_detail'
                else:
                    st.error("Failed to submit review")

# Main app
def main():
    # Initialize sample data if properties.json doesn't exist
    if not os.path.exists('data/properties.json'):
        initialize_sample_data()
    
    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")
        
        if st.session_state.user:
            st.write(f"Welcome, {st.session_state.user['full_name']}")
            st.button("Logout", key="logout_button", on_click=logout)
        else:
            st.button("Login", key="sidebar_login_button", on_click=change_page, args=('login',))
            st.button("Register", key="sidebar_register_button", on_click=change_page, args=('register',))
        
        st.markdown("---")
        
        if st.session_state.user:
            if st.session_state.user['user_type'] == 'owner':
                st.button("My Properties", key="sidebar_my_properties_button", on_click=change_page, args=('dashboard',))
                st.button("Add Property", key="sidebar_add_property_button", on_click=change_page, args=('add_property',))
            else:
                st.button("Find Properties", key="sidebar_find_properties_button", on_click=change_page, args=('dashboard',))
                st.button("My Bookings", key="sidebar_my_bookings_button", on_click=change_page, args=('dashboard',))
            
            st.button("Wallet", key="sidebar_wallet_button", on_click=change_page, args=('wallet',))
            st.button("Profile", key="sidebar_profile_button", on_click=change_page, args=('profile',))
            st.button("KYC Verification", key="sidebar_kyc_button", on_click=change_page, args=('kyc_verification',))
    
    # Render current page
    if st.session_state.page == 'home':
        render_home()
    elif st.session_state.page == 'login':
        render_login()
    elif st.session_state.page == 'dashboard':
        render_dashboard()
    elif st.session_state.page == 'add_property':
        render_add_property()
    elif st.session_state.page == 'property_detail':
        render_property_detail()
    elif st.session_state.page == 'live_verification':
        render_live_verification()
    elif st.session_state.page == 'kyc_verification':
        render_kyc_verification()
    elif st.session_state.page == 'write_review':
        render_write_review()

if __name__ == "__main__":
    main()