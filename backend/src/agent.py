import asyncio
import logging
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from livekit import rtc

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    inference,
    room_io,
    tokenize,
)

from livekit.plugins import (
    deepgram,
    groq,
    murf,
    noise_cancellation,
    silero,
)

from database import (
    init_database,
    get_user,
    save_user,
)

from facilities import find_nearest_facility
from prompt import SYSTEM_PROMPT


# ================================================================
# CONFIGURATION
# ================================================================

logger = logging.getLogger("agent")

# agent.py is inside:
# backend/src/agent.py
#
# Therefore .env.local is:
# backend/.env.local

ENV_FILE = Path(__file__).resolve().parent.parent / ".env.local"

load_dotenv(ENV_FILE)

DATABASE_PATH = Path(__file__).parent / "health_access.db"


# ================================================================
# API KEYS
# ================================================================

LIVEKIT_URL = os.getenv("LIVEKIT_URL")

LIVEKIT_API_KEY = os.getenv(
    "LIVEKIT_API_KEY"
)

LIVEKIT_API_SECRET = os.getenv(
    "LIVEKIT_API_SECRET"
)

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

DEEPGRAM_API_KEY = os.getenv(
    "DEEPGRAM_API_KEY"
)

MURF_API_KEY = os.getenv(
    "MURF_API_KEY"
)

AGENT_NAME = os.getenv(
    "AGENT_NAME",
    "my-agent",
)


# ================================================================
# ENVIRONMENT VALIDATION
# ================================================================

def validate_environment():

    logger.info(
        "Checking environment variables..."
    )

    missing = []

    if not LIVEKIT_URL:
        missing.append("LIVEKIT_URL")

    if not LIVEKIT_API_KEY:
        missing.append("LIVEKIT_API_KEY")

    if not LIVEKIT_API_SECRET:
        missing.append("LIVEKIT_API_SECRET")

    if not GROQ_API_KEY:
        missing.append("GROQ_API_KEY")

    if not DEEPGRAM_API_KEY:
        missing.append("DEEPGRAM_API_KEY")

    if not MURF_API_KEY:
        missing.append("MURF_API_KEY")

    if missing:

        raise RuntimeError(
            "Missing environment variables: "
            + ", ".join(missing)
        )

    logger.info(
        "Environment variables loaded successfully."
    )

    logger.info(
        "LiveKit URL: %s",
        LIVEKIT_URL,
    )

    logger.info(
        "Groq API key loaded: %s...",
        GROQ_API_KEY[:8],
    )

    logger.info(
        "Deepgram API key loaded: %s...",
        DEEPGRAM_API_KEY[:8],
    )

    logger.info(
        "Murf API key loaded: %s...",
        MURF_API_KEY[:8],
    )


# ================================================================
# ESCALATION DATABASE
# ================================================================

def init_escalation_database():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS escalations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference_id TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            summary TEXT NOT NULL,
            urgency TEXT NOT NULL,
            language TEXT,
            preferred_followup TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL
        )
        """
    )

    connection.commit()

    connection.close()

    logger.info(
        "Escalation database initialized."
    )


def save_escalation(
    user_id: str,
    reason: str,
    summary: str,
    urgency: str,
    language: str,
    preferred_followup: str,
):

    reference_id = (
        f"ESC-{datetime.now().strftime('%Y%m%d')}-"
        f"{uuid.uuid4().hex[:6].upper()}"
    )

    created_at = datetime.now().isoformat(
        timespec="seconds"
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO escalations (
            reference_id,
            user_id,
            reason,
            summary,
            urgency,
            language,
            preferred_followup,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            reference_id,
            user_id,
            reason,
            summary,
            urgency,
            language,
            preferred_followup,
            "open",
            created_at,
        ),
    )

    connection.commit()

    connection.close()

    return {
        "success": True,
        "reference_id": reference_id,
        "status": "open",
        "message": (
            "Human assistance request "
            "created successfully."
        ),
    }


# ================================================================
# CALL ANALYTICS DATABASE
# ================================================================

def init_analytics_database():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS call_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT UNIQUE NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT NOT NULL,
            outcome TEXT NOT NULL
        )
        """
    )

    connection.commit()

    connection.close()

    logger.info(
        "Call analytics database initialized."
    )


def save_call_analytics(
    call_id: str,
    started_at: str,
    ended_at: str,
    outcome: str,
):

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO call_analytics (
            call_id,
            started_at,
            ended_at,
            outcome
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            call_id,
            started_at,
            ended_at,
            outcome,
        ),
    )

    connection.commit()

    connection.close()

    logger.info(
        "Call analytics saved: %s -> %s",
        call_id,
        outcome,
    )


# ================================================================
# CLINIC & APPOINTMENT SPECIALIST
# ================================================================

class ClinicAppointmentSpecialist(Agent):

    def __init__(
        self,
        user_id: str,
        call_state: dict,
        chat_ctx=None,
    ) -> None:

        self.user_id = user_id

        self.call_state = call_state

        super().__init__(
            instructions="""
You are the Clinic and Appointment Specialist
for the Health Access voice assistant.

Your job is focused and limited.

You help users:

- Find nearby healthcare facilities.
- Understand general clinic or hospital access.
- Understand what information they may need when
  contacting a clinic.
- Understand general appointment preparation.
- Help users navigate healthcare access.

You are NOT a doctor, nurse, pharmacist,
or medical professional.

You MUST NOT:

- Diagnose medical conditions.
- Prescribe medicines.
- Recommend prescription medicines.
- Give personalized medication dosages.
- Create treatment plans.
- Interpret medical tests as a diagnosis.
- Claim that you contacted a clinic.
- Claim that you booked an appointment unless
  a real booking system confirms it.

If the user describes potentially serious emergency
symptoms, do not spend time on appointment planning.
Tell them to seek urgent professional medical attention.

Use the healthcare facility lookup tool when the user
asks for a nearby hospital, clinic, PHC, healthcare
facility, or medical center.

Language:

- Match the user's language.
- Support English, Hindi, and Hinglish.
- Use natural Indian conversational language.
- Do not use overly formal Hindi.

Voice style:

- Be concise.
- Ask one question at a time.
- Be friendly and practical.
- Do not repeat information the user already provided.

The user has already been speaking with the main
Health Access Assistant.

Continue naturally from the existing conversation.

When you take over, briefly introduce yourself and
acknowledge the reason for the handoff.
""",
            chat_ctx=chat_ctx,
        )

    async def on_enter(self):

        logger.info(
            "Clinic Appointment Specialist entered."
        )

        await self.session.generate_reply(
            instructions=(
                "Introduce yourself briefly as the Clinic "
                "and Appointment Specialist. Acknowledge "
                "the user's clinic or appointment request "
                "and continue helping."
            )
        )

    @function_tool
    async def find_healthcare_facility(
        self,
        context: RunContext,
        location: str,
    ):

        logger.info(
            "Specialist facility lookup: %s",
            location,
        )

        try:

            result = await asyncio.to_thread(
                find_nearest_facility,
                location,
            )

            logger.info(
                "Specialist facility result: %s",
                result,
            )

            if result and result.get("found"):

                self.call_state[
                    "successful"
                ] = True

            return result

        except Exception as e:

            logger.exception(
                "Specialist facility lookup failed: %s",
                e,
            )

            return {
                "found": False,
                "error": True,
                "message": (
                    "I couldn't access the healthcare "
                    "facility information right now. "
                    "Please try again later."
                ),
            }


# ================================================================
# MAIN HEALTH ACCESS ASSISTANT
# ================================================================

class Assistant(Agent):

    def __init__(
        self,
        user_id: str,
        call_state: dict,
    ) -> None:

        self.user_id = user_id

        self.call_state = call_state

        super().__init__(
            instructions=SYSTEM_PROMPT
        )

    # ============================================================
    # USER MEMORY
    # ============================================================

    @function_tool
    async def lookup_user(
        self,
        context: RunContext,
    ):

        logger.info(
            "Looking up user: %s",
            self.user_id,
        )

        try:

            user = get_user(
                self.user_id
            )

            if user is None:

                return {
                    "found": False,
                    "message": (
                        "No previous user information "
                        "was found."
                    ),
                }

            return {
                "found": True,
                "name": user["name"],
                "language_preference": (
                    user["language_preference"]
                ),
                "age_band": user["age_band"],
                "last_triage_outcome": (
                    user["last_triage_outcome"]
                ),
                "last_interaction": (
                    user["last_interaction"]
                ),
            }

        except Exception:

            logger.exception(
                "User lookup failed."
            )

            return {
                "found": False,
                "error": True,
                "message": (
                    "Unable to access user memory."
                ),
            }

    # ============================================================
    # SAVE USER MEMORY
    # ============================================================

    @function_tool
    async def save_user_memory(
        self,
        context: RunContext,
        name: str | None = None,
        language_preference: str | None = None,
        age_band: str | None = None,
        last_triage_outcome: str | None = None,
    ):

        logger.info(
            "Saving approved memory for user: %s",
            self.user_id,
        )

        try:

            save_user(
                user_id=self.user_id,
                name=name,
                language_preference=language_preference,
                age_band=age_band,
                last_triage_outcome=last_triage_outcome,
            )

            return {
                "success": True,
                "message": (
                    "The approved information "
                    "has been saved."
                ),
            }

        except Exception:

            logger.exception(
                "Saving user memory failed."
            )

            return {
                "success": False,
                "message": (
                    "Unable to save the approved "
                    "information."
                ),
            }

    # ============================================================
    # FIND HEALTHCARE FACILITY
    # ============================================================

    @function_tool
    async def find_healthcare_facility(
        self,
        context: RunContext,
        location: str,
    ):

        logger.info(
            "Healthcare facility lookup requested: %s",
            location,
        )

        try:

            result = await asyncio.to_thread(
                find_nearest_facility,
                location,
            )

            logger.info(
                "Healthcare facility lookup result: %s",
                result,
            )

            if result and result.get("found"):

                self.call_state[
                    "successful"
                ] = True

            return result

        except Exception:

            logger.exception(
                "Healthcare facility lookup failed."
            )

            return {
                "found": False,
                "error": True,
                "message": (
                    "I couldn't access the healthcare "
                    "facility information right now. "
                    "Please try again later."
                ),
            }

    # ============================================================
    # HUMAN ESCALATION
    # ============================================================

    @function_tool
    async def create_human_escalation(
        self,
        context: RunContext,
        reason: str,
        summary: str,
        urgency: str,
        language: str,
        preferred_followup: str,
    ):

        logger.info(
            "Human escalation requested. "
            "User=%s Reason=%s",
            self.user_id,
            reason,
        )

        allowed_reasons = {
            "red_flag_symptom",
            "diagnosis_request",
        }

        if reason not in allowed_reasons:

            return {
                "success": False,
                "message": (
                    "This escalation reason "
                    "is not supported."
                ),
            }

        allowed_urgency = {
            "low",
            "medium",
            "high",
            "emergency",
        }

        if urgency not in allowed_urgency:

            urgency = "medium"

        sensitive_terms = [
            "password",
            "otp",
            "one time password",
            "pin",
            "account number",
            "card number",
            "cvv",
            "credit card",
            "debit card",
        ]

        summary_lower = summary.lower()

        for term in sensitive_terms:

            if term in summary_lower:

                return {
                    "success": False,
                    "message": (
                        "The escalation summary contains "
                        "private information. Please remove "
                        "sensitive information before "
                        "creating the request."
                    ),
                }

        try:

            result = await asyncio.to_thread(
                save_escalation,
                self.user_id,
                reason,
                summary,
                urgency,
                language,
                preferred_followup,
            )

            if result.get("success"):

                self.call_state[
                    "successful"
                ] = True

            return result

        except Exception:

            logger.exception(
                "Escalation creation failed."
            )

            return {
                "success": False,
                "message": (
                    "Unable to create the human "
                    "assistance request."
                ),
            }

    # ============================================================
    # HANDOFF
    # ============================================================

    @function_tool
    async def handoff_to_clinic_specialist(
        self,
        context: RunContext,
    ):

        logger.info(
            "Handing off user %s to Clinic "
            "Appointment Specialist",
            self.user_id,
        )

        chat_ctx = self.chat_ctx.copy(
            exclude_instructions=True
        )

        specialist = ClinicAppointmentSpecialist(
            user_id=self.user_id,
            call_state=self.call_state,
            chat_ctx=chat_ctx,
        )

        return (
            specialist,
            (
                "Transferring you to the Clinic "
                "and Appointment Specialist."
            ),
        )


# ================================================================
# AGENT SERVER
# ================================================================

server = AgentServer()


# ================================================================
# PREWARM
# ================================================================

def prewarm(
    proc: JobProcess
):

    logger.info(
        "Prewarming agent process..."
    )

    proc.userdata["vad"] = (
        silero.VAD.load()
    )

    init_database()

    init_escalation_database()

    init_analytics_database()

    logger.info(
        "Prewarm completed."
    )


server.setup_fnc = prewarm


# ================================================================
# LIVEKIT SESSION
# ================================================================

@server.rtc_session(
    agent_name=AGENT_NAME
)
async def my_agent(
    ctx: JobContext
):

    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    user_id = ctx.room.name

    call_id = ctx.room.name

    started_at = datetime.now().isoformat(
        timespec="seconds"
    )

    # ============================================================
    # CALL STATE
    # ============================================================

    call_state = {
        "user_spoke": False,
        "agent_spoke": False,
        "successful": False,
    }

    logger.info(
        "=================================================="
    )

    logger.info(
        "STARTING HEALTH ACCESS SESSION"
    )

    logger.info(
        "Room: %s",
        ctx.room.name,
    )

    logger.info(
        "=================================================="
    )

    # ============================================================
    # AGENT SESSION
    # ============================================================

    session = AgentSession(

        # ========================================================
        # DEEPGRAM STT
        # ========================================================

        stt=deepgram.STT(
            model="nova-3",
            api_key=DEEPGRAM_API_KEY,
        ),

        # ========================================================
        # GROQ LLM
        # ========================================================

        llm=groq.LLM(
            model="llama-3.3-70b-versatile",
            api_key=GROQ_API_KEY,
            temperature=0.3,
            max_retries=2,
        ),

        # ========================================================
        # MURF TTS
        # ========================================================

        tts=murf.TTS(
            api_key=MURF_API_KEY,
            voice="Abhinav",
            locale="hi-IN",
            style="Conversational",
            tokenizer=tokenize.basic.SentenceTokenizer(
                min_sentence_len=2,
            ),
            text_pacing=True,
        ),

        # ========================================================
        # LIVEKIT TURN DETECTOR
        # ========================================================

        turn_detection=inference.TurnDetector(
            version="v1-mini"
        ),

        # ========================================================
        # VAD
        # ========================================================

        vad=ctx.proc.userdata["vad"],

        # ========================================================
        # PREEMPTIVE GENERATION
        # ========================================================

        preemptive_generation=True,
    )

    # ============================================================
    # SESSION EVENTS
    # ============================================================

    @session.on(
        "user_input_transcribed"
    )
    def on_user_input_transcribed(
        event
    ):

        call_state[
            "user_spoke"
        ] = True

        logger.info(
            "USER INPUT RECEIVED: %s",
            getattr(
                event,
                "transcript",
                "",
            ),
        )

    @session.on(
        "agent_state_changed"
    )
    def on_agent_state_changed(
        event
    ):

        new_state = getattr(
            event,
            "new_state",
            None,
        )

        logger.info(
            "AGENT STATE: %s",
            new_state,
        )

        if (
            call_state["user_spoke"]
            and new_state == "speaking"
        ):

            call_state[
                "agent_spoke"
            ] = True

            call_state[
                "successful"
            ] = True

    @session.on(
        "error"
    )
    def on_session_error(
        event
    ):

        logger.error(
            "AGENT SESSION ERROR: %s",
            event,
        )

    @session.on(
        "close"
    )
    def on_session_close(
        event
    ):

        logger.info(
            "AGENT SESSION CLOSED: %s",
            event,
        )

    # ============================================================
    # SAVE ANALYTICS
    # ============================================================

    async def save_call_result():

        ended_at = datetime.now().isoformat(
            timespec="seconds"
        )

        outcome = (
            "successful"
            if call_state["successful"]
            else "failed"
        )

        try:

            await asyncio.to_thread(
                save_call_analytics,
                call_id,
                started_at,
                ended_at,
                outcome,
            )

            logger.info(
                "Call completed: %s -> %s",
                call_id,
                outcome,
            )

        except Exception:

            logger.exception(
                "Failed to save call analytics."
            )

    ctx.add_shutdown_callback(
        save_call_result
    )

    # ============================================================
    # START SESSION
    # ============================================================

    logger.info(
        "Starting AgentSession..."
    )

    await session.start(

        agent=Assistant(
            user_id=user_id,
            call_state=call_state,
        ),

        room=ctx.room,

        room_options=room_io.RoomOptions(

            audio_input=(
                room_io.AudioInputOptions(

                    noise_cancellation=(
                        lambda params: (
                            noise_cancellation.BVCTelephony()
                            if (
                                params.participant.kind
                                == rtc.ParticipantKind
                                .PARTICIPANT_KIND_SIP
                            )
                            else noise_cancellation.BVC()
                        )
                    ),

                )
            ),

        ),
    )

    logger.info(
        "AgentSession started successfully."
    )

    # ============================================================
    # INITIAL GREETING
    # ============================================================

    logger.info(
        "Generating initial greeting..."
    )

    try:

        await session.generate_reply(
            instructions=(
                "Greet the user briefly. Say that you "
                "are the Health Access Assistant and "
                "ask how you can help. Use natural "
                "Indian English or Hindi/Hinglish. "
                "Keep it short because this is a "
                "voice conversation."
            )
        )

        logger.info(
            "Initial greeting generated."
        )

    except Exception:

        logger.exception(
            "Initial greeting failed."
        )


# ================================================================
# RUN APPLICATION
# ================================================================

if __name__ == "__main__":

    logger.info(
        "Starting Health Access Agent..."
    )

    validate_environment()

    cli.run_app(
        server
    )
