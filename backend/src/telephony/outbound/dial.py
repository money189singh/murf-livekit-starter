import argparse
import asyncio
import json
import logging
import os
import uuid

from dotenv import load_dotenv
from livekit import api


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv(".env.local")


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("outbound-dial")


# ============================================================
# CONFIGURATION
# ============================================================

TRUNK_ID = os.getenv("LIVEKIT_SIP_OUTBOUND_TRUNK_ID")

# IMPORTANT:
# This must match the agent_name set in
# telephony/outbound/agent.py's @server.rtc_session(agent_name=...)
# decorator, NOT the webpage agent's "my-agent" name. If these
# don't match, this job can get dispatched to the wrong agent
# worker (or fail to dispatch at all).
AGENT_NAME = os.getenv("OUTBOUND_AGENT_NAME", "TELEagent")


# ============================================================
# CLEAN LINPHONE DESTINATION
# ============================================================

def clean_destination(destination: str) -> str:
    """
    Convert a Linphone SIP address into the SIP username
    expected by LiveKit's SipCallTo.

    Examples:

        sip:money7171@sip.linphone.org
        money7171@sip.linphone.org
        money7171

    All become:

        money7171
    """

    destination = destination.strip()

    # Remove sip: prefix
    if destination.lower().startswith("sip:"):
        destination = destination[4:]

    # Remove everything after @
    if "@" in destination:
        destination = destination.split("@", 1)[0]

    return destination.strip()


# ============================================================
# MAKE OUTBOUND CALL
# ============================================================

async def make_call(destination: str):

    # --------------------------------------------------------
    # Check trunk
    # --------------------------------------------------------

    if not TRUNK_ID:
        raise RuntimeError(
            "LIVEKIT_SIP_OUTBOUND_TRUNK_ID is missing from .env.local"
        )

    # --------------------------------------------------------
    # Clean destination
    # --------------------------------------------------------

    sip_user = clean_destination(destination)

    if not sip_user:
        raise ValueError(
            "Invalid destination. Please provide your Linphone username."
        )

    # --------------------------------------------------------
    # Create unique room
    # --------------------------------------------------------

    room_name = f"outbound-{uuid.uuid4().hex[:12]}"

    logger.info(
        "Creating outbound call room: %s",
        room_name,
    )

    logger.info(
        "Original destination: %s",
        destination,
    )

    logger.info(
        "LiveKit SIP user: %s",
        sip_user,
    )

    # ========================================================
    # CONNECT TO LIVEKIT
    # ========================================================

    async with api.LiveKitAPI() as lkapi:

        # ====================================================
        # 1. DISPATCH AGENT
        # ====================================================

        logger.info(
            "Dispatching agent: %s",
            AGENT_NAME,
        )

        # IMPORTANT:
        # agent.py expects ctx.job.metadata to contain JSON.
        #
        # Therefore we send:
        #
        # {
        #     "to": "money7171"
        # }
        #
        # instead of simply:
        #
        # "money7171"

        metadata = json.dumps(
            {
                "to": sip_user,
            }
        )

        logger.info(
            "Agent metadata: %s",
            metadata,
        )

        try:

            await lkapi.agent_dispatch.create_dispatch(
                api.CreateAgentDispatchRequest(
                    room=room_name,
                    agent_name=AGENT_NAME,
                    metadata=metadata,
                )
            )

            logger.info(
                "Agent dispatched successfully."
            )

        except Exception as error:

            logger.exception(
                "Agent dispatch failed: %s",
                error,
            )

            raise

        # ====================================================
        # 2. CREATE SIP PARTICIPANT
        # ====================================================

        logger.info(
            "Calling Linphone user: %s",
            sip_user,
        )

        try:

            participant = await lkapi.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(

                    # Your LiveKit outbound trunk
                    sip_trunk_id=TRUNK_ID,

                    # IMPORTANT:
                    # Use the Linphone username only.
                    #
                    # Correct:
                    # money7171
                    #
                    # NOT:
                    # sip:money7171@sip.linphone.org

                    sip_call_to=sip_user,

                    # Room where the SIP participant will join
                    room_name=room_name,

                    # Identity inside LiveKit
                    participant_identity="linphone-user",

                    # Display name
                    participant_name="Healthcare Support Agent",

                    # Wait until Linphone answers
                    wait_until_answered=True,

                )
            )

            logger.info(
                "========================================"
            )

            logger.info(
                "CALL CONNECTED SUCCESSFULLY"
            )

            logger.info(
                "Participant: %s",
                participant,
            )

            logger.info(
                "========================================"
            )

        except Exception as error:

            logger.exception(
                "SIP call failed: %s",
                error,
            )

            raise


# ============================================================
# MAIN
# ============================================================

async def main():

    parser = argparse.ArgumentParser(
        description="Make an outbound LiveKit SIP call"
    )

    parser.add_argument(
        "--to",
        required=True,
        help=(
            "Linphone username, SIP user, "
            "or full SIP address"
        ),
    )

    args = parser.parse_args()

    await make_call(args.to)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())
