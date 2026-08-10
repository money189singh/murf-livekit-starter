import asyncio
import logging

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


logger = logging.getLogger("agent")

load_dotenv(".env.local")


# ================================================================
# ASSISTANT
# ================================================================

class Assistant(Agent):

    def __init__(self, user_id: str) -> None:

        self.user_id = user_id

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

        Use this when you need to know whether this caller has
        spoken with the assistant before.
        """

        logger.info(
            "Looking up user: %s",
            self.user_id
        )

        user = get_user(self.user_id)

        if user is None:

            logger.info(
                "No previous memory found for user: %s",
                self.user_id
            )

            return {
                "found": False,
                "message": "No previous user information was found.",
            }

        logger.info(
            "Returning user found: %s",
            user["name"]
        )

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
        Save limited user memory after the user has explicitly
        given permission.

        Do NOT use this tool unless the user has clearly agreed
        that the assistant may remember the information.
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
        Find real nearby healthcare facilities using live
        OpenStreetMap data.

        Use this tool whenever the user asks for a nearby
        hospital, clinic, doctor, PHC, healthcare facility,
        emergency facility, or medical center.

        The location should be a city, neighborhood, area,
        landmark, or other place provided by the user.
        """

        logger.info(
            "Healthcare facility lookup requested for location: %s",
            location
        )

        try:

            # Run the normal blocking API request in a separate
            # thread so it does not block the LiveKit agent.
            result = await asyncio.to_thread(
                find_nearest_facility,
                location
            )

            logger.info(
                "Healthcare facility lookup result: %s",
                result
            )

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
                    "I couldn't access the live healthcare "
                    "facility information right now. "
                    "Please try again later."
                ),
            }


# ================================================================
# AGENT SERVER
# ================================================================

server = AgentServer()


# ================================================================
# PREWARM
# ================================================================

def prewarm(proc: JobProcess):

    proc.userdata["vad"] = silero.VAD.load()

    # Create the SQLite database/table if it doesn't exist.
    init_database()


server.setup_fnc = prewarm


# ================================================================
# LIVEKIT SESSION
# ================================================================

@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):

    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Use the LiveKit room/participant identity as the caller ID.
    user_id = ctx.room.name

    logger.info(
        "Starting session for user: %s",
        user_id
    )

    # ============================================================
    # AGENT SESSION
    # ============================================================

    session = AgentSession(

        # --------------------------------------------------------
        # Speech-to-text
        # --------------------------------------------------------

        stt=deepgram.STT(
            model="nova-3",
        ),

        # --------------------------------------------------------
        # Language model
        # --------------------------------------------------------

        llm=google.LLM(
            model="gemini-3.5-flash",
        ),

        # --------------------------------------------------------
        # Text-to-speech
        # --------------------------------------------------------

        tts=murf.TTS(
            voice="Abhinav",
            locale="hi-IN",
            style="Conversational",
            tokenizer=tokenize.basic.SentenceTokenizer(
                min_sentence_len=2
            ),
            text_pacing=True,
        ),

        # --------------------------------------------------------
        # Multilingual turn detection
        # --------------------------------------------------------

        turn_detection=MultilingualModel(),

        # --------------------------------------------------------
        # Voice activity detection
        # --------------------------------------------------------

        vad=ctx.proc.userdata["vad"],

        # --------------------------------------------------------
        # Start generating responses before the user has
        # completely finished speaking.
        # --------------------------------------------------------

        preemptive_generation=True,
    )

    # ============================================================
    # START SESSION
    # ============================================================

    await session.start(

        agent=Assistant(
            user_id=user_id
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

    # Connect the agent to the LiveKit room.
    await ctx.connect()


# ================================================================
# RUN APPLICATION
# ================================================================

if __name__ == "__main__":
    cli.run_app(server)
