const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

// Hackathon Demo Mode API
// In a production environment, this would call Hindsight API and Groq LLM API.
app.post('/api/prep', (req, res) => {
  const { participantId } = req.body;
  
  // Simulate Hindsight Memory Retrieval + Groq LLM Processing
  setTimeout(() => {
    res.json({
      success: true,
      message: "Successfully retrieved historical context from Hindsight and synthesized with Groq.",
      data: {
        summary: "Active technical relationship. Participant faced recent deployment blockers.",
        risks: ["Missed follow-up on Health Concern", "Deployment blocker not resolved"],
        agenda: [
          "Follow up on flu recovery.",
          "Provide Vercel .env template.",
          "Review PR #42 architecture."
        ]
      }
    });
  }, 2000);
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`MeetPrep AI Backend running on port ${PORT}`));
