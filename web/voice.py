"""Browser-native speech-in / speech-out. No server audio code needed."""
import json
import streamlit.components.v1 as components


def speech_input(tag: str = "voice_input") -> None:
    """Renders a mic button that transcribes speech into a visible text box.

    Streamlit's iframe can't push values back into the script on its own,
    so this component writes the transcript into its own visible box and
    the user copies it. Fully browser-local — nothing is uploaded.
    """
    components.html(
        f"""
        <div style="font-family:sans-serif;padding:6px">
          <button id="mic-{tag}" style="padding:8px 14px;border-radius:8px;
            border:1px solid #888;background:#111;color:#fff;cursor:pointer">
            🎙️ Speak
          </button>
          <span id="status-{tag}" style="margin-left:10px;color:#888"></span>
          <div style="margin-top:8px">
            <input id="out-{tag}" type="text" placeholder="Transcript appears here — copy it into the question box above"
              style="width:100%;padding:8px;border:1px solid #ccc;border-radius:6px;font-size:14px" />
          </div>
        </div>
        <script>
          const btn = document.getElementById("mic-{tag}");
          const status = document.getElementById("status-{tag}");
          const out = document.getElementById("out-{tag}");
          const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
          if (!SR) {{
            btn.disabled = true;
            status.textContent = "Speech not supported in this browser (use Chrome/Edge)";
          }} else {{
            const rec = new SR();
            rec.lang = "en-US";
            rec.interimResults = false;
            btn.onclick = () => {{
              status.textContent = "listening...";
              try {{ rec.start(); }} catch (e) {{ status.textContent = "already listening"; }}
            }};
            rec.onresult = (e) => {{
              const text = e.results[0][0].transcript;
              out.value = text;
              out.select();
              status.textContent = "✓ captured";
            }};
            rec.onerror = (e) => {{ status.textContent = "error: " + e.error; }};
            rec.onend = () => {{
              if (status.textContent === "listening...") status.textContent = "";
            }};
          }}
        </script>
        """,
        height=110,
    )


def speak(text: str) -> None:
    """Speak a short summary aloud in the browser. No `key` needed."""
    safe = json.dumps(text)
    components.html(
        f"""
        <script>
          const u = new SpeechSynthesisUtterance({safe});
          u.lang = "en-US";
          speechSynthesis.speak(u);
        </script>
        """,
        height=0,
    )