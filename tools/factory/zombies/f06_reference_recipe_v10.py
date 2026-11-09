"""Original F06 art-direction values derived from the founder's visual goals.

This is a pure-Python calibration recipe: no external game textures, screenshots
or third-party pixel data are embedded. All numeric functions are testable
without Blender so reference use is measurable even in restricted environments.
"""
from math import exp


JACKET_BASE = (0.205, 0.270, 0.260)  # faded slate/teal workwear
JACKET_LINING = (0.130, 0.164, 0.154)
EARTH_TWILL = (
    (0.160, 0.174, 0.135),  # dark lichen
    (0.285, 0.289, 0.223),  # sun-faded olive
    (0.365, 0.332, 0.257),  # dusty loam
    (0.205, 0.199, 0.174),  # charcoal earth
)
OLD_DRY_DAMAGE = (0.158, 0.073, 0.063)


def localized_damage(x, z):
    """Compact damage field on ONE chest panel; no random global splatter."""
    cluster = exp(-(((x - 0.117) / 0.057) ** 2 +
                    ((z - 1.323) / 0.065) ** 2))
    secondary = 0.31 * exp(-(((x - 0.071) / 0.031) ** 2 +
                              ((z - 1.365) / 0.038) ** 2))
    return min(0.72, 0.60 * cluster + secondary)


def periorbital_tone(x, z):
    """Restrained asymmetrical bruising, not black floating eyeballs."""
    left = exp(-(((x + 0.055) / 0.033) ** 2 +
                 ((z - 1.683) / 0.019) ** 2))
    right = exp(-(((x - 0.056) / 0.029) ** 2 +
                  ((z - 1.689) / 0.018) ** 2))
    cheek = exp(-(((x + 0.076) / 0.032) ** 2 +
                  ((z - 1.627) / 0.041) ** 2))
    return max(0.65, 1.0 - 0.16 * left - 0.10 * right - 0.055 * cheek)


def palette_is_muted(colors):
    """A conservative original-material gamut guard for F11 candidates."""
    return all(len(c) == 3 and all(0 <= v <= .50 for v in c) and
               max(c) - min(c) <= .23 for c in colors)
