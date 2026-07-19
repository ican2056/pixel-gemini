"""Pixel 10 Pro Google One Gemini Offer Checker.

Single-file Replit edition. Account data stays in this process and is sent
only to the Google pages opened by Selenium.
"""

import getpass
import logging


class _Config:
    DEVICE_MODEL = "Pixel 10 Pro"
    DEVICE_BRAND = "google"
    DEVICE_MANUFACTURER = "Google"
    ANDROID_VERSION = "16"
    ANDROID_SDK = "36"
    BUILD_ID = "CP1A.260405.005"
    DEVICE_RAM_GB = 16
    DEVICE_CPU_CORES = 8
    DEVICE_MAX_TOUCH = 5
    DEVICE_GPU_VENDOR = "Imagination Technologies"
    DEVICE_GPU_RENDERER = "PowerVR DXT-48-1536"
    SCREEN_CSS_WIDTH = 412
    SCREEN_CSS_HEIGHT = 915
    SCREEN_PIXEL_RATIO = 3.5
    CHROME_VERSION = "149.0.7827.200"
    CHROME_MAJOR_VERSION = 149
    USER_AGENT_TEMPLATES = [
        (
            "Mozilla/5.0 (Linux; Android 10; K) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/{chrome} Mobile Safari/537.36"
        ),
    ]
    GMAIL_LOGIN_URL = "https://accounts.google.com/signin/v2/identifier"
    GOOGLE_ONE_URL = "https://one.google.com/"
    GOOGLE_ONE_OFFERS_URL = "https://one.google.com/about/plans"
    GEMINI_OFFER_KEYWORDS = [
        "gemini pro", "gemini advanced", "12 month", "12-month",
        "free trial", "activate", "get started", "claim offer",
        "redeem",
    ]
    WEBDRIVER_TIMEOUT = 30
    IMPLICIT_WAIT = 10
    PAGE_LOAD_TIMEOUT = 60
    HEADLESS = False


config = _Config()

"""
Android Pixel 10 Pro device simulator.

Each session gets unique identifiers (IMEI, Android ID, device fingerprint,
Chrome version patch) while the hardware identity remains "Pixel 10 Pro".

Key implementation detail:
  Chrome 110+ uses UA Reduction — the User-Agent string always shows
  "Android 10; K" regardless of real device. The actual device model
  is communicated via Sec-CH-UA-Model client hint (set via CDP).
"""

import random
import string
import uuid
from dataclasses import dataclass, field



# ── Real Google Pixel TAC prefixes (Type Allocation Code) ────────────────────
# These are genuine GSMA-registered TAC codes for Google Pixel devices.
PIXEL_TAC_PREFIXES = [
    "35272012",  # Pixel 9 Pro
    "35383711",  # Pixel 8 Pro
    "35174912",  # Pixel 7 Pro
    "35632208",  # Pixel 6a
    "35383714",  # Pixel 8
    "35272014",  # Pixel 9
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _luhn_checksum(number: str) -> int:
    digits = [int(d) for d in number]
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    total = sum(odd_digits)
    for d in even_digits:
        total += sum(divmod(d * 2, 10))
    return total % 10


def _generate_imei() -> str:
    """Generate a Luhn-valid IMEI using a real Google Pixel TAC prefix."""
    tac = random.choice(PIXEL_TAC_PREFIXES)   # 8-digit real TAC
    serial = "".join(random.choices(string.digits, k=6))
    partial = tac + serial                      # 14 digits
    check_digit = (10 - _luhn_checksum(partial + "0")) % 10
    return partial + str(check_digit)


def _generate_android_id() -> str:
    return "".join(random.choices("0123456789abcdef", k=16))


def _generate_device_fingerprint(model: str, build_id: str, android: str) -> str:
    slug = model.lower().replace(" ", "_")
    return f"google/{slug}/{slug}:{android}/{build_id}/eng.user.release-keys"


def _random_chrome_patch() -> str:
    """Return a realistic Chrome 149 version string with slight random patch."""
    major = config.CHROME_MAJOR_VERSION       # 149
    build = random.randint(7820, 7840)
    patch = random.randint(180, 220)
    return f"{major}.0.{build}.{patch}"


# ── Device profile dataclass ──────────────────────────────────────────────────

@dataclass
class DeviceProfile:
    imei:               str
    android_id:         str
    device_fingerprint: str
    user_agent:         str
    chrome_version:     str
    session_id:         str = field(default_factory=lambda: str(uuid.uuid4()))

    # Fixed Pixel 10 Pro hardware identity
    model:           str   = config.DEVICE_MODEL
    brand:           str   = config.DEVICE_BRAND
    manufacturer:    str   = config.DEVICE_MANUFACTURER
    android_version: str   = config.ANDROID_VERSION
    android_sdk:     str   = config.ANDROID_SDK
    build_id:        str   = config.BUILD_ID

    # Hardware capabilities (spoofed via CDP + JS injection)
    device_memory:          int   = 16        # 16 GB RAM (spoofed, browser API has no cap in JS)
    hardware_concurrency:   int   = 8         # Tensor G5 reported cores
    max_touch_points:       int   = 5         # realistic multitouch
    screen_width:           int   = config.SCREEN_CSS_WIDTH   # 412
    screen_height:          int   = config.SCREEN_CSS_HEIGHT  # 915
    pixel_ratio:            float = config.SCREEN_PIXEL_RATIO # 3.5
    gpu_vendor:             str   = config.DEVICE_GPU_VENDOR
    gpu_renderer:           str   = config.DEVICE_GPU_RENDERER

    def client_hints_metadata(self) -> dict:
        """
        Full userAgentMetadata dict for CDP Emulation.setUserAgentOverride.
        This is what Google reads via the Sec-CH-UA-* headers to identify
        the real device behind the reduced User-Agent string.
        """
        major = str(config.CHROME_MAJOR_VERSION)
        return {
            "brands": [
                {"brand": "Google Chrome",  "version": major},
                {"brand": "Chromium",       "version": major},
                {"brand": "Not:A-Brand",    "version": "24"},
            ],
            "fullVersionList": [
                {"brand": "Google Chrome",  "version": self.chrome_version},
                {"brand": "Chromium",       "version": self.chrome_version},
                {"brand": "Not:A-Brand",    "version": "24.0.0.0"},
            ],
            "platform":        "Android",
            "platformVersion": f"{config.ANDROID_VERSION}.0.0",
            "architecture":    "arm",
            "model":           self.model,      # "Pixel 10 Pro" — the real device hint
            "mobile":          True,
            "bitness":         "64",
            "wow64":           False,
        }

    def navigator_js(self) -> str:
        """
        JavaScript injected on every new document via CDP
        Page.addScriptToEvaluateOnNewDocument.

        Overrides all detectable browser fingerprint signals to match a real
        physical Pixel 10 Pro running Chrome 149.
        """
        gpu_vendor   = self.gpu_vendor.replace("'", "\\'")
        gpu_renderer = self.gpu_renderer.replace("'", "\\'")
        return f"""
(function () {{
  'use strict';

  // ── 1. Remove automation trace ──────────────────────────────────────────
  try {{
    const desc = Object.getOwnPropertyDescriptor(navigator, 'webdriver');
    if (desc) {{
      Object.defineProperty(navigator, 'webdriver', {{
        get: () => undefined,
        configurable: true
      }});
    }}
  }} catch (e) {{}}

  // ── 2. Platform ─────────────────────────────────────────────────────────
  try {{
    Object.defineProperty(navigator, 'platform', {{
      get: () => 'Linux armv8l',
      configurable: true
    }});
  }} catch (e) {{}}

  // ── 3. Hardware ─────────────────────────────────────────────────────────
  try {{
    Object.defineProperty(navigator, 'deviceMemory', {{
      get: () => {self.device_memory},
      configurable: true
    }});
  }} catch (e) {{}}

  try {{
    Object.defineProperty(navigator, 'hardwareConcurrency', {{
      get: () => {self.hardware_concurrency},
      configurable: true
    }});
  }} catch (e) {{}}

  try {{
    Object.defineProperty(navigator, 'maxTouchPoints', {{
      get: () => {self.max_touch_points},
      configurable: true
    }});
  }} catch (e) {{}}

  // ── 4. Touch support flags ──────────────────────────────────────────────
  try {{
    window.ontouchstart = null;
    window.ontouchmove  = null;
    window.ontouchend   = null;
    window.TouchEvent   = window.TouchEvent || function () {{}};
  }} catch (e) {{}}

  // ── 5. Vendor ───────────────────────────────────────────────────────────
  try {{
    Object.defineProperty(navigator, 'vendor', {{
      get: () => 'Google Inc.',
      configurable: true
    }});
  }} catch (e) {{}}

  // ── 6. Language ─────────────────────────────────────────────────────────
  try {{
    Object.defineProperty(navigator, 'language', {{
      get: () => 'en-US',
      configurable: true
    }});
    Object.defineProperty(navigator, 'languages', {{
      get: () => Object.freeze(['en-US', 'en']),
      configurable: true
    }});
  }} catch (e) {{}}

  // ── 7. Screen geometry ──────────────────────────────────────────────────
  try {{
    Object.defineProperty(screen, 'width',       {{ get: () => {self.screen_width},  configurable: true }});
    Object.defineProperty(screen, 'height',      {{ get: () => {self.screen_height}, configurable: true }});
    Object.defineProperty(screen, 'availWidth',  {{ get: () => {self.screen_width},  configurable: true }});
    Object.defineProperty(screen, 'availHeight', {{ get: () => {self.screen_height}, configurable: true }});
    Object.defineProperty(screen, 'colorDepth',  {{ get: () => 24, configurable: true }});
    Object.defineProperty(screen, 'pixelDepth',  {{ get: () => 24, configurable: true }});
    Object.defineProperty(window, 'devicePixelRatio', {{
      get: () => {self.pixel_ratio},
      configurable: true
    }});
    Object.defineProperty(window, 'innerWidth',  {{ get: () => {self.screen_width},  configurable: true }});
    Object.defineProperty(window, 'innerHeight', {{ get: () => {self.screen_height}, configurable: true }});
  }} catch (e) {{}}

  // ── 8. WebGL GPU fingerprint ────────────────────────────────────────────
  const patchWebGL = (Ctx) => {{
    if (!Ctx) return;
    const orig = Ctx.prototype.getParameter;
    Ctx.prototype.getParameter = function (param) {{
      if (param === 0x9245) return '{gpu_vendor}';   // UNMASKED_VENDOR_WEBGL
      if (param === 0x9246) return '{gpu_renderer}'; // UNMASKED_RENDERER_WEBGL
      if (param === 0x1F00) return '{gpu_vendor}';   // VENDOR
      if (param === 0x1F01) return '{gpu_renderer}'; // RENDERER
      return orig.call(this, param);
    }};
  }};
  try {{ patchWebGL(WebGLRenderingContext);  }} catch (e) {{}}
  try {{ patchWebGL(WebGL2RenderingContext); }} catch (e) {{}}

  // ── 9. Battery API ──────────────────────────────────────────────────────
  try {{
    const level = 0.82 + Math.random() * 0.16;
    const fakeBattery = {{
      charging: true,
      chargingTime: 0,
      dischargingTime: Infinity,
      level: level,
      addEventListener:    () => {{}},
      removeEventListener: () => {{}},
      dispatchEvent:       () => false,
    }};
    navigator.getBattery = () => Promise.resolve(fakeBattery);
  }} catch (e) {{}}

  // ── 10. Network info ────────────────────────────────────────────────────
  try {{
    const conn = {{
      effectiveType: '4g',
      downlink:      12.5,
      rtt:           45,
      saveData:      false,
      type:          'wifi',
      addEventListener:    () => {{}},
      removeEventListener: () => {{}},
    }};
    Object.defineProperty(navigator, 'connection', {{
      get: () => conn,
      configurable: true
    }});
  }} catch (e) {{}}

  // ── 11. Plugins / MimeTypes (Android Chrome has none) ──────────────────
  try {{
    Object.defineProperty(navigator, 'plugins', {{
      get: () => Object.freeze([]),
      configurable: true
    }});
    Object.defineProperty(navigator, 'mimeTypes', {{
      get: () => Object.freeze([]),
      configurable: true
    }});
  }} catch (e) {{}}

  // ── 12. Permissions (notifications always denied on Android) ───────────
  try {{
    const origQuery = navigator.permissions.query.bind(navigator.permissions);
    navigator.permissions.query = (params) => {{
      if (params && params.name === 'notifications') {{
        return Promise.resolve({{ state: 'denied', onchange: null }});
      }}
      return origQuery(params);
    }};
  }} catch (e) {{}}

  // ── 13. Chrome runtime object (present on real Chrome) ─────────────────
  try {{
    if (!window.chrome) {{
      window.chrome = {{
        runtime: {{
          connect:   () => {{}},
          sendMessage: () => {{}},
        }},
        loadTimes:  () => {{}},
        csi:        () => {{}},
      }};
    }}
  }} catch (e) {{}}

}})();
"""

    def as_headers(self) -> dict:
        return {
            "User-Agent":      self.user_agent,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
        }

    def summary(self) -> str:
        return (
            f"📱 *Device Profile*\n"
            f"Model: {self.model}  |  Build: {self.build_id}\n"
            f"Android: {self.android_version}  |  Chrome: {self.chrome_version}\n"
            f"RAM: {self.device_memory}GB  |  CPU: {self.hardware_concurrency} cores\n"
            f"Screen: {self.screen_width}×{self.screen_height} @{self.pixel_ratio}×\n"
            f"GPU: {self.gpu_renderer}\n"
            f"IMEI: `{self.imei}`\n"
            f"Android ID: `{self.android_id}`\n"
            f"Session: `{self.session_id[:8]}…`"
        )


# ── Public factory ────────────────────────────────────────────────────────────

def create_device_profile() -> DeviceProfile:
    """
    Create a fresh Pixel 10 Pro device profile with unique per-session
    identifiers and a fully spoofed hardware fingerprint.
    """
    chrome_version = _random_chrome_patch()

    # Chrome UA Reduction: device model never appears in UA string
    template   = config.USER_AGENT_TEMPLATES[0]
    user_agent = template.format(chrome=chrome_version)

    fingerprint = _generate_device_fingerprint(
        config.DEVICE_MODEL,
        config.BUILD_ID,
        config.ANDROID_VERSION,
    )
    return DeviceProfile(
        imei=_generate_imei(),
        android_id=_generate_android_id(),
        device_fingerprint=fingerprint,
        user_agent=user_agent,
        chrome_version=chrome_version,
    )

"""
Google One automation using Selenium.

Logs into a Gmail account, navigates to Google One, detects the
12-month free Gemini Pro offer, and returns the activation / payment link.

progress_callback(msg, screenshot_bytes=None) is called at every key step
so callers can display local progress.
"""

import logging
import re
import shutil
import time
from typing import Callable, Optional
from urllib.parse import urlparse

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


logger = logging.getLogger(__name__)

ProgressCB = Optional[Callable[[str, Optional[bytes]], None]]


# ── Progress reporting ──────────────────────────────────────────────────────

def _report(cb: ProgressCB, msg: str, driver: Optional[webdriver.Chrome] = None) -> None:
    """Write progress locally; no screenshots or account data are transmitted."""
    logger.info(msg)
    if cb:
        try:
            cb(msg, None)
        except Exception as exc:
            logger.warning("progress_callback error: %s", exc)


# ── Driver factory ────────────────────────────────────────────────────────────

def _build_driver(profile: DeviceProfile) -> webdriver.Chrome:
    """
    Return a visible Chrome WebDriver fully configured to impersonate a
    real Google Pixel 10 Pro running Android 16 / Chrome 149.

    Spoofing layers (applied in order):
      1. Chrome launch flags   – mobile emulation, reduced UA, anti-detection
      2. CDP commands          – authoritative screen metrics, UA client hints,
                                 touch emulation
      3. JS injection          – navigator props, WebGL GPU, battery, network,
                                 chrome runtime object, plugins
    """
    options = Options()

    if config.HEADLESS:
        options.add_argument("--headless=new")

    # ── Core stability flags ──────────────────────────────────────────────────
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--mute-audio")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-sync")
    options.add_argument("--metrics-recording-only")
    options.add_argument("--js-flags=--max-old-space-size=512")
    options.add_argument("--renderer-process-limit=1")

    # ── Realism flags (match a real Chrome on Android) ────────────────────────
    options.add_argument("--enable-features=NetworkService,NetworkServiceInProcess")
    options.add_argument("--lang=en-US")

    # ── Window size = Pixel 10 Pro CSS viewport ───────────────────────────────
    w, h = profile.screen_width, profile.screen_height
    options.add_argument(f"--window-size={w},{h}")
    options.add_argument(f"--user-agent={profile.user_agent}")

    # ── Anti-detection ────────────────────────────────────────────────────────
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # ── Chrome-level mobile emulation ─────────────────────────────────────────
    # Reduced UA: "Android 10; K" — device model intentionally absent (Chrome 110+)
    mobile_emulation = {
        "deviceMetrics": {
            "width":      w,
            "height":     h,
            "pixelRatio": profile.pixel_ratio,
            "touch":      True,
        },
        "userAgent": profile.user_agent,
    }
    options.add_experimental_option("mobileEmulation", mobile_emulation)

    # ── Launch browser ────────────────────────────────────────────────────────
    chromium_binary = shutil.which("chromium") or shutil.which("chromium-browser")
    chromedriver_binary = shutil.which("chromedriver") or "chromedriver"
    if chromium_binary:
        options.binary_location = chromium_binary
    service = Service(executable_path=chromedriver_binary)
    driver = webdriver.Chrome(service=service, options=options)

    # ── CDP layer 1: authoritative screen metrics + touch ─────────────────────
    driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
        "width":             w,
        "height":            h,
        "deviceScaleFactor": profile.pixel_ratio,
        "mobile":            True,
        "screenWidth":       w,
        "screenHeight":      h,
        "positionX":         0,
        "positionY":         0,
    })

    # ── CDP layer 2: User-Agent + full Sec-CH-UA-* client hints ──────────────
    # This is what Google reads to know the real device behind the reduced UA.
    driver.execute_cdp_cmd("Emulation.setUserAgentOverride", {
        "userAgent":         profile.user_agent,
        "acceptLanguage":    "en-US,en;q=0.9",
        "platform":          "Linux armv8l",
        "userAgentMetadata": profile.client_hints_metadata(),
    })

    # ── CDP layer 3: multitouch emulation ────────────────────────────────────
    driver.execute_cdp_cmd("Emulation.setTouchEmulationEnabled", {
        "enabled":       True,
        "maxTouchPoints": profile.max_touch_points,
    })

    # ── CDP layer 4: JS navigator/WebGL/battery/network spoofing ─────────────
    # Injected before every page's own JS runs.
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": profile.navigator_js()
    })

    driver.implicitly_wait(config.IMPLICIT_WAIT)
    driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
    return driver


# ── Helpers ───────────────────────────────────────────────────────────────────

def _wait_for(driver: webdriver.Chrome, by: str, value: str,
              timeout: int = config.WEBDRIVER_TIMEOUT):
    """Return element after waiting for it to be clickable."""
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )


def _click_element_by_inner_text(driver: webdriver.Chrome,
                                 keyword: str, tag: str = "*") -> bool:
    """Click the first visible element whose full inner text contains keyword."""
    try:
        el = driver.find_element(
            By.XPATH,
            f"//{tag}[contains(translate(., "
            f"'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"
            f", '{keyword.lower()}')]"
        )
        if el.is_displayed():
            el.click()
            return True
    except Exception:
        pass
    # JS fallback — walks every element and checks innerText
    try:
        driver.execute_script(
            """
            var kw = arguments[0].toLowerCase();
            var els = document.querySelectorAll(arguments[1]);
            for (var i = 0; i < els.length; i++) {
                if (els[i].innerText && els[i].innerText.toLowerCase().includes(kw)
                        && els[i].offsetParent !== null) {
                    els[i].click();
                    return true;
                }
            }
            return false;
            """,
            keyword.lower(), tag
        )
        return True
    except Exception:
        pass
    return False


def _enter_totp(driver: webdriver.Chrome,
                cb: ProgressCB = None) -> bool:
    """Prompt for the current six-digit code and submit it to a visible TOTP field."""
    totp_field = None
    for inp in driver.find_elements(By.CSS_SELECTOR, "input"):
        try:
            if (inp.get_attribute("aria-hidden") or "").lower() == "true":
                continue
            itype = (inp.get_attribute("type") or "").lower()
            iname = (inp.get_attribute("name") or "").lower()
            iac = (inp.get_attribute("autocomplete") or "").lower()
            if (itype in ("tel", "number") or "pin" in iname
                    or "totp" in iname or "one-time" in iac
                    or "security" in iname):
                totp_field = inp
                break
            if itype == "text" and inp.is_displayed():
                totp_field = inp
        except Exception:
            continue

    if not totp_field:
        _report(cb, "⚠️ TOTP input field not found; switching to VNC assistance.", driver)
        return False

    code = _prompt_totp_code()
    _report(cb, "🔢 Entering the supplied verification code…", driver)
    totp_field.clear()
    totp_field.send_keys(code)
    time.sleep(0.5)

    for sid in ["totpNext", "passwordNext"]:
        try:
            driver.find_element(By.ID, sid).click()
            return True
        except NoSuchElementException:
            continue
    try:
        driver.find_element(
            By.CSS_SELECTOR, 'button[type="submit"], [jsname="LgbsSe"]'
        ).click()
        return True
    except NoSuchElementException:
        return False


def _click_authenticator_option(driver: webdriver.Chrome,
                                cb: ProgressCB = None) -> bool:
    """
    Click the Authenticator app option on Google's method-selection page.

    The <li> elements have no jsaction. The real click handler is on a child
    <div> or <a> INSIDE the authenticator <li>. Strategy:
      1. Find the <li> whose innerText contains "authenticator"
      2. Look INSIDE it for any jsaction child, <a>, or <button>
      3. If none, click the first <div> child (Google wraps options in divs)
      4. Last resort: plain .click() + dispatchEvent on the <li> itself
    """
    result = driver.execute_script(
        """
        // Strategy A: data-challengetype="6" = TOTP (Google Authenticator).
        // Do NOT use data-challengeid — it is not unique and matches other options.
        var directEl = document.querySelector('[data-action="selectchallenge"][data-challengetype="6"]');
        if (directEl && directEl.offsetParent !== null) {
            directEl.click();
            return 'direct_challengetype6';
        }

        // Strategy B: find <li> whose innerText contains "authenticator",
        // then click its first child with role=link/button or any jsaction,
        // or fall back to the first <div> child (which is Google's click wrapper).
        var kw = 'authenticator';
        var targetLi = null;
        var lis = document.querySelectorAll('li');
        for (var i = 0; i < lis.length; i++) {
            var t = (lis[i].innerText || '').toLowerCase();
            if (t.includes(kw) && lis[i].offsetParent !== null) {
                targetLi = lis[i];
                break;
            }
        }
        if (!targetLi) return 'li_not_found';

        // Prefer role=link/button or any jsaction child inside the li
        var jaEl = targetLi.querySelector('[role="link"], [role="button"], [jsaction], a, button');
        if (jaEl) {
            jaEl.click();
            return 'inner_role:' + jaEl.tagName + '/' + (jaEl.getAttribute('role') || '');
        }

        // First <div> child is Google's click container
        var divEl = targetLi.querySelector('div');
        if (divEl) {
            divEl.click();
            return 'inner_div';
        }

        // Last resort: click the LI itself
        targetLi.click();
        targetLi.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));
        return 'li_click_dispatch';
        """
    )
    _report(cb, f"🔍 Authenticator click: {result}", driver)
    if result and result not in ("li_not_found",):
        return True

    # DOM fallback via Selenium ActionChains
    try:
        from selenium.webdriver.common.action_chains import ActionChains
        el = driver.find_element(
            By.XPATH,
            "//li[.//*[contains(translate(.,"
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'authenticator')]]"
        )
        ActionChains(driver).move_to_element(el).click(el).perform()
        _report(cb, "✅ Clicked Authenticator via ActionChains", driver)
        return True
    except Exception as e:
        _report(cb, f"⚠️ ActionChains fallback failed: {e}", driver)

    return False


def _click_try_another_way(driver: webdriver.Chrome) -> bool:
    """Click the 'Try another way' link/button. Returns True on success."""
    # JS innerText scan — most reliable across Google UI variants
    try:
        driver.execute_script(
            """
            var els = document.querySelectorAll('a, button, [role="button"]');
            for (var i = 0; i < els.length; i++) {
                if ((els[i].innerText || '').toLowerCase().includes('try another way')
                        && els[i].offsetParent !== null) {
                    els[i].click(); return;
                }
            }
            """
        )
        return True
    except Exception:
        pass
    # DOM fallback
    for el in driver.find_elements(By.CSS_SELECTOR, "a, button, [role='button']"):
        try:
            if "try another way" in (el.get_attribute("innerText") or el.text or "").lower() \
                    and el.is_displayed():
                el.click()
                return True
        except Exception:
            continue
    return False


def _handle_2fa(driver: webdriver.Chrome,
                cb: ProgressCB = None) -> None:
    """
    Handle any Google 2FA challenge after password submission.

    Detection is CONTENT-based, not URL-based, because Google reuses the
    /skotp URL for both the g.co/sc device code page AND the TOTP page.

    Flow:
      1. If page shows "g.co/sc"  →  click "Try another way"
      2. If page shows method list →  click "Authenticator app" option
      3. Prompt for and enter the current six-digit authenticator code
    """
    hostname = urlparse(driver.current_url).hostname or ""
    if "accounts.google.com" not in hostname:
        _report(cb, "ℹ️ Step 4/6 — No 2FA challenge, already past login", driver)
        return

    src = driver.page_source.lower()
    path = urlparse(driver.current_url).path
    _report(cb, f"🔐 Step 4/6 — Challenge page\n📍 {path}", driver)

    # ── Stage 1: g.co/sc device-code page → click "Try another way" ──────────
    if "g.co/sc" in src:
        _report(cb,
                "🔄 Step 4a — g.co/sc page detected (device browser code).\n"
                "Clicking 'Try another way' to switch to Authenticator app…",
                driver)
        clicked = _click_try_another_way(driver)
        time.sleep(2)
        src = driver.page_source.lower()
        path = urlparse(driver.current_url).path
        _report(cb,
                f"{'✅' if clicked else '⚠️'} Step 4a — "
                f"{'Navigated away from g.co/sc' if clicked else 'Try another way not found'}\n"
                f"📍 Now: {path}",
                driver)

    # ── Stage 2: Method selection page → pick Authenticator app ──────────────
    src = driver.page_source.lower()
    # Selection page = has "authenticator" in content but no TOTP code input yet
    has_authenticator_option = "authenticator" in src
    has_totp_input = any(
        kw in src for kw in ['name="pin"', 'type="tel"', 'type="number"']
    )

    if has_authenticator_option and not has_totp_input:
        _report(cb,
                "🔍 Step 4b — Method selection page.\n"
                "Selecting 'Authenticator app'…",
                driver)

        # Log the clickable items on the page to aid debugging
        try:
            items_info = driver.execute_script(
                """
                var out = [];
                var items = document.querySelectorAll('li, [role="option"], [role="listitem"]');
                for (var i = 0; i < items.length; i++) {
                    var t = (items[i].innerText || '').trim().substring(0, 80);
                    var ja = items[i].getAttribute('jsaction') || '';
                    if (t) out.push(items[i].tagName + ' ja=' + ja.substring(0,30) + ' | ' + t);
                }
                return out.join('\\n');
                """
            )
            _report(cb, f"📋 Options found:\n{items_info or '(none)'}", driver)
        except Exception:
            pass

        picked = _click_authenticator_option(driver, cb)

        if picked:
            # Wait up to 8s for the TOTP input to appear (actual page navigation)
            try:
                WebDriverWait(driver, 8).until(
                    lambda d: any(
                        (inp.get_attribute("type") or "") in ("tel", "number", "text")
                        and inp.is_displayed()
                        for inp in d.find_elements(By.CSS_SELECTOR, "input")
                        if (inp.get_attribute("aria-hidden") or "").lower() != "true"
                    )
                )
                _report(cb,
                        f"✅ Step 4b — TOTP input appeared\n"
                        f"📍 Now: {urlparse(driver.current_url).path}",
                        driver)
            except Exception:
                _report(cb,
                        f"⚠️ Step 4b — TOTP input not found after waiting\n"
                        f"📍 Now: {urlparse(driver.current_url).path}",
                        driver)
        else:
            _report(cb, "⚠️ Step 4b — Could not click Authenticator option", driver)
            time.sleep(2)

    # ── Stage 3: TOTP input page → enter the code ────────────────────────────
    time.sleep(0.5)
    _report(cb, "🔑 Step 4c — Entering authenticator TOTP code…", driver)
    submitted = _enter_totp(driver, cb)
    if submitted:
        time.sleep(3)
        _report(cb,
                f"✅ Step 4 — TOTP submitted\n📍 URL: {driver.current_url[:80]}",
                driver)
    else:
        _report(cb,
                "⚠️ Step 4 — Could not find TOTP input field.\n"
                f"📍 Current page: {urlparse(driver.current_url).path}",
                driver)


def _prompt_totp_code() -> str:
    """Read a current six-digit authenticator code without storing a TOTP secret."""
    while True:
        code = input("当前六位验证码: ").strip().replace(" ", "")
        if len(code) == 6 and code.isdigit():
            return code
        print("验证码应为六位数字，请重新输入。")


# ── Login ─────────────────────────────────────────────────────────────────────

def _manual_login_takeover(driver: webdriver.Chrome,
                           cb: ProgressCB = None) -> bool:
    """Let the user finish an unusual Google challenge through Replit VNC."""
    _report(
        cb,
        "⚠️ 自动登录仍停留在 Google 登录/验证页面。\n"
        "请打开 Replit VNC，在可见的 Chromium 中完成验证码、设备确认或其他步骤。",
        driver,
    )
    while True:
        answer = input("处理完成后按回车继续；输入 q 取消: ").strip().lower()
        if answer == "q":
            return False
        parsed = urlparse(driver.current_url)
        hostname = parsed.hostname or ""
        path = parsed.path or ""
        if not (hostname == "accounts.google.com"
                and ("signin" in path or "challenge" in path)):
            _report(cb, "✅ VNC 手动验证已完成。", driver)
            return True
        print(f"浏览器仍在验证页面: {driver.current_url[:120]}")


def _gmail_login(driver: webdriver.Chrome, email: str, password: str,
                 cb: ProgressCB = None) -> bool:
    """
    Perform Gmail login with console-assisted 2FA.
    Calls cb() with a local progress message at every key step.
    Returns True on success, False on detectable failure.
    """
    try:
        # ── Step 1: Load login page ───────────────────────────────────────────
        _report(cb, "🌐 Step 1/6 — Loading Google sign-in page…", driver)
        driver.get(config.GMAIL_LOGIN_URL)
        time.sleep(2)

        # ── Step 2: Enter email ───────────────────────────────────────────────
        _report(cb, "📧 Step 2/6 — Entering email…", driver)
        email_field = _wait_for(driver, By.CSS_SELECTOR,
                                'input[name="identifier"], input[type="email"]')
        email_field.clear()
        email_field.send_keys(email)
        _wait_for(driver, By.ID, "identifierNext").click()
        time.sleep(2)

        # ── Step 3: Enter password ────────────────────────────────────────────
        _report(cb, "🔒 Step 3/6 — Entering password…", driver)
        password_field = _wait_for(driver, By.CSS_SELECTOR,
                                   'input[type="password"]')
        password_field.clear()
        password_field.send_keys(password)
        _wait_for(driver, By.ID, "passwordNext").click()
        time.sleep(3)

        # ── Step 4: 2FA / TOTP ────────────────────────────────────────────────
        _report(cb, "🔐 Step 4/6 — Checking for 2FA challenge…", driver)
        _handle_2fa(driver, cb)

        # ── Step 5: Verify login ──────────────────────────────────────────────
        current_url = driver.current_url
        parsed = urlparse(current_url)
        hostname = parsed.hostname or ""
        path = parsed.path or ""

        if (hostname == "accounts.google.com"
                and ("signin" in path or "challenge" in path)):
            return _manual_login_takeover(driver, cb)

        # Check for visible error text
        try:
            error_el = driver.find_element(
                By.CSS_SELECTOR, '[jsname="B34EJ"], [aria-live="assertive"]'
            )
            if error_el.text.strip():
                _report(cb,
                        f"❌ Step 5/6 — Login error: {error_el.text.strip()}",
                        driver)
                return False
        except NoSuchElementException:
            pass

        if (hostname == "myaccount.google.com"
                or (hostname.endswith(".google.com") and "/u/" in path)):
            _report(cb, "✅ Step 5/6 — Logged in successfully!", driver)
            return True

        if not (hostname == "accounts.google.com"
                and path.startswith("/signin")):
            _report(cb,
                    f"✅ Step 5/6 — Login appears successful\n"
                    f"📍 URL: {current_url[:80]}",
                    driver)
            return True

        _report(cb,
                f"❌ Step 5/6 — Still on sign-in page after login\n"
                f"📍 URL: {current_url[:80]}",
                driver)
        return False

    except TimeoutException as exc:
        _report(cb, f"⏱️ Timeout during login: {exc}", driver)
        return _manual_login_takeover(driver, cb)
    except WebDriverException as exc:
        _report(cb, f"❌ WebDriver error during login: {exc}", driver)
        return False


# ── Offer detection ───────────────────────────────────────────────────────────

def _extract_payment_link(driver: webdriver.Chrome) -> Optional[str]:
    """Scan current page for a Gemini Pro offer / activation link."""
    keywords = config.GEMINI_OFFER_KEYWORDS
    url_pat = re.compile(
        r"(gemini|upgrade|activate|offer|redeem|trial|checkout)",
        re.IGNORECASE,
    )

    all_links = driver.find_elements(By.TAG_NAME, "a")

    for link in all_links:
        try:
            text = (link.text + " " + (link.get_attribute("aria-label") or "")).lower()
            href = link.get_attribute("href") or ""
            if any(kw in text for kw in keywords) and href:
                return href
        except Exception:
            continue

    for link in all_links:
        try:
            href = link.get_attribute("href") or ""
            if url_pat.search(href):
                return href
        except Exception:
            continue

    for btn in driver.find_elements(By.CSS_SELECTOR, "button, [role='button']"):
        try:
            if any(kw in btn.text.lower() for kw in keywords):
                try:
                    parent = btn.find_element(By.XPATH, "ancestor::a")
                    href = parent.get_attribute("href") or ""
                    if href:
                        return href
                except NoSuchElementException:
                    pass
                return driver.current_url
        except Exception:
            continue

    return None


def _navigate_google_one(driver: webdriver.Chrome,
                         cb: ProgressCB = None) -> Optional[str]:
    """Navigate Google One pages and return the Gemini offer link."""
    for url in (config.GOOGLE_ONE_URL, config.GOOGLE_ONE_OFFERS_URL):
        try:
            _report(cb, f"🔍 Step 6/6 — Scanning: {url}", driver)
            driver.get(url)
            time.sleep(3)

            for selector in (
                '[aria-label="Accept all"]',
                'button[jsname="higCR"]',
                '[data-action="accept"]',
            ):
                try:
                    driver.find_element(By.CSS_SELECTOR, selector).click()
                    time.sleep(1)
                    break
                except NoSuchElementException:
                    pass

            _report(cb, f"🔎 Searching page for Gemini offer links…", driver)
            link = _extract_payment_link(driver)
            if link:
                _report(cb,
                        f"🎯 Offer link found!\n🔗 {link}",
                        driver)
                return link
            else:
                _report(cb, f"😔 No offer link on {url}, trying next…", driver)

        except (TimeoutException, WebDriverException) as exc:
            _report(cb, f"⚠️ Error loading {url}: {exc}", driver)

    return None


# ── Public API ────────────────────────────────────────────────────────────────

class GoogleAutomationError(Exception):
    """Raised when automation encounters an unrecoverable error."""


def check_gemini_offer(email: str, password: str,
                       device: DeviceProfile,
                       progress_callback: ProgressCB = None) -> Optional[str]:
    """
    Main entry point.

    Logs into email/password with console-assisted 2FA, navigates to Google One,
    and returns the Gemini Pro offer link (or None).

    progress_callback(msg: str, screenshot_bytes: Optional[bytes]) can be used
    for local progress output. Screenshot bytes are always None.
    """
    driver: Optional[webdriver.Chrome] = None
    try:
        _report(progress_callback,
                f"🤖 Starting Pixel 10 Pro simulator\n"
                f"📱 Session: {device.session_id[:8]}…\n"
                f"🌐 User-Agent: {device.user_agent[:60]}…")

        driver = _build_driver(device)
        _report(progress_callback, "✅ Browser launched successfully", driver)

        logged_in = _gmail_login(
            driver, email, password,
            cb=progress_callback,
        )
        if not logged_in:
            raise GoogleAutomationError(
                "Login failed — please check your credentials."
            )

        offer_link = _navigate_google_one(driver, cb=progress_callback)
        return offer_link

    finally:
        if driver:
            try:
                _report(progress_callback, "🧹 Closing browser session…")
                driver.quit()
            except Exception:
                pass

def main() -> None:
    """Collect credentials locally and run the original offer-check flow once."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    print("Pixel 10 Pro Google One Gemini Offer Checker")
    email = input("Google email: ").strip()
    if not email:
        print("Error: Google email is required.")
        return
    password = getpass.getpass("Google password (input hidden): ")
    if not password:
        print("Error: Google password is required.")
        return

    print("Launching the visible browser, logging in, and checking the offer…")
    device = create_device_profile()
    try:
        offer_link = check_gemini_offer(
            email=email,
            password=password,
            device=device,
        )
    except GoogleAutomationError as exc:
        print(f"Error: {exc}")
        return
    except KeyboardInterrupt:
        print("\nCancelled.")
        return
    finally:
        password = ""

    if offer_link:
        print(f"Offer link: {offer_link}")
    else:
        print("No matching Google One Gemini offer was found.")


if __name__ == "__main__":
    main()
