#!/usr/bin/env python3
import os
import sys
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

# Page Setup
st.set_page_config(
    page_title="MeetPrep AI Agent",
    page_icon="🧠",
    layout="centered"
)

# Custom Styling (Simple and Clean)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.title-container {
    text-align: center;
    margin-bottom: 25px;
    padding-bottom: 15px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.status-badge {
    font-size: 0.8rem;
    color: #a0aec0;
    margin-top: 5px;
}
</style>
""", unsafe_allow_html=True)

# ─── INITIALIZE STATE ─────────────────────────────────────────────────────────
if "initialized" not in st.session_state:
    st.session_state.use_cloud = check_hindsight_connection(HINDSIGHT_URL)
    if st.session_state.use_cloud:
        st.session_state.hindsight_client = get_hindsight()
    else:
        st.session_state.hindsight_client = None
        
    st.session_state.groq_client = None
    if GROQ_API_KEY:
        try:
            st.session_state.groq_client = get_groq()
        except Exception:
            pass

    # Conversation history
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I'm your **MeetPrep AI Agent** 🧠\n\nWhat would you like to do?\n\n1. **Prepare for an upcoming meeting**\n2. **Save notes from a completed meeting**"
        }
    ]
    st.session_state.step = "menu"
    st.session_state.save_participant = ""
    st.session_state.initialized = True

# Mode indicator label
mode_label = "CLOUD MODE" if st.session_state.use_cloud else "LOCAL MODE"

# Render header
st.markdown(f"""
<div class="title-container">
    <h2 style="margin:0;">🧠 MeetPrep AI Agent</h2>
    <div class="status-badge">Memory Mode: <b>{mode_label}</b></div>
</div>
""", unsafe_allow_html=True)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔌 Connection Status")
    if st.session_state.use_cloud:
        st.success("Hindsight Cloud connected!")
    else:
        st.warning("Running in LOCAL MODE (local_memory.json)")
        
    if GROQ_API_KEY:
        st.success("Groq LLM is ready.")
    else:
        st.error("GROQ_API_KEY is missing!")
        
    st.markdown("---")
    st.markdown("### ⚡ Demo Options")
    if st.button("Seed Mock Memories (Alex, Sarah, John)", use_container_width=True):
        seed_demo_data()
        st.session_state.messages.append({
            "role": "assistant",
            "content": "✓ **Demo data seeded!** I've loaded mock records for **Alex**, **Sarah**, and **John** into local memory."
        })
        st.rerun()
        
    if st.button("Reset Conversation", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I'm your **MeetPrep AI Agent** 🧠\n\nWhat would you like to do?\n\n1. **Prepare for an upcoming meeting**\n2. **Save notes from a completed meeting**"
            }
        ]
        st.session_state.step = "menu"
        st.session_state.save_participant = ""
        st.rerun()

# ─── CONVERSATION WINDOW ──────────────────────────────────────────────────────
# Display past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Show option helper buttons only if we are in the main menu step
if st.session_state.step == "menu":
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 1. Prepare for a meeting", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "1. Prepare for a meeting"})
            st.session_state.step = "prep_name"
            st.session_state.messages.append({"role": "assistant", "content": "Who is the meeting with? (Enter name):"})
            st.rerun()
    with col2:
        if st.button("📝 2. Save meeting notes", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "2. Save meeting notes"})
            st.session_state.step = "save_name"
            st.session_state.messages.append({"role": "assistant", "content": "Who was the meeting with? (Enter name):"})
            st.rerun()

# Accept text input from user
user_input = st.chat_input("Type here...")

# Process inputs
if user_input:
    # Append user's message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

# Processing step execution after rerun
if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
    last_text = st.session_state.messages[-1]["content"].strip()
    
    if st.session_state.step == "menu":
        # Handle textual choice (1, 2, prep, save)
        if last_text == "1" or "prep" in last_text.lower():
            st.session_state.step = "prep_name"
            reply = "Who is the meeting with? (Enter name):"
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()
        elif last_text == "2" or "save" in last_text.lower():
            st.session_state.step = "save_name"
            reply = "Who was the meeting with? (Enter name):"
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()
        else:
            reply = "Please enter **1** (to prepare) or **2** (to save notes), or use the buttons below."
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()
            
    elif st.session_state.step == "prep_name":
        # We got the name, now fetch memory and run LLM brief synthesis
        participant = last_text
        
        with st.chat_message("assistant"):
            st.markdown(f"🔍 *Retrieving memory for **{participant}**...*")
            
            with st.spinner("Synthesizing brief with Groq..."):
                # Retrieve memory
                if st.session_state.use_cloud:
                    memory = cloud_recall(st.session_state.hindsight_client, participant)
                else:
                    memory = local_recall(participant)
                
                # Verify Groq Client
                if not st.session_state.groq_client:
                    brief = "🔴 **Error:** Groq API client is not initialized. Please set `GROQ_API_KEY` in your `.env` file."
                else:
                    brief = generate_meeting_prep_brief(st.session_state.groq_client, participant.capitalize(), memory)
                    
                if brief is None:
                    brief = "🔴 **Error:** Failed to generate brief. Please verify your Groq API Key."
            
            # Print brief
            st.markdown(brief)
            st.session_state.messages.append({"role": "assistant", "content": brief})
            
            # Print prompt menu and reset to idle
            menu_prompt = "What would you like to do next?\n\n1. **Prepare for an upcoming meeting**\n2. **Save notes from a completed meeting**"
            st.markdown(menu_prompt)
            st.session_state.messages.append({"role": "assistant", "content": menu_prompt})
            
            st.session_state.step = "menu"
            st.rerun()
            
    elif st.session_state.step == "save_name":
        # We got the name, now ask for notes
        st.session_state.save_participant = last_text
        st.session_state.step = "save_notes"
        
        reply = f"Tell me what happened in your meeting with **{last_text.capitalize()}**.\n\n*Include: topics discussed, commitments made, follow-ups, and important details.*"
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()
        
    elif st.session_state.step == "save_notes":
        # We got the notes, now structure with AI and save
        notes = last_text
        participant = st.session_state.save_participant
        
        with st.chat_message("assistant"):
            st.markdown(f"💾 *Structuring and saving notes for **{participant.capitalize()}**...*")
            
            with st.spinner("Processing memory..."):
                if not st.session_state.groq_client:
                    structured = notes
                else:
                    structured = structure_notes_with_ai(st.session_state.groq_client, participant.capitalize(), notes)
                
                # Save notes
                saved = False
                if st.session_state.use_cloud:
                    saved = cloud_retain(st.session_state.hindsight_client, participant.capitalize(), structured)
                    if not saved:
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
                reply = f"✓ **{save_msg}**\n\nPerfect! I've saved the meeting with **{participant.capitalize()}** to memory. Next time you prepare for a meeting with them, I'll remember everything you just told me. 🧠"
            else:
                reply = "🔴 **Error:** Could not save notes. Please check your storage configuration."
                
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            
            # Print prompt menu and reset to idle
            menu_prompt = "What would you like to do next?\n\n1. **Prepare for an upcoming meeting**\n2. **Save notes from a completed meeting**"
            st.markdown(menu_prompt)
            st.session_state.messages.append({"role": "assistant", "content": menu_prompt})
            
            st.session_state.save_participant = ""
            st.session_state.step = "menu"
            st.rerun()
