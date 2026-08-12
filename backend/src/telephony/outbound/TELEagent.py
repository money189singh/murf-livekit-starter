import json
import logging
import os

from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    room_io,
    tokenize,
)
from livekit.plugins import (
    murf,
    silero,
    google,
    deepgram,
    noise_cancellation,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from database import init_database
from prompt import SYSTEM_PROMPT


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv(".env.local")

logger = logging.getLogger("outbound-agent")

logging.basicConfig(level=logging.INFO)


# ============================================================
# AGENT
# ============================================================

class Assistant(Agent):

    def __init__(self) -> None:

        super().__init__(
            instructions=SYSTEM_PROMPT
            + """
            
You are making an outbound healthcare support call.

At the beginning of the call:

1. Clearly introduce yourself as an AI healthcare support assistant.
2. Explain why you are calling.
3. Tell the person they can end the call whenever they want.

Be concise, friendly, respectful and helpful.

Speak naturally in Hindi when the caller speaks Hindi.

Speak English when the caller speaks English.

If the caller uses a mixture of Hindi and English, respond naturally using the same style.

Do not claim that you are a human.

Do not invent healthcare information.

Do not diagnose medical conditions.

Do not recommend prescription medicines.

If you do not know something, say so honestly.

If the caller needs professional medical help, recommend contacting an appropriate healthcare professional or emergency service.

Never pressure the caller to continue the conversation.
"""
        )


# ============================================================
# SERVER
# ============================================================

server = AgentServer()


# ============================================================
# PREWARM
# ============================================================

def prewarm(proc: JobProcess):

    proc.userdata["vad"] = silero.VAD.load()

    init_database()


server.setup_fnc = prewarm


# ============================================================
# OUTBOUND AGENT
# ============================================================

@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):

    logger.info("========================================")
    logger.info("Outbound agent starting")
    logger.info("Room: %s", ctx.room.name)
    logger.info("========================================")

    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # ========================================================
    # 1. READ DISPATCH METADATA
    # ========================================================

    try:

        metadata = ctx.job.metadata or "{}"

        logger.info(
            "Received job metadata: %s",
            metadata,
        )

        dial_info = json.loads(metadata)

    except json.JSONDecodeError:

        logger.error(
            "Invalid job metadata: %s",
            ctx.job.metadata,
        )

        return

    # Our dial.py sends:
    #
    # {
    #     "to": "money7171"
    # }

    sip_user = dial_info.get("to")

    if not sip_user:

        logger.error(
            "No SIP destination found in job metadata"
        )

        return

    logger.info(
        "Outbound destination: %s",
        sip_user,
    )

    # ========================================================
    # 2. WAIT FOR SIP PARTICIPANT
    # ========================================================

    # IMPORTANT:
    #
    # dial.py already creates the SIP participant.
    #
    # Therefore this agent should NOT create another
    # SIP participant.
    #
    # dial.py uses:
    #
    # participant_identity="linphone-user"

    sip_participant_identity = "linphone-user"

    logger.info(
        "Waiting for SIP participant: %s",
        sip_participant_identity,
    )

    try:

        participant = await ctx.wait_for_participant(
            identity=sip_participant_identity
        )

        logger.info(
            "SIP participant joined successfully: %s",
            participant.identity,
        )

    except Exception as error:

        logger.exception(
            "Could not find SIP participant: %s",
            error,
        )

        return

    # ========================================================
    # 3. CREATE AGENT SESSION
    # ========================================================

    logger.info(
        "Creating AgentSession"
    )

    session = AgentSession(

        # ----------------------------------------------------
        # Speech-to-Text
        # ----------------------------------------------------

        stt=deepgram.STT(
            model="nova-3",
        ),

        # ----------------------------------------------------
        # Language Model
        # ----------------------------------------------------

        llm=google.LLM(
            model="gemini-3.5-flash",
        ),

        # ----------------------------------------------------
        # Text-to-Speech
        # ----------------------------------------------------

        tts=murf.TTS(
            voice="Abhinav",
            locale="hi-IN",
            style="Conversational",
            tokenizer=tokenize.basic.SentenceTokenizer(
                min_sentence_len=2
            ),
            text_pacing=True,
        ),

        # ----------------------------------------------------
        # Multilingual turn detection
        # ----------------------------------------------------

        turn_detection=MultilingualModel(),

        # ----------------------------------------------------
        # Voice activity detection
        # ----------------------------------------------------

        vad=ctx.proc.userdata["vad"],

        preemptive_generation=True,
    )

    # ========================================================
    # 4. START AGENT SESSION
    # ========================================================

    logger.info(
        "Starting voice session"
    )

    await session.start(

        agent=Assistant(),

        room=ctx.room,

        room_options=room_io.RoomOptions(

            audio_input=room_io.AudioInputOptions(

                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if (
                        params.participant.kind
                        == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    )
                    else noise_cancellation.BVC()
                ),

            ),
        ),
    )

    # ========================================================
    # 5. GREET THE CALLER
    # ========================================================

    # IMPORTANT:
    #
    # session.start() only wires up the pipeline and starts
    # listening. It does NOT make the agent speak first.
    #
    # On an outbound call the callee has no reason to speak
    # first, so without this the call connects but stays
    # completely silent.

    logger.info(
        "Triggering initial greeting"
    )

    await session.generate_reply(
        instructions=(
            "Greet the caller. Introduce yourself as an AI healthcare "
            "support assistant, briefly explain why you are calling, "
            "and let them know they can end the call whenever they want."
        )
    )

    # ========================================================
    # 6. READY
    # ========================================================

    logger.info(
        "========================================"
    )

    logger.info(
        "OUTBOUND HEALTHCARE AGENT IS READY"
    )

    logger.info(
        "Caller: %s",
        sip_user,
    )

    logger.info(
        "SIP participant: %s",
        participant.identity,
    )

    logger.info(
        "========================================"
    )


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    cli.run_app(server)
