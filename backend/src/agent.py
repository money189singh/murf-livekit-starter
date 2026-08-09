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
    inference,
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
from prompt import SYSTEM_PROMPT


logger = logging.getLogger("agent")

load_dotenv(".env.local")


class Assistant(Agent):

    def __init__(self, user_id: str) -> None:

        self.user_id = user_id

        super().__init__(
            instructions=SYSTEM_PROMPT
        )

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

        logger.info("Looking up user: %s", self.user_id)

        user = get_user(self.user_id)

        if user is None:
            logger.info("No previous memory found for user: %s", self.user_id)

            return {
                "found": False,
                "message": "No previous user information was found.",
            }

        logger.info("Returning user found: %s", user["name"])

        return {
            "found": True,
            "name": user["name"],
            "language_preference": user["language_preference"],
            "age_band": user["age_band"],
            "last_triage_outcome": user["last_triage_outcome"],
            "last_interaction": user["last_interaction"],
        }

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

        logger.info("Saving approved memory for user: %s", self.user_id)

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


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

    # Create the SQLite database/table if it doesn't exist.
    init_database()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):

    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Use the LiveKit room/participant identity as the caller ID.
    user_id = ctx.room.name

    logger.info("Starting session for user: %s", user_id)

    session = AgentSession(

        # Speech-to-text
        stt=deepgram.STT(
            model="nova-3",
        ),

        # Language model
        llm=google.LLM(
            model="gemini-3.5-flash",
        ),

        # Text-to-speech
        tts=murf.TTS(
            voice="Abhinav",
            locale="hi-IN",
            style="Conversational",
            tokenizer=tokenize.basic.SentenceTokenizer(
                min_sentence_len=2
            ),
            text_pacing=True,
        ),

        # Multilingual turn detection
        turn_detection=MultilingualModel(),

        # Voice activity detection
        vad=ctx.proc.userdata["vad"],

        # Start generating responses before the user has completely
        # finished speaking.
        preemptive_generation=True,
    )

    await session.start(
        agent=Assistant(user_id=user_id),
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


if __name__ == "__main__":
    cli.run_app(server)
