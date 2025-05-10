# utils/video_stream.py
import streamlit as st
import json
import uuid
import time
from datetime import datetime
import os
import base64
from PIL import Image
import io
import hashlib

def setup_webrtc_component():
    """
    Sets up WebRTC component for live video streaming.
    Uses streamlit-webrtc component.
    """
    # Check if streamlit-webrtc is installed, if not provide instructions
    try:
        from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
        import av
        
        class VideoProcessor(VideoProcessorBase):
            def __init__(self):
                self.frames = []
                self.max_frames = 10  # Store up to 10 frames for verification
            
            def recv(self, frame):
                # Process the video frame
                img = frame.to_ndarray(format="bgr24")
                
                # Store frame if we haven't reached max
                if len(self.frames) < self.max_frames:
                    self.frames.append(img)
                
                return av.VideoFrame.from_ndarray(img, format="bgr24")
            
            def get_verification_frames(self):
                return self.frames
        
        # Create processor instance
        processor = VideoProcessor()
        
        # Create WebRTC streamer
        webrtc_ctx = webrtc_streamer(
            key="property-verification",
            video_processor_factory=lambda: processor,
            media_stream_constraints={"video": True, "audio": False},
        )
        
        return webrtc_ctx, processor
    
    except ImportError:
        st.error("streamlit-webrtc is not installed. Please install it using: pip install streamlit-webrtc")
        st.code("pip install streamlit-webrtc opencv-python-headless av")
        return None, None

def capture_verification_image(webrtc_ctx, processor):
    """Capture an image from the live video stream for verification."""
    if webrtc_ctx and webrtc_ctx.state.playing and processor:
        frames = processor.get_verification_frames()
        if frames:
            # Get the last frame
            img = frames[-1]
            
            # Convert to PIL Image
            img_pil = Image.fromarray(img[:, :, ::-1])  # Convert BGR to RGB
            
            # Save to buffer
            buf = io.BytesIO()
            img_pil.save(buf, format="JPEG")
            
            # Create timestamp
            timestamp = datetime.now().isoformat()
            
            # Create verification record
            verification_id = str(uuid.uuid4())
            verification_data = {
                "id": verification_id,
                "timestamp": timestamp,
                "image_hash": hashlib.sha256(buf.getvalue()).hexdigest()
            }
            
            # Save image to file
            os.makedirs("data/verification_images", exist_ok=True)
            img_path = f"data/verification_images/{verification_id}.jpg"
            with open(img_path, "wb") as f:
                f.write(buf.getvalue())
            
            # Add file path to verification data
            verification_data["image_path"] = img_path
            
            return verification_data, buf.getvalue()
    
    return None, None

def start_live_verification_session(property_id, owner_id, renter_id):
    """Start a live verification session between property owner and renter."""
    # Generate a unique session ID
    session_id = str(uuid.uuid4())
    
    # Create session record
    session_data = {
        "id": session_id,
        "property_id": property_id,
        "owner_id": owner_id,
        "renter_id": renter_id,
        "created_at": datetime.now().isoformat(),
        "status": "pending",  # pending, active, completed, cancelled
        "images": []
    }
    
    # Save session data
    try:
        sessions = load_verification_sessions()
        sessions.append(session_data)
        save_verification_sessions(sessions)
        return session_id
    except Exception as e:
        print(f"Error creating verification session: {e}")
        return None

def load_verification_sessions():
    """Load verification sessions from JSON file."""
    try:
        with open('data/verification_sessions.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Create empty file if it doesn't exist
        os.makedirs('data', exist_ok=True)
        with open('data/verification_sessions.json', 'w') as f:
            json.dump([], f)
        return []

def save_verification_sessions(sessions):
    """Save verification sessions to JSON file."""
    with open('data/verification_sessions.json', 'w') as f:
        json.dump(sessions, f, indent=4)

def add_verification_image(session_id, image_data):
    """Add a verification image to a session."""
    sessions = load_verification_sessions()
    
    for session in sessions:
        if session['id'] == session_id:
            session['images'].append(image_data)
            session['last_updated'] = datetime.now().isoformat()
            save_verification_sessions(sessions)
            return True
    
    return False

def complete_verification_session(session_id, verified=True):
    """Mark a verification session as completed."""
    sessions = load_verification_sessions()
    
    for session in sessions:
        if session['id'] == session_id:
            session['status'] = "completed"
            session['verified'] = verified
            session['completed_at'] = datetime.now().isoformat()
            save_verification_sessions(sessions)
            return True
    
    return False

def get_verification_session(session_id):
    """Get a specific verification session."""
    sessions = load_verification_sessions()
    
    for session in sessions:
        if session['id'] == session_id:
            return session
    
    return None

# AI-based image verification (simplified version)
def verify_property_images(listing_images, verification_images, threshold=0.7):
    """
    Compare property listing images with verification images using simple hashing.
    In a real implementation, you would use more advanced image similarity algorithms.
    """
    try:
        import cv2
        import numpy as np
        
        # This is a simplified approach, in a real system you'd use:
        # - SIFT or ORB feature matching
        # - Neural network-based similarity
        # - Scene recognition algorithms
        
        if not listing_images or not verification_images:
            return False, 0.0
        
        # Convert verification image to OpenCV format
        if isinstance(verification_images[0], str):
            # Path to image
            verification_img = cv2.imread(verification_images[0])
        else:
            # Raw image data
            nparr = np.frombuffer(verification_images[0], np.uint8)
            verification_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        max_similarity = 0.0
        
        for listing_img_path in listing_images:
            listing_img = cv2.imread(listing_img_path)
            
            # Resize images to same dimensions
            if listing_img.shape != verification_img.shape:
                listing_img = cv2.resize(listing_img, (verification_img.shape[1], verification_img.shape[0]))
            
            # Calculate histogram similarity (a simple approach)
            hist1 = cv2.calcHist([listing_img], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            hist2 = cv2.calcHist([verification_img], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            
            cv2.normalize(hist1, hist1)
            cv2.normalize(hist2, hist2)
            
            similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            max_similarity = max(max_similarity, similarity)
        
        return max_similarity >= threshold, max_similarity
    
    except ImportError:
        st.error("OpenCV is required for image verification. Install it with: pip install opencv-python-headless")
        return False, 0.0
    except Exception as e:
        st.error(f"Error in image verification: {e}")
        return False, 0.0
