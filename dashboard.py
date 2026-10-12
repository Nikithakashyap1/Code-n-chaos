
import time
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st
from streamlit_webrtc import (
    webrtc_streamer,
    WebRtcMode,
    RTCConfiguration,
)

from hand_tracking import RehabHandTracker
from rehab_exercise import EXERCISES, get_exercise_instructions

BASE = Path(__file__).parent
MODEL = BASE / "hand_landmarker.task"
DATA = BASE / "rehab_data"
HISTORY = DATA / "sessions.csv"
CUSTOM_GESTURES = DATA / "custom_gestures.csv"
DATA.mkdir(exist_ok=True)

st.set_page_config(
    page_title="RehabMotion | Movement Studio",
    page_icon="✦",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

.stApp {
    background:
      radial-gradient(ellipse at 80% 0%, #29245a 0%, transparent 35%),
      #090e1b;
    color: #edf4ff;
    font-family: 'DM Sans', sans-serif;
}
[data-testid="stSidebar"] {
    background: #10182a;
    border-right: 1px solid #263149;
}
h1, h2, h3 {
    font-family: 'Space Grotesk', sans-serif !important;
}
.block-container {
    max-width: 1450px;
    padding-top: 2rem;
}
div[data-testid="stMetric"] {
    background: #121d30;
    border: 1px solid #28364c;
    padding: 18px;
    border-radius: 18px;
}
div[data-testid="stMetricValue"] { color: #61f5d4; }
div.stButton > button {
    border-radius: 12px;
    min-height: 44px;
    border: 1px solid #55e8d0;
    background: linear-gradient(100deg,#55e8d0,#a78bfa);
    color: #08121d;
    font-weight: 800;
}
.hero {
    background: linear-gradient(120deg,#14283a,#25234c);
    border: 1px solid #35405d;
    padding: 34px;
    border-radius: 25px;
}
.eyebrow {
    color: #61f5d4;
    letter-spacing: 3px;
    font-size: 12px;
    font-weight: 700;
}
.card {
    background: #121d30;
    border: 1px solid #28364c;
    border-radius: 18px;
    padding: 22px;
}
.muted { color: #a6b6cf; }
</style>
""", unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state.page = "Overview"
if "exercise" not in st.session_state:
    st.session_state.exercise = "Finger Flexion"
if "started" not in st.session_state:
    st.session_state.started = None
if "saved" not in st.session_state:
    st.session_state.saved = False

def read_history():
    if HISTORY.exists():
        try:
            return pd.read_csv(HISTORY)
        except Exception:
            pass
    return pd.DataFrame(columns=[
        "date", "exercise", "repetitions", "seconds"
    ])

def save_session(exercise, reps, seconds):
    df = read_history()
    new = pd.DataFrame([{
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "exercise": exercise,
        "repetitions": int(reps),
        "seconds": int(seconds),
    }])
    pd.concat([df, new], ignore_index=True).to_csv(
        HISTORY, index=False
    )

with st.sidebar:
    st.markdown(
        "<h2>✦ Rehab<span style='color:#61f5d4'>Motion</span></h2>"
        "<p style='color:#8fa4c3'>HAND MOVEMENT STUDIO</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    for name, icon in [
        ("Overview", "◈"),
        ("AI Exercise Studio", "◎"),
        ("Exercise Library", "▤"),
        ("Custom Gestures", "✋"),
        ("My Progress", "↗"),
        ("About", "ⓘ"),
    ]:
        if st.button(f"{icon}  {name}", key=f"nav_{name}",
                     use_container_width=True):
            st.session_state.page = name
            st.rerun()

page = st.session_state.page

if page == "Overview":
    df = read_history()
    total_reps = (
        int(pd.to_numeric(df["repetitions"], errors="coerce")
            .fillna(0).sum()) if not df.empty else 0
    )
    total_minutes = (
        int(pd.to_numeric(df["seconds"], errors="coerce")
            .fillna(0).sum() // 60) if not df.empty else 0
    )

    st.markdown("""
    <div class="hero">
      <div class="eyebrow">YOUR MOVEMENT, YOUR PACE</div>
      <h1>Small movements.<br>
      <span style="color:#61f5d4">Meaningful progress.</span></h1>
      <p class="muted">A guided hand-movement practice space
      with live camera tracking, predefined exercises, and
      a personal progress log.</p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    a, b, c = st.columns(3)
    a.metric("Sessions logged", len(df))
    b.metric("Repetitions recorded", total_reps)
    c.metric("Practice time", f"{total_minutes} min")

    st.write("")
    st.subheader("Your movement workspace")
    a, b = st.columns(2)
    with a:
        st.markdown("""
        <div class="card">
        <h3>◎ AI Exercise Studio</h3>
        <p class="muted">Live webcam tracking, hand landmarks,
        repetition counter, and session controls.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Exercise Studio", use_container_width=True):
            st.session_state.page = "AI Exercise Studio"
            st.rerun()
    with b:
        st.markdown("""
        <div class="card">
        <h3>↗ My Progress</h3>
        <p class="muted">Review your session history and
        track practice over time.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("View My Progress", use_container_width=True):
            st.session_state.page = "My Progress"
            st.rerun()

elif page == "AI Exercise Studio":
    st.markdown(
        '<div class="eyebrow">CAMERA-POWERED PRACTICE</div>',
        unsafe_allow_html=True,
    )
    st.title("AI Exercise Studio")
    st.write(
        "Keep one hand fully in view, use good lighting, "
        "and move slowly."
    )

    if not MODEL.exists():
        st.error(
            "hand_landmarker.task was not found. "
            "Put it beside dashboard.py."
        )
        st.stop()

    left, right = st.columns([1.6, 1])

    with right:
        exercise = st.selectbox(
            "Choose an exercise",
            list(EXERCISES.keys()),
            index=list(EXERCISES.keys()).index(
                st.session_state.exercise
            ),
        )
        st.session_state.exercise = exercise
        info = EXERCISES[exercise]

        st.markdown(
            f"""<div class="card">
            <div class="eyebrow">{info['category']}</div>
            <h3>{info['icon']} {exercise}</h3>
            <p class="muted">{info['description']}</p>
            <hr>
            <b>How to do it</b>
            <p>{get_exercise_instructions(exercise)}</p>
            <b>Suggested target: {info['target']} reps</b>
            </div>""",
            unsafe_allow_html=True,
        )
        st.write("")
        start_col, end_col = st.columns(2)

        with start_col:
            if st.button("▶ Start", use_container_width=True):
                st.session_state.started = time.time()
                st.session_state.saved = False
                st.toast("Session started!")

        with end_col:
            if st.button("■ End & Save", use_container_width=True):
                if st.session_state.started is None:
                    st.warning("Start a session first.")
                elif not st.session_state.saved:
                    seconds = int(
                        time.time() - st.session_state.started
                    )
                    processor = st.session_state.get(
                        "_rehab_processor"
                    )
                    reps = (
                        processor.get_stats()["repetitions"]
                        if processor else 0
                    )
                    save_session(exercise, reps, seconds)
                    st.session_state.saved = True
                    st.session_state.started = None
                    st.success(
                        f"Saved! {reps} reps in "
                        f"{seconds // 60}m {seconds % 60}s."
                    )
                else:
                    st.info("This session has already been saved.")

    with left:
        st.markdown(
            '<div class="card"><h3>◉ Live camera feed</h3>'
            '<p class="muted">Allow camera access when prompted.</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        ctx = webrtc_streamer(
            key="rehabmotion-camera",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=lambda: RehabHandTracker(MODEL),
            rtc_configuration=RTCConfiguration({
                "iceServers": [
                    {"urls": ["stun:stun.l.google.com:19302"]}
                ]
            }),
            media_stream_constraints={
                "video": True, "audio": False
            },
            async_processing=True,
        )

        if ctx.video_processor:
            st.session_state["_rehab_processor"] = ctx.video_processor
            stats = ctx.video_processor.get_stats()
        else:
            stats = {
                "hand_detected": False,
                "repetitions": 0,
                "movement": "Waiting",
                "status": "Start the camera",
            }

        st.write("")
        a, b, c = st.columns(3)
        a.metric(
            "Hand status",
            "Detected" if stats["hand_detected"] else "Not detected",
        )
        b.metric("Repetitions", stats["repetitions"])
        c.metric("Movement state", stats["movement"])

        st.caption(stats["status"])
        if not stats["hand_detected"]:
            st.info(
                "Try one hand, palm toward the camera, "
                "30–60 cm away, with all fingertips visible."
            )
        if st.session_state.started:
            st.success("Session in progress")

    st.warning(
        "The repetition counter uses a basic hand-opening heuristic. "
        "It is not validated for clinical use."
    )

elif page == "Exercise Library":
    st.markdown(
        '<div class="eyebrow">EXPLORE THE MOVEMENTS</div>',
        unsafe_allow_html=True,
    )
    st.title("Exercise Library")
    cols = st.columns(2)
    for i, (name, info) in enumerate(EXERCISES.items()):
        with cols[i % 2]:
            st.markdown(
                f"""<div class="card">
                <div class="eyebrow">{info['category']}</div>
                <h3>{info['icon']} {name}</h3>
                <p class="muted">{info['description']}</p>
                <p><b>Suggested target:</b> {info['target']} reps</p>
                <p>{get_exercise_instructions(name)}</p>
                </div>""",
                unsafe_allow_html=True,
            )
            if st.button(f"Practice {name}", key=f"ex_{i}",
                         use_container_width=True):
                st.session_state.exercise = name
                st.session_state.page = "AI Exercise Studio"
                st.rerun()

elif page == "Custom Gestures":
    st.markdown(
        '<div class="eyebrow">MAKE IT YOUR OWN</div>',
        unsafe_allow_html=True,
    )
    st.title("✋ Custom Gestures")
    st.write(
        "Create your own gesture entries and build a personal "
        "library for future camera-based recognition."
    )

    with st.form("add_custom_gesture", clear_on_submit=True):
        st.subheader("＋ Add a new gesture")

        gesture_name = st.text_input(
            "Gesture name",
            placeholder="e.g. Two-finger tap",
        )
        gesture_description = st.text_area(
            "Instructions",
            placeholder="Describe how the hand should move...",
        )
        target_reps = st.number_input(
            "Target repetitions",
            min_value=1,
            max_value=100,
            value=10,
            step=1,
        )

        submitted = st.form_submit_button("Save Gesture")

        if submitted:
            if not gesture_name.strip():
                st.error("Please enter a gesture name.")
            elif not gesture_description.strip():
                st.error("Please enter instructions.")
            else:
                if CUSTOM_GESTURES.exists():
                    try:
                        custom_df = pd.read_csv(CUSTOM_GESTURES)
                    except Exception:
                        custom_df = pd.DataFrame()
                else:
                    custom_df = pd.DataFrame()

                if (
                    not custom_df.empty
                    and "name" in custom_df.columns
                    and custom_df["name"].astype(str).str.casefold().eq(
                        gesture_name.strip().casefold()
                    ).any()
                ):
                    st.warning("A gesture with that name already exists.")
                else:
                    new_gesture = pd.DataFrame([{
                        "name": gesture_name.strip(),
                        "description": gesture_description.strip(),
                        "target_reps": int(target_reps),
                        "created_at": datetime.now().strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                    }])

                    pd.concat(
                        [custom_df, new_gesture],
                        ignore_index=True,
                    ).to_csv(CUSTOM_GESTURES, index=False)

                    st.success(
                        f"Saved '{gesture_name.strip()}' to your library!"
                    )

    st.divider()
    st.subheader("Your saved gestures")

    if CUSTOM_GESTURES.exists():
        try:
            saved_gestures = pd.read_csv(CUSTOM_GESTURES)
        except Exception:
            saved_gestures = pd.DataFrame()
    else:
        saved_gestures = pd.DataFrame()

    if saved_gestures.empty:
        st.info(
            "Your library is empty. Add your first custom gesture above."
        )
    else:
        for _, gesture in saved_gestures.iterrows():
            with st.container(border=True):
                st.markdown(f"### ✋ {gesture['name']}")
                st.write(gesture["description"])
                st.caption(
                    f"Target: {gesture['target_reps']} repetitions"
                    f" · Added: {gesture.get('created_at', 'Unknown')}"
                )

elif page == "My Progress":
    st.markdown(
        '<div class="eyebrow">YOUR PRACTICE LOG</div>',
        unsafe_allow_html=True,
    )
    st.title("My Progress")
    df = read_history()
    if df.empty:
        st.info(
            "No sessions saved yet. Complete a session in "
            "AI Exercise Studio and select End & Save."
        )
    else:
        df["repetitions"] = pd.to_numeric(
            df["repetitions"], errors="coerce"
        ).fillna(0)
        df["seconds"] = pd.to_numeric(
            df["seconds"], errors="coerce"
        ).fillna(0)
        a, b, c = st.columns(3)
        a.metric("Sessions", len(df))
        b.metric("Total repetitions", int(df["repetitions"].sum()))
        c.metric("Practice minutes", int(df["seconds"].sum() // 60))
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        st.subheader("Repetitions per session")
        st.line_chart(df.dropna(subset=["date"]).set_index("date")["repetitions"])
        st.subheader("Session history")
        st.dataframe(df.sort_values("date", ascending=False),
                     use_container_width=True, hide_index=True)
        st.download_button(
            "Export history CSV",
            df.to_csv(index=False).encode("utf-8"),
            "rehabmotion_sessions.csv",
            "text/csv",
        )

elif page == "About":
    st.title("About RehabMotion")
    st.markdown("""
    <div class="card">
    <h3>Movement, made more visible.</h3>
    <p class="muted">RehabMotion is a student prototype exploring
    webcam-based hand landmark tracking and guided hand-movement
    practice.</p>
    <hr>
    <h3>What it includes</h3>
    <ul>
      <li>MediaPipe hand landmark tracking</li>
      <li>Six predefined exercise guides</li>
      <li>Session timer and basic repetition count</li>
      <li>Local CSV history and progress charts</li>
    </ul>
    <p class="muted">This is not a medical device. Repetition
    counting is approximate and is not clinically validated.
    Follow your clinician's advice and stop if movement causes pain.</p>
    </div>
    """, unsafe_allow_html=True)
