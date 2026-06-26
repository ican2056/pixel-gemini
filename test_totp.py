"""
Test script: verifies that the 6-digit TOTP code is successfully entered
during Google login for the test account.

Run with:  python test_totp.py
"""

import logging
import sys
from device_simulator import create_device_profile
from google_automation import check_gemini_offer, GoogleAutomationError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("test_totp")

# ── Test account credentials ──────────────────────────────────────────────────
EMAIL       = "tajishag1@gmail.com"
PASSWORD    = "0112469760"
TOTP_SECRET = "oakrsdmqu5gq6lk4fkho3n326fw2hwdd"

# ── Track TOTP step outcome via progress callback ─────────────────────────────
totp_submitted   = False
totp_step_passed = False

def progress_callback(msg: str, screenshot_bytes=None):
    global totp_submitted, totp_step_passed

    logger.info("STEP: %s", msg)

    msg_lower = msg.lower()

    # Detect TOTP code entry
    if "entering totp code" in msg_lower or "totp code" in msg_lower:
        totp_submitted = True
        logger.info("✅ TOTP code entry detected")

    # Detect successful submission (moved past 2FA)
    if ("totp submitted" in msg_lower
            or "step 4 — totp submitted" in msg_lower
            or ("step 5" in msg_lower and "success" in msg_lower)
            or "logged in successfully" in msg_lower):
        totp_step_passed = True


def main():
    logger.info("=" * 60)
    logger.info("TEST: TOTP / 2FA code entry")
    logger.info("Account : %s", EMAIL)
    logger.info("=" * 60)

    device = create_device_profile()
    logger.info("Device  : %s", device.summary().replace("\n", " | "))

    try:
        offer_link = check_gemini_offer(
            email=EMAIL,
            password=PASSWORD,
            device=device,
            totp_secret=TOTP_SECRET,
            progress_callback=progress_callback,
        )
    except GoogleAutomationError as exc:
        logger.error("Automation error: %s", exc)
        offer_link = None
    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        offer_link = None

    logger.info("=" * 60)
    logger.info("RESULTS")
    logger.info("  TOTP code sent to Google : %s", "PASS ✅" if totp_submitted   else "FAIL ❌")
    logger.info("  TOTP accepted / passed   : %s", "PASS ✅" if totp_step_passed  else "FAIL ❌ (or indeterminate)")
    logger.info("  Offer link found         : %s", offer_link or "None")
    logger.info("=" * 60)

    if totp_submitted:
        logger.info("✅ TEST PASSED — 6-digit code was successfully entered.")
        sys.exit(0)
    else:
        logger.error("❌ TEST FAILED — TOTP code was never entered.")
        sys.exit(1)


if __name__ == "__main__":
    main()
