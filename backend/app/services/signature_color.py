"""Personal signature colour — assigned once, never changed.

Algorithm: golden-angle spiral in HSL keyed by sequential ``user_id``.
Each integer id maps to a unique hue on the continuous circle without scanning
the database. Saturation/lightness get a small deterministic jitter from
``telegram_id`` so nearby ids still look distinct after hex quantisation.
"""

from __future__ import annotations

import colorsys
import hashlib

# Golden angle in degrees — maximises angular separation for successive integers.
_GOLDEN_ANGLE = 137.50776405003785


def _u32(text: str) -> int:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")


def signature_color_for(user_id: int, telegram_id: str) -> str:
    """Return ``#RRGGBB`` unique-ish for this user; pure function, no DB."""
    hue = (max(1, int(user_id)) * _GOLDEN_ANGLE) % 360.0
    seed = _u32(f"asstylist:{telegram_id}:{user_id}")
    saturation = 0.55 + ((seed % 22) / 100.0)  # 0.55–0.76
    lightness = 0.46 + (((seed >> 8) % 14) / 100.0)  # 0.46–0.59
    r, g, b = colorsys.hls_to_rgb(hue / 360.0, lightness, saturation)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
