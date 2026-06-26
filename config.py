"""
Configuration and constants for the Pixel 10 Pro Google One Gemini Bot.
"""

import os

# ── Telegram ──────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# ── Device specs – Google Pixel 10 Pro (Android 16) ──────────────────────────
DEVICE_MODEL        = "Pixel 10 Pro"
DEVICE_BRAND        = "google"
DEVICE_MANUFACTURER = "Google"
ANDROID_VERSION     = "16"
ANDROID_SDK         = "36"
BUILD_ID            = "BP2A.250505.001"       # Realistic Pixel 10 Pro build ID

# Hardware profile (used for navigator injection)
DEVICE_RAM_GB       = 16                      # 16 GB RAM → reports 8 via API cap
DEVICE_CPU_CORES    = 9                       # Tensor G5: 1+3+2+3 cluster = 9 cores
DEVICE_MAX_TOUCH    = 10                      # 10-point multitouch
DEVICE_GPU_VENDOR   = "Imagination Technologies"
DEVICE_GPU_RENDERER = "PowerVR Rogue DXT72"   # Tensor G5 integrated GPU

# Screen – Pixel 10 Pro: 6.3" OLED 1440×3120 @ 495 ppi
# CSS viewport at ~3.5× density
SCREEN_CSS_WIDTH    = 412
SCREEN_CSS_HEIGHT   = 917
SCREEN_PIXEL_RATIO  = 3.5

# Chrome 136 (latest stable on Android)
CHROME_VERSION       = "136.0.7103.125"
CHROME_MAJOR_VERSION = 136

# User-Agent templates (Chrome 136, Android 16, Pixel 10 Pro)
USER_AGENT_TEMPLATES = [
    (
        "Mozilla/5.0 (Linux; Android {android}; {model} Build/{build}) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/{chrome} Mobile Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Linux; Android {android}; {model} Build/{build}; wv) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Version/4.0 Chrome/{chrome} Mobile Safari/537.36"
    ),
]

# ── Google URLs ───────────────────────────────────────────────────────────────
GMAIL_LOGIN_URL      = "https://accounts.google.com/signin/v2/identifier"
GOOGLE_ONE_URL       = "https://one.google.com/"
GOOGLE_ONE_OFFERS_URL = "https://one.google.com/about/plans"

# ── Gemini offer detection keywords ──────────────────────────────────────────
GEMINI_OFFER_KEYWORDS = [
    "gemini pro",
    "gemini advanced",
    "12 month",
    "12-month",
    "free trial",
    "activate",
    "get started",
    "claim offer",
    "redeem",
]

# ── Selenium / WebDriver ──────────────────────────────────────────────────────
WEBDRIVER_TIMEOUT  = 30   # seconds – explicit wait
IMPLICIT_WAIT      = 10   # seconds
PAGE_LOAD_TIMEOUT  = 60   # seconds
HEADLESS           = True # always headless on Replit

# ── Session storage ───────────────────────────────────────────────────────────
SESSION_STORE: dict = {}

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL  = "INFO"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
