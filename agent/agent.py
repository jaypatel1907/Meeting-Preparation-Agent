#!/usr/bin/env python3
"""
MeetPrep AI Agent
-----------------
A real conversational AI agent that:
1. Retrieves past meeting history from Hindsight memory (or local fallback)
2. Generates a meeting prep brief using Groq LLM
3. Saves new meeting notes back into persistent memory

Usage:
  python agent.py           — Normal mode (uses .env for config)
  python agent.py --demo    — Demo mode (seeds sample data for Alex, Sarah, John)
"""

import os
import sys
import json
import datetime
import socket
import urllib.parse

# ─── SAFE PRINT FOR WINDOWS ───────────────────────────────────────────────────
_builtin_print = print
def print(*args, **kwargs):
    """Safe print wrapper that handles UnicodeEncodeError on Windows CP1252 terminals."""
    new_args = []
    for arg in args:
        if isinstance(arg, str):
            try:
                encoding = sys.stdout.encoding or 'utf-8'
                arg.encode(encoding)
                new_args.append(arg)
            except UnicodeEncodeError:
                encoding = sys.stdout.encoding or 'ascii'
                safe_str = arg
                replacements = {
                    '✓': '[OK]',
                    '⚠': '[WARN]',
                    '✗': '[ERROR]',
                    '──': '--',
                    '═': '=',
                    '║': '|',
                    '🧠': 'Memory',
                    '🤖': 'Agent',
                    '👋': 'Bye',
                    '🚀': 'Go',
                    '✨': '*'
                }
                for u_char, r_char in replacements.items():
                    safe_str = safe_str.replace(u_char, r_char)
                safe_str = safe_str.encode(encoding, errors='replace').decode(encoding)
                new_args.append(safe_str)
        else:
            new_args.append(arg)
    _builtin_print(*new_args, **kwargs)

# ─── AUTO LOAD .env FILE ───────────────────────────────────────────────────────
def load_dotenv():
    """Simple .env file loader — no external dependency needed."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val

load_dotenv()

# ─── CONFIG ───────────────────────────────────────────────────────────────────
GROQ_API_KEY      = os.getenv("GROQ_API_KEY", "")
HINDSIGHT_URL     = os.getenv("HINDSIGHT_URL", "http://localhost:8888")
HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY", "")
MEMORY_BANK_ID    = "meetprep-agent"
MODEL             = "llama-3.3-70b-versatile"
LOCAL_MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_memory.json")
# ──────────────────────────────────────────────────────────────────────────────

# Colors
BLUE   = "\033[94m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

# ─── DEMO SEED DATA ───────────────────────────────────────────────────────────
DEMO_MEMORIES = [
    {
        "participant": "alex",
        "display_name": "Alex",
        "date": "2026-05-20",
        "notes": (
            "Meeting Date: 20 May 2026. Participant: Alex. "
            "Discussed the PR #42 code review — Alex promised to complete it by 25 May 2026. "
            "Alex mentioned he has been unwell with flu this week and may need a few extra days. "
            "He is interested in Rust and wants help exploring async programming patterns. "
            "Follow-up: Check if PR #42 was merged. "
            "Next meeting: Discuss the upcoming product deployment planned for Q3."
        )
    },
    {
        "participant": "alex",
        "display_name": "Alex",
        "date": "2026-04-15",
        "notes": (
            "Meeting Date: 15 April 2026. Participant: Alex. "
            "We reviewed Alex's contribution to the microservices migration project. "
            "Alex raised concerns about database connection pooling under load. "
            "He committed to writing a benchmarking script to identify the bottleneck. "
            "He also mentioned he is mentoring two junior developers, Priya and Sam. "
            "Follow-up: Share results of benchmarking with the team by end of April."
        )
    },
    {
        "participant": "sarah",
        "display_name": "Sarah",
        "date": "2026-05-30",
        "notes": (
            "Meeting Date: 30 May 2026. Participant: Sarah. "
            "Discussed Sarah's role in the upcoming community hackathon (HackBaroda). "
            "Sarah is leading the Community Track and wants to finalize problem statements. "
            "She committed to sending the finalized problem statement document by June 2. "
            "Concerns: She is worried about low participant registration so far. "
            "Personal: Sarah's baby shower is next week, team has planned a small surprise. "
            "Follow-up: Check if the problem statement doc was shared."
        )
    },
    {
        "participant": "sarah",
        "display_name": "Sarah",
        "date": "2026-04-22",
        "notes": (
            "Meeting Date: 22 April 2026. Participant: Sarah. "
            "Sarah proposed a new open-source workshop series for the community. "
            "She wants to run 3 workshops: Git & GitHub, Python basics, and REST APIs. "
            "She will need sponsorship for venue and catering. "
            "Action: Help Sarah draft the sponsorship proposal by end of April. "
            "Sarah has expertise in developer advocacy and technical writing."
        )
    },
    {
        "participant": "john",
        "display_name": "John",
        "date": "2026-05-10",
        "notes": (
            "Meeting Date: 10 May 2026. Participant: John. "
            "John is leading the infrastructure team. Discussed the cloud migration to GCP. "
            "John committed to setting up staging environment by 20 May 2026 — status unknown. "
            "He raised concerns about budget overrun in Q2. "
            "John is interested in speaking at the next community meetup about Kubernetes. "
            "Personal note: John just returned from a 2-week vacation in Japan. "
            "Follow-up: Confirm staging environment is live. Invite John for the Kubernetes talk."
        )
    },
]

# ─── TERMINAL UI HELPERS ──────────────────────────────────────────────────────

def banner(mode_label=""):
    label = f"  [{mode_label}]" if mode_label else ""
    print(f"""
{BLUE}{BOLD}╔══════════════════════════════════════════════════════╗
║          🧠  MeetPrep AI Agent{label:<24}║
║   Powered by Hindsight Memory + Groq LLM             ║
╚══════════════════════════════════════════════════════╝{RESET}
""")

def section(title):
    print(f"\n{CYAN}{BOLD}── {title} {'─' * max(0, 48 - len(title))}{RESET}")

def info(msg):
    print(f"  {DIM}{msg}{RESET}")

def success(msg):
    print(f"  {GREEN}✓ {msg}{RESET}")

def warn(msg):
    print(f"  {YELLOW}⚠  {msg}{RESET}")

def error(msg):
    print(f"  {RED}✗ {msg}{RESET}")

def agent_says(msg):
    print(f"\n{BLUE}{BOLD}🤖 Agent:{RESET} {msg}")

def user_input(prompt="You: "):
    try:
        return input(f"\n{GREEN}{BOLD}{prompt}{RESET}").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n\nGoodbye! 👋")
        sys.exit(0)

# ─── CONNECTIVITY CHECK ───────────────────────────────────────────────────────

def check_hindsight_connection(url: str) -> bool:
    """Quick TCP check to see if the Hindsight server is reachable."""
    try:
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 8888)
        if not host or "xxx" in host or "your-instance" in host or "your_" in host:
            return False
        sock = socket.create_connection((host, port), timeout=5)
        sock.close()
        return True
    except Exception:
        return False

# ─── LOCAL FILE MEMORY (FALLBACK) ─────────────────────────────────────────────

def load_local_memory() -> dict:
    """Load local memory store from disk."""
    if os.path.exists(LOCAL_MEMORY_FILE):
        try:
            with open(LOCAL_MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_local_memory(store: dict):
    """Persist local memory store to disk."""
    with open(LOCAL_MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2, ensure_ascii=False)

def local_retain(participant: str, content: str):
    """Add a memory entry for a participant in local storage."""
    store = load_local_memory()
    key = participant.lower().strip()
    if key not in store:
        store[key] = []
    store[key].append({
        "date": datetime.date.today().isoformat(),
        "text": content
    })
    save_local_memory(store)
    success(f"Memory saved locally for {participant} in local_memory.json")

def local_recall(participant: str) -> str:
    """Recall all memory entries for a participant from local storage."""
    store = load_local_memory()
    key = participant.lower().strip()
    entries = store.get(key, [])
    if not entries:
        return ""
    parts = []
    for e in entries:
        parts.append(f"[{e.get('date', 'unknown date')}]\n{e.get('text', '')}")
    success(f"Found {len(entries)} memory fragments locally for {participant}.")
    return "\n\n---\n\n".join(parts)

# ─── HINDSIGHT CLIENT HELPERS ─────────────────────────────────────────────────

def get_hindsight():
    """Initialize and return a Hindsight client."""
    try:
        from hindsight_client import Hindsight
        kwargs = {"base_url": HINDSIGHT_URL}
        if HINDSIGHT_API_KEY:
            kwargs["api_key"] = HINDSIGHT_API_KEY
        return Hindsight(**kwargs)
    except ImportError:
        error("hindsight_client package is not installed. Run: pip install hindsight-client")
        return None
    except Exception as e:
        error(f"Cannot initialize Hindsight: {e}")
        return None

def cloud_retain(hindsight, participant: str, content: str) -> bool:
    """Store memory in Hindsight Cloud. Returns True on success."""
    today = datetime.date.today()
    full_content = f"Meeting Date: {today.strftime('%d %B %Y')}\nParticipant: {participant}\nMeeting Notes: {content}"
    doc_id = f"{participant.lower().replace(' ', '-')}-{today.isoformat()}"
    try:
        hindsight.retain(bank_id=MEMORY_BANK_ID, content=full_content, document_id=doc_id)
        success(f"Memory saved to Hindsight Cloud for {participant}.")
        return True
    except Exception as e:
        error(f"Failed to save to Hindsight Cloud: {e}")
        return False

def cloud_recall(hindsight, participant: str) -> str:
    """Recall memories from Hindsight Cloud. Returns combined text."""
    query = f"Meeting with {participant}. Discussions, commitments, action items, concerns, follow-ups."
    try:
        results = hindsight.recall(bank_id=MEMORY_BANK_ID, query=query)
        if not results or not results.results:
            return ""
        texts = [r.text for r in results.results]
        success(f"Found {len(texts)} memory fragments in Hindsight Cloud for {participant}.")
        return "\n\n---\n\n".join(texts)
    except Exception as e:
        warn(f"Hindsight Cloud recall failed: {e}")
        return ""

# ─── GROQ CLIENT ──────────────────────────────────────────────────────────────

def get_groq():
    """Initialize and return a Groq client."""
    if not GROQ_API_KEY:
        error("GROQ_API_KEY is not set.")
        error("Get a free key at: https://console.groq.com")
        error("Then add it to your .env file: GROQ_API_KEY=your_key_here")
        sys.exit(1)
    try:
        from groq import Groq
        return Groq(api_key=GROQ_API_KEY)
    except ImportError:
        error("groq package is not installed. Run: pip install groq")
        sys.exit(1)

# ─── AI OPERATIONS ────────────────────────────────────────────────────────────

def structure_notes_with_ai(groq_client, participant: str, raw_notes: str) -> str:
    """Use Groq to extract and structure key facts from meeting notes before storing."""
    prompt = f"""Extract and structure the key information from these raw meeting notes to store in memory.

Participant: {participant}
Date: {datetime.date.today().strftime('%d %B %Y')}
Raw Notes:
{raw_notes}

Format the output as clear, factual sentences covering:
- Key discussion topics
- Commitments and promises made (who does what by when)
- Action items
- Important personal details mentioned
- Follow-ups needed
- Any concerns or issues raised

Be concise and factual. Write it as structured sentences, not bullet points."""
    try:
        from groq import Groq
        response = groq_client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=600
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return raw_notes  # fallback: store raw notes as-is


def generate_meeting_prep_brief(groq_client, participant: str, memory: str) -> str:
    """Use Groq LLM to generate a structured meeting prep brief."""
    if memory:
        memory_section = f"""Here is the HISTORICAL MEMORY retrieved from past interactions with {participant}:
---
{memory}
---
Use this memory as the PRIMARY basis for all your recommendations. Reference specific details."""
    else:
        memory_section = f"No past meeting history found for {participant}. This appears to be a first meeting."

    timestamp = datetime.datetime.now().strftime("%d %B %Y, %H:%M")
    memory_source = "Hindsight Cloud / Local Memory" if memory else "No previous history"

    prompt = f"""You are an intelligent Meeting Preparation Agent for community leaders, mentors, and organizers.

{memory_section}

Generate a professional, actionable Meeting Preparation Brief for the upcoming meeting with {participant}.

## 📋 Meeting Prep Brief: {participant}
**Generated:** {timestamp}
**Memory Source:** {memory_source}

---

### 🧠 Relationship Summary
(2-3 sentences summarizing the relationship and key context from memory)

### ⚠️ Open Commitments & Follow-ups
(List unresolved commitments or action items from past meetings. If none, say "None detected.")

### 🚨 Risk Alerts
(Any risks: missed deadlines, long gaps since contact, recurring issues. If none, say "None detected.")

### 📅 Recommended Agenda
1. (item based on memory)
2. (item based on memory)
3. (item based on memory)
4. (item based on memory)

### 💬 Conversation Starters
- (personal opener based on memory details)
- (work/technical opener based on memory)

### 💡 Key Things to Remember
- (important personal or professional detail from memory)
- (another key detail)

Be specific and reference actual details from the memory. If no memory exists, give general first-meeting advice."""

    info("Synthesizing meeting brief with Groq LLM...")
    try:
        response = groq_client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a professional AI meeting preparation agent. Always base your recommendations on actual historical memory. Be concise, specific, and actionable."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        error(f"Groq LLM call failed: {e}")
        if "invalid_api_key" in str(e) or "401" in str(e):
            error("Your GROQ_API_KEY is invalid. Get a free key at: https://console.groq.com")
            error("Then update your .env file and restart the agent.")
        return None  # Signal failure to caller

# ─── DEMO MODE ────────────────────────────────────────────────────────────────

def seed_demo_data():
    """Pre-load demo memories for Alex, Sarah, and John into local storage."""
    section("Seeding Demo Data")
    store = load_local_memory()
    seeded = 0
    for entry in DEMO_MEMORIES:
        key = entry["participant"]
        if key not in store:
            store[key] = []
        # Avoid duplicates
        if not any(e.get("text") == entry["notes"] for e in store[key]):
            store[key].append({
                "date": entry["date"],
                "text": entry["notes"]
            })
            seeded += 1
    save_local_memory(store)
    success(f"Demo data seeded! Added {seeded} memory entries.")
    success("Participants loaded: Alex, Sarah, John")
    info("Try Option 1 and enter 'alex', 'sarah', or 'john' to see memory in action!")

# ─── MAIN AGENT LOOP ──────────────────────────────────────────────────────────

def run_agent(demo_mode: bool = False):
    # Determine memory mode
    section("Initializing")
    hindsight_client = None
    use_cloud = False

    info(f"Checking Hindsight connection at: {HINDSIGHT_URL}")
    if check_hindsight_connection(HINDSIGHT_URL):
        hindsight_client = get_hindsight()
        if hindsight_client:
            use_cloud = True
            success("✅ Hindsight Cloud connected!")
        else:
            warn("Hindsight client failed to initialize.")
    else:
        warn(f"Cannot reach Hindsight server at: {HINDSIGHT_URL}")
        warn("Switching to LOCAL MEMORY mode (local_memory.json).")
        info("To use Hindsight Cloud, update HINDSIGHT_URL in your .env file.")

    memory_mode_label = "CLOUD MODE" if use_cloud else "LOCAL MODE"
    banner(memory_mode_label)

    groq_client = get_groq()
    success("Groq LLM ready.")

    if use_cloud:
        success("Memory: Hindsight Cloud")
    else:
        success(f"Memory: Local file ({os.path.basename(LOCAL_MEMORY_FILE)})")

    # Seed demo data if requested
    if demo_mode:
        seed_demo_data()

    agent_says(
        "Hello! I'm your MeetPrep AI Agent 🧠\n"
        "  I remember every meeting you've had and use that memory to prepare you for future ones.\n"
        f"  Memory Mode: {BOLD}{memory_mode_label}{RESET}"
    )

    while True:
        agent_says(
            "What would you like to do?\n"
            "  1. Prepare for an upcoming meeting\n"
            "  2. Save notes from a completed meeting\n"
            "  3. Exit"
        )
        choice = user_input("Choose (1/2/3): ")

        # ── OPTION 1: Prepare for a meeting ──────────────────────────────────
        if choice == "1":
            participant = user_input("Who is the meeting with? (Enter name): ")
            if not participant:
                warn("Please enter a participant name.")
                continue

            section(f"Retrieving Memory for {participant}")
            if use_cloud:
                memory = cloud_recall(hindsight_client, participant)
            else:
                memory = local_recall(participant)

            if not memory:
                warn(f"No past history found for '{participant}'. This may be your first meeting.")
            else:
                success("Historical context found. Passing to Groq for synthesis...")

            section("Generating Meeting Prep Brief")
            brief = generate_meeting_prep_brief(groq_client, participant, memory)

            if brief is None:
                warn("Meeting brief could not be generated. Fix your GROQ_API_KEY and try again.")
            else:
                print(f"\n{'═' * 60}")
                print(brief)
                print(f"{'═' * 60}")
                agent_says("Your meeting prep brief is ready! Good luck 🚀")
                agent_says("After the meeting, use option 2 to save your notes.")

        # ── OPTION 2: Save meeting notes ──────────────────────────────────────
        elif choice == "2":
            participant = user_input("Who was the meeting with? (Enter name): ")
            if not participant:
                warn("Please enter a participant name.")
                continue

            agent_says(f"Tell me what happened in your meeting with {participant}.")
            agent_says(
                "Include: topics discussed, commitments made, follow-ups, important things they said.\n"
                "  (Press ENTER twice when done)"
            )

            lines = []
            while True:
                line = user_input("> ")
                if line == "" and lines and lines[-1] == "":
                    break
                lines.append(line)

            raw_notes = "\n".join(lines).strip()
            if not raw_notes:
                warn("No notes entered. Nothing saved.")
                continue

            section("Processing & Saving to Memory")
            info("Structuring notes with AI...")
            structured = structure_notes_with_ai(groq_client, participant, raw_notes)

            saved = False
            if use_cloud:
                saved = cloud_retain(hindsight_client, participant, structured)
                if not saved:
                    fallback = user_input("Cloud save failed. Save to local memory instead? (y/n): ")
                    if fallback.lower() == "y":
                        local_retain(participant, structured)
                        saved = True
            else:
                local_retain(participant, structured)
                saved = True

            if saved:
                agent_says(
                    f"Perfect! I've saved the meeting with {participant} to memory. "
                    f"Next time you prepare for a meeting with them, I'll remember everything you just told me. 🧠"
                )
            else:
                error("Notes could not be saved. Please check your configuration.")

        # ── OPTION 3: Exit ────────────────────────────────────────────────────
        elif choice == "3":
            agent_says("Goodbye! I'll remember everything for next time. 🧠✨")
            break

        else:
            warn("Please enter 1, 2, or 3.")


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    demo_flag = "--demo" in sys.argv
    run_agent(demo_mode=demo_flag)
