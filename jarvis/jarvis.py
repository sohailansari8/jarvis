import tkinter as tk
import speech_recognition as sr
import pyttsx3 #pip install pyttsx3
import speech_recognition as sr #pip install speechRecognition
import datetime
import wikipedia #pip install wikipedia
import webbrowser
import os
import random
import pyautogui






# Initialize text and speech engines
engine = pyttsx3.init()
r = sr.Recognizer()
engine.runAndWait()


    
def wishme():
    print("Welcome back sir!!")
    speak("Welcome back sir!!")
    
    hour = datetime.datetime.now().hour
    if hour >= 4 and hour < 12:
        speak("Good Morning Sir!!")
        print("Good Morning Sir!!")
    elif hour >= 12 and hour < 16:
        speak("Good Afternoon Sir!!")
        print("Good Afternoon Sir!!")
    elif hour >= 16 and hour < 24:
        speak("Good Evening Sir!!")
        print("Good Evening Sir!!")
    else:
        speak("Good Night Sir, See You Tommorrow")

    speak("Jarvis at your service sir, please tell me how may I help you.")
    print("Jarvis at your service sir, please tell me how may I help you.")

def speak(audio):
    engine.say(audio)
    engine.runAndWait()
    
# Create function to trigger the speak button when the user presses Ctrl + Alt + Q
def trigger_speak(event):
    speak_button.invoke()
        
def time():
    Time = datetime.datetime.now().strftime("%I:%M:%S")
    speak("the current time is")
    speak(Time)
    print("The current time is ", Time)

def date():
    day = int(datetime.datetime.now().day)
    month = int(datetime.datetime.now().month)
    year = int(datetime.datetime.now().year)
    speak("the current date is")
    speak(day)
    speak(month)
    speak(year)
    print("The current date is " + str(day) + "/" + str(month) + "/" + str(year))


    
# Function to handle voice input
def take_voice_input():
    with sr.Microphone() as source:
        print("Listening...")
        audio = r.listen(source,0,5)
        try:
            print("Recognizing...")
            query = r.recognize_google(audio, language='en-in')
            query = query.lower()  # Convert query to lowercase
            print(f"User said: {query}\n")
            text_entry.delete(0, tk.END)
            text_entry.insert(0, query)
        except Exception as e:
            print("Say that again please...")
            return query

def take_text_input(query=None):  # add default argument for query
    if query is not None:  # check if query is provided
        return query  # return the query directly
    query = text_entry.get()  # get the query from the text entry
    if not query.strip():  # check if query is empty
        return ""  # return empty string if query is empty
    text_entry.delete(0, tk.END)  # clear the text entry
    return query  # return the query
# Call wishme function
wishme()


# Function to handle button clicks
def on_button_click(button_text):
    global text_entry
    if button_text == "Speak":
        query = take_voice_input()

    elif button_text == "Query":
        query = take_text_input()

        # Add this condition to check if query is empty
        if query:
            # Update Listbox to show the latest query at the bottom
            query_listbox.see(tk.END)

            # Insert the query into the Listbox
            query_listbox.insert(tk.END, query)

        
    # Add code here to process the query
        if 'wikipedia' in query:
            speak('Searching Wikipedia...')
            query = query.replace("wikipedia", "")
            results = wikipedia.summary(query, sentences=2)
            speak("According to Wikipedia")
            print(results)
            speak(results)
            
        
        elif "time" in query:
            time() 
              
        elif 'date' in query:
                date()
                
        elif "hello" in query:
                speak("Hello Sir, Welcome Back!")
    
        elif "bye" in query:
                speak("Nice to meet you sir, Have a nice day!")
        
        
        elif "who are you" in query:
            speak("I'm JARVIS created by Mr. Diptesh and I'm a desktop voice assistant.")
            print("I'm JARVIS created by Mr. diptesh and I'm a desktop voice assistant.")

        elif "how are you" in query:
            speak("I'm fine sir, What about you?")
            print("I'm fine sir, What about you?")

        elif "fine" in query:
            speak("Glad to hear that sir!!")
            print("Glad to hear that sir!!")

        elif "good" in query:
            speak("Glad to hear that sir!!")
            print("Glad to hear that sir!!")
        
            
        elif 'open youtube' in query:
            webbrowser.open("youtube.com")
            speak("opening youtube sir...")
                
        elif 'open google' in query:
            
            webbrowser.open("google.com")
            speak("opening google sir...")

        elif 'open facebook' in query:
            webbrowser.open("facebook.com")
            speak("opening facebook sir...")

        elif 'open instagram' in query:
            webbrowser.open("instagram.com")
            speak("opening instagram sir...")
          
        elif 'open stackoverflow' in query:
            webbrowser.open("stackoverflow.com")   
            speak("opening stackoverflow sir...")

        elif 'open calculator' in query:
            os.startfile('calc.exe')
            speak("opening calculator sir...")
        
        elif 'open notepad' in query:
            os.startfile('notepad.exe')
            speak("opening notepad sir...")
        
       
        
        elif 'open chrome' in query:
            file_path ="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            os.startfile(file_path)
            speak("opening chrome sir...")
            
        elif "search on chrome" in query:
            try:
                speak("What should I search?")
                print("What should I search?")
                chromePath = "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
                search = take_text_input()
                webbrowser.get(chromePath).open_new_tab(search)
                print(search)

            except Exception as e:
                speak("Can't open now, please try again later.")
                print("Can't open now, please try again later.")
            
        
        

        elif "offline" in query:
            quit()
            
           
        elif 'open edge' in query:
            file_path ="C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
            os.startfile(file_path)
            speak("opening edge sir...")  
        
        elif 'open whatsapp' in query:
            file_path = "C:\\Users\\Lenovo\\OneDrive\\Desktop\\WhatsApp - Shortcut.lnk"
            os.startfile(file_path)
            speak("opening whatsapp sir...")
            
       
        
        # elif 'open chrome' in query:
        #     file_path ="C:\Users\dipte\OneDrive\Desktop\Snapchat - Shortcut.lnk"
        #     os.startfile(file_path)
        #     speak("opening chrome sir...")
        
        elif 'open snapchat' in query:
            file_path ="C:\\Users\\Lenovo\\OneDrive\\Desktop\\Snapchat.lnk"
            os.startfile(file_path)
            speak("opening snapchat sir...")          
                
        elif 'open calculator' in query:
            os.startfile('calc.exe')
            speak("opening calculator sir...")  
              
        elif 'play music' in query:
            music_dir = "C:\\Users\\Lenovo\\OneDrive\\Desktop\\music"
            songs = os.listdir(music_dir)
            random_song = random.choice(songs)
            print(f"Playing: {random_song}")
            os.startfile(os.path.join(music_dir, random_song))
 
        elif "start" in query:
            query = query.replace("start","")
            query = query.replace("jarvis","")
            pyautogui.press("super")
            pyautogui.typewrite(query)
            pyautogui.sleep(1)
            pyautogui.press("enter")
            speak("opening your app sir....")
            
        elif "close notepad" in query:
            speak ("closing the notepad sir...")
            os.system("taskkill /f /im notepad.exe")
            
        elif "close edge" in query:
            speak ("closing the edge sir...")
            os.system("taskkill /f /im msedge.exe")
            
        elif "close chrome" in query:
            speak ("closing the chrome sir...")
            os.system("taskkill /f /im chrome.exe")        
        
        elif "close whatsapp" in query:
            speak ("closing the whatsapp sir...")
            os.system("taskkill /f /im whatsapp.exe")
            
        elif "close code" in query:
            speak ("closing the code sir...")
            os.system("taskkill /f /im code.exe") 
            
       
        
        elif "close music" in query:
            speak ("closing the music sir...")
            os.system("taskkill /f /pid 18244")
            
        elif "close calculator" in query:
            speak ("closing the calculator sir...")
            os.system("taskkill /f /pid 10472")
        
                    
                
        elif "finally sleep" in query:
            speak("going to sleep sir")
            exit()
       
      
        
        else:
            speak("Sorry, I don't understand this query")
            print("Sorry, I don't understand this query")
        
    
        


# Create GUI window
window = tk.Tk()
window.title("Jarvis Assistant")
window.geometry("800x400")
window.bind_class("Tk", "<Control-q>", trigger_speak)
window.configure(bg='light blue')
window.resizable(True,True)



# Add Speak button
speak_button = tk.Button(window, text="Speak", command=lambda: on_button_click("Speak"))
speak_button.pack(side=tk.RIGHT, padx=(50, 50))


    
# Add Query button
query_button = tk.Button(window, text="Query", command=lambda: on_button_click("Query"))
query_button.pack(side=tk.LEFT, padx=(50, 50))
# Add Label
text_label = tk.Label(window, text="Jarvis Desktop Assistant", font=("Algerian", 20),  bg="light blue")
text_label.pack(side=tk.TOP, padx=(20, 20), pady=(20, 10))

# Add Text Entry widget with modify bind to execute query on Enter key press
text_entry = tk.Entry(window, width=80, font=("Helvetica", 15),border=3)
text_entry.pack(side=tk.TOP, padx=(20, 10), pady=(20, 10))
text_entry.bind("<Control-q>", trigger_speak)  # add this line to the text entry widget
text_entry.focus_set()  # add this line to set the focus on the text entry widget
text_entry.bind("<Control-Key-t>", lambda event: text_entry.focus())

# Add a bind method to the window to execute query when Enter key is pressed
window.bind('<Return>', lambda event: on_button_click("Query"))

# Add Listbox widget to display query history
query_listbox = tk.Listbox(window, width=50, height=10,background= 'light yellow', fg='black',font=('Arial', 15),borderwidth=3)
query_listbox.pack(side=tk.TOP, padx=(40, 20), pady=(50, 20))

# Run GUI window
window.mainloop()
