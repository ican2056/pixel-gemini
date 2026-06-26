"""
Android Pixel 10 Pro device simulator.

Each session gets unique identifiers (IMEI, Android ID, device fingerprint,
Chrome version patch) while the hardware identity remains "Pixel 10 Pro".
"""

import random
import string
import uuid
import hashlib
from dataclasses import dataclass, field

import config


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
    tac = "35" + "".join(random.choices(string.digits, k=6))
    serial = "".join(random.choices(string.digits, k=6))
    partial = tac + serial
    check_digit = (10 - _luhn_checksum(partial + "0")) % 10
    return partial + str(check_digit)


def _generate_android_id() -> str:
    return "".join(random.choices("0123456789abcdef", k=16))


def _generate_device_fingerprint(model: str, build_id: str, android: str) -> str:
    return (
        f"google/{model.lower().replace(' ', '_')}/"
        f"{model.lower().replace(' ', '_')}:{android}/"
        f"{build_id}/eng.user.release-keys"
    )


def _random_chrome_patch() -> str:
    """Return a realistic Chrome 136 version string with a slight random patch."""
    major = config.CHROME_MAJOR_VERSION
    build = random.randint(7095, 7120)
    patch = random.randint(100, 145)
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
    model:          str = config.DEVICE_MODEL
    brand:          str = config.DEVICE_BRAND
    manufacturer:   str = config.DEVICE_MANUFACTURER
    android_version:str = config.ANDROID_VERSION
    android_sdk:    str = config.ANDROID_SDK
    build_id:       str = config.BUILD_ID

    # Hardware capabilities reported via navigator / CDP
    device_memory:      int   = 8         # GB capped at 8 by browser API
    hardware_concurrency:int  = 9         # Tensor G5 CPU cores
    max_touch_points:   int   = 10
    screen_width:       int   = config.SCREEN_CSS_WIDTH
    screen_height:      int   = config.SCREEN_CSS_HEIGHT
    pixel_ratio:        float = config.SCREEN_PIXEL_RATIO
    gpu_vendor:         str   = config.DEVICE_GPU_VENDOR
    gpu_renderer:       str   = config.DEVICE_GPU_RENDERER

    def ua_brands(self) -> list[dict]:
        """Return Sec-CH-UA brands list for Chrome 136."""
        major = str(config.CHROME_MAJOR_VERSION)
        return [
            {"brand": "Chromium",      "version": major},
            {"brand": "Google Chrome", "version": major},
            {"brand": "Not.A/Brand",   "version": "99"},
        ]

    def client_hints_metadata(self) -> dict:
        """Return userAgentMetadata dict for CDP Emulation.setUserAgentOverride."""
        major = str(config.CHROME_MAJOR_VERSION)
        parts = self.chrome_version.split(".")
        return {
            "brands": self.ua_brands(),
            "fullVersionList": [
                {"brand": "Chromium",      "version": self.chrome_version},
                {"brand": "Google Chrome", "version": self.chrome_version},
                {"brand": "Not.A/Brand",   "version": "99.0.0.0"},
            ],
            "platform":        "Android",
            "platformVersion": config.ANDROID_VERSION,
            "architecture":    "arm",
            "model":           self.model,
            "mobile":          True,
            "bitness":         "64",
            "wow64":           False,
        }

    def navigator_js(self) -> str:
        """
        JavaScript snippet injected on every new document.
        Overrides navigator properties to match a real Pixel 10 Pro.
        """
        gpu_vendor   = self.gpu_vendor.replace("'", "\\'")
        gpu_renderer = self.gpu_renderer.replace("'", "\\'")
        return f"""
(function() {{
  // ── Remove webdriver trace ────────────────────────────────────────────────
  try {{
    Object.defineProperty(navigator, 'webdriver', {{
      get: () => undefined, configurable: true
    }});
  }} catch(e) {{}}

  // ── Platform ──────────────────────────────────────────────────────────────
  try {{
    Object.defineProperty(navigator, 'platform', {{
      get: () => 'Linux armv8l', configurable: true
    }});
  }} catch(e) {{}}

  // ── Hardware ──────────────────────────────────────────────────────────────
  try {{
    Object.defineProperty(navigator, 'deviceMemory', {{
      get: () => {self.device_memory}, configurable: true
    }});
  }} catch(e) {{}}

  try {{
    Object.defineProperty(navigator, 'hardwareConcurrency', {{
      get: () => {self.hardware_concurrency}, configurable: true
    }});
  }} catch(e) {{}}

  try {{
    Object.defineProperty(navigator, 'maxTouchPoints', {{
      get: () => {self.max_touch_points}, configurable: true
    }});
  }} catch(e) {{}}

  // ── Vendor ────────────────────────────────────────────────────────────────
  try {{
    Object.defineProperty(navigator, 'vendor', {{
      get: () => 'Google Inc.', configurable: true
    }});
  }} catch(e) {{}}

  // ── Languages ─────────────────────────────────────────────────────────────
  try {{
    Object.defineProperty(navigator, 'languages', {{
      get: () => ['en-US', 'en'], configurable: true
    }});
    Object.defineProperty(navigator, 'language', {{
      get: () => 'en-US', configurable: true
    }});
  }} catch(e) {{}}

  // ── Screen ────────────────────────────────────────────────────────────────
  try {{
    Object.defineProperty(screen, 'width',       {{ get: () => {self.screen_width},  configurable: true }});
    Object.defineProperty(screen, 'height',      {{ get: () => {self.screen_height}, configurable: true }});
    Object.defineProperty(screen, 'availWidth',  {{ get: () => {self.screen_width},  configurable: true }});
    Object.defineProperty(screen, 'availHeight', {{ get: () => {self.screen_height}, configurable: true }});
    Object.defineProperty(screen, 'colorDepth',  {{ get: () => 24, configurable: true }});
    Object.defineProperty(screen, 'pixelDepth',  {{ get: () => 24, configurable: true }});
    Object.defineProperty(window, 'devicePixelRatio', {{
      get: () => {self.pixel_ratio}, configurable: true
    }});
  }} catch(e) {{}}

  // ── WebGL GPU identity ────────────────────────────────────────────────────
  try {{
    const getParam = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(param) {{
      if (param === 37445) return '{gpu_vendor}';
      if (param === 37446) return '{gpu_renderer}';
      return getParam.call(this, param);
    }};
    const getParam2 = WebGL2RenderingContext.prototype.getParameter;
    WebGL2RenderingContext.prototype.getParameter = function(param) {{
      if (param === 37445) return '{gpu_vendor}';
      if (param === 37446) return '{gpu_renderer}';
      return getParam2.call(this, param);
    }};
  }} catch(e) {{}}

  // ── Battery (simulate a charged phone) ───────────────────────────────────
  try {{
    const fakeBattery = {{
      charging: true, chargingTime: 0, dischargingTime: Infinity,
      level: 0.87 + Math.random() * 0.13,
      addEventListener: () => {{}}, removeEventListener: () => {{}}
    }};
    navigator.getBattery = () => Promise.resolve(fakeBattery);
  }} catch(e) {{}}

  // ── Connection ────────────────────────────────────────────────────────────
  try {{
    Object.defineProperty(navigator, 'connection', {{
      get: () => ({{
        effectiveType: '4g', downlink: 10, rtt: 50,
        saveData: false, type: 'wifi',
        addEventListener: () => {{}}, removeEventListener: () => {{}}
      }}),
      configurable: true
    }});
  }} catch(e) {{}}

  // ── Plugins (Android Chrome has none) ────────────────────────────────────
  try {{
    Object.defineProperty(navigator, 'plugins', {{
      get: () => [], configurable: true
    }});
    Object.defineProperty(navigator, 'mimeTypes', {{
      get: () => [], configurable: true
    }});
  }} catch(e) {{}}

  // ── Permissions API ───────────────────────────────────────────────────────
  try {{
    const origQuery = navigator.permissions.query.bind(navigator.permissions);
    navigator.permissions.query = (params) => {{
      if (params.name === 'notifications') {{
        return Promise.resolve({{ state: 'denied', onchange: null }});
      }}
      return origQuery(params);
    }};
  }} catch(e) {{}}
}})();
"""

    def as_headers(self) -> dict:
        return {
            "User-Agent":     self.user_agent,
            "X-Device-Model": self.model,
            "X-Android-ID":   self.android_id,
            "Accept-Language":"en-US,en;q=0.9",
            "Accept-Encoding":"gzip, deflate, br",
        }

    def summary(self) -> str:
        return (
            f"📱 *Device Profile*\n"
            f"Model: {self.model}\n"
            f"Android: {self.android_version}  |  Chrome: {self.chrome_version}\n"
            f"RAM: {self.device_memory}GB  |  CPU cores: {self.hardware_concurrency}\n"
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
    identifiers and full hardware fingerprint.
    """
    chrome_version = _random_chrome_patch()
    template   = random.choice(config.USER_AGENT_TEMPLATES)
    user_agent = template.format(
        android=config.ANDROID_VERSION,
        model=config.DEVICE_MODEL,
        build=config.BUILD_ID,
        chrome=chrome_version,
    )
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
