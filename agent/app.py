#!/usr/bin/env python3
import os
import sys
import re
import datetime
import streamlit as st

# Ensure agent directory is in path so it can import agent.py correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent import (
    load_dotenv,
    GROQ_API_KEY,
    HINDSIGHT_URL,
    HINDSIGHT_API_KEY,
    MEMORY_BANK_ID,
    MODEL,
    LOCAL_MEMORY_FILE,
    check_hindsight_connection,
    load_local_memory,
    save_local_memory,
    local_retain,
    local_recall,
    get_hindsight,
    cloud_retain,
    cloud_recall,
    get_groq,
    structure_notes_with_ai,
    generate_meeting_prep_brief,
    seed_demo_data
)

# Load environment variables
load_dotenv()

# Set Page Configuration
st.set_page_config(
    page_title="MeetPrep AI - Smart Agent Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

h1, h2, h3, .sidebar-title {
    font-family: 'Outfit', sans-serif;
}

/* Sidebar Custom Look */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #13141c 0%, #0d0e12 100%);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}

/* Status badge styling */
.status-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 15px;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}

.status-pill.connected {
    background-color: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.status-pill.fallback {
    background-color: rgba(245, 158, 11, 0.15);
    color: #f59e0b;
    border: 1px solid rgba(245, 158, 11, 0.3);
}

/* Pulsing dot indicator */
.pulse-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 6px;
    display: inline-block;
}

.pulse-dot.connected {
    background-color: #10b981;
    box-shadow: 0 0 8px #10b981;
    animation: pulse 2s infinite;
}

.pulse-dot.fallback {
    background-color: #f59e0b;
    box-shadow: 0 0 8px #f59e0b;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { transform: scale(0.9); opacity: 0.6; }
    50% { transform: scale(1.1); opacity: 1; }
    100% { transform: scale(0.9); opacity: 0.6; }
}

/* Vertical Timeline Styling */
.timeline-container {
    border-left: 2px solid rgba(118, 75, 162, 0.4);
    padding-left: 20px;
    margin-left: 10px;
    margin-top: 20px;
}

.timeline-item {
    position: relative;
    margin-bottom: 25px;
}

.timeline-dot {
    position: absolute;
    left: -27px;
    top: 5px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background-color: #764ba2;
    border: 2px solid #0d0e12;
    box-shadow: 0 0 8px #764ba2;
}

.timeline-date {
    color: #667eea;
    font-weight: 600;
    font-size: 0.9rem;
    margin-bottom: 5px;
}

.timeline-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 12px 15px;
    color: #e2e8f0;
}

/* Custom Header Gradients */
.main-title {
    background: linear-gradient(135deg, #a5b4fc 0%, #c084fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.2rem;
    font-weight: 700;
    margin-bottom: 5px;
}

/* Styled Alert Messages */
.alert-box {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.2);
    border-radius: 8px;
    padding: 10px 15px;
    color: #fca5a5;
    margin-bottom: 15px;
}

.onboarding-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ─── INITIALIZE SESSION STATE ──────────────────────────────────────────────────
if "initialized" not in st.session_state:
    # Check Hindsight Cloud connection
    with st.spinner("Checking database connectivity..."):
        is_connected = check_hindsight_connection(HINDSIGHT_URL)
        st.session_state.use_cloud = is_connected
        if is_connected:
            st.session_state.hindsight_client = get_hindsight()
        else:
            st.session_state.hindsight_client = None
    
    # Check/Setup Groq Client
    st.session_state.groq_client = None
    if GROQ_API_KEY:
        try:
            st.session_state.groq_client = get_groq()
        except Exception:
            pass

    # Chat & State parameters
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I'm your **MeetPrep AI Agent** 🧠\n\nI store every meeting we have, extract commitments, build participant profiles, and compile detailed briefs to make you ready for your next call.\n\n*How can I help you today?*"
        }
    ]
    st.session_state.step = "idle"
    st.session_state.current_participant = ""
    st.session_state.action_type = ""
    
    # Caches for profiles & commitments to optimize performance
    st.session_state.profile_cache = {}
    st.session_state.commitment_cache = {}
    
    st.session_state.initialized = True

# Helper to read participant list
def get_stored_participants_list():
    try:
        store = load_local_memory()
        return list(store.keys())
    except Exception:
        return []

# Helper to clear cached summaries
def clear_caches_for_participant(participant: str):
    key = participant.lower().strip()
    st.session_state.profile_cache.pop(key, None)
    st.session_state.commitment_cache.pop(key, None)

# Helper to seed data and clear cache
def trigger_seed_demo_data():
    seed_demo_data()
    # Reset caches for alex, sarah, john to trigger regeneration
    for name in ["alex", "sarah", "john"]:
        clear_caches_for_participant(name)
    st.session_state.messages.append({
        "role": "assistant",
        "content": "✅ **Demo memories seeded successfully!** I have loaded rich meeting history for **Alex**, **Sarah**, and **John**.\n\nYou can click their profiles in the sidebar or ask me: *\"Prepare for Alex\"* or *\"Save notes for Sarah\"* to test the agent!"
    })

# ─── PARSE NATURAL LANGUAGE INPUT ──────────────────────────────────────────────
def parse_natural_command(text: str):
    text = text.lower().strip()
    
    # Pattern for preparing/recalling
    prep_patterns = [
        r"^prepare\s+for\s+([a-zA-Z0-9_\-\s]+)$",
        r"^prep\s+for\s+([a-zA-Z0-9_\-\s]+)$",
        r"^brief\s+for\s+([a-zA-Z0-9_\-\s]+)$",
        r"^recall\s+([a-zA-Z0-9_\-\s]+)$",
        r"^prep\s+([a-zA-Z0-9_\-\s]+)$",
        r"^prepare\s+([a-zA-Z0-9_\-\s]+)$",
    ]
    for p in prep_patterns:
        m = re.match(p, text)
        if m:
            return "prepare", m.group(1).strip()
            
    # Pattern for saving notes
    save_patterns = [
        r"^save\s+notes\s+for\s+([a-zA-Z0-9_\-\s]+)$",
        r"^save\s+for\s+([a-zA-Z0-9_\-\s]+)$",
        r"^store\s+notes\s+for\s+([a-zA-Z0-9_\-\s]+)$",
        r"^add\s+notes\s+for\s+([a-zA-Z0-9_\-\s]+)$",
        r"^save\s+notes\s+([a-zA-Z0-9_\-\s]+)$",
    ]
    for p in save_patterns:
        m = re.match(p, text)
        if m:
            return "save", m.group(1).strip()
            
    return None, None

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<h2 style='margin-bottom:0;'>🧠 MeetPrep AI</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#718096; font-size:0.85rem; margin-top:2px;'>Persistent Memory Meeting Assistant</p>", unsafe_allow_html=True)
    
    # ─── CONNECTION STATUS ────────────────────────────────────────────────────
    st.markdown("### 🔌 Connection Status")
    
    if st.session_state.use_cloud:
        st.markdown("""
        <div class="status-card">
            <span class="status-pill connected">
                <span class="pulse-dot connected"></span>Cloud Mode (Active)
            </span>
            <div style="font-size:0.75rem; color:#a0aec0; margin-top:8px;">Connected to Hindsight Cloud DB</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="status-card">
            <span class="status-pill fallback">
                <span class="pulse-dot fallback"></span>Local Memory Fallback
            </span>
            <div style="font-size:0.75rem; color:#a0aec0; margin-top:8px;">Hindsight Cloud offline. Storing notes in <code>local_memory.json</code></div>
        </div>
        """, unsafe_allow_html=True)
        
    # Groq API check
    if GROQ_API_KEY:
        st.markdown("<div style='font-size:0.8rem; color:#48bb78; font-weight:600;'>✓ Groq API: Configured</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='alert-box' style='padding:5px 10px; font-size:0.75rem;'>✗ Groq API Key is not set in .env! LLM operations will fail.</div>", unsafe_allow_html=True)
        
    st.markdown("---")
    
    # ─── SELECT ACTIVE PROFILE ────────────────────────────────────────────────
    st.markdown("### 👥 Select Participant Profile")
    participants = get_stored_participants_list()
    
    # Sort for predictability
    participants = sorted(participants)
    
    if not participants:
        st.info("No participants stored yet. Seed demo data to start!")
        active_participant = None
    else:
        # Check if active participant exists, default to first or 'alex' if available
        default_idx = 0
        if "active_participant" in st.session_state and st.session_state.active_participant in participants:
            default_idx = participants.index(st.session_state.active_participant)
        elif "alex" in participants:
            default_idx = participants.index("alex")
            
        active_participant = st.selectbox(
            "Select participant to view their memory profile & timeline:",
            options=participants,
            index=default_idx,
            format_func=lambda x: x.capitalize()
        )
        st.session_state.active_participant = active_participant

    st.markdown("---")
    
    # ─── QUICK DEMO & CONTROLS ────────────────────────────────────────────────
    st.markdown("### ⚡ Demo Controls")
    
    if st.button("Seeding Demo Data (Alex, Sarah, John)", use_container_width=True, type="secondary"):
        trigger_seed_demo_data()
        st.rerun()
        
    if st.button("Clear Conversation History", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "Conversation history cleared! Let's start fresh. How can I assist you?"}
        ]
        st.session_state.step = "idle"
        st.session_state.current_participant = ""
        st.session_state.action_type = ""
        st.rerun()

# ─── MAIN LAYOUT TABS ─────────────────────────────────────────────────────────
st.markdown("<div class='main-title'>MeetPrep AI Agent Dashboard</div>", unsafe_allow_html=True)
st.markdown("<p style='color:#a0aec0; margin-top:-5px; margin-bottom:20px;'>Hindsight Memory Core + Groq Llama 3.3 Synthesis Engine</p>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "💬 Chat Assistant", 
    "📊 Participant Memory Profile", 
    "⏱️ Relationship Timeline", 
    "✅ Action & Commitment Tracker"
])

# ──────────────────────────────────────────────────────────────────────────────
# TAB 1: CHAT ASSISTANT
# ──────────────────────────────────────────────────────────────────────────────
with tab1:
    # Onboarding helper if chat is default
    if len(st.session_state.messages) <= 1:
        st.markdown("""
        <div class="onboarding-card">
            <h4 style="margin-top:0; color:#c084fc;">💡 Quick Demo Actions</h4>
            <p style="font-size:0.9rem; color:#a0aec0;">Click one of the quick actions below, or type your request directly into the chatbox at the bottom of the page!</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📋 Prepare brief for Alex", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "Prepare brief for Alex"})
                st.session_state.step = "run_brief"
                st.session_state.current_participant = "alex"
                st.rerun()
        with col2:
            if st.button("📋 Prepare brief for Sarah", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "Prepare brief for Sarah"})
                st.session_state.step = "run_brief"
                st.session_state.current_participant = "sarah"
                st.rerun()
        with col3:
            if st.button("📝 Save notes for a participant", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "Save meeting notes"})
                st.session_state.step = "waiting_for_name"
                st.session_state.action_type = "save"
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Who did you have the meeting with?"
                })
                st.rerun()

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Process pending brief execution (triggered by quick action buttons or chat parsing)
    if st.session_state.step == "run_brief":
        participant = st.session_state.current_participant
        st.session_state.active_participant = participant  # Align active view
        
        with st.chat_message("assistant"):
            st.markdown(f"🔍 *Retrieving historical memory fragments for **{participant.capitalize()}** from memory...*")
            
            with st.spinner("Synthesizing brief with Groq LLM..."):
                # Retrieve memory
                if st.session_state.use_cloud:
                    memory = cloud_recall(st.session_state.hindsight_client, participant)
                else:
                    memory = local_recall(participant)
                
                # Generate prep brief
                if not st.session_state.groq_client:
                    brief = "🔴 **Error:** Groq API client is not initialized. Please set `GROQ_API_KEY` in your `.env` file."
                else:
                    brief = generate_meeting_prep_brief(st.session_state.groq_client, participant.capitalize(), memory)
                    
                if brief is None:
                    brief = "🔴 **Error:** Failed to generate brief. Please verify your Groq API Key or network connectivity."
                
            st.markdown(brief)
            st.session_state.messages.append({"role": "assistant", "content": brief})
            st.session_state.step = "idle"
            st.session_state.current_participant = ""
            st.rerun()

    # Chat input box
    user_input = st.chat_input("Ask me to prepare for a meeting, save notes, or just chat...")

    if user_input:
        # Append user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.rerun()

# This block executes after user_input causes a rerun, ensuring the UI rendering completes first
if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
    last_user_message = st.session_state.messages[-1]["content"]
    
    # Process according to current step state
    if st.session_state.step == "idle":
        action, name = parse_natural_command(last_user_message)
        
        if action == "prepare":
            st.session_state.step = "run_brief"
            st.session_state.current_participant = name
            st.rerun()
            
        elif action == "save":
            st.session_state.current_participant = name
            st.session_state.step = "waiting_for_save_notes"
            response_text = f"Got it! Let's save notes for **{name.capitalize()}**. Tell me what happened in your meeting with them.\n\n*Include topics, decisions, commitments, and follow-ups. (Press Enter to submit)*"
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            st.rerun()
            
        elif "save" in last_user_message.lower() and "note" in last_user_message.lower():
            st.session_state.step = "waiting_for_name"
            st.session_state.action_type = "save"
            st.session_state.messages.append({"role": "assistant", "content": "Who did you have the meeting with?"})
            st.rerun()
            
        elif "prepare" in last_user_message.lower() or "brief" in last_user_message.lower() or "prep" in last_user_message.lower():
            st.session_state.step = "waiting_for_name"
            st.session_state.action_type = "prepare"
            st.session_state.messages.append({"role": "assistant", "content": "Who is the meeting with?"})
            st.rerun()
            
        else:
            # Conversational Fallback - call Groq directly to provide smart instructions
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    if not st.session_state.groq_client:
                        reply = "Hello! Please set your `GROQ_API_KEY` in the `.env` file to start chatting conversationally. You can also prepare briefs for Alex, Sarah, or John by clicking the quick actions!"
                    else:
                        system_prompt = "You are a professional AI meeting preparation assistant. Guide the user on how to prepare for meetings or save notes. You can instruct them to type things like 'Prepare for Alex' or 'Save notes for Sarah'."
                        try:
                            response = st.session_state.groq_client.chat.completions.create(
                                model=MODEL,
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": last_user_message}
                                ],
                                temperature=0.5,
                                max_tokens=300
                            )
                            reply = response.choices[0].message.content.strip()
                        except Exception as e:
                            reply = f"I am online, but encountered an issue contacting Groq: {e}. You can still run local commands like *'Prepare for Alex'*."
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()
            
    elif st.session_state.step == "waiting_for_name":
        name = last_user_message.strip()
        if not name:
            st.session_state.messages.append({"role": "assistant", "content": "Please enter a valid participant name."})
            st.rerun()
            
        if st.session_state.action_type == "prepare":
            st.session_state.step = "run_brief"
            st.session_state.current_participant = name
            st.rerun()
            
        elif st.session_state.action_type == "save":
            st.session_state.current_participant = name
            st.session_state.step = "waiting_for_save_notes"
            response_text = f"Got it! Let's save notes for **{name.capitalize()}**. Tell me what happened in your meeting with them.\n\n*Include topics, decisions, commitments, and follow-ups.*"
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            st.rerun()
            
    elif st.session_state.step == "waiting_for_save_notes":
        notes = last_user_message.strip()
        participant = st.session_state.current_participant
        
        with st.chat_message("assistant"):
            st.markdown(f"💾 *Structuring and saving notes for **{participant.capitalize()}**...*")
            
            with st.spinner("Structuring notes with AI..."):
                if not st.session_state.groq_client:
                    structured = notes
                else:
                    structured = structure_notes_with_ai(st.session_state.groq_client, participant.capitalize(), notes)
                
                # Save notes
                saved = False
                if st.session_state.use_cloud:
                    saved = cloud_retain(st.session_state.hindsight_client, participant.capitalize(), structured)
                    if not saved:
                        # Fallback to local
                        local_retain(participant.lower(), structured)
                        saved = True
                        save_msg = f"Cloud save failed. Notes saved locally for **{participant.capitalize()}**."
                    else:
                        save_msg = f"Notes successfully stored in Hindsight Cloud memory for **{participant.capitalize()}**!"
                else:
                    local_retain(participant.lower(), structured)
                    saved = True
                    save_msg = f"Notes successfully stored in local memory for **{participant.capitalize()}**!"
            
            if saved:
                reply = f"✓ **{save_msg}**\n\nI have successfully processed and saved the meeting details. I will remember this when you ask me to prepare for your next meeting with **{participant.capitalize()}**!"
                # Clear cached profile and timeline so they regenerate with new notes
                clear_caches_for_participant(participant)
            else:
                reply = "🔴 **Error:** Could not save notes. Please check your storage configuration."
                
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            
            # Reset state
            st.session_state.step = "idle"
            st.session_state.current_participant = ""
            st.session_state.active_participant = participant.lower() # Sync selectbox
            st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# TAB 2: PARTICIPANT MEMORY PROFILE
# ──────────────────────────────────────────────────────────────────────────────
with tab2:
    if not active_participant:
        st.warning("Please seed demo data or save a meeting note to initialize profiles.")
    else:
        st.markdown(f"## 👤 Memory Profile: {active_participant.capitalize()}")
        
        # Load memory entries
        store = load_local_memory()
        entries = store.get(active_participant.lower().strip(), [])
        
        if not entries:
            st.info(f"No meeting history found for {active_participant.capitalize()}.")
        else:
            # Combine all memory entries for prompt context
            combined_memory = "\n\n---\n\n".join([f"[{e['date']}]\n{e['text']}" for e in entries])
            
            # Check Cache
            cache_key = active_participant.lower().strip()
            
            if cache_key not in st.session_state.profile_cache:
                with st.spinner("Generating participant profile from historical notes..."):
                    if not st.session_state.groq_client:
                        profile_content = "Please configure `GROQ_API_KEY` to generate a dynamic profile."
                    else:
                        # Create prompt for profile extraction
                        prompt = f"""You are an expert community coordinator. Analyze the following meeting history for {active_participant.capitalize()} and build a comprehensive Profile.
                        
                        History:
                        {combined_memory}
                        
                        Extract:
                        - **Expertise & Skills**: (List key skills, knowledge areas, e.g. Rust, GCP)
                        - **Interests**: (Topics of interest, hobbies, personal details)
                        - **Recurring Topics**: (Topics that come up in multiple meetings)
                        - **Communication Preferences**: (How they communicate, style, preferences)
                        - **Key Contributions**: (Things they've accomplished)
                        - **Major Concerns**: (Issues raised, worries, blocks)
                        
                        Be professional, concise and structured. Use Markdown formatting.
                        """
                        try:
                            response = st.session_state.groq_client.chat.completions.create(
                                model=MODEL,
                                messages=[{"role": "user", "content": prompt}],
                                temperature=0.2,
                                max_tokens=800
                            )
                            profile_content = response.choices[0].message.content.strip()
                        except Exception as e:
                            profile_content = f"Error generating profile: {e}"
                
                # Cache the profile
                st.session_state.profile_cache[cache_key] = profile_content
            
            # Display Profile
            st.markdown(st.session_state.profile_cache[cache_key])

# ──────────────────────────────────────────────────────────────────────────────
# TAB 3: RELATIONSHIP TIMELINE
# ──────────────────────────────────────────────────────────────────────────────
with tab3:
    if not active_participant:
        st.warning("Please seed demo data or save a meeting note to view the timeline.")
    else:
        st.markdown(f"## ⏱️ Interaction Timeline: {active_participant.capitalize()}")
        
        store = load_local_memory()
        entries = store.get(active_participant.lower().strip(), [])
        
        if not entries:
            st.info(f"No timeline entries found for {active_participant.capitalize()}.")
        else:
            # Sort entries by date desc
            sorted_entries = sorted(entries, key=lambda x: x.get("date", ""), reverse=True)
            
            st.markdown("<div class='timeline-container'>", unsafe_allow_html=True)
            for entry in sorted_entries:
                date_str = entry.get("date", "Unknown Date")
                # Format date if possible
                try:
                    dt = datetime.date.fromisoformat(date_str)
                    formatted_date = dt.strftime("%d %B %Y")
                except ValueError:
                    formatted_date = date_str
                    
                text_content = entry.get("text", "")
                
                # HTML injection for timeline look
                st.markdown(f"""
                <div class="timeline-item">
                    <div class="timeline-dot"></div>
                    <div class="timeline-date">{formatted_date}</div>
                    <div class="timeline-card">
                        {text_content.replace(chr(10), '<br>')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# TAB 4: ACTION & COMMITMENT TRACKER
# ──────────────────────────────────────────────────────────────────────────────
with tab4:
    if not active_participant:
        st.warning("Please seed demo data or save a meeting note to view commitments.")
    else:
        st.markdown(f"## ✅ Commitments & Action Tracker: {active_participant.capitalize()}")
        
        store = load_local_memory()
        entries = store.get(active_participant.lower().strip(), [])
        
        if not entries:
            st.info(f"No meeting history found for {active_participant.capitalize()}.")
        else:
            combined_memory = "\n\n---\n\n".join([f"[{e['date']}]\n{e['text']}" for e in entries])
            cache_key = active_participant.lower().strip()
            
            if cache_key not in st.session_state.commitment_cache:
                with st.spinner("Extracting action items and commitments..."):
                    if not st.session_state.groq_client:
                        commitments_content = "Please configure `GROQ_API_KEY` to extract commitments."
                    else:
                        prompt = f"""You are a professional project manager. Read the meeting history for {active_participant.capitalize()} and extract all commitments, promises, and action items.
                        
                        History:
                        {combined_memory}
                        
                        Output a clean Markdown checklist. For each item, list:
                        1. The commitment description (what was promised and by whom)
                        2. Date of commitment
                        3. Status: **Pending**, **Completed**, or **Overdue** (assess status based on context or current date: {datetime.date.today().isoformat()})
                        
                        Be concise. If no commitments are found in memory, output 'No commitments or action items detected in history.'
                        """
                        try:
                            response = st.session_state.groq_client.chat.completions.create(
                                model=MODEL,
                                messages=[{"role": "user", "content": prompt}],
                                temperature=0.1,
                                max_tokens=600
                            )
                            commitments_content = response.choices[0].message.content.strip()
                        except Exception as e:
                            commitments_content = f"Error extracting commitments: {e}"
                
                st.session_state.commitment_cache[cache_key] = commitments_content
                
            st.markdown(st.session_state.commitment_cache[cache_key])
