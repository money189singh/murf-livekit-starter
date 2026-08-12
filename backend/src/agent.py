import asyncio
import logging
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
    tokenize,
    room_io,
)

from livekit.plugins import (
    murf,
    silero,
    google,
    deepgram,
    noise_cancellation,
)

from livekit.plugins.turn_detector.multilingual import MultilingualModel

from database import init_database, get_user, save_user
from facilities import find_nearest_facility
from prompt import SYSTEM_PROMPT


# ================================================================
# CONFIGURATION
# ================================================================

logger = logging.getLogger("agent")

load_dotenv(".env.local")

DATABASE_PATH = Path(__file__).parent / "health_access.db"


# ================================================================
# ESCALATION DATABASE
# ================================================================

def init_escalation_database():
    """
    Create the escalation table if it does not already exist.
    """

    connection = sqlite3.connect(DATABASE_PATH)

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


def save_escalation(
    user_id: str,
    reason: str,
    summary: str,
    urgency: str,
    language: str,
    preferred_followup: str,
):
    """
    Save a human escalation request.
    """

    reference_id = (
        f"ESC-{datetime.now().strftime('%Y%m%d')}-"
        f"{uuid.uuid4().hex[:6].upper()}"
    )

    created_at = datetime.now().isoformat(
        timespec="seconds"
    )

    connection = sqlite3.connect(DATABASE_PATH)

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
        "message": "Human assistance request created successfully.",
    }


# ================================================================
# CALL ANALYTICS DATABASE
# ================================================================

def init_analytics_database():
    """
    Create the call analytics table.
    """

    connection = sqlite3.connect(DATABASE_PATH)

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

    logger.info("Call analytics database initialized.")


def save_call_analytics(
    call_id: str,
    started_at: str,
    ended_at: str,
    outcome: str,
):
    """
    Save one completed call.
    """

    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO call_analytics (
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
# ASSISTANT
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
    # TOOL 1: LOOK UP USER MEMORY
    # ============================================================

    @function_tool
    async def lookup_user(
        self,
        context: RunContext,
    ):
        """
        Look up the current caller in the memory database.
        """

        logger.info(
            "Looking up user: %s",
            self.user_id
        )

        user = get_user(self.user_id)

        if user is None:

            return {
                "found": False,
                "message": "No previous user information was found.",
            }

        return {
            "found": True,
            "name": user["name"],
            "language_preference": user["language_preference"],
            "age_band": user["age_band"],
            "last_triage_outcome": user["last_triage_outcome"],
            "last_interaction": user["last_interaction"],
        }

    # ============================================================
    # TOOL 2: SAVE USER MEMORY
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
        """
        Save limited user memory after explicit permission.
        """

        logger.info(
            "Saving approved memory for user: %s",
            self.user_id
        )

        save_user(
            user_id=self.user_id,
            name=name,
            language_preference=language_preference,
            age_band=age_band,
            last_triage_outcome=last_triage_outcome,
        )

        return {
            "success": True,
            "message": "The approved information has been saved.",
        }

    # ============================================================
    # TOOL 3: FIND NEAREST HEALTHCARE FACILITY
    # ============================================================

    @function_tool
    async def find_healthcare_facility(
        self,
        context: RunContext,
        location: str,
    ):
        """
        Find healthcare facilities using the existing facility
        lookup system.
        """

        logger.info(
            "Healthcare facility lookup requested: %s",
            location
        )

        try:

            result = await asyncio.to_thread(
                find_nearest_facility,
                location
            )

            logger.info(
                "Healthcare facility lookup result: %s",
                result
            )

            # A successful facility lookup counts as a successful
            # call outcome.
            if result and result.get("found"):

                self.call_state["successful"] = True

            return result

        except Exception as e:

            logger.exception(
                "Healthcare facility lookup failed: %s",
                e
            )

            return {
                "found": False,
                "error": True,
                "message": (
                    "I couldn't access the healthcare facility "
                    "information right now. Please try again later."
                ),
            }

    # ============================================================
    # TOOL 4: CREATE HUMAN ESCALATION
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
        """
        Create a human-help request.

        This tool must only be called after the caller has explicitly
        given permission.
        """

        logger.info(
            "Human escalation requested. User=%s Reason=%s",
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
                "message": "This escalation reason is not supported.",
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
                        "The escalation summary contains private "
                        "information. Please remove sensitive "
                        "information before creating the request."
                    ),
                }

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

            # A successful escalation is a successful call outcome.
            self.call_state["successful"] = True

        return result


# ================================================================
# AGENT SERVER
# ================================================================

server = AgentServer()


# ================================================================
# PREWARM
# ================================================================

def prewarm(proc: JobProcess):

    proc.userdata["vad"] = silero.VAD.load()

    init_database()

    init_escalation_database()

    init_analytics_database()


server.setup_fnc = prewarm


# ================================================================
# LIVEKIT SESSION
# ================================================================

@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):

    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    user_id = ctx.room.name

    call_id = ctx.room.name

    started_at = datetime.now().isoformat(
        timespec="seconds"
    )

    # ------------------------------------------------------------
    # Per-call state
    # ------------------------------------------------------------

    call_state = {
        "user_spoke": False,
        "agent_spoke": False,
        "successful": False,
    }

    logger.info(
        "Starting session for user: %s",
        user_id
    )

    # ============================================================
    # AGENT SESSION
    # ============================================================

    session = AgentSession(

        stt=deepgram.STT(
            model="nova-3",
        ),

        llm=google.LLM(
            model="gemini-3.5-flash",
        ),

        tts=murf.TTS(
            voice="Abhinav",
            locale="hi-IN",
            style="Conversational",
            tokenizer=tokenize.basic.SentenceTokenizer(
                min_sentence_len=2
            ),
            text_pacing=True,
        ),

        turn_detection=MultilingualModel(),

        vad=ctx.proc.userdata["vad"],

        preemptive_generation=True,
    )

    # ============================================================
    # CALL ANALYTICS EVENTS
    # ============================================================

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(event):

        # Any real user speech means the call has started.
        call_state["user_spoke"] = True

    @session.on("agent_state_changed")
    def on_agent_state_changed(event):

        # Only count agent speech after the user has actually spoken.
        if (
            call_state["user_spoke"]
            and getattr(event, "new_state", None) == "speaking"
        ):
            call_state["agent_spoke"] = True

            # Receiving a response means the caller received
            # some form of assistance.
            call_state["successful"] = True

    # ============================================================
    # SAVE ANALYTICS WHEN CALL ENDS
    # ============================================================

    async def save_call_result():

        ended_at = datetime.now().isoformat(
            timespec="seconds"
        )

        if call_state["successful"]:

            outcome = "successful"

        else:

            outcome = "failed"

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

    await session.start(

        agent=Assistant(
            user_id=user_id,
            call_state=call_state,
        ),

        room=ctx.room,

        room_options=room_io.RoomOptions(

            audio_input=room_io.AudioInputOptions(

                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),

            ),
        ),
    )

    await ctx.connect()


# ================================================================
# RUN APPLICATION
# ================================================================

if __name__ == "__main__":
    cli.run_app(server)
