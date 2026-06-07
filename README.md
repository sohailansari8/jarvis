<p align="center">
  <img src="assets/banner.png" alt="JARVIS AI Desktop Assistant" width="100%"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white"/>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/UI-PyQt5-41CD52?style=for-the-badge&logo=qt&logoColor=white"/>
  <img src="https://img.shields.io/badge/AI-Gemini%20%7C%20GPT--4o%20%7C%20Groq%20%7C%20Ollama-FF6B35?style=for-the-badge&logo=googlegemini&logoColor=white"/>
  
</p>

<h1 align="center">J.A.R.V.I.S — AI Desktop Assistant</h1>

<p align="center">
  <b>Just A Rather Very Intelligent System</b><br/>
  A fully-featured, voice-activated AI desktop assistant for Windows — powered by Gemini, GPT-4o, Groq, or a fully local Ollama model.
</p>

---

## ✨ What JARVIS Can Do

### 🎙️ Voice & Text Input
| Feature | How to Trigger |
|---|---|
| Wake word activation | Say **"Hey Jarvis"** — always listening in background |
| Voice command | Click **Speak** button or press `Ctrl+Q` |
| Text command | Type in the chat box and press `Enter` |
| Conversational memory | References like *"open the first one"*, *"run it"* are understood from context |

---

### 🤖 AI Reasoning (Multi-Provider)
JARVIS routes every command through a powerful AI brain before falling back to keyword handlers.

| Provider | Speed | Cost | Vision |
|---|---|---|---|
| **Google Gemini 2.0 Flash** | ⚡ Very Fast | Free tier | ✅ Yes |
| **OpenAI GPT-4o / GPT-4o-mini** | Fast | Paid | ✅ Yes |
| **Groq (Llama 3.3 70B)** | ⚡⚡ Ultra Fast | Free tier | ❌ |
| **Ollama (local)** | Depends on hardware | Free / offline | ❌ |

Switch between providers at any time from the **⚙ Settings** panel — no restart needed.

---

### 👁️ Screen Vision
JARVIS can **see your screen** and reason about it:

- *"What is on my screen right now?"*
- *"Describe what you see"*
- *"What application is open?"*
- *"Read the text on screen"*
- *"What is happening on the screen?"*

Screenshots are automatically captured and sent to the AI when vision-triggering phrases are detected.

---

### 🌐 Web & Browser Control
```
"Open YouTube"              → Opens youtube.com
"Open Google / Reddit / GitHub / Netflix ..."
"Search for Python tutorials"
"Play [song name] on YouTube"    → Searches + auto-plays first result
"Play the 4th video"             → Clicks the 4th result on current page
"Play the second video"          → Ordinal words understood (first–tenth)
"Pause / resume YouTube"
"Next video" / "Previous video"
"Fullscreen" / "Mute"
"Skip 10 seconds"
"Volume up / down"
```

---

### 🖥️ App Control
```
"Open Notepad / Chrome / Edge / Calculator / Paint / Word / Excel ..."
"Close Chrome"
"Open [any app name]"   → Uses Windows Search as universal fallback
"Start [app]"
```

---

### 📁 File System
```
"List Python files on my Desktop"
"Open C:/Users/sohail/Documents/report.pdf"
"Find all .txt files in Downloads"
"Run the first file"    → Context-aware, remembers the list
```

---

### 🖱️ Desktop Automation
```
"Click at 500 300"          → Click screen coordinates
"Click the Submit button"   → OCR-powered text finding & clicking
"Type Hello World"          → Types text into active window
"Press Ctrl+C"
"Scroll down 3"
"Minimize / Maximize window"
"Switch window"  (Alt+Tab)
"Show desktop"
"Lock screen"
"Copy / Paste"
```

---

### 🎵 Media & Volume
```
"Play music"              → Plays random track from ~/Music
"Stop music / Pause music"
"Volume up / Volume down"
"Mute / Unmute"
"Next track / Previous track"
```

---

### 💻 System Information
```
"System stats"     → CPU %, RAM %, Battery %
"Battery status"
"CPU usage"
"Memory usage"
```

---

### 📋 Clipboard
```
"Read clipboard"           → Reads & speaks clipboard content
"Copy [text] to clipboard"
"Paste"
```

---

### 🔧 Shell Commands
```
"Run [shell command]"    → Executes in cmd, output fed back to AI
```
*Example: "Run dir Desktop" → Jarvis lists files and can then open one*

---

### 💬 Knowledge & Conversation
```
"What time is it?"
"What's today's date?"
"Search Wikipedia for [topic]"
"Tell me a joke"
"What's the weather?"    → Live weather from wttr.in
"Hello / How are you / Who are you"
```

---

### 📸 Screenshots
```
"Take a screenshot"     → Saves PNG + feeds image to AI for description
"What's on my screen?"  → Auto-captures and describes with AI vision
```

---

## 🏗️ Project Structure

```
jarvis/
├── main.py                  # Entry point (PyQt5 UI)
├── run_jarvis.bat           # One-click Windows launcher
├── requirements.txt         # All Python dependencies
├── .env                     # 🔒 Your API keys (never committed)
├── .env.example             # Template — safe to commit
├── .gitignore
│
├── core/
│   ├── ai_brain.py          # Multi-provider AI engine (Gemini/OpenAI/Groq/Ollama)
│   ├── config.py            # Settings persistence
│   ├── context_manager.py   # Conversation memory & saved outputs
│   ├── speech_engine.py     # TTS (edge-tts + pygame fallback)
│   └── state_machine.py     # Listening / processing states
│
├── handlers/
│   ├── command_router.py    # AI-first dispatcher, keyword fallback
│   ├── ai_executor.py       # Executes structured AI action dicts
│   ├── web_handler.py       # Browser, YouTube, search
│   ├── system_handler.py    # App open/close, stats, screenshots
│   ├── media_handler.py     # Music, volume, media keys
│   └── ocr_handler.py       # Tesseract OCR — find & click text on screen
│
├── ui/
│   ├── main_window.py       # Main PyQt5 glassmorphism UI
│   ├── settings_dialog.py   # Settings panel (API keys, provider, voice)
│   ├── status_dashboard.py  # Live system stats widget
│   └── glass_widgets.py     # Custom translucent UI components
│
└── screenshots/             # Saved by Jarvis (git-ignored)
```

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/your-username/jarvis.git
cd jarvis
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up your API key
```bash
# Copy the template
copy .env.example .env

# Open .env and fill in your key:
# GEMINI_API_KEY=AIzaSy...
```
> **Free Gemini key** → [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

### 4. Run JARVIS
```bash
# Option A — double-click:
run_jarvis.bat

# Option B — terminal:
python main.py
```

---

## ⚙️ Configuration

All settings are available in the **⚙ Settings** panel inside the app:

| Setting | Description |
|---|---|
| AI Provider | Switch between Gemini / OpenAI / Groq / Ollama |
| API Keys | Enter and save provider keys securely |
| AI Model | Choose specific model per provider |
| Screen Vision | Enable/disable screenshot attachment |
| Vision Always | Send screenshot with every query |
| Voice | TTS voice, speed, volume |
| Wake Word | Toggle always-on "Hey Jarvis" listener |

---

## 📦 Dependencies

```
PyQt5           — Modern GUI framework
SpeechRecognition — Microphone voice input (Google STT)
edge-tts        — High-quality Microsoft neural TTS
pygame          — Audio playback for TTS
google-genai    — Google Gemini AI
openai          — OpenAI + Groq (same SDK)
pyautogui       — Desktop automation
Pillow          — Image processing & screenshots
pytesseract     — OCR (optional — needs Tesseract binary)
psutil          — System statistics
pyperclip       — Clipboard access
wikipedia       — Wikipedia search
pyjokes         — Joke generator
requests        — HTTP requests & weather
```

### Optional: Tesseract OCR (for click-by-text)
Download from: https://github.com/UB-Mannheim/tesseract/wiki  
Install to the default path: `C:\Program Files\Tesseract-OCR\`

---

## 🔒 Security & Privacy

| File | Status | Contains |
|---|---|---|
| `.env` | ❌ Git-ignored | Your real API keys |
| `.env.example` | ✅ Committed | Placeholder template |
| `jarvis_config.json` | ❌ Git-ignored | Saved settings with keys |
| `screenshots/` | ❌ Git-ignored | Screen captures |

> API keys are stored locally only — never sent anywhere except the chosen AI provider's official API endpoint.

---

## 🛣️ Roadmap

- [ ] Smart home integration (Home Assistant)
- [ ] Email & calendar integration
- [ ] Custom wake word training
- [ ] Plugin system for community extensions
- [ ] Linux & macOS support
- [ ] Mobile companion app

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request



---

<p align="center">
  Made with ❤️ — <i>"Sometimes you gotta run before you can walk."</i> — Tony Stark
</p>
