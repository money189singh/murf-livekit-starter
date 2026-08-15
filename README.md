# 🏥 Health Access Voice AI Agent — VoiceForBharat

A real-time healthcare access voice assistant built during the **10 Days of Voice Agents — VoiceForBharat Edition**.

The agent is designed to help users understand healthcare access options, find nearby healthcare facilities, and get appropriate next-step guidance through a natural voice conversation.

> ⚠️ This project is an AI healthcare access assistant, not a doctor or medical professional. It does not diagnose medical conditions or prescribe medication.

---

## 🎙️ What is this project?

The Health Access Voice Agent is a conversational AI assistant that allows users to interact with a healthcare-access system using their voice.

Instead of requiring users to navigate websites or applications manually, users can simply speak to the agent.

For example:

> **User:** "I need to find a clinic near me."

The agent can understand the request, identify the user's location, search for nearby healthcare facilities, and present the available options.

The project was built as part of:

**10 Days of Voice Agents — VoiceForBharat Edition**

---

# 🚀 Features

### 🎙️ Real-time Voice Conversation

Users can communicate with the agent naturally using their microphone.

The system processes:

**Voice → Speech-to-Text → LLM → Tools → Text-to-Speech → Voice**

---

### 🧠 AI-powered Conversation

The agent uses an LLM to understand user requests and generate conversational responses.

The project currently uses **Groq** as the LLM provider.

The LLM is controlled by a dedicated system prompt containing:

- Agent personality
- Objectives
- Healthcare safety rules
- Conversation guidelines
- Escalation rules

---

### 🔊 Murf Falcon Text-to-Speech

The agent uses **Murf Falcon** for voice generation.

Murf provides natural-sounding speech suitable for real-time voice applications.

The project also uses an Indian English voice to make the assistant more natural for Indian users.

---

### 🇮🇳 Indian Language Support

The agent is designed to support conversations involving:

- English
- Hindi
- Hinglish / code-mixed speech

The goal is to make healthcare access easier for users who are more comfortable communicating in Indian languages.

---

### 🛡️ Healthcare Safety Guardrails

The agent is specifically designed with healthcare safety in mind.

The assistant must:

- Never claim to be a doctor or medical professional
- Never diagnose a medical condition
- Never prescribe medication
- Avoid presenting uncertain information as medical fact
- Recognize situations that may require urgent medical attention
- Encourage appropriate professional medical care
- Escalate to a human when necessary

The goal is to provide **healthcare access guidance**, not medical diagnosis.

---

### 📍 Nearby Healthcare Facility Search

The agent includes a healthcare facility search tool using:

- OpenStreetMap
- Nominatim
- Overpass API

The system:

1. Converts a location into coordinates
2. Searches for nearby healthcare facilities
3. Calculates distance
4. Removes duplicate facilities
5. Sorts facilities by distance
6. Returns the nearest available facilities

Supported facility types include:

- Hospitals
- Clinics
- Doctors
- Healthcare centres
- Other mapped healthcare facilities

The search currently uses a radius of approximately **10 km**.

---

### 🤝 Human Escalation

The agent can recognize situations where an AI assistant should not continue handling the conversation alone.

Instead of pretending to know the answer, it can guide the user toward human assistance.

---

### 🔄 Specialist Agent Handoff

The project supports the concept of transferring conversations to a specialist agent when a request requires more specific assistance.

This allows the system to move beyond a single general-purpose agent.

---

### 🧠 User Memory

The project includes local storage for information needed to support returning users and conversation workflows.

SQLite is used for local project data.

---

### 📊 Call Analytics

The project includes call analytics functionality for tracking conversation outcomes.

The analytics system can be used to understand information such as:

- Call/session information
- Conversation outcomes
- Escalation events
- Agent interactions
- Call performance

This makes it possible to move from simply building a voice agent to measuring how the agent performs.

---

## 🏗️ Architecture

```mermaid
flowchart LR

    A["🎙️ User"] --> B["LiveKit"]

    B --> C["Deepgram STT"]

    C --> D["Groq LLM"]

    D --> E{"Tools"}

    E --> F["📍 Healthcare Search"]
    E --> G["🧠 Memory"]
    E --> H["🤝 Human Escalation"]
    E --> I["🔄 Specialist Handoff"]

    F --> D
    G --> D
    H --> D
    I --> D

    D --> J["Murf Falcon TTS"]

    J --> B

    B --> K["🔊 User"]

    D --> L["📊 Call Analytics"]


🧩 Main Technology Stack
Component	Technology
Real-time communication	LiveKit
Speech-to-Text	Deepgram
Large Language Model	Groq
Text-to-Speech	Murf Falcon
Voice Activity Detection	Silero
Healthcare facility search	OpenStreetMap
Geocoding	Nominatim
Healthcare data search	Overpass API
Backend	Python
Frontend	Next.js / React
Local data	SQLite
📁 Project Structure
murf-livekit-starter/
│
├── backend/
│   │
│   ├── src/
│   │   ├── agent.py
│   │   ├── ...
│   │
│   ├── .env.example
│   ├── pyproject.toml
│   └── ...
│
├── frontend/
│   │
│   ├── app/
│   ├── components/
│   ├── ...
│   └── package.json
│
├── .gitignore
├── AGENTS.md
└── README.md
⚙️ Setup
Prerequisites

You need:

Python 3.10+
Node.js 18+
uv
pnpm
A LiveKit Cloud project
API keys for the services used by the agent
Install uv

For Windows PowerShell:

powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
Install pnpm
npm install -g pnpm
🔐 Environment Variables

Never commit API keys to GitHub.

Create your local environment file:

backend/.env.local

Use backend/.env.example as the template.

Example:

LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_SIP_OUTBOUND_TRUNK_ID=your_sip_trunk_id


MURF_API_KEY=your_murf_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
GROQ_API_KEY=your_groq_api_key


AGENT_NAME=my-agent

Replace the placeholder values with your own credentials.

Do not put real API keys in:

README files
GitHub source code
screenshots
blog posts
LinkedIn posts
public documentation
🐍 Backend Setup

Open PowerShell and go to the backend:

cd backend

Install dependencies:

uv sync

If required by the project, download the agent files:

uv run python src/agent.py download-files
▶️ Start the Voice Agent

From the backend directory:

uv run python src/agent.py dev

The LiveKit agent should register with your LiveKit project.

You should see logs similar to:

starting worker
plugin registered
registered worker
AgentSession started successfully
AGENT STATE: listening
🌐 Start the Frontend

Open a second terminal.

From the project root:

cd frontend

Install dependencies:

pnpm install

Start the development server:

pnpm dev

Then open:

http://localhost:3000

Allow microphone access and start a conversation with the agent.

📍 Healthcare Facility Search

The healthcare search tool uses public OpenStreetMap services.

The workflow is:

User location
      ↓
Nominatim geocoding
      ↓
Latitude / Longitude
      ↓
Overpass API
      ↓
Healthcare facilities
      ↓
Distance calculation
      ↓
Sort by nearest
      ↓
Return top facilities

The system searches multiple healthcare-related OpenStreetMap tags including:

hospital
clinic
doctors
healthcare=hospital
healthcare=clinic
healthcare=doctor
healthcare=centre

Distances are calculated using the Haversine formula.

🛡️ Healthcare Safety

This project intentionally does not position the AI as a medical professional.

The assistant should not:

❌ Diagnose diseases
❌ Prescribe medication
❌ Claim certainty about medical conditions
❌ Replace a doctor or emergency service

Instead, it should:

✅ Provide general health information
✅ Help users understand possible next steps
✅ Help users locate healthcare facilities
✅ Recognize potentially urgent situations
✅ Encourage professional medical care
✅ Escalate when appropriate
🧠 Changing the Agent Personality

The main system prompt is located in:

backend/src/agent.py

Look for:

SYSTEM_PROMPT

This controls the agent's:

Personality
Objectives
Safety rules
Conversation style
Escalation behavior

You can modify the prompt to adapt the agent for different use cases.

🎤 Voice Pipeline

The complete voice pipeline is:

User speaks
     ↓
LiveKit
     ↓
Deepgram
     ↓
Speech converted to text
     ↓
Groq LLM
     ↓
Agent reasoning + tools
     ↓
Response text
     ↓
Murf Falcon
     ↓
Generated speech
     ↓
LiveKit
     ↓
User hears response
📊 Call Analytics

The agent records information required for call analytics.

The analytics system is designed to help evaluate:

Conversation outcomes
Agent interactions
Escalations
Call/session performance

This makes it possible to analyze the voice agent after conversations instead of relying only on live interaction.

🧪 Testing

After starting both the backend and frontend:

Open the frontend.
Allow microphone access.
Connect to the agent.
Say:
Hello

Try healthcare-related requests such as:

I need help finding a clinic.
Can you find a hospital near me?
I need a doctor near Delhi.
मुझे अपने पास एक क्लिनिक ढूंढना है।

The agent should understand the request and use the appropriate workflow.

🐛 Challenges During Development

Building the project involved several real-world challenges.

API Authentication

One of the challenges was dealing with invalid API credentials and understanding which service was responsible for the failure.

For example, the voice pipeline could successfully connect to LiveKit and Deepgram while the LLM failed because of an invalid API key.

This highlighted the importance of testing each component independently.

Multilingual Voice Interaction

Getting Hindi and Hinglish conversations to feel natural required additional attention to:

Speech recognition
Language detection
Prompt instructions
Voice selection
Response style
Healthcare Facility Search

Finding nearby healthcare facilities was another challenge.

A simple LLM response is not enough when a user asks:

"Find a clinic near me."

The agent needs an actual tool capable of:

Resolving the location
Searching live geographic data
Calculating distances
Returning useful facilities

This led to the integration of OpenStreetMap, Nominatim and Overpass.

Voice Agent Debugging

Another major lesson was that a voice agent consists of multiple independent systems.

A problem can come from:

Microphone
↓
LiveKit
↓
STT
↓
LLM
↓
Tools
↓
TTS
↓
Audio output

Debugging the logs at each stage made it much easier to identify where a failure was happening.

🔒 Security

This repository intentionally does not contain production API credentials.

Before running the project, create your own environment file and add your credentials locally.

Never commit:

.env.local
.env
API keys
LiveKit secrets
SIP credentials
Caller information
Private user data
Production databases
📚 Useful Resources
Murf API Documentation
Murf Voice Library
LiveKit Documentation
Deepgram Documentation
OpenStreetMap
Nominatim
Overpass API
📝 Project Blog

This project was built as part of:

10 Days of Voice Agents — VoiceForBharat Edition

Read the complete project journey:

[Add your published Day 10 blog link here]

💻 Source Code

This repository contains the complete project source code:

https://github.com/money189singh/murf-livekit-starter

🙏 Acknowledgements

Thanks to Murf AI for the:

10 Days of Voice Agents — VoiceForBharat Edition

and for providing the opportunity to explore real-time voice AI using Murf Falcon.

📜 License

MIT License



### One important change from your old README


Your old README says:


> `clone https://github.com/murf-ai/murf-livekit-starter.git`


**Change that.** Since this is now *your* project, use:


```powershell
git clone https://github.com/money189singh/murf-livekit-starter.git
cd murf-livekit-starter
