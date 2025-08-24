# config.py
# Configuration and constants for Magical Texture

# Pastel color definitions (HSV)
PASTELS = {
    "pastel_cyan": (0.50, 0.30, 0.92),
    "pastel_pink": (0.92, 0.25, 0.95),
    "pastel_lavender": (0.75, 0.20, 0.90),
    "pastel_mint": (0.40, 0.25, 0.92),
    "pastel_peach": (0.08, 0.30, 0.95),
    "pastel_lemon": (0.15, 0.25, 0.95),
    "pastel_coral": (0.02, 0.35, 0.90),
    "pastel_sky": (0.55, 0.20, 0.95),
    "deep_blue": (0.65, 0.60, 0.80),  # Added deeper blue as requested
}

# User-friendly color names and descriptions
PRETTY = {
    "pastel_cyan": "Aqua Dream",
    "pastel_pink": "Soft Blossom", 
    "pastel_lavender": "Mystic Lavender",
    "pastel_mint": "Fresh Mint",
    "pastel_peach": "Warm Peach",
    "pastel_lemon": "Sunny Lemon",
    "pastel_coral": "Ocean Coral",
    "pastel_sky": "Sky Blue",
    "deep_blue": "Ocean Depths",
}

# Detailed descriptions for UI
COLOR_DESCRIPTIONS = {
    "pastel_cyan": "💧 Aqua Dream - Cool blue-green like tropical waters",
    "pastel_pink": "🌸 Soft Blossom - Gentle pink like cherry blossoms", 
    "pastel_lavender": "💜 Mystic Lavender - Light purple with magical charm",
    "pastel_mint": "🌿 Fresh Mint - Soft green like spring leaves",
    "pastel_peach": "🍑 Warm Peach - Orange-pink like sunset clouds",
    "pastel_lemon": "🍋 Sunny Lemon - Light yellow like morning sunshine",
    "pastel_coral": "🪸 Ocean Coral - Pink-orange like coral reefs",
    "pastel_sky": "☁️ Sky Blue - Light blue like clear summer sky",
    "deep_blue": "🌊 Ocean Depths - Rich deep blue like midnight waters",
}

# Effect mode descriptions for users
EFFECT_DESCRIPTIONS = {
    "Basic": "Simple, uniform color change - clean and consistent",
    "Gradient": "Smooth color transitions from center to edge with subtle highlights", 
    "Aurora": "Magical color shimmer effect like northern lights"
}

# Default UI values
DEFAULT_KEEP_VALUE = 0.7
DEFAULT_SAT_SCALE = 1.0
DEFAULT_HIGHLIGHT = 0.4
DEFAULT_AURORA_STRENGTH = 0.3
DEFAULT_RING_INNER = 0.07
DEFAULT_RING_OUTER = 0.14
DEFAULT_RING_SOFT = 0.06

# UI Settings
GALLERY_COLUMNS = 4
GALLERY_HEIGHT = 600
DEFAULT_PREFIX = "magical_eye"