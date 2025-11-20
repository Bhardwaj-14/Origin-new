from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus,
    GetMicPendingState,
    SetMicPendingState
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
import requests
from datetime import datetime

env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
os.makedirs("Data", exist_ok=True)
if not os.path.exists("Data/ChatLog.json"):
    with open("Data/ChatLog.json", "w", encoding="utf-8") as file:
        json.dump([], file)
DefaultMessage = f'''{Username}: Hello {Assistantname}, How are you?
{Assistantname}: Welcome back sir! I am doing well. How may I help you?'''
subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]

def fetch_weather_summary():
    try:
        location_resp = requests.get("https://ipapi.co/json/", timeout=5)
        location_resp.raise_for_status()
        location = location_resp.json()
        latitude = location.get("latitude")
        longitude = location.get("longitude")
        city = location.get("city")
        region = location.get("region")
        if latitude is None or longitude is None:
            raise ValueError("Missing coordinates")

        weather_resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current_weather": "true"
            },
            timeout=5
        )
        weather_resp.raise_for_status()
        current_weather = weather_resp.json().get("current_weather", {})
        temperature = current_weather.get("temperature")
        windspeed = current_weather.get("windspeed")
        weather_desc = current_weather.get("weathercode")

        if temperature is None:
            raise ValueError("Missing temperature")

        location_text = ", ".join(filter(None, [city, region])) or "your location"
        weather_text = f"The temperature at {location_text} is {temperature}°C with winds at {windspeed} km/h."
        if weather_desc is not None:
            weather_text += f" Weather code {weather_desc}."
        return weather_text
    except Exception as e:
        print(f"Weather fetch failed: {e}")
        return "Weather data is currently unavailable, sir, but I will update you once I regain access."

def generate_intro_message():
    now = datetime.now()
    date_text = now.strftime("%A, %d %B %Y")
    time_text = now.strftime("%I:%M %p").lstrip("0")
    weather_text = fetch_weather_summary()
    return (
        f"Good day sir, {Assistantname} online. "
        f"It's {date_text}, and the time is {time_text}. "
        f"{weather_text} Ready at your command."
    )

def play_intro_message():
    fallback = "Jarvis online and ready to assist, sir."
    try:
        hello = generate_intro_message()
    except Exception as e:
        print(f"Intro generation error: {e}")
        hello = fallback

    try:
        TextToSpeech(hello)
    except Exception as e:
        print(f"Intro TextToSpeech error: {e}")

def type(text):
    text = text.replace("type ", "")  # Remove the 'type' keyword
    pyautogui.typewrite(text)  # Simulate typing the text
    pyautogui.press('enter')  # Optionally press Enter after typing
    print(f"Typed: {text}")
    TextToSpeech("Done Sir...")


def ShowDefaultChatIfNoChats():
    with open(r"Data/ChatLog.json", "r", encoding="utf-8") as file:
        if len(file.read()) < 5:
            with open(TempDirectoryPath("Database.data"), "w", encoding="utf-8") as db_file:
                db_file.write("")
            with open(TempDirectoryPath("Responses.data"), "w", encoding="utf-8") as res_file:
                res_file.write(DefaultMessage)

def ReadChatLogJson():
    with open(r"Data/ChatLog.json", "r", encoding="utf-8") as file:
        chatlog_data = json.load(file)
    return chatlog_data

def ChatLogIntegration():
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

def ShowChatsOnGUI():
    with open(TempDirectoryPath("Database.data"), "r", encoding="utf-8") as file:
        data = file.read()
    if len(data) > 0:
        with open(TempDirectoryPath("Responses.data"), "w", encoding="utf-8") as file:
            file.write(data)

def InitialExecution():
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()

InitialExecution()

def MainExecution():
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""

    SetAssistantStatus("Listening... ")
    Query = SpeechRecognition()
    if not Query:
        SetAssistantStatus("Available ... ")
        return
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

    if "type" in Query:  # Check if the query is to type something
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

def FirstThread():
    while True:
        CurrentStatus = GetMicrophoneStatus()
        pending = GetMicPendingState()
        if CurrentStatus == "True" and pending in ["", "True"]:
            MainExecution()
            if pending and pending != "":
                SetMicPendingState("")
                if pending == "False":
                    SetMicrophoneStatus("False")
                    SetAssistantStatus("Available ... ")
                else:
                    SetMicrophoneStatus("True")
                    SetAssistantStatus("Listening... ")
        else:
            AIStatus = GetAssistantStatus()
            if "Available ... " in AIStatus:
                sleep(0.1)
            else:
                SetAssistantStatus("Available ... ")

def SecondThread():
    GraphicalUserInterface(on_ready=lambda: threading.Thread(target=play_intro_message, daemon=True).start())

if __name__ == "__main__":
    thread2 = threading.Thread(target=FirstThread, daemon=True)
    thread2.start()
    SecondThread()
