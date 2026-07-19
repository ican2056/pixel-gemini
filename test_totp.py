"""
Test script: verifies that the 6-digit TOTP code is entered AND that the
account is confirmed as logged in afterwards.

Run with:  python test_totp.py
"""

import getpass
import logging
import re
import sys

import google_automation
from device_simulator import create_device_profile
from google_automation import GoogleAutomationError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("test_totp")


_TOTP_IN_LOG = re.compile(r"(?i)(TOTP code:\s*`?)\d{6}(`?)")


def _redact_totp(text: str) -> str:
    """Keep the current six-digit code out of Replit logs."""
    return _TOTP_IN_LOG.sub(r"\1[REDACTED]\2", text)


class _TotpLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _redact_totp(record.getMessage())
        record.args = ()
        return True


logging.getLogger("google_automation").addFilter(_TotpLogFilter())


def _prompt_nonempty(prompt: str, *, hidden: bool = False) -> str:
    while True:
        value = (getpass.getpass(prompt) if hidden else input(prompt)).strip()
        if value:
            return value
        print("Value cannot be empty. Please try again.")


def _prompt_totp_code(_unused_secret: str) -> str:
    """Ask for the current code only when Google presents a TOTP challenge."""
    while True:
        code = getpass.getpass(
            "Current 6-digit Google Authenticator code (input hidden): "
        ).strip().replace(" ", "")
        if re.fullmatch(r"\d{6}", code):
            return code
        print("The verification code must contain exactly 6 digits.")

# ── Tracked checks ────────────────────────────────────────────────────────────
totp_code_entered  = False   # 6-digit code was typed into the field
totp_submitted     = False   # form was submitted after entering the code
account_logged_in  = False   # Google confirmed login after TOTP


def progress_callback(msg: str, screenshot_bytes=None):
    global totp_code_entered, totp_submitted, account_logged_in

    safe_msg = _redact_totp(msg)
    logger.info("STEP: %s", safe_msg)
    msg_lower = msg.lower()

    # Check 1 – 6-digit code was entered into the TOTP field
    if "entering totp code" in msg_lower or "totp code" in msg_lower:
        totp_code_entered = True

    # Check 2 – TOTP form was submitted (Google received the code)
    if "totp submitted" in msg_lower or "step 4 — totp submitted" in msg_lower:
        totp_submitted = True

    # Check 3 – Account is confirmed logged in AFTER the TOTP step
    if (
        "logged in successfully" in msg_lower
        or ("step 5" in msg_lower and "success" in msg_lower)
        or "myaccount.google.com" in msg_lower
    ):
        account_logged_in = True


def main():
    print("Pixel 10 Pro Google One Gemini Offer Test")
    email = _prompt_nonempty("Google email: ")
    password = _prompt_nonempty("Google password (input hidden): ", hidden=True)

    # Replit opens its authenticated VNC pane when Chromium creates a native
    # window. No external VNC server or additional Python package is required.
    google_automation.config.HEADLESS = False

    logger.info("=" * 60)
    logger.info("TEST: 6-digit TOTP entry + login confirmation")
    logger.info("Account credentials received from the terminal")
    logger.info("=" * 60)

    device = create_device_profile()
    logger.info("Device  : %s", device.summary().replace("\n", " | "))

    # Keep google_automation.py unchanged: replace only its code generator for
    # this console test so it asks for a current code instead of a TOTP secret.
    google_automation._generate_totp = _prompt_totp_code

    try:
        offer_link = google_automation.check_gemini_offer(
            email=email,
            password=password,
            device=device,
            # A non-empty marker enables the existing 2FA branch. The marker is
            # never used to generate a code because of the provider above.
            totp_secret="manual-terminal-code",
            progress_callback=progress_callback,
            keep_browser_open=True,
        )
    except GoogleAutomationError as exc:
        logger.error("Automation error: %s", exc)
        offer_link = None
    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        offer_link = None
    finally:
        password = ""

    # ── Print results ─────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("RESULTS")
    logger.info(
        "  1. 6-digit code entered into field : %s",
        "PASS ✅" if totp_code_entered else "FAIL ❌",
    )
    logger.info(
        "  2. TOTP form submitted to Google   : %s",
        "PASS ✅" if totp_submitted else "FAIL ❌",
    )
    logger.info(
        "  3. Account logged in after TOTP    : %s",
        "PASS ✅" if account_logged_in else "FAIL ❌",
    )
    logger.info(
        "  4. Offer link found                : %s",
        offer_link or "None (offer may not be available on this account)",
    )
    logger.info("=" * 60)

    all_passed = totp_code_entered and totp_submitted and account_logged_in

    if all_passed:
        logger.info(
            "✅ ALL CHECKS PASSED — "
            "code entered, submitted, and account confirmed logged in."
        )
        sys.exit(0)
    else:
        failed = []
        if not totp_code_entered:
            failed.append("6-digit code was never entered")
        if not totp_submitted:
            failed.append("TOTP form was not submitted")
        if not account_logged_in:
            failed.append("account login was NOT confirmed after TOTP")
        logger.error("❌ TEST FAILED — %s", "; ".join(failed))
        sys.exit(1)

if __name__ == "__main__":
    main()
