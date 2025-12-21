"""
Enhanced Streamlit Application for VisionTrack AI
Refactored to use service layer and database integration
"""
import streamlit as st
import cv2
import tempfile
import numpy as np
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, RTCConfiguration, WebRtcMode
import os
import uuid
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from config import settings
from database import init_db, get_db, DatabaseService
from services.detection_service import DetectionService
from utils.logger import logger

# Initialize database
init_db()

# --- Page Config ---
st.set_page_config(
    page_title=f"{settings.APP_NAME} | YOLOv8 & DeepSORT",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

html, body, [class*="st-"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background-image: url("https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&q=80&w=2070&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
    background-size: cover;
    background-attachment: fixed;
    background-repeat: no-repeat;
}

.glass-card {
    background-color: rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(15px);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 20px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}

[data-testid="stSidebar"] {
    background: none;
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 2rem;
    padding-left: 1rem;
    padding-right: 1rem;
    background-color: rgba(10, 10, 20, 0.6);
    backdrop-filter: blur(20px);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    margin: 1rem;
}

[data-testid="stAppViewContainer"] > .main > .block-container {
    padding-top: 3rem;
    padding-left: 3rem;
    padding-right: 3rem;
    padding-bottom: 3rem;
}

h1 {
    color: #FFFFFF;
    font-weight: 700;
    text-shadow: 2px 2px 8px rgba(0,0,0,0.5);
}
h2 {
    color: #FFFFFF;
    font-weight: 600;
}
h3 {
    color: #E0E0E0;
    font-weight: 600;
}

p, .stMarkdown, [data-testid="stText"] {
    color: #E0E0E0;
    font-size: 1.05rem;
}

[data-testid="stTabs"] {
    background-color: rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(15px);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 10px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}

.stButton button {
    background: linear-gradient(45deg, #00A3FF, #007ACC);
    color: #FFFFFF;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    padding: 0.75rem 1.5rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(0, 163, 255, 0.3);
}
.stButton button:hover {
    background: linear-gradient(45deg, #007ACC, #00A3FF);
    box-shadow: 0 6px 20px rgba(0, 163, 255, 0.5);
    transform: translateY(-2px);
}
</style>
""", unsafe_allow_html=True)

# --- Constants ---
WEBRTC_RTC_CONFIGURATION = RTCConfiguration({
    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
})

# --- Model Loading ---
@st.cache_resource
def load_detection_service():
    """Load detection service with caching"""
    try:
        service = DetectionService()
        logger.info("Detection service loaded successfully")
        return service
    except Exception as e:
        logger.error(f"Error loading detection service: {e}")
        st.error(f"Error loading model: {e}")
        st.stop()

detection_service = load_detection_service()

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    with st.container(border=True):
        confidence_threshold = st.slider(
            "Confidence Threshold", 
            0.0, 1.0, 
            settings.DEFAULT_CONFIDENCE_THRESHOLD, 
            0.05
        )
    
    with st.container(border=True):
        selected_mode_string = st.radio(
            "WebRTC Mode", 
            ("SENDRECV", "RECVONLY"), 
            index=0, 
            key="webrtc_mode_tracking"
        )
    
    st.markdown("---")
    st.subheader("Webcam Status")
    status_placeholder = st.empty()
    
    st.markdown("---")
    with st.container(border=True):
        st.markdown("<h5>About this Project</h5>", unsafe_allow_html=True)
        st.markdown(
            f"**{settings.APP_NAME} v{settings.APP_VERSION}**\n\n"
            "Advanced AI/ML pipeline:\n"
            "1. **Detection:** YOLOv8\n"
            "2. **Tracking:** DeepSORT\n"
            "3. **API:** FastAPI REST\n"
            "4. **Database:** SQLite/PostgreSQL\n"
            "5. **Analytics:** Real-time metrics\n\n"
            "Production-ready architecture."
        )
        st.sidebar.link_button("View on GitHub", "https://github.com/your-username/visiontrack-ai")

# --- Webcam Transformer ---
class YOLOv8TrackingTransformer(VideoTransformerBase):
    """Video transformer for real-time tracking"""
    def __init__(self, service_instance, confidence_level):
        self.service = service_instance
        self.confidence = confidence_level
        self.tracker = service_instance.create_tracker()
    
    def update_confidence(self, new_confidence):
        self.confidence = new_confidence

    def transform(self, frame):
        try:
            img_bgr = frame.to_ndarray(format="bgr24")
            annotated_frame, _, _ = self.service.track_objects(
                img_bgr, 
                self.tracker, 
                self.confidence
            )
            return annotated_frame
        except Exception as e:
            logger.error(f"Error in video transform: {e}")
            return frame.to_ndarray(format="bgr24")

def create_webcam_transformer():
    """Create webcam transformer instance"""
    if 'video_transformer_tracking' not in st.session_state:
        st.session_state.video_transformer_tracking = YOLOv8TrackingTransformer(
            detection_service, 
            confidence_threshold
        )
    st.session_state.video_transformer_tracking.update_confidence(confidence_threshold)
    return st.session_state.video_transformer_tracking

# --- Main Page ---
st.title(f"✨ {settings.APP_NAME}")
st.markdown(
    f"**Version {settings.APP_VERSION}** - Real-Time Object Detection & Tracking Engine. "
    "Powered by **YOLOv8** and **DeepSORT** with production-ready architecture."
)

model_info = detection_service.get_model_info()
st.success(
    f"Model '{model_info['model_name']}' loaded. "
    f"Classes: {model_info['num_classes']}. "
    f"Confidence threshold: {confidence_threshold}", 
    icon="✅"
)
st.divider()

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🖼️ Image Upload", 
    "🎬 Video Upload", 
    "📹 Live Webcam",
    "📊 Analytics Dashboard",
    "⚙️ Settings & Export"
])

# --- Image Tab ---
with tab1:
    st.header("Detect Objects in an Image")
    st.markdown("Upload an image, and the AI will detect and label objects with database tracking.")
    
    uploaded_image = st.file_uploader(
        "Upload Image", 
        type=["jpg", "jpeg", "png"], 
        key="image_uploader", 
        label_visibility="collapsed"
    )
    
    if uploaded_image:
        col1, col2 = st.columns(2)
        image = cv2.imdecode(
            np.frombuffer(uploaded_image.read(), np.uint8), 
            cv2.IMREAD_COLOR
        )
        
        if image is None:
            st.error("Could not decode image.")
        else:
            with col1:
                st.image(image, caption="Original Image", use_container_width=True, channels="BGR")
            
            if st.button("🚀 Detect Objects", key="image_detect_button"):
                with st.spinner("🕵️‍♂️ Analyzing image..."):
                    # Create session
                    session_id = str(uuid.uuid4())
                    db = next(get_db())
                    
                    try:
                        DatabaseService.create_session(
                            db=db,
                            session_id=session_id,
                            session_type="image",
                            model_name=model_info['model_name'],
                            confidence_threshold=confidence_threshold
                        )
                        
                        # Detect objects
                        annotated_image, detections = detection_service.detect_objects(
                            image, 
                            confidence_threshold
                        )
                        
                        # Save to database
                        for det in detections:
                            DatabaseService.add_detection(
                                db=db,
                                session_id=session_id,
                                class_id=det["class_id"],
                                class_name=det["class_name"],
                                confidence=det["confidence"],
                                bbox=det["bbox"]
                            )
                        
                        DatabaseService.update_session(
                            db=db,
                            session_id=session_id,
                            total_detections=len(detections),
                            total_frames=1,
                            status="completed"
                        )
                        db.commit()
                        
                        with col2:
                            st.image(
                                annotated_image, 
                                caption="Detected Image", 
                                use_container_width=True, 
                                channels="BGR"
                            )
                        
                        with st.expander("🔍 Detection Results", expanded=True):
                            if detections:
                                st.write(f"**Total Detections:** {len(detections)}")
                                st.write(f"**Session ID:** `{session_id}`")
                                
                                # Class distribution
                                class_counts = {}
                                for det in detections:
                                    class_counts[det["class_name"]] = class_counts.get(det["class_name"], 0) + 1
                                
                                df = pd.DataFrame([
                                    {"Class": k, "Count": v} 
                                    for k, v in class_counts.items()
                                ])
                                
                                if not df.empty:
                                    fig = px.bar(
                                        df, 
                                        x="Class", 
                                        y="Count",
                                        title="Detection Distribution",
                                        color="Count",
                                        color_continuous_scale="Blues"
                                    )
                                    fig.update_layout(
                                        plot_bgcolor='rgba(0,0,0,0)',
                                        paper_bgcolor='rgba(0,0,0,0)',
                                        font_color='white'
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                
                                # Detailed results
                                for det in detections:
                                    st.write(
                                        f"- **{det['class_name']}** "
                                        f"(Confidence: {det['confidence']:.2f})"
                                    )
                            else:
                                st.write("No objects detected.")
                    except Exception as e:
                        logger.error(f"Error processing image: {e}")
                        st.error(f"Error: {e}")
                    finally:
                        db.close()

# --- Video Tab ---
with tab2:
    st.header("Track Objects in a Video")
    st.markdown("Upload a video, and the AI will detect and track objects frame by frame.")
    
    uploaded_video = st.file_uploader(
        "Upload Video", 
        type=["mp4", "avi", "mov", "mkv"], 
        key="video_uploader", 
        label_visibility="collapsed"
    )
    
    if uploaded_video:
        video_path = None
        try:
            temp_dir = tempfile.gettempdir()
            file_suffix = os.path.splitext(uploaded_video.name)[1]
            tfile = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=file_suffix or '.tmp', 
                dir=temp_dir
            )
            tfile.write(uploaded_video.read())
            video_path = tfile.name
            tfile.close()

            st.video(video_path)
            
            if st.button("🚀 Track Objects in Video", key="video_detect_button"):
                session_id = str(uuid.uuid4())
                db = next(get_db())
                
                try:
                    DatabaseService.create_session(
                        db=db,
                        session_id=session_id,
                        session_type="video",
                        model_name=model_info['model_name'],
                        confidence_threshold=confidence_threshold
                    )
                    
                    video_output_placeholder = st.empty()
                    video_tracker = detection_service.create_tracker()
                    cap = cv2.VideoCapture(video_path)
                    
                    if not cap.isOpened():
                        st.error("Error: Could not open video file.")
                    else:
                        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                        progress_bar = st.progress(0, text="Initializing...") if total_frames > 0 else None
                        
                        frame_counter = 0
                        total_detections = 0
                        
                        while cap.isOpened():
                            ret, frame = cap.read()
                            if not ret:
                                break
                            if frame is None or frame.size == 0:
                                continue
                            
                            annotated_frame, detections, fps = detection_service.track_objects(
                                frame, 
                                video_tracker, 
                                confidence_threshold
                            )
                            
                            # Save detections
                            for det in detections:
                                DatabaseService.add_detection(
                                    db=db,
                                    session_id=session_id,
                                    class_id=det["class_id"],
                                    class_name=det["class_name"],
                                    confidence=det["confidence"],
                                    bbox=det["bbox"],
                                    frame_number=frame_counter,
                                    track_id=det.get("track_id")
                                )
                                total_detections += 1
                            
                            video_output_placeholder.image(
                                annotated_frame, 
                                channels="BGR", 
                                use_container_width=True
                            )
                            
                            frame_counter += 1
                            if progress_bar is not None and total_frames > 0:
                                progress_text = f"Processing frame {frame_counter} / {total_frames} | FPS: {fps:.2f}"
                                progress_bar.progress(
                                    frame_counter / total_frames, 
                                    text=progress_text
                                )

                        DatabaseService.update_session(
                            db=db,
                            session_id=session_id,
                            total_detections=total_detections,
                            total_frames=frame_counter,
                            status="completed"
                        )
                        db.commit()
                        
                        st.success(f"Video processing complete. Session ID: `{session_id}`")
                        if progress_bar:
                            progress_bar.empty()
                
                except Exception as e:
                    logger.error(f"Error processing video: {e}")
                    st.error(f"Error: {e}")
                finally:
                    if cap:
                        cap.release()
                    db.close()
                    if video_path and os.path.exists(video_path) and tempfile.gettempdir() in os.path.abspath(video_path):
                        os.remove(video_path)
        except Exception as e:
            st.error(f"Error handling uploaded video: {e}")

# --- Webcam Tab ---
with tab3:
    st.header("Live Webcam Tracking")
    st.info("Click 'Start' to begin. Note: Performance depends on your network connection.", icon="ℹ️")

    mode_enum = WebRtcMode.SENDRECV if selected_mode_string == "SENDRECV" else WebRtcMode.RECVONLY

    webrtc_ctx = webrtc_streamer(
        key="yolo-webcam-tracking",
        mode=mode_enum,
        rtc_configuration=WEBRTC_RTC_CONFIGURATION,
        media_stream_constraints={"video": True, "audio": False},
        video_transformer_factory=create_webcam_transformer,
        async_processing=True,
    )
    
    if webrtc_ctx.state.playing:
        status_placeholder.success("Webcam is **LIVE**", icon="🔴")
        if 'video_transformer_tracking' in st.session_state:
            st.sidebar.write(f"Confidence: **{st.session_state.video_transformer_tracking.confidence:.2f}**")
    else:
        status_placeholder.info("Webcam is **STOPPED**", icon="⚫")

# --- Analytics Dashboard Tab ---
with tab4:
    st.header("📊 Analytics Dashboard")
    st.markdown("View insights and statistics from your detection sessions.")
    
    db = next(get_db())
    try:
        days = st.slider("Select time range (days)", 1, 30, 7)
        analytics = DatabaseService.get_analytics(db, days)
        
        if analytics["total_sessions"] > 0:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Sessions", analytics["total_sessions"])
            with col2:
                st.metric("Total Detections", analytics["total_detections"])
            with col3:
                st.metric("Avg Confidence", f"{analytics['avg_confidence']:.2f}")
            with col4:
                st.metric("Avg Processing Time", f"{analytics['avg_processing_time']:.2f}s")
            
            # Class distribution chart
            if analytics["class_distribution"]:
                st.subheader("Class Distribution")
                df_class = pd.DataFrame([
                    {"Class": k, "Count": v} 
                    for k, v in analytics["class_distribution"].items()
                ])
                fig = px.pie(
                    df_class, 
                    values="Count", 
                    names="Class",
                    title="Detection Class Distribution"
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Sessions by type
            if analytics["sessions_by_type"]:
                st.subheader("Sessions by Type")
                df_type = pd.DataFrame([
                    {"Type": k, "Count": v} 
                    for k, v in analytics["sessions_by_type"].items()
                ])
                fig = px.bar(
                    df_type, 
                    x="Type", 
                    y="Count",
                    color="Count",
                    color_continuous_scale="Viridis"
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for the selected time range.")
    finally:
        db.close()

# --- Settings & Export Tab ---
with tab5:
    st.header("⚙️ Settings & Export")
    
    st.subheader("Model Information")
    st.json(model_info)
    
    st.subheader("Export Data")
    session_id_input = st.text_input("Enter Session ID to export")
    
    if st.button("Export Session Data"):
        if session_id_input:
            db = next(get_db())
            try:
                stats = DatabaseService.get_session_stats(db, session_id_input)
                if stats:
                    st.json(stats)
                    st.download_button(
                        label="Download as JSON",
                        data=str(stats),
                        file_name=f"session_{session_id_input}.json",
                        mime="application/json"
                    )
                else:
                    st.error("Session not found")
            finally:
                db.close()
        else:
            st.warning("Please enter a session ID")

