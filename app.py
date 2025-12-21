import streamlit as st
import cv2
from ultralytics import YOLO
import tempfile
import supervision as sv
import numpy as np
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, RTCConfiguration, WebRtcMode
import os
import time
from deep_sort_realtime.deepsort_tracker import DeepSort

# --- Page Config ---
st.set_page_config(
    page_title="VisionTrack AI | YOLOv8 & DeepSORT",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (THE "MAGIC" TO MAKE IT LOOK GOOD) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

/* --- Global Styles --- */
html, body, [class*="st-"] {
    font-family: 'Inter', sans-serif;
}

/* --- Main App Background --- */
.stApp {
    background-image: url("https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&q=80&w=2070&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
    background-size: cover;
    background-attachment: fixed;
    background-repeat: no-repeat;
}

/* --- Glassmorphism Card Effect --- */
.glass-card {
    background-color: rgba(0, 0, 0, 0.4); /* Darker semi-transparent background */
    backdrop-filter: blur(15px); /* Increased blur */
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1); /* Subtle white border */
    padding: 20px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37); /* Deeper shadow */
}

/* --- Sidebar --- */
[data-testid="stSidebar"] {
    background: none; /* Remove default sidebar background */
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 2rem;
    padding-left: 1rem;
    padding-right: 1rem;
    /* Apply glass card effect to the sidebar inner container */
    background-color: rgba(10, 10, 20, 0.6); /* Darker glass for sidebar */
    backdrop-filter: blur(20px);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    margin: 1rem; /* Give sidebar 'floating' look */
}

/* --- Main Content Area --- */
[data-testid="stAppViewContainer"] > .main > .block-container {
    padding-top: 3rem;
    padding-left: 3rem;
    padding-right: 3rem;
    padding-bottom: 3rem;
}

/* --- Titles and Headers --- */
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

/* --- General Text --- */
p, .stMarkdown, [data-testid="stText"] {
    color: #E0E0E0; /* Lighter grey for better readability */
    font-size: 1.05rem;
}

/* --- Tabs --- */
[data-testid="stTabs"] {
    /* Apply glass card effect to the whole tab container */
    background-color: rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(15px);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 10px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}
[data-testid="stTabs"] button {
    font-size: 1.1rem;
    font-weight: 600;
    color: #A0A0A0; /* Dimmed color for inactive tabs */
    border-radius: 8px;
    padding: 0.5rem 1rem;
    transition: all 0.3s ease;
}
[data-testid="stTabs"] button:hover {
    color: #FFFFFF;
    background-color: rgba(255, 255, 255, 0.1);
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #FFFFFF;
    background-color: #00A3FF; /* Bright accent color */
    border: none;
    box-shadow: 0 0 15px 5px rgba(0, 163, 255, 0.3);
}

/* --- Sidebar Controls --- */
[data-testid="stSlider"] {
    border: 1px solid rgba(255, 255, 255, 0.1);
    background-color: rgba(0, 0, 0, 0.2);
    padding: 15px;
    border-radius: 10px;
}
[data-testid="stRadio"] {
    border: 1px solid rgba(255, 255, 255, 0.1);
    background-color: rgba(0, 0, 0, 0.2);
    padding: 15px;
    border-radius: 10px;
}

/* --- Buttons --- */
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
.stButton button:focus {
    box-shadow: 0 0 0 3px rgba(0, 163, 255, 0.5);
}

/* --- File Uploader --- */
[data-testid="stFileUploader"] {
    background-color: rgba(0, 0, 0, 0.2);
    border: 2px dashed rgba(255, 255, 255, 0.3);
    border-radius: 10px;
}
[data-testid="stFileUploader"] label {
    color: #FFFFFF;
    font-weight: 600;
}

/* --- Expander (Detected Objects) --- */
[data-testid="stExpander"] {
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 10px;
    background-color: rgba(0, 0, 0, 0.2);
}
[data-testid="stExpander"] summary {
    font-size: 1.1rem;
    font-weight: 600;
    color: #FFFFFF;
}

/* --- Info/Warning Boxes --- */
[data-testid="stAlert"] {
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    background-color: rgba(0, 0, 0, 0.2);
    padding: 1rem;
}

/* --- Success Box --- */
[data-testid="stAlert"][data-testid*="stSuccess"] {
    background-color: rgba(0, 255, 100, 0.1);
    border-color: rgba(0, 255, 100, 0.3);
}

/* --- Warning Box --- */
[data-testid="stAlert"][data-testid*="stWarning"] {
    background-color: rgba(255, 200, 0, 0.1);
    border-color: rgba(255, 200, 0, 0.3);
}

/* --- Video/Image Display --- */
.stImage, .stVideo {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

</style>
""", unsafe_allow_html=True)

# --- Constants ---
CONFIDENCE_THRESHOLD_DEFAULT = 0.3
MODEL_PATH = 'yolov8n.pt'
WEBRTC_RTC_CONFIGURATION = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})

# --- Model Loading ---
@st.cache_resource
def load_yolo_model(model_path):
    try:
        model = YOLO(model_path)
        _ = model.model.names
        return model
    except Exception as e:
        st.error(f"Error loading YOLO model '{model_path}': {e}")
        st.stop()

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    with st.container(border=True):
        confidence_threshold = st.slider(
            "Confidence Threshold", 0.0, 1.0, CONFIDENCE_THRESHOLD_DEFAULT, 0.05
        )
        
    with st.container(border=True):
        selected_mode_string = st.radio(
            "WebRTC Mode", ("SENDRECV", "RECVONLY"), index=0, key="webrtc_mode_tracking"
        )
    
    st.markdown("---")
    st.subheader("Webcam Status")
    status_placeholder = st.empty() # Placeholder for status
    
    st.markdown("---")
    with st.container(border=True):
        st.markdown("<h5>About this Project</h5>", unsafe_allow_html=True)
        st.markdown(
            "This app demonstrates a complete AI/ML pipeline:\n"
            "1. **Detection:** YOLOv8\n"
            "2. **Tracking:** DeepSORT\n"
            "3. **Interface:** Streamlit\n\n"
            "Built to showcase end-to-end engineering skills."
        )
        st.sidebar.link_button("View on GitHub", "https://github.com/asaadshaikh/YOLOv8-Streamlit-Tracker")

model = load_yolo_model(MODEL_PATH)

# --- Annotator Setup ---
try:
    colors = sv.ColorPalette.DEFAULT
    box_annotator = sv.BoxAnnotator(color=colors, thickness=2)
    label_annotator = sv.LabelAnnotator(color=colors, text_color="white", text_scale=0.5, text_thickness=1)
except AttributeError:
    # Fallback for different supervision versions
    try:
        box_annotator = sv.BoxAnnotator(color="white", thickness=2)
        label_annotator = sv.LabelAnnotator(color="white", text_color="red", text_scale=0.5, text_thickness=1)
    except Exception as e:
        st.error(f"Error initializing annotators: {e}. Check supervision installation.")
        st.stop()
except Exception as e:
    st.error(f"An unexpected error occurred during annotator setup: {e}")
    st.stop()


# --- Helper Functions ---
def process_image(image, confidence):
    results = model.predict(image, conf=confidence, verbose=False)
    result = results[0]
    detections = sv.Detections.from_ultralytics(result)

    annotated_image = image.copy()
    labels = []
    if len(detections) > 0 and detections.class_id is not None:
        labels = [
            f"{model.model.names[class_id]} {conf:0.2f}"
            for class_id, conf in zip(detections.class_id, detections.confidence)
            if class_id in model.model.names
        ]
        annotated_image = box_annotator.annotate(scene=annotated_image, detections=detections)
        if len(labels) == len(detections):
            annotated_image = label_annotator.annotate(scene=annotated_image, detections=detections, labels=labels)
    return annotated_image, detections

def process_frame_with_tracking(frame, confidence, tracker):
    start_time = time.time()
    results = model.predict(frame, conf=confidence, verbose=False)
    detections = sv.Detections.from_ultralytics(results[0])

    formatted_detections = []
    if len(detections) > 0:
        for i in range(len(detections)):
            bbox = detections.xyxy[i]
            conf = detections.confidence[i]
            cls_id = detections.class_id[i]
            if len(bbox) == 4:
                formatted_detections.append((bbox, conf, int(cls_id)))

    deepsort_detections = []
    for bbox_xyxy, conf, cls_id in formatted_detections:
        x1, y1, x2, y2 = bbox_xyxy
        w, h = x2 - x1, y2 - y1 # Corrected typo here (was yB)
        if w > 0 and h > 0:
            deepsort_detections.append(([int(x1), int(y1), int(w), int(h)], conf, cls_id))
    
    tracks = []
    if deepsort_detections:
        try:
            tracks = tracker.update_tracks(deepsort_detections, frame=frame)
        except Exception:
            pass 

    tracked_bboxes_xyxy = []
    track_ids = []
    track_class_ids = []
    for track in tracks:
        if not track.is_confirmed() or track.time_since_update > 1:
            continue
        track_id = track.track_id
        ltrb = track.to_ltrb()
        class_id = track.get_det_class()
        if ltrb is not None and class_id is not None and class_id in model.model.names:
            tracked_bboxes_xyxy.append(ltrb)
            track_ids.append(track_id)
            track_class_ids.append(class_id)

    tracked_detections = sv.Detections.empty()
    if tracked_bboxes_xyxy:
        tracked_detections = sv.Detections(xyxy=np.array(tracked_bboxes_xyxy))

    annotated_frame = frame.copy()
    if len(tracked_detections) > 0:
        labels = [
            f"#{track_id} {model.model.names[cls_id]}"
            for track_id, cls_id in zip(track_ids, track_class_ids)
        ]
        annotated_frame = box_annotator.annotate(scene=annotated_frame, detections=tracked_detections)
        if len(labels) == len(tracked_detections):
            annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=tracked_detections, labels=labels)
    
    end_time = time.time()
    fps = 1 / (end_time - start_time) if (end_time - start_time) > 0 else 0
    cv2.putText(annotated_frame, f"FPS: {fps:.2f}", (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
    
    return annotated_frame

# --- Webcam Transformer ---
class YOLOv8TrackingTransformer(VideoTransformerBase):
    def __init__(self, model_instance, confidence_level):
        self.model = model_instance
        self.confidence = confidence_level
        self.tracker = DeepSort(max_age=30, n_init=3, nms_max_overlap=1.0)
    
    def update_confidence(self, new_confidence):
        self.confidence = new_confidence

    def transform(self, frame):
        try:
            img_bgr = frame.to_ndarray(format="bgr24")
            annotated_frame = process_frame_with_tracking(img_bgr, self.confidence, self.tracker)
            return annotated_frame
        except Exception:
            return frame.to_ndarray(format="bgr24")

def create_webcam_transformer():
    if 'video_transformer_tracking' not in st.session_state:
        st.session_state.video_transformer_tracking = YOLOv8TrackingTransformer(model, confidence_threshold)
    st.session_state.video_transformer_tracking.update_confidence(confidence_threshold)
    return st.session_state.video_transformer_tracking

# --- Main Page ---
st.title("✨ VisionTrack AI")
st.markdown(
    "Welcome to the Real-Time Object Detection & Tracking Engine. "
    "Powered by **YOLOv8** and **DeepSORT**."
)
st.success(f"Model '{MODEL_PATH}' loaded. Confidence threshold: {confidence_threshold}", icon="✅")
st.divider()

tab1, tab2, tab3 = st.tabs(["🖼️ Image Upload", "🎬 Video Upload", "📹 Live Webcam"])

# --- Image Tab ---
with tab1:
    st.header("Detect Objects in an Image")
    st.markdown("Upload an image, and the AI will detect and label objects.")
    
    uploaded_image = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"], key="image_uploader", label_visibility="collapsed")
    
    if uploaded_image:
        col1, col2 = st.columns(2)
        image = cv2.imdecode(np.frombuffer(uploaded_image.read(), np.uint8), cv2.IMREAD_COLOR)
        
        if image is None:
            st.error("Could not decode image.")
        else:
            with col1:
                st.image(image, caption="Original Image", use_container_width=True, channels="BGR")
            
            if st.button("🚀 Detect Objects", key="image_detect_button"):
                with st.spinner("🕵️‍♂️ Analyzing image..."):
                    annotated_image, detections = process_image(image, confidence_threshold)
                with col2:
                    st.image(annotated_image, caption="Detected Image", use_container_width=True, channels="BGR")
                
                with st.expander("🔍 Detection Results", expanded=True):
                    if len(detections) > 0 and detections.class_id is not None:
                        detected_items = set()
                        for class_id, confidence in zip(detections.class_id, detections.confidence):
                            if class_id in model.model.names:
                                class_name = model.model.names[class_id]
                                detected_items.add(f"- **{class_name}** (Confidence: {confidence:.2f})")
                        if detected_items:
                            for item in sorted(list(detected_items)):
                                st.write(item)
                        else:
                            st.write("No objects detected with valid class IDs.")
                    else:
                        st.write("No objects detected.")

# --- Video Tab ---
with tab2:
    st.header("Track Objects in a Video")
    st.markdown("Upload a video, and the AI will detect and track objects frame by frame.")
    
    uploaded_video = st.file_uploader("Upload Video", type=["mp4", "avi", "mov", "mkv"], key="video_uploader", label_visibility="collapsed")
    
    if uploaded_video:
        video_path = None
        try:
            temp_dir = tempfile.gettempdir()
            file_suffix = os.path.splitext(uploaded_video.name)[1]
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix or '.tmp', dir=temp_dir)
            tfile.write(uploaded_video.read())
            video_path = tfile.name
            tfile.close()

            st.video(video_path)
            
            if st.button("🚀 Track Objects in Video", key="video_detect_button"):
                video_output_placeholder = st.empty()
                video_tracker = DeepSort(max_age=30, n_init=3, nms_max_overlap=1.0)
                cap = None
                try:
                    cap = cv2.VideoCapture(video_path)
                    if not cap.isOpened():
                        st.error("Error: Could not open video file.")
                    else:
                        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                        progress_bar = st.progress(0, text="Initializing...") if total_frames > 0 else None
                        
                        frame_counter = 0
                        while cap.isOpened():
                            ret, frame = cap.read()
                            if not ret: break
                            if frame is None or frame.size == 0: continue
                            
                            annotated_frame = process_frame_with_tracking(frame, confidence_threshold, video_tracker)
                            video_output_placeholder.image(annotated_frame, channels="BGR", use_container_width=True)
                            
                            frame_counter += 1
                            if progress_bar is not None and total_frames > 0:
                                progress_text = f"Processing frame {frame_counter} / {total_frames}"
                                progress_bar.progress(frame_counter / total_frames, text=progress_text)

                        st.success("Video processing complete.")
                        if progress_bar: progress_bar.empty()
                
                finally:
                    if cap: cap.release()
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

    

