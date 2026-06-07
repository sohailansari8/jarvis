import tkinter as tk
from tkinter import ttk
import speech_recognition as sr
import pyttsx3
import datetime
import wikipedia
import webbrowser
import os
import random
import pyautogui
import threading
import pyjokes
import requests
import psutil

# Initialize text and speech engines
engine = pyttsx3.init()
r = sr.Recognizer()
engine.runAndWait()

def speak(audio):
    engine.say(audio)
    engine.runAndWait()

def wishme():
    hour = datetime.datetime.now().hour
    if hour >= 4 and hour < 12:
        greeting = "Good Morning Sir!!"
    elif hour >= 12 and hour < 16:
        greeting = "Good Afternoon Sir!!"
    elif hour >= 16 and hour < 24:
        greeting = "Good Evening Sir!!"
    else:
        greeting = "Good Night Sir, See You Tomorrow"

    welcome_msg = f"{greeting} Jarvis at your service sir, please tell me how may I help you."
    print(welcome_msg)
    speak(welcome_msg)
    return welcome_msg

def update_ui_text(query):
    text_entry.delete(0, tk.END)
    text_entry.insert(0, query)
    if query:
        query_listbox.insert(tk.END, "You: " + query)
        query_listbox.see(tk.END)

def update_ui_response(response):
    if response:
        query_listbox.insert(tk.END, "Jarvis: " + response)
        query_listbox.see(tk.END)
        print("Jarvis: " + response)

def take_voice_input():
    with sr.Microphone() as source:
        print("Listening...")
        window.after(0, update_ui_response, "Listening...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
            print("Recognizing...")
            window.after(0, update_ui_response, "Recognizing...")
            query = r.recognize_google(audio, language='en-in')
            query = query.lower()
            return query
        except sr.WaitTimeoutError:
            print("Listening timed out...")
            return ""
        except Exception as e:
            print("Say that again please...")
            return ""

def process_query(query):
    if not query:
        return
        
    update_ui_text(query)
    
    if 'wikipedia' in query:
        speak('Searching Wikipedia...')
        query = query.replace("wikipedia", "").strip()
        try:
            results = wikipedia.summary(query, sentences=2)
            speak("According to Wikipedia")
            update_ui_response(results)
            speak(results)
        except Exception as e:
            msg = "Could not find any results on Wikipedia."
            update_ui_response(msg)
            speak(msg)
            
    elif "time" in query:
        Time = datetime.datetime.now().strftime("%I:%M %p")
        msg = f"The current time is {Time}"
        update_ui_response(msg)
        speak(msg)
          
    elif 'date' in query:
        date_str = datetime.datetime.now().strftime("%d %B %Y")
        msg = f"Today's date is {date_str}"
        update_ui_response(msg)
        speak(msg)
            
    elif "hello" in query:
        msg = "Hello Sir, Welcome Back!"
        update_ui_response(msg)
        speak(msg)
        
    elif "who are you" in query:
        msg = "I'm JARVIS created by Mr. Diptesh and I'm a desktop voice assistant."
        update_ui_response(msg)
        speak(msg)

    elif "how are you" in query:
        msg = "I'm fine sir, What about you?"
        update_ui_response(msg)
        speak(msg)

    elif "fine" in query or "good" in query:
        msg = "Glad to hear that sir!!"
        update_ui_response(msg)
        speak(msg)

    elif 'open youtube' in query:
        webbrowser.open("youtube.com")
        msg = "opening youtube sir..."
        update_ui_response(msg)
        speak(msg)
            
    elif 'open google' in query:
        webbrowser.open("google.com")
        msg = "opening google sir..."
        update_ui_response(msg)
        speak(msg)

    elif 'open facebook' in query:
        webbrowser.open("facebook.com")
        msg = "opening facebook sir..."
        update_ui_response(msg)
        speak(msg)

    elif 'open instagram' in query:
        webbrowser.open("instagram.com")
        msg = "opening instagram sir..."
        update_ui_response(msg)
        speak(msg)
      
    elif 'open stackoverflow' in query:
        webbrowser.open("stackoverflow.com")   
        msg = "opening stackoverflow sir..."
        update_ui_response(msg)
        speak(msg)

    elif 'open calculator' in query:
        os.system('start calc')
        msg = "opening calculator sir..."
        update_ui_response(msg)
        speak(msg)
    
    elif 'open notepad' in query:
        os.system('start notepad')
        msg = "opening notepad sir..."
        update_ui_response(msg)
        speak(msg)
    
    elif 'open chrome' in query:
        os.system('start chrome')
        msg = "opening chrome sir..."
        update_ui_response(msg)
        speak(msg)
        
    elif "search on chrome" in query:
        speak("What should I search?")
        search = take_voice_input()
        if search:
            url = f"https://www.google.com/search?q={search}"
            webbrowser.open(url)
            msg = f"Searching for {search}"
            update_ui_response(msg)
            speak(msg)
        
    elif 'open edge' in query:
        os.system('start msedge')
        msg = "opening edge sir..."
        update_ui_response(msg)
        speak(msg)
    
    elif 'open whatsapp' in query:
        os.system('start whatsapp')
        msg = "opening whatsapp sir..."
        update_ui_response(msg)
        speak(msg)
        
    elif 'open snapchat' in query:
        os.system('start snapchat')
        msg = "opening snapchat sir..."
        update_ui_response(msg)
        speak(msg)
          
    elif 'play music' in query:
        music_dir = os.path.join(os.path.expanduser("~"), "Music")
        if os.path.exists(music_dir) and os.listdir(music_dir):
            songs = os.listdir(music_dir)
            random_song = random.choice(songs)
            msg = f"Playing: {random_song}"
            update_ui_response(msg)
            os.startfile(os.path.join(music_dir, random_song))
            speak("Playing music")
        else:
            msg = "Could not find any music in your Music folder."
            update_ui_response(msg)
            speak(msg)

    elif "start" in query:
        app_name = query.replace("start","").replace("jarvis","").strip()
        pyautogui.press("super")
        pyautogui.sleep(0.5)
        pyautogui.typewrite(app_name)
        pyautogui.sleep(1)
        pyautogui.press("enter")
        msg = f"opening {app_name} sir...."
        update_ui_response(msg)
        speak(msg)
        
    elif "close" in query:
        app_name = query.replace("close", "").strip()
        msg = f"closing {app_name} sir..."
        update_ui_response(msg)
        speak(msg)
        if "notepad" in app_name: os.system("taskkill /f /im notepad.exe")
        elif "edge" in app_name: os.system("taskkill /f /im msedge.exe")
        elif "chrome" in app_name: os.system("taskkill /f /im chrome.exe")
        elif "whatsapp" in app_name: os.system("taskkill /f /im whatsapp.exe")
        elif "code" in app_name: os.system("taskkill /f /im code.exe")
        elif "calculator" in app_name: os.system("taskkill /f /im calculator.exe")
        elif "music" in app_name: os.system("taskkill /f /im wmplayer.exe")
        else:
            os.system(f"taskkill /f /im {app_name}.exe")

    elif "joke" in query:
        joke = pyjokes.get_joke()
        update_ui_response(joke)
        speak(joke)

    elif "weather" in query:
        try:
            res = requests.get("https://wttr.in/?format=3")
            weather_data = res.text
            update_ui_response(weather_data)
            speak("The current weather is " + weather_data)
        except:
            msg = "Sorry, I couldn't fetch the weather right now."
            update_ui_response(msg)
            speak(msg)

    elif "system stats" in query or "battery" in query or "cpu" in query:
        cpu = psutil.cpu_percent()
        battery = psutil.sensors_battery()
        if battery:
            msg = f"CPU usage is at {cpu} percent. Battery is at {battery.percent} percent."
        else:
            msg = f"CPU usage is at {cpu} percent. Battery information not available."
        update_ui_response(msg)
        speak(msg)
                
    elif "bye" in query or "offline" in query or "finally sleep" in query or "quit" in query:
        msg = "Going offline. Have a nice day sir!"
        update_ui_response(msg)
        speak(msg)
        window.after(2000, window.destroy)
        import sys
        sys.exit()
    
    else:
        msg = "Sorry, I don't understand this query"
        update_ui_response(msg)
        speak(msg)

def on_speak_button_click():
    threading.Thread(target=handle_speak_action, daemon=True).start()

def handle_speak_action():
    query = take_voice_input()
    if query:
        window.after(0, process_query, query)

def on_query_button_click():
    query = text_entry.get()
    if query.strip():
        process_query(query)

def trigger_speak(event):
    on_speak_button_click()

# Wake word background listener
def wake_word_listener():
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=1)
        print("Wake word listener started. Say 'Hey Jarvis' to activate.")
        while True:
            try:
                # Listen briefly for the wake word
                audio = r.listen(source, timeout=1, phrase_time_limit=3)
                query = r.recognize_google(audio, language='en-in').lower()
                if "hey jarvis" in query:
                    print("Wake word detected!")
                    window.after(0, update_ui_response, "Yes sir? I am listening...")
                    speak("Yes sir?")
                    # Listen for the actual command
                    command_audio = r.listen(source, timeout=5, phrase_time_limit=8)
                    command = r.recognize_google(command_audio, language='en-in').lower()
                    print(f"Command after wake word: {command}")
                    window.after(0, process_query, command)
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except Exception as e:
                continue

def start_wake_word_thread():
    t = threading.Thread(target=wake_word_listener, daemon=True)
    t.start()

# --- GUI Setup ---
window = tk.Tk()
window.title("Jarvis AI Assistant")
window.geometry("850x550")
window.configure(bg='#1e1e2e')

# Use modern ttk styling
style = ttk.Style()
try:
    style.theme_use('clam')
except:
    pass

style.configure('TButton', font=('Segoe UI', 12), padding=10, background='#89b4fa', foreground='#11111b')
style.configure('TLabel', font=('Segoe UI', 24, 'bold'), background='#1e1e2e', foreground='#cba6f7')

# Title Label
text_label = ttk.Label(window, text="Jarvis Desktop Assistant")
text_label.pack(side=tk.TOP, pady=(20, 10))

# Chat History Listbox
history_frame = tk.Frame(window, bg='#1e1e2e')
history_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=40, pady=10)

scrollbar = tk.Scrollbar(history_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

query_listbox = tk.Listbox(history_frame, yscrollcommand=scrollbar.set, 
                           bg='#313244', fg='#cdd6f4', font=('Segoe UI', 12), 
                           borderwidth=0, highlightthickness=0, selectbackground='#45475a')
query_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.config(command=query_listbox.yview)

# Input area
input_frame = tk.Frame(window, bg='#1e1e2e')
input_frame.pack(side=tk.TOP, fill=tk.X, padx=40, pady=10)

text_entry = tk.Entry(input_frame, font=("Segoe UI", 14), bg='#313244', fg='#cdd6f4', borderwidth=0, insertbackground='white')
text_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 10))
text_entry.bind('<Return>', lambda event: on_query_button_click())
text_entry.bind("<Control-q>", trigger_speak)
text_entry.focus_set()

# Buttons
button_frame = tk.Frame(window, bg='#1e1e2e')
button_frame.pack(side=tk.BOTTOM, pady=20)

query_button = ttk.Button(button_frame, text="Send Query", command=on_query_button_click)
query_button.pack(side=tk.LEFT, padx=10)

speak_button = ttk.Button(button_frame, text="Speak (Ctrl+Q)", command=on_speak_button_click)
speak_button.pack(side=tk.LEFT, padx=10)

window.bind("<Control-q>", trigger_speak)

# Start background services
start_wake_word_thread()

# Welcome message
initial_msg = wishme()
update_ui_response(initial_msg)

# Run GUI window
window.mainloop()
