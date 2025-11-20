from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus
)
from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from dotenv import dotenv_values
from asyncio import run
from time import sleep
import subprocess
import threading
import json
import os
import pyautogui

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")
DefaultMessage = f'''{Username}: Hello {Assistantname}, How are you?
{Assistantname}: Welcome back sir! I am doing well. How may I help you?'''
subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]

def type(text):
    text = text.replace("type ", "")  # Remove the 'type' keyword
    pyautogui.typewrite(text)  # Simulate typing the text
    pyautogui.press('enter')  # Optionally press Enter after typing
    print(f"Typed: {text}")
    TextToSpeech("Done Sir...")

def ShowDefaultChatIfNoChats():
    try:
        with open(r"Data/ChatLog.json", "r", encoding="utf-8") as file:
            if len(file.read()) < 5:
                with open(TempDirectoryPath("Database.data"), "w", encoding="utf-8") as db_file:
                    db_file.write("")
                with open(TempDirectoryPath("Responses.data"), "w", encoding="utf-8") as res_file:
                    res_file.write(DefaultMessage)
    except Exception as e:
        print(f"Error in ShowDefaultChatIfNoChats: {e}")

def ReadChatLogJson():
    try:
        with open(r"Data/ChatLog.json", "r", encoding="utf-8") as file:
            chatlog_data = json.load(file)
        return chatlog_data
    except Exception as e:
        print(f"Error reading ChatLog.json: {e}")
        return []

def ChatLogIntegration():
    try:
        json_data = ReadChatLogJson()
        formatted_chatlog = ""
        for entry in json_data:
            if entry["role"] == "user":
                formatted_chatlog += f"User: {entry['content']}\n"
            elif entry["role"] == "assistant":
                formatted_chatlog += f"Assistant: {entry['content']}\n"

        formatted_chatlog = formatted_chatlog.replace("User", Username + " ")
        formatted_chatlog = formatted_chatlog.replace("Assistant", Assistantname + " ")

        with open(TempDirectoryPath("Database.data"), "w", encoding="utf-8") as file:
            file.write(AnswerModifier(formatted_chatlog))
    except Exception as e:
        print(f"Error in ChatLogIntegration: {e}")

def ShowChatsOnGUI():
    try:
        with open(TempDirectoryPath("Database.data"), "r", encoding="utf-8") as file:
            data = file.read()
        if len(data) > 0:
            with open(TempDirectoryPath("Responses.data"), "w", encoding="utf-8") as file:
                file.write(data)
    except Exception as e:
        print(f"Error in ShowChatsOnGUI: {e}")

def InitialExecution():
    print("Starting Initial Execution...")
    SetMicrophoneStatus("False")  # Fixed typo: was "Flase"
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()
    print("Initial Execution Complete")

def WelcomeMessage():
    """Separate function for welcome message to avoid blocking startup"""
    try:
        print("Generating welcome message...")
        hello = ChatBot("Introduce yourself as if JARVIS was just started up... also give me the date and weather updates")
        TextToSpeech(hello)
    except Exception as e:
        print(f"Error in welcome message: {e}")

def MainExecution():
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""

    try:
        SetAssistantStatus("Listening... ")
        # Using SpeechRecognition instead of input
        Query = SpeechRecognition()
        
        if not Query or Query.strip() == "":
            return False
            
        print(f"Query received: {Query}")
        ShowTextToScreen(f"{Username}: {Query}")
        SetAssistantStatus("Thinking... ")
        Decision = FirstLayerDMM(Query)

        print(f"\nDecision: {Decision}\n")

        G = any([i for i in Decision if i.startswith("general")])
        R = any([i for i in Decision if i.startswith("realtime")])

        Merged_query = " and ".join(
            [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
        )

        for queries in Decision:
            if "generate" in queries:
                ImageGenerationQuery = str(queries)
                ImageExecution = True

        for queries in Decision:
            if not TaskExecution:
                if any(queries.startswith(func) for func in Functions):
                    run(Automation(list(Decision)))
                    TaskExecution = True

        if "type" in Query.lower():  # Check if the query is to type something
            type(Query)

        if ImageExecution:
            with open(r"Frontend/Files/ImageGeneration.data", "w") as file:
                file.write(f"{ImageGenerationQuery}, True")

            try:
                p1 = subprocess.Popen(
                    ["python", r"Backend/ImageGeneration.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    shell=False,
                )
                subprocesses.append(p1)

            except Exception as e:
                print(f"Error starting ImageGeneration.py: {e}")

        if G and R or R:
            SetAssistantStatus("Searching... ")
            Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
            ShowTextToScreen(f"{Assistantname}: {Answer}")
            SetAssistantStatus("Answering... ")
            TextToSpeech(Answer)
            return True

        else:
            for queries in Decision:
                if "general" in queries:
                    SetAssistantStatus("Thinking... ")
                    QueryFinal = queries.replace("general ", "")
                    Answer = ChatBot(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname}: {Answer}")
                    SetAssistantStatus("Answering... ")
                    TextToSpeech(Answer)
                    return True

                elif "realtime" in queries:
                    SetAssistantStatus("Searching... ")
                    QueryFinal = queries.replace("realtime ", "")
                    Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname}: {Answer}")
                    SetAssistantStatus("Answering... ")
                    TextToSpeech(Answer)
                    return True

                elif "exit" in queries:
                    QueryFinal = "Goodbye Jarvis"
                    Answer = ChatBot(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname}: {Answer}")
                    SetAssistantStatus("Answering... ")
                    TextToSpeech(Answer)
                    os._exit(1)
                    
    except Exception as e:
        print(f"Error in MainExecution: {e}")
        SetAssistantStatus("Error occurred")
        return False

def FirstThread():
    # Run welcome message after GUI starts
    sleep(2)  # Give GUI time to initialize
    WelcomeMessage()
    
    while True:
        try:
            CurrentStatus = GetMicrophoneStatus()
            if CurrentStatus == "True":
                MainExecution()
            else:
                AIStatus = GetAssistantStatus()
                if "Available ... " in AIStatus:
                    sleep(0.1)
                else:
                    SetAssistantStatus("Available ... ")
        except Exception as e:
            print(f"Error in FirstThread: {e}")
            sleep(1)

def SecondThread():
    try:
        GraphicalUserInterface()
    except Exception as e:
        print(f"Error in SecondThread (GUI): {e}")

if __name__ == "__main__":
    print("Starting Jarvis...")
    
    # Initialize first
    InitialExecution()
    
    # Start worker thread
    thread2 = threading.Thread(target=FirstThread, daemon=True)
    thread2.start()
    print("Worker thread started")
    
    # Start GUI (blocking)
    print("Starting GUI...")
    SecondThread()