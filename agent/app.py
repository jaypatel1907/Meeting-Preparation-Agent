#!/usr/bin/env python3
import os
import sys
import json
import re
import io
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

# Override terminal print helper functions dynamically to prevent encoding errors on Windows
import agent
agent.success = lambda msg: None
agent.warn = lambda msg: None
agent.error = lambda msg: None
agent.info = lambda msg: None
agent.section = lambda title: None
agent.agent_says = lambda msg: None
agent.banner = lambda mode_label="": None

# ─── CRM DATABASE UTILITIES ───────────────────────────────────────────────────
CRM_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "participant_crm_profiles.json")

def load_crm_profiles():
    if os.path.exists(CRM_FILE):
        try:
            with open(CRM_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_crm_profiles(profiles):
    try:
        with open(CRM_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def update_crm_profiles_with_ai(groq_client, raw_transcript_or_notes):
    """Analyzes transcript, extracts/updates CRM profiles for participants."""
    if not groq_client:
        return
    
    prompt = f"""You are an AI Meeting Intelligence System.
Your task is to analyze the following meeting transcript/notes and extract information to build participant intelligence profiles.

Transcript/Notes:
{raw_transcript_or_notes}

For each participant identified in the text, extract:
1. Identity tracking (Name)
2. Contribution tracking (Summary of what they said, decisions made, focus areas)
3. Activity Level (0-100 score, status: active/moderate/low)
4. Task Responsibility Tracking (Tasks assigned, deadline)
5. Delay / Risk Detection (Bottlenecks, delay risks)
6. Behavioral insights (Leadership details, passivity, reliability)

Return the output strictly as a JSON object in this format (do not return any other text, explanations, or code blocks, just raw JSON):
{{
  "participants": [
    {{
      "name": "Alex",
      "summary": "Summarized points Alex focused on, including code reviews.",
      "activity_score": 85,
      "tasks": ["Finish code review for PR #42 by May 25"],
      "status": "active",
      "risk_flags": ["Missed deadline for PR review"],
      "behavior_insight": "Exhibits leadership by driving PR discussions but shows slight reliability risks."
    }}
  ]
}}

If no participants are found, return an empty list of participants. If data is missing for a participant, mark it as 'unknown' or leave list empty. Do not make assumptions beyond the text.
"""
    
    try:
        response = groq_client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1500
        )
        result_text = response.choices[0].message.content.strip()
        
        # Clean JSON markdown blocks if present
        if result_text.startswith("```json"):
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif result_text.startswith("```"):
            result_text = result_text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(result_text)
        extracted_participants = data.get("participants", [])
        
        # Load existing profiles
        profiles = load_crm_profiles()
        
        # Merge each extracted participant profile
        for ep in extracted_participants:
            name = ep.get("name", "").strip().lower()
            if not name:
                continue
                
            if name in profiles:
                # Merge existing profile with new details using Groq
                existing = profiles[name]
                merge_prompt = f"""You are an AI Meeting Intelligence System.
Your task is to merge the existing participant CRM profile with new meeting insights to produce an updated profile.

Existing Profile:
{json.dumps(existing)}

New Meeting Insights:
{json.dumps(ep)}

Merge the information. Keep history, track progress of tasks, update scores, and add new behavioral insights.
Return the updated profile strictly as a JSON object in this format (no explanations, just raw JSON):
{{
  "name": "{ep.get('name')}",
  "summary": "(Consolidated summary of contribution and recurring topics)",
  "activity_score": (Updated activity score 0-100),
  "tasks": [(Consolidated list of tasks with updated status/deadlines)],
  "status": "(active/moderate/low)",
  "risk_flags": [(Updated delay risks or bottlenecks)],
  "behavior_insight": "(Updated behavioral insight)"
}}
"""
                merge_response = groq_client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": merge_prompt}],
                    temperature=0.1,
                    max_tokens=1000
                )
                merge_text = merge_response.choices[0].message.content.strip()
                
                if merge_text.startswith("```json"):
                    merge_text = merge_text.split("```json")[1].split("```")[0].strip()
                elif merge_text.startswith("```"):
                    merge_text = merge_text.split("```")[1].split("```")[0].strip()
                    
                updated_ep = json.loads(merge_text)
                profiles[name] = updated_ep
            else:
                profiles[name] = ep
                
        # Save back to database
        save_crm_profiles(profiles)
        
    except Exception:
        pass



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
    st.session_state.processed_file = ""
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

# ─── PARTICIPANT CRM DISPLAY ──────────────────────────────────────────────────
if 'selected_crm' in locals() and selected_crm and selected_crm != "-- Select --":
    prof = crm_profiles[selected_crm.lower()]
    
    st.markdown(f"<h3 style='margin-top:10px;'>👤 CRM Intelligence: <b>{prof.get('name')}</b></h3>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Activity Score", value=f"{prof.get('activity_score', 'unknown')}/100")
    with col2:
        status_val = prof.get('status', 'unknown').upper()
        st.metric(label="Participation Status", value=status_val)
        
    st.markdown("#### 🧠 Behavioral Insight")
    st.info(prof.get('behavior_insight', 'No insights generated.'))
    
    st.markdown("#### 📝 Contribution Summary")
    st.write(prof.get('summary', 'No summary available.'))
    
    st.markdown("#### ⏱️ Tasks & Responsibilities")
    tasks = prof.get('tasks', [])
    if not tasks:
        st.write("- *No tasks currently assigned.*")
    else:
        for t in tasks:
            st.markdown(f"- [ ] {t}")
            
    st.markdown("#### 🚨 Delay & Risk Flags")
    risks = prof.get('risk_flags', [])
    if not risks:
        st.write("- *No risks or bottlenecks detected.*")
    else:
        for r in risks:
            st.markdown(f"- 🔴 {r}")
            
    st.markdown("---")

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
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
        
    st.markdown("---")
    st.markdown("### 📁 Document Memory")
    uploaded_file = st.file_uploader("Upload meeting document (PDF, TXT):", type=["pdf", "txt"])
    
    st.markdown("---")
    st.markdown("### 👥 Participant CRM Profiles")
    crm_profiles = load_crm_profiles()
    if not crm_profiles:
        st.info("No CRM profiles tracked yet. Save notes or upload documents to build profiles.")
        selected_crm = None
    else:
        crm_names = sorted(list(crm_profiles.keys()))
        selected_crm = st.selectbox(
            "Select participant profile to view CRM intelligence:",
            options=["-- Select --"] + [n.capitalize() for n in crm_names]
        )



# ─── PROCESS UPLOADED DOCUMENT ────────────────────────────────────────────────
if uploaded_file is not None and st.session_state.get("processed_file") != uploaded_file.name:
    st.session_state.processed_file = uploaded_file.name
    
    with st.spinner("Processing and analyzing meeting document..."):
        file_text = ""
        # 1. Extract text from uploaded document
        if uploaded_file.name.endswith(".txt"):
            file_text = uploaded_file.read().decode("utf-8", errors="replace")
        elif uploaded_file.name.endswith(".pdf"):
            try:
                import io
                from pypdf import PdfReader
                pdf_reader = PdfReader(io.BytesIO(uploaded_file.read()))
                pages_text = []
                for page in pdf_reader.pages:
                    t = page.extract_text()
                    if t:
                        pages_text.append(t)
                file_text = "\n".join(pages_text)
            except Exception as e:
                st.error(f"Failed to parse PDF document: {e}")
                
        if not file_text.strip():
            st.error("Document is empty or text could not be extracted.")
        else:
            # 2. Extract key info using Groq
            if not st.session_state.groq_client:
                st.error("Groq API is not ready. Cannot process document.")
            else:
                prompt = f"""You are an AI Meeting Assistant with document memory capability.
Your job is to process meeting-related files such as PDFs, Word documents, text files, slides, and notes.

Extract key details from this document:
Document Name: {uploaded_file.name}
Document Content:
{file_text}

You MUST output your response exactly in this structured format:

### 📋 Summary
(A brief, professional 2-3 sentence summary of the document's main topics and overall context.)

### 📌 Key Points
- (Important point 1)
- (Important point 2)
- (Decisions mentioned)

### ⚠️ Action Items
- (Action item description, assigned person, and deadline if mentioned)

[PARTICIPANTS]: (List the names of people/participants mentioned in this document, separated by commas. Example: Alex, Sarah. If none, write "None".)
"""
                try:
                    response = st.session_state.groq_client.chat.completions.create(
                        model=MODEL,
                        messages=[
                            {"role": "system", "content": "You are a professional AI meeting preparation assistant. Extract key meeting insights from documents exactly in the requested format."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.1,
                        max_tokens=1000
                    )
                    analysis = response.choices[0].message.content.strip()
                    
                    # 3. Parse identified participants
                    participants = []
                    import re
                    part_match = re.search(r"\[PARTICIPANTS\]:\s*(.*)", analysis, re.IGNORECASE)
                    if part_match:
                        raw_parts = part_match.group(1).strip()
                        if raw_parts and raw_parts.lower() != "none":
                            participants = [p.strip().lower() for p in raw_parts.split(",") if p.strip()]
                    
                    # Strip the participants tagging line from final display
                    display_analysis = re.sub(r"\[PARTICIPANTS\]:.*", "", analysis, flags=re.IGNORECASE).strip()
                    
                    # Update CRM database
                    update_crm_profiles_with_ai(st.session_state.groq_client, file_text)
                    
                    # 4. Link context and store in memory
                    related_meetings = []
                    stored_confirmations = []
                    
                    if participants:
                        for p in participants:
                            # Retrieve past history
                            if st.session_state.use_cloud:
                                history = cloud_recall(st.session_state.hindsight_client, p)
                            else:
                                history = local_recall(p)
                                
                            # Track related meetings
                            if history:
                                count = len(history.split("\n\n---\n\n"))
                                related_meetings.append(f"Linked with {p.capitalize()}'s profile ({count} past meetings found).")
                            else:
                                related_meetings.append(f"Created a new profile history for {p.capitalize()}.")
                                
                            # Format memory entry
                            memory_content = f"Document: {uploaded_file.name}\nKey insights extracted from document:\n{display_analysis}"
                            
                            # Store in memory
                            if st.session_state.use_cloud:
                                saved = cloud_retain(st.session_state.hindsight_client, p.capitalize(), memory_content)
                                if not saved:
                                    local_retain(p, memory_content)
                                    stored_confirmations.append(f"Saved locally for {p.capitalize()} (Cloud save failed)")
                                else:
                                    stored_confirmations.append(f"Saved to Cloud Memory for {p.capitalize()}")
                            else:
                                local_retain(p, memory_content)
                                stored_confirmations.append(f"Saved to Local Memory for {p.capitalize()}")
                    else:
                        related_meetings.append("No specific participant names identified in the document.")
                        stored_confirmations.append("Document processed, but not linked to any specific participant.")
                        
                    # 5. Construct final message response in requested format
                    related_meetings_str = "\n".join([f"- {m}" for m in related_meetings])
                    stored_confirmations_str = "\n".join([f"- {c}" for c in stored_confirmations])
                    
                    final_reply = f"""{display_analysis}

### ⏱️ Related Meetings
{related_meetings_str}

### 💾 Stored Memory Confirmation
{stored_confirmations_str}"""

                    # Append to conversation messages
                    st.session_state.messages.append({"role": "user", "content": f"Uploaded document: `{uploaded_file.name}`"})
                    st.session_state.messages.append({"role": "assistant", "content": final_reply})
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error analyzing document with Groq: {e}")

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
                update_crm_profiles_with_ai(st.session_state.groq_client, notes)
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
