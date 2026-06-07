# 🧠 MeetPrep AI Agent

> A real conversational AI agent powered by **Hindsight** (persistent memory) and **Groq** (LLM).
> Built for HackBaroda — Community Edition Problem Statement 4.

The agent **remembers every meeting you've had** and uses that historical context to prepare you for your next one. The more you use it, the smarter it gets.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧠 **Persistent Memory** | Stores structured meeting notes in Hindsight Cloud |
| 🤖 **AI Prep Briefs** | Groq LLM synthesizes memory into actionable prep documents |
| ⚠️ **Commitment Tracking** | Recalls open action items and follow-ups from past meetings |
| 🚨 **Risk Alerts** | Detects missed deadlines and long gaps in contact |
| 📂 **Local Fallback Mode** | Works offline using `local_memory.json` if Hindsight is unavailable |
| 🎬 **Demo Mode** | `--demo` flag seeds data for Alex, Sarah & John instantly |

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
cd agent
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
```
Edit `.env` and fill in your keys:
```env
GROQ_API_KEY=your_groq_api_key_here
HINDSIGHT_URL=https://your-instance.hindsight.vectorize.io
HINDSIGHT_API_KEY=your_hindsight_api_key_here
```
- **Groq API Key**: Free at [console.groq.com](https://console.groq.com)
- **Hindsight Cloud**: Sign up at [ui.hindsight.vectorize.io](https://ui.hindsight.vectorize.io) — use promo code **MEMHACK6** for $50 free credits

### 3. Run the agent
```bash
# Normal mode
python agent.py

# Demo mode (pre-loads data for Alex, Sarah, John)
python agent.py --demo
```

---

## 🎬 Demo Flow (For Judges)

1. **Launch demo**: `python agent.py --demo`
2. **Choose Option 1** (Prepare for meeting)
3. **Enter "alex"** as the participant
4. Watch the agent pull historical memory and generate a personalized brief with:
   - The open PR #42 commitment
   - Alex's health context (flu)
   - Relevant agenda items
5. **Choose Option 2** (Save notes) to add a new meeting
6. **Choose Option 1 again** — the agent now remembers the new meeting too!

---

## 🔧 How It Works

```
You: "Meeting with Alex"
        ↓
[Hindsight Recall] → Retrieves all past interactions with Alex
        ↓
[Groq LLM]        → Synthesizes memory into a structured prep brief
        ↓
You receive:       → Relationship summary, open commitments, agenda, risk alerts

After meeting:
You: "Alex fixed the bug, but deployment is delayed..."
        ↓
[Groq LLM]        → Structures raw notes into clean facts
        ↓
[Hindsight Retain] → Stores permanently in memory for future sessions
```

---

## 📁 Project Structure

```
agent/
├── agent.py            # Main AI agent (run this!)
├── requirements.txt    # Python dependencies
├── .env.example        # Template for environment variables
├── .env                # Your actual keys (gitignored)
├── local_memory.json   # Local fallback memory store (auto-created)
└── README.md           # This file
```

---

## 📦 Tech Stack

- **LLM**: [Groq](https://console.groq.com) — `llama-3.3-70b-versatile`
- **Memory**: [Hindsight by Vectorize](https://github.com/vectorize-io/hindsight)
- **Language**: Python 3.8+
- **Hackathon**: [HackBaroda](https://hackbaroda.com) Community Edition

---

## 🏆 Why This Wins

**Memory is the differentiator.**

Without memory, every AI conversation starts from zero. With Hindsight, this agent:
- Knows that Alex is still waiting on his PR #42 review
- Knows Sarah's baby shower was last week
- Knows John's staging environment was supposed to go live May 20

This is the **true value of persistent memory** — it makes AI actually useful for real relationships.
