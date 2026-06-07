export const mockParticipants = [
  {
    id: "p1",
    name: "Alex",
    role: "Open Source Contributor",
    avatar: "https://ui-avatars.com/api/?name=Alex&background=3b82f6&color=fff",
    profile: {
      interests: ["React", "State Management", "Open Source Architecture"],
      communicationStyle: "Technical, direct, prefers bullet points over long emails.",
      skills: ["JavaScript", "React", "Node.js"],
      contributionHistory: "Submitted 15 PRs in the last 6 months. Active in community Discord.",
      recurringConcerns: "Often struggles with setting up local development environments."
    }
  },
  {
    id: "p2",
    name: "Sarah",
    role: "Community Mentor",
    avatar: "https://ui-avatars.com/api/?name=Sarah&background=10b981&color=fff",
    profile: {
      interests: ["Mentorship", "Diversity in Tech", "Hackathons"],
      communicationStyle: "Empathetic, prefers video calls for 1-on-1s.",
      skills: ["Community Building", "Python", "Public Speaking"],
      contributionHistory: "Mentored 10+ students this year. Organizes monthly workshops.",
      recurringConcerns: "Worried about participant burnout in long hackathons."
    }
  },
  {
    id: "p3",
    name: "John",
    role: "Event Organizer",
    avatar: "https://ui-avatars.com/api/?name=John&background=f59e0b&color=fff",
    profile: {
      interests: ["Sponsorships", "Logistics", "Marketing"],
      communicationStyle: "Action-oriented, short messages, uses Slack heavily.",
      skills: ["Project Management", "Budgeting"],
      contributionHistory: "Organized 3 major regional hackathons.",
      recurringConcerns: "Sponsor retention and budget constraints."
    }
  }
];

export const mockMeetings = [
  {
    id: "m1",
    participantId: "p1",
    date: "2026-05-12",
    topic: "Discussed HackBaroda Hackathon Integration",
    notes: "Alex is very interested in integrating our new APIs into his open source project for the hackathon. Mentioned he might need some guidance on the auth flow.",
    commitments: [],
    events: ["Hackathon planning initiated"]
  },
  {
    id: "m2",
    participantId: "p1",
    date: "2026-05-18",
    topic: "PR #42 Review and Architecture",
    notes: "Walked through Alex's PR #42. It's solid but needs a few performance tweaks on the frontend. I promised to review the final changes once he pushes them.",
    commitments: [
      { id: "c1", task: "Review PR #42 for Alex", status: "Pending", dueDate: "2026-05-25" }
    ],
    events: ["Architecture discussion"]
  },
  {
    id: "m3",
    participantId: "p1",
    date: "2026-05-28",
    topic: "Quick Catch-up / Health",
    notes: "Alex had to postpone some work because he came down with a bad flu. Told him to take it easy and not rush the PR.",
    commitments: [],
    events: ["Health concern mentioned"]
  },
  {
    id: "m4",
    participantId: "p1",
    date: "2026-06-05",
    topic: "Deployment Help Requested",
    notes: "Alex is stuck on the Vercel deployment step for the hackathon project. He's getting a build error related to environment variables.",
    commitments: [
      { id: "c2", task: "Send Alex the updated .env template", status: "Overdue", dueDate: "2026-06-06" }
    ],
    events: ["Deployment blocker"]
  },
  {
    id: "m5",
    participantId: "p2",
    date: "2026-05-20",
    topic: "Mentorship Program Launch",
    notes: "Sarah proposed a new structure for the 1-on-1 mentorship sessions.",
    commitments: [
      { id: "c3", task: "Approve mentorship budget", status: "Completed", dueDate: "2026-05-22" }
    ],
    events: ["Program launch discussion"]
  }
];
