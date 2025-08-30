import os, re, base64, time
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st
import streamlit.components.v1 as components
from langdetect import detect

# ---------- MUST be first ----------
st.set_page_config(page_title="Uche's Wisdom", page_icon="💜", layout="centered")

# ---------- Custom Styles ----------
st.markdown("""
<style>
  body{background:linear-gradient(to right,#00c4cc,#feca57);color:#2c2c2c;}
  .stChatMessage{background:#fff3e0;border-radius:12px;padding:10px;margin:6px 0;}
  .stChatMessage[data-testid="stChatMessage-user"]{background:#b2ebf2;color:#2c2c2c;}
  .stChatMessage[data-testid="stChatMessage-assistant"]{background:#ffcc80;color:#2c2c2c;}
  .header{background:linear-gradient(to right,#00c4cc,#feca57);padding:20px;border-radius:10px;text-align:center;margin-bottom:10px;}
  .logo{font-size:2.0em;color:#2c2c2c;font-weight:700;font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;}
  #MainMenu{visibility:hidden;}
  footer{visibility:hidden;}
  footer:after{content:'💖 Built by Mohammad — for Inegbu Uchechukwu Jacinta, with love.';visibility:visible;display:block;text-align:center;padding:10px;font-size:14px;color:#555;}
  .sidebar .stButton>button{width:100%;margin-bottom:10px;}
  .chat-container{height:60vh;overflow-y:auto;scrollbar-width:thin;scrollbar-color:#feca57 #00c4cc;padding-right:6px;}
  .chat-container::-webkit-scrollbar{width:8px;}
  .chat-container::-webkit-scrollbar-thumb{background-color:#feca57;border-radius:4px;}
  .chat-container::-webkit-scrollbar-track{background:#00c4cc;}
  .action-row { margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# ---------- Helpers ----------
def remove_emojis(text: str) -> str:
    emoji_pattern = re.compile("[" +
        u"\U0001F600-\U0001F64F" + u"\U0001F300-\U0001F5FF" +
        u"\U0001F680-\U0001F6FF" + u"\U0001F1E0-\U0001F1FF" +
        u"\U00002500-\U00002BEF" + u"\U00002702-\U000027B0" +
        u"\U000024C2-\U0001F251" + "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r"", text)

def js_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", " ")

def process_image(file):
    b = file.getvalue()
    mime = "image/png" if file.name.lower().endswith(".png") else "image/jpeg"
    return base64.b64encode(b).decode("utf-8"), mime

def detect_mood(text):
    t = text.lower()
    if any(w in t for w in ["happy", "excited", "great"]): return "happy"
    if any(w in t for w in ["sad", "stress", "tired"]): return "sad"
    return "neutral"

def speak(text):
    safe = remove_emojis(text)
    try:
        lang = detect(text)
        lang_code = "fil-PH" if lang in ["tl", "fil"] else "en-US"
    except Exception:
        lang_code = "en-US"
    components.html(f"""
      <script>
      if ('speechSynthesis' in window){{
        const u = new SpeechSynthesisUtterance("{js_escape(safe)}");
        u.lang="{lang_code}"; u.pitch=1.05; u.rate=0.95; speechSynthesis.speak(u);
      }} else {{ alert('Speech synthesis not supported.'); }}
      </script>
    """, height=0)

# ---------- Keys / Client ----------
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    st.error("⚠️ OPENROUTER_API_KEY missing in .env file.")
    st.stop()

try:
    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
except Exception as e:
    st.error(f"OpenRouter init error: {e}")
    st.stop()

with st.expander("Debug"):
    st.write(f"API Key starts with: {api_key[:5]}…")
    st.write("OpenAI client initialized ✔️")

# ---------- Header ----------
st.markdown('<div class="header"><div class="logo">Uche`s Wisdom – shadow of Mohammad</div></div>', unsafe_allow_html=True)

# ---------- Session ----------
if "messages" not in st.session_state:
    st.session_state["messages"] = [{
        "role": "system",
        "content": (
            "You are Uche's Wisdom AI, built by Mohammad to act like him—warm, funny, and helpful. "
            "User is Inegbu Uchechukwu Jacinta (educator). Assist with lessons, mentoring, tech tips, personal advice. "
            "Casual, mohammad like tone; auto-detect language (Igbo, Yoruba, English). Mood-based style."
        )
    }]

if "tools_visible" not in st.session_state:
    st.session_state["tools_visible"] = False

# ---------- ACTION ROW (Top) - Removed image uploader, keeping voice for now
st.markdown('<div class="action-row">', unsafe_allow_html=True)
col1, col2 = st.columns([1, 1])
with col2:
    components.html("""
      <button onclick="recordAndSend()" style="padding:8px 12px;border-radius:8px;border:0;cursor:pointer;width:100%">🎤 Record Voice (5s)</button>
      <script>
      async function recordAndSend(){
        try{
          const stream = await navigator.mediaDevices.getUserMedia({audio:true});
          const rec = new MediaRecorder(stream); let chunks=[];
          rec.ondataavailable=e=>chunks.push(e.data);
          rec.onstop=()=>{ const _=new Blob(chunks,{type:'audio/webm'});
            alert('🎤 Voice recorded! (Connect to STT API to use)');
          };
          rec.start(); setTimeout(()=>rec.stop(),5000);
        }catch(err){ alert('Mic permission denied/not available.');}
      }
      </script>
    """, height=60)
st.markdown('</div>', unsafe_allow_html=True)

# ---------- CHAT HISTORY (Below Action Row) ----------
with st.container():
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for m in st.session_state["messages"]:
        if m["role"] != "system":
            with st.chat_message(m["role"]):
                st.markdown(m["content"])
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- IMAGE ANALYSIS ----------
uploaded_image = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"], key="chat_image")  # Moved here
if uploaded_image is not None:
    b64, mime = process_image(uploaded_image)
    vision_messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": "Analyze this image carefully. It might contain notes, questions, or study material. Provide a detailed, conversational summary or solution in the same language as the content, as if you’re explaining it to a friend. Add a touch of humor if appropriate."},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}
        ]
    }]
    st.session_state["messages"].append({"role": "user", "content": f"📷 {uploaded_image.name}"})
    with st.chat_message("user"):
        st.image(uploaded_image, caption="Uploaded Image", use_container_width=True)
    with st.chat_message("assistant"):
        ph = st.empty(); full = ""
        try:
            model = os.getenv("VISION_MODEL", "openai/gpt-4o-mini")
            resp = client.chat.completions.create(
                model=model,
                messages=vision_messages,
                max_tokens=1000
            )
            full = resp.choices[0].message.content
            ph.markdown(full); speak(full)
        except Exception as e:
            full = f"Sorry, image analysis failed: {e} (Model: {model})"
            ph.markdown(full)
    st.session_state["messages"].append({"role": "assistant", "content": full})

# ---------- TEXT INPUT (STICKY BOTTOM) ----------
user_input = st.chat_input("Say something to Uche's Wisdom...")
if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        ph = st.empty(); full = ""
        try:
            stream = client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=st.session_state["messages"],
                stream=True,
            )
            for chunk in stream:
                try:
                    delta = chunk.choices[0].delta
                    text = (delta.content or "") if delta else ""
                except Exception:
                    text = ""
                if text:
                    full += text
                    ph.markdown(full + "▌")
            ph.markdown(full or "_(no response)_")
            # Removed automatic speak here
        except Exception as e:
            full = f"Sorry, I hit an error: {e}"
            ph.markdown(full)
    st.session_state["messages"].append({"role": "assistant", "content": full})

# ---------- Read aloud last (Updated to be the only voice trigger) ----------
if st.button("🔊 Read Last Response"):
    if st.session_state["messages"] and st.session_state["messages"][-1]["role"] == "assistant":
        speak(st.session_state["messages"][-1]["content"])
        st.success("Playing the last response for you!")

# ---------- Sidebar: Student Tools ----------
st.sidebar.header("educator tools")
if st.sidebar.button("Show/Hide Tools"):
    st.session_state["tools_visible"] = not st.session_state["tools_visible"]

if st.session_state["tools_visible"]:
    if "timer_running" not in st.session_state:
        st.session_state.update({"timer_running": False, "timer_start": 0.0, "timer_elapsed": 0.0})

    if st.sidebar.button("Start Study Timer"):
        if not st.session_state["timer_running"]:
            st.session_state["timer_start"] = time.time()
            st.session_state["timer_running"] = True
            st.sidebar.success("Timer started! Focus on your goals, uche! 💪")
        else: st.sidebar.info("Timer is already running!")

    if st.sidebar.button("Stop Study Timer"):
        if st.session_state["timer_running"]:
            st.session_state["timer_elapsed"] += time.time() - st.session_state["timer_start"]
            st.session_state["timer_running"] = False
            m, s = divmod(int(st.session_state["timer_elapsed"]), 60)
            st.sidebar.success(f"Study time: {m} minutes and {s} seconds. Great job, uche! 🎉")
        else: st.sidebar.info("Timer is not running!")

    if "notes" not in st.session_state: st.session_state["notes"] = ""
    note_in = st.sidebar.text_area("Add a quick note", st.session_state["notes"], key="note_input")
    if st.sidebar.button("Save Note"):
        st.session_state["notes"] = note_in
        st.sidebar.success("Note saved! 📝")
    if st.session_state["notes"]: st.sidebar.write(st.session_state["notes"])

    if st.button("Need some motivation?"):
        mood = detect_mood("neutral")
        resp = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": f"Provide a short motivational quote. Mood: {mood}"}]
        )
        txt = resp.choices[0].message.content
        with st.chat_message("assistant"):
            st.markdown(txt); speak(txt)
        st.session_state["messages"].append({"role": "assistant", "content": txt})