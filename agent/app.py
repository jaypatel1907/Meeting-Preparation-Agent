#!/usr/bin/env python3
import os
import sys
import json
import re
import io
import datetime
import importlib
import streamlit as st

# Ensure agent directory is in path so it can import agent.py correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import agent
importlib.reload(agent)

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
    seed_demo_data,
    extract_timeline_events_with_ai,
    append_timeline_events,
    load_timeline_events
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

# ─── LOCAL STORAGE WITH TOPICS & SEARCH UTILITIES ──────────────────────────────
def local_retain_with_metadata(participant: str, date_str: str, topics_str: str, content: str):
    """Save meeting note containing topics and custom date to local store."""
    store = load_local_memory()
    key = participant.lower().strip()
    if key not in store:
        store[key] = []
    store[key].append({
        "date": date_str,
        "topics": topics_str,
        "text": content
    })
    save_local_memory(store)

def custom_local_recall(participant: str) -> str:
    """Overridden recall function showing topics in retrieved history."""
    store = load_local_memory()
    key = participant.lower().strip()
    entries = store.get(key, [])
    if not entries:
        return ""
    parts = []
    for e in entries:
        topics_section = f"Topics: {e.get('topics')}\n" if e.get("topics") else ""
        parts.append(f"[{e.get('date', 'unknown date')}]\n{topics_section}Notes: {e.get('text', '')}")
    return "\n\n---\n\n".join(parts)

# Override agent module recall with our metadata-aware recall
import agent
agent.local_recall = custom_local_recall

def search_local_meetings(query: str) -> list:
    """Search meeting history by participant name, date, or topics."""
    query = query.lower().strip()
    results = []
    if not query:
        return results
    
    store = load_local_memory()
    for participant, entries in store.items():
        participant_match = query in participant.lower()
        for e in entries:
            date_str = e.get("date", "")
            topics_str = e.get("topics", "")
            text_str = e.get("text", "")
            
            if (participant_match or 
                query in date_str.lower() or 
                query in topics_str.lower() or 
                query in text_str.lower()):
                results.append({
                    "participant": participant.capitalize(),
                    "date": date_str,
                    "topics": topics_str,
                    "text": text_str
                })
    return results


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

def render_timeline_view(participant: str):
    st.markdown("---")
    st.markdown(f"### ⏳ Timeline & Context: {participant.capitalize()}")
    
    events = load_timeline_events().get(participant.lower(), [])
    profiles = load_crm_profiles()
    prof = profiles.get(participant.lower(), {})
    
    if not events and not prof:
        st.info(f"No timeline events or CRM data found yet for **{participant.capitalize()}**.")
        st.markdown("👉 **How to use:** Go to 'Save Meeting Notes' and save a new note. AI will automatically extract events to build this timeline!")
        return
        
    last_interaction = events[0].get("date", "Unknown") if events else "Unknown"
    
    # Calculate top topics from tags
    all_tags = []
    for e in events:
        all_tags.extend(e.get("tags", []))
    from collections import Counter
    top_tags = [t[0] for t in Counter(all_tags).most_common(3)]
    topics_str = ", ".join(top_tags) if top_tags else "None"
    
    open_follows = len([e for e in events if e.get("type", "").lower() == "follow-up"])
    pending_tasks = len(prof.get("tasks", []))
    health = prof.get("activity_score", "N/A")
    
    # Quick Context Card
    st.markdown(f"""
    <div style='background: rgba(30,41,59,0.7); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 15px; margin-bottom: 20px;'>
        <h4 style='margin-top:0;'>⚡ Quick Context</h4>
        <div style='display: flex; justify-content: space-between; flex-wrap: wrap;'>
            <div><b>Last Interaction:</b> {last_interaction}</div>
            <div><b>Top Topics:</b> {topics_str}</div>
            <div><b>Open Follow-ups:</b> {open_follows}</div>
            <div><b>Pending Tasks:</b> {pending_tasks}</div>
            <div><b>Relationship Health:</b> {health}/100</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Timeline Insights
    if st.button("Generate Timeline Insights 🧠", key=f"insights_{participant}"):
        with st.spinner("Generating insights..."):
            if st.session_state.groq_client and events:
                prompt = f"Analyze these timeline events and summarize frequently discussed topics, most recent commitments, unresolved issues, and recurring themes:\n{json.dumps(events)}"
                try:
                    resp = st.session_state.groq_client.chat.completions.create(
                        model=MODEL, messages=[{"role":"user", "content":prompt}], temperature=0.2, max_tokens=600
                    )
                    st.info(resp.choices[0].message.content.strip())
                except Exception as e:
                    st.error(f"Failed to generate insights: {{e}}")
            else:
                st.error("No events found or Groq client not initialized.")
    
    # Search & Filter
    col1, col2 = st.columns([2, 1])
    with col1:
        search_kw = st.text_input("Search Timeline:", key=f"tl_search_{participant}")
    with col2:
        ev_types = ["All Events", "Meeting", "Decision", "Commitment", "Follow-up", "Task Assigned", "Task Completed", "Risk Alert"]
        filter_type = st.selectbox("Filter by Type:", options=ev_types, key=f"tl_filter_{participant}")
        
    filtered_events = events
    if search_kw:
        filtered_events = [e for e in filtered_events if search_kw.lower() in str(e).lower()]
    if filter_type != "All Events":
        filtered_events = [e for e in filtered_events if e.get("type") == filter_type]
        
    limit_key = f"tl_limit_{participant}"
    if limit_key not in st.session_state:
        st.session_state[limit_key] = 10
        
    display_events = filtered_events[:st.session_state[limit_key]]
    
    icons = {
        "Meeting": "📞", "Decision": "✅", "Commitment": "🤝", 
        "Follow-up": "📌", "Task Assigned": "📝", "Task Completed": "🟢", "Risk Alert": "🔴"
    }
    
    for e in display_events:
        icon = icons.get(e.get("type"), "🔹")
        tags = ", ".join(e.get("tags", []))
        st.markdown(f"""
        <div style='border-left: 3px solid #6366f1; padding-left: 15px; margin-bottom: 15px;'>
            <div style='color: #94a3b8; font-size: 0.85rem;'>[{e.get('date', 'Unknown')}] {icon} <b>{e.get('type', 'Event')}</b></div>
            <div style='margin-top: 5px;'>{e.get('summary', '')}</div>
            <div style='color: #64748b; font-size: 0.8rem; margin-top: 5px;'><i>Tags: {tags}</i></div>
        </div>
        """, unsafe_allow_html=True)
        
    if not display_events:
        st.info("No timeline events found. Go to 'Save Meeting Notes' and log a meeting to see the AI build your timeline!")
        
    if len(filtered_events) > st.session_state[limit_key]:
        if st.button("Load More ⬇️", key=f"tl_load_{participant}"):
            st.session_state[limit_key] += 10
            st.rerun()


# Page Setup
st.set_page_config(
    page_title="MeetPrep AI Agent",
    page_icon="🧠",
    layout="centered"
)

# Custom Styling (Rich Aesthetics)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: #f8fafc;
}

/* Hide deploy button but keep hamburger menu */
.stDeployButton {
    display: none !important;
}

.title-container {
    text-align: center;
    margin-bottom: 25px;
    padding-bottom: 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.header-title {
    background: linear-gradient(135deg, #818cf8 0%, #c084fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.8rem !important;
    font-weight: 800;
    text-align: center;
    margin: 0;
    letter-spacing: -0.025em;
}

.status-badge {
    font-size: 0.85rem;
    color: #94a3b8;
    margin-top: 8px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.header-subtitle {
    font-size: 1.1rem;
    color: #94a3b8;
    text-align: center;
    margin-bottom: 40px;
    font-weight: 400;
    line-height: 1.6;
}

/* Custom Card Layout */
.nav-card {
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 16px;
    padding: 28px 24px;
    text-align: center;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    min-height: 230px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.nav-card:hover {
    transform: translateY(-6px);
    border-color: rgba(99, 102, 241, 0.5);
    box-shadow: 0 12px 30px rgba(99, 102, 241, 0.25);
}

.nav-icon {
    font-size: 2.8rem;
    margin-bottom: 18px;
    filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3));
}

.nav-title {
    font-size: 1.25rem;
    font-weight: 700;
    margin-bottom: 10px;
    color: #f8fafc;
    letter-spacing: -0.01em;
}

.nav-desc {
    font-size: 0.85rem;
    color: #94a3b8;
    line-height: 1.5;
    margin-bottom: 0;
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
            "content": "Hello! I'm your **MeetPrep AI Agent** 🧠\n\nUse the options below to prepare, save, upload, view profiles, or search."
        }
    ]
    st.session_state.step = "menu"
    st.session_state.save_participant = ""
    st.session_state.processed_file = ""
    st.session_state.active_tab = "dashboard"
    st.session_state.initialized = True

# Mode indicator label
mode_label = "CLOUD MODE" if st.session_state.use_cloud else "LOCAL MODE"

# Render header
st.markdown(f"""
<div class="title-container">
    <h1 class="header-title">🧠 MeetPrep AI</h1>
</div>
""", unsafe_allow_html=True)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ App Controls")
    if st.button("Reset Conversation", use_container_width=True, key="sidebar_reset_btn"):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I'm your **MeetPrep AI Agent** 🧠\n\nUse the options below to prepare, save, upload, view profiles, or search."
            }
        ]
        st.session_state.step = "menu"
        st.session_state.save_participant = ""
        st.session_state.processed_file = ""
        st.session_state.active_tab = "dashboard"
        if "last_prep_name" in st.session_state:
            del st.session_state.last_prep_name
        if "current_brief" in st.session_state:
            del st.session_state.current_brief
        if "doc_analysis_result" in st.session_state:
            del st.session_state.doc_analysis_result
        st.rerun()
        
    if st.button("Seed Mock Memories", use_container_width=True, key="sidebar_seed_btn"):
        seed_demo_data()
        st.rerun()

# ─── ACTIVE PAGE ROUTING ──────────────────────────────────────────────────────
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "dashboard"

if st.session_state.active_tab == "dashboard":
    st.markdown("### 🛠️ Select an Assistant Tool:")
    
    row1_col1, row1_col2, row1_col3 = st.columns(3)
    
    with row1_col1:
        st.markdown("""
        <div class="nav-card">
            <div class="nav-icon">📝</div>
            <div class="nav-title">1. Save Notes</div>
            <div class="nav-desc">Save structured notes to persistent memory with AI fact extraction.</div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Save Notes 📝", use_container_width=True, key="nav_btn_save"):
            st.session_state.active_tab = "save"
            st.rerun()
            
    with row1_col2:
        st.markdown("""
        <div class="nav-card">
            <div class="nav-icon">📋</div>
            <div class="nav-title">2. Prepare Brief</div>
            <div class="nav-desc">Generate AI briefings, track past commitments, and get custom icebreakers.</div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Start Preparing 📋", use_container_width=True, key="nav_btn_prep"):
            st.session_state.active_tab = "prep"
            st.rerun()
            
    with row1_col3:
        st.markdown("""
        <div class="nav-card">
            <div class="nav-icon">📁</div>
            <div class="nav-title">3. Doc Memory</div>
            <div class="nav-desc">Upload PDFs/text transcript documents to parse and save to memory.</div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Upload Document 📁", use_container_width=True, key="nav_btn_doc"):
            st.session_state.active_tab = "document"
            st.rerun()
            
    st.write("")
    row2_col1, row2_col2 = st.columns(2)
    
    with row2_col1:
        st.markdown("""
        <div class="nav-card">
            <div class="nav-icon">👥</div>
            <div class="nav-title">4. CRM Intelligence</div>
            <div class="nav-desc">Analyze team contributions, activity metrics, and behavioral insights.</div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("View Profiles 👥", use_container_width=True, key="nav_btn_crm"):
            st.session_state.active_tab = "crm"
            st.rerun()
            
    with row2_col2:
        st.markdown("""
        <div class="nav-card">
            <div class="nav-icon">🔍</div>
            <div class="nav-title">5. Search Memories</div>
            <div class="nav-desc">Search your entire meeting database by names, dates, or keywords.</div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Search History 🔍", use_container_width=True, key="nav_btn_search"):
            st.session_state.active_tab = "search"
            st.rerun()

else:
    # Sub-page layout with Back Button
    if st.button("← Back to Dashboard Portal", key="back_to_dashboard_btn"):
        st.session_state.active_tab = "dashboard"
        st.rerun()
        
    st.markdown("---")
    
    # ─── SUB-PAGE 1: PREPARE FOR MEETING ──────────────────────────────────────
    if st.session_state.active_tab == "prep":
        st.markdown("## 📋 Prepare for Meeting")
        st.markdown("Retrieve past history and synthesize an actionable meeting brief using Groq LLM.")
        prep_name = st.text_input(
            "Who is the meeting with? (Enter name):",
            key="main_prep_name",
            placeholder="e.g. Alex, Sarah"
        )
        
        if prep_name:
            cleaned_prep_name = prep_name.strip()
            if st.session_state.get("last_prep_name") != cleaned_prep_name:
                st.session_state.last_prep_name = cleaned_prep_name
                with st.spinner(f"Retrieving memory and generating brief for {cleaned_prep_name}..."):
                    if st.session_state.use_cloud:
                        memory = cloud_recall(st.session_state.hindsight_client, cleaned_prep_name)
                    else:
                        memory = local_recall(cleaned_prep_name)
                    
                    if not st.session_state.groq_client:
                        st.session_state.current_brief = "🔴 **Error:** Groq API client is not initialized."
                    else:
                        brief = generate_meeting_prep_brief(st.session_state.groq_client, cleaned_prep_name.capitalize(), memory)
                        if brief is None:
                            st.session_state.current_brief = "🔴 **Error:** Failed to generate brief."
                        else:
                            st.session_state.current_brief = brief
                            
            if st.session_state.get("current_brief"):
                st.markdown("### 📋 Generated Brief")
                st.markdown(st.session_state.current_brief)
                
                # Render Timeline & Context
                render_timeline_view(cleaned_prep_name)
        else:
            st.session_state.last_prep_name = ""
            st.session_state.current_brief = ""
            
    # ─── SUB-PAGE 2: SAVE MEETING NOTES ───────────────────────────────────────
    elif st.session_state.active_tab == "save":
        st.markdown("## 📝 Save Meeting Notes")
        st.markdown("Log a completed meeting. AI will extract commitments, tasks, and follow-ups.")
        with st.form("save_notes_form"):
            p_name = st.text_input("Who was the meeting with? (Participant Name)*", placeholder="Participant name...")
            col_dt1, col_dt2 = st.columns(2)
            with col_dt1:
                m_date = st.date_input("Meeting Date", value=datetime.date.today())
            with col_dt2:
                m_time = st.time_input("Meeting Time", value=datetime.datetime.now().time())
            m_topics = st.text_input("Meeting Topics (e.g. PR Review, GCP migration)", placeholder="Key topics...")
            m_notes = st.text_area("Meeting Notes (Tell me what happened...)*", height=200, placeholder="Notes...")
            
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                submitted = st.form_submit_button("Save to Memory", use_container_width=True)
            with col_s2:
                canceled = st.form_submit_button("Cancel", use_container_width=True)
                
            if submitted:
                if not p_name.strip() or not m_notes.strip():
                    st.error("Please fill in Participant Name and Meeting Notes.")
                else:
                    with st.spinner("Structuring notes with AI..."):
                        if not st.session_state.groq_client:
                            structured = m_notes
                        else:
                            structured = structure_notes_with_ai(st.session_state.groq_client, p_name.capitalize(), m_notes)
                        
                        dt_combined = datetime.datetime.combine(m_date, m_time)
                        date_str = dt_combined.strftime("%Y-%m-%d %I:%M %p")
                        topics_str = m_topics.strip() or "General Discussion"
                        
                        saved = False
                        if st.session_state.use_cloud:
                            h_content = f"Meeting Date: {date_str}\nTopics: {topics_str}\nNotes: {structured}"
                            saved = cloud_retain(st.session_state.hindsight_client, p_name.capitalize(), h_content)
                            if not saved:
                                local_retain_with_metadata(p_name.lower(), date_str, topics_str, structured)
                                saved = True
                                save_msg = f"Cloud save failed. Notes saved locally for **{p_name.capitalize()}**."
                            else:
                                save_msg = f"Notes successfully stored in Hindsight Cloud memory for **{p_name.capitalize()}**!"
                        else:
                            local_retain_with_metadata(p_name.lower(), date_str, topics_str, structured)
                            saved = True
                            save_msg = f"Notes successfully stored in local memory for **{p_name.capitalize()}**!"
                        
                        if saved:
                            full_text_for_crm = f"Meeting Date: {date_str}\nTopics: {topics_str}\nNotes: {structured}"
                            update_crm_profiles_with_ai(st.session_state.groq_client, full_text_for_crm)
                            
                            if st.session_state.groq_client:
                                new_events = extract_timeline_events_with_ai(
                                    st.session_state.groq_client, p_name.capitalize(), date_str, structured
                                )
                                append_timeline_events(p_name.capitalize(), new_events)
                                
                            st.success(save_msg)
                            
            if canceled:
                st.session_state.active_tab = "dashboard"
                st.rerun()

    # ─── SUB-PAGE 3: DOCUMENT MEMORY ──────────────────────────────────────────
    elif st.session_state.active_tab == "document":
        st.markdown("## 📁 Document Memory Integration")
        st.markdown("Upload meeting transcripts or documents (PDF/TXT) to automatically parse, summarize, and integrate into participant records.")
        uploaded_file = st.file_uploader(
            "Upload meeting document (PDF, TXT):", 
            type=["pdf", "txt"], 
            key="main_uploaded_file"
        )

        if uploaded_file is not None:
            if st.session_state.get("processed_file") != uploaded_file.name:
                st.session_state.processed_file = uploaded_file.name
                
                with st.spinner("Processing and analyzing meeting document..."):
                    file_text = ""
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
                                
                                participants = []
                                import re
                                part_match = re.search(r"\[PARTICIPANTS\]:\s*(.*)", analysis, re.IGNORECASE)
                                if part_match:
                                    raw_parts = part_match.group(1).strip()
                                    if raw_parts and raw_parts.lower() != "none":
                                        participants = [p.strip().lower() for p in raw_parts.split(",") if p.strip()]
                                
                                display_analysis = re.sub(r"\[PARTICIPANTS\]:.*", "", analysis, flags=re.IGNORECASE).strip()
                                update_crm_profiles_with_ai(st.session_state.groq_client, file_text)
                                
                                related_meetings = []
                                stored_confirmations = []
                                
                                if participants:
                                    for p in participants:
                                        if st.session_state.use_cloud:
                                            history = cloud_recall(st.session_state.hindsight_client, p)
                                        else:
                                            history = local_recall(p)
                                            
                                        if history:
                                            count = len(history.split("\n\n---\n\n"))
                                            related_meetings.append(f"Linked with {p.capitalize()}'s profile ({count} past meetings found).")
                                        else:
                                            related_meetings.append(f"Created a new profile history for {p.capitalize()}.")
                                            
                                        memory_content = f"Document: {uploaded_file.name}\nKey insights extracted from document:\n{display_analysis}"
                                        
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
                                            
                                        if st.session_state.groq_client:
                                            doc_date = datetime.date.today().isoformat()
                                            new_events = extract_timeline_events_with_ai(
                                                st.session_state.groq_client, p.capitalize(), doc_date, memory_content
                                            )
                                            append_timeline_events(p.capitalize(), new_events)
                                else:
                                    related_meetings.append("No specific participant names identified in the document.")
                                    stored_confirmations.append("Document processed, but not linked to any specific participant.")
                                    
                                related_meetings_str = "\n".join([f"- {m}" for m in related_meetings])
                                stored_confirmations_str = "\n".join([f"- {c}" for c in stored_confirmations])
                                
                                st.session_state.doc_analysis_result = f"""{display_analysis}

### ⏱️ Related Meetings
{related_meetings_str}

### 💾 Stored Memory Confirmation
{stored_confirmations_str}"""
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"Error analyzing document with Groq: {e}")

            if st.session_state.get("doc_analysis_result"):
                st.markdown("### 📋 Extracted Document Analysis")
                st.markdown(st.session_state.doc_analysis_result)
        else:
            st.session_state.processed_file = ""
            st.session_state.doc_analysis_result = ""

    # ─── SUB-PAGE 4: CRM PROFILES ─────────────────────────────────────────────
    elif st.session_state.active_tab == "crm":
        st.markdown("## 👥 Participant CRM Profiles")
        st.markdown("View profiles, contribution metrics, assigned tasks, bottlenecks, and behavioral insights.")
        crm_profiles = load_crm_profiles()
        if not crm_profiles:
            st.info("No CRM profiles tracked yet.")
            selected_crm = None
        else:
            crm_names = sorted(list(crm_profiles.keys()))
            selected_crm = st.selectbox(
                "Select participant profile to view CRM intelligence:",
                options=["-- Select --"] + [n.capitalize() for n in crm_names],
                key="main_selected_crm"
            )

        if selected_crm and selected_crm != "-- Select --":
            prof = crm_profiles[selected_crm.lower()]
            
            st.markdown(f"<h4 style='margin-top:10px;'>👤 CRM Intelligence: <b>{prof.get('name')}</b></h4>", unsafe_allow_html=True)
            
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
                    
            # Render Timeline & Context
            render_timeline_view(selected_crm)

    # ─── SUB-PAGE 5: SEARCH MEETINGS ──────────────────────────────────────────
    elif st.session_state.active_tab == "search":
        st.markdown("## 🔍 Search Meetings & Memory")
        st.markdown("Query the database for past meeting logs using names, dates, or keywords.")
        search_query = st.text_input(
            "Search Name, Date, or Topic:",
            key="main_search_query",
            placeholder="Type to search..."
        )

        if search_query:
            st.markdown(f"#### 🔍 Search Results for: *\"{search_query}\"*")
            search_results = search_local_meetings(search_query)
            if not search_results:
                st.info("No matching meetings found in memory.")
            else:
                st.write(f"Found {len(search_results)} matching meeting(s):")
                for res in search_results:
                    with st.expander(f"📅 {res['date']} - Meeting with {res['participant']}"):
                        if res.get('topics'):
                            st.markdown(f"**Topics Discussed:** {res['topics']}")
                        st.markdown("**Meeting Notes:**")
                        st.write(res['text'])



