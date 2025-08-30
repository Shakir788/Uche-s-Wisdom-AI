import base64
import io
from PIL import Image
import re
from langdetect import detect

def process_image(uploaded_file):
    """Convert uploaded image to base64 and MIME type."""
    img = Image.open(uploaded_file)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    mime = "image/png"
    return img_str, mime

def detect_mood(text):
    """Detect mood based on input text (simple heuristic)."""
    text = text.lower()
    if any(word in text for word in ['happy', 'excited', 'great']):
        return 'happy'
    elif any(word in text for word in ['sad', 'stress', 'tired']):
        return 'sad'
    else:
        return 'neutral'

def remove_emojis(text):
    """Remove emojis from text."""
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def js_escape(text):
    """Escape text for safe use in JavaScript."""
    return text.replace('"', '\\"').replace('\n', '\\n')