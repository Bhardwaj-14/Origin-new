#from AppOpener import close, open as appopen(for windows)
from selenium import webdriver
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
from webbrowser import open as webopen
from pywhatkit import search, playonyt
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from rich import print
from groq import Groq
import webbrowser
import subprocess
import requests
import asyncio
import os
import platform
import ctypes
import json
import shutil
import re
from pathlib import Path

env_vars = dotenv_values(".env")
GroqAPIkey = env_vars.get("GroqAPIKey")
APP_PATHS_FILE = Path("Data/AppPaths.json")

def load_app_paths():
    if APP_PATHS_FILE.exists():
        try:
            with open(APP_PATHS_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return {}
    return {}

def save_app_paths(paths):
    os.makedirs("Data", exist_ok=True)
    with open(APP_PATHS_FILE, "w", encoding="utf-8") as file:
        json.dump(paths, file, indent=4)

APP_PATHS = load_app_paths()

def prompt_for_app_path(app):
    print(f"Please provide the full path to the executable for '{app}'.")
    print("Leave blank to skip or if you want to set it later.")
    while True:
        user_input = input(f"Path for {app}: ").strip().strip('"')
        if not user_input:
            return None
        if os.path.exists(user_input):
            APP_PATHS[app.lower()] = user_input
            save_app_paths(APP_PATHS)
            return user_input
        else:
            print("Path not found. Please try again or press Enter to skip.")

def _candidate_executable_names(app):
    cleaned = re.sub(r"[^a-zA-Z0-9]", "", app).lower()
    base = app.lower().strip()
    names = {base, cleaned, base.replace(" ", ""), f"{base.replace(' ', '')}.exe", f"{cleaned}.exe", f"{base}.exe"}
    final = set()
    for name in names:
        if not name:
            continue
        final.add(name if name.endswith(".exe") else f"{name}.exe")
    return final

def auto_detect_app_path(app):
    candidate_names = _candidate_executable_names(app)
    for name in candidate_names:
        detected = shutil.which(name)
        if detected:
            return detected

    search_dirs = [
        os.environ.get("PROGRAMFILES"),
        os.environ.get("PROGRAMFILES(X86)"),
        os.environ.get("LOCALAPPDATA"),
        os.environ.get("APPDATA"),
        str(Path.home() / "AppData/Local/Programs"),
    ]

    for directory in filter(None, search_dirs):
        directory_path = Path(directory)
        if not directory_path.exists():
            continue
        try:
            for candidate in candidate_names:
                found = next(directory_path.rglob(candidate), None)
                if found:
                    return str(found)
        except (PermissionError, OSError):
            continue
    return None

classes = ['zCubwf', 'hgKElc', 'LTKZOO sY7ric', 'gsrt vk_b FzvWSb YwPhnf', 'pclqee', 'tw-Data-text tw-text-small tw-ta',
           'IZ6rdc', 'O5uR6d LTKOO', 'vlzY6d', 'webanswers-webanswers_table__webanswers-table', 'dDoNo ikb48b gsrt', 'sXLaOe',
           'LWkfKe', 'VQF4g', 'qv3Wpe', 'kno-rdesc', 'SPZz6b']

useragent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.142.86 Safari/537.36'
client = Groq(api_key=GroqAPIkey)

professional_responses = [
    "Your satisfaction is my top priority sir; feel free to summon me if there is anything I could help you with.",
    "I'm at your service for any additional assistance or support you may need-don't hesitate to ask."
]

messages = []

SystemChatBot = [{"role": "system", "content": f"Hello, I am {env_vars.get('Username')} your owner, You're a content writer. You have to write content like letter, articles, essays, research papers etc."}]

def GoogleSearch(Topic):
    search(Topic)
    return True

def Content(Topic):

    def OpenNotepad(File):
        system_name = platform.system().lower()
        file_path = os.path.abspath(File)

        if system_name == "windows":
            try:
                os.startfile(file_path)
            except OSError as exc:
                print(f"Failed to open {file_path}: {exc}")
        elif system_name == "darwin":
            subprocess.run(["open", "-a", "TextEdit", file_path])
        else:
            subprocess.run(["xdg-open", file_path], check=False)

    def ContentWriterAI(prompt):
        messages.append({"role": "system", "content": f"{prompt}"})

        completion = client.chat.completions.create(
            model="moonshotai/kimi-k2-instruct",
            messages=SystemChatBot + messages,
            max_tokens=2048,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None
        )

        Answer = ""

        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        Answer = Answer.replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})
        return Answer

    Topic = Topic.replace("Content", "").strip()
    ContentByAI = ContentWriterAI(Topic)

    os.makedirs("Data", exist_ok=True)
    with open(f"Data/{Topic.lower().replace(' ', '')}.txt", "w", encoding="utf-8") as file:
        file.write(ContentByAI)

    OpenNotepad(f"Data/{Topic.lower().replace(' ', '')}.txt")
    return True

def YoutubeSearch(Topic):
    Url4Search = f"https://www.youtube.com/results?search_query={Topic}"
    webbrowser.open(Url4Search)
    return True

def PlayYoutube(query):
    playonyt(query)
    return True

''' windows
def OpenApp(app, sess=requests.session()):
    try:
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True
    except:
        def extract_links(html):
            if html is None:
                return []
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.find_all('a', {'jsname': 'UWckNb'})
            return [link.get('href') for link in links]
        
        def search_google(query):
            url = f"https://www.google.com/search?q={query}"
            headers = {"User-Agent": useragent}
            response = sess.get(url, headers=headers)

            if response.status_code == 200:
                return response.text
            else:
                print("Failed to retrieve search results")
            return None

        html = search_google(app)

        if html:
            link = extract_links(html)[0]
            webopen(link)

        return True
'''

def OpenApp(app, sess=requests.session()):
    system_name = platform.system().lower()

    if system_name == "windows":
        app_key = app.lower().strip()
        custom_path = APP_PATHS.get(app_key)

        if not custom_path:
            detected = auto_detect_app_path(app)
            if detected:
                APP_PATHS[app_key] = detected
                save_app_paths(APP_PATHS)
                custom_path = detected

        if not custom_path:
            custom_path = prompt_for_app_path(app)

        if custom_path:
            try:
                subprocess.run([custom_path], check=True)
                return True
            except Exception as exc:
                print(f"Failed to open '{app}' using stored path: {exc}")

        try:
            subprocess.run(["cmd", "/c", "start", "", app], check=True)
            return True
        except subprocess.CalledProcessError:
            print(f"App '{app}' could not be opened via start command.")
            return False

    try:
        # Attempt to open the app directly using macOS's open command
        subprocess.run(["open", f"-a", app], check=True)
        return True
    except subprocess.CalledProcessError:
        # If the app is not found, perform a web search
        print(f"App '{app}' not found locally. Online search feature will be introduced later...")

def CloseApp(app):
    if "chrome" in app:
        pass
    else:
        try:
            subprocess.run(["osascript", "-e", f'tell application "{app}" to quit'], check=True)
            return True
        except subprocess.CalledProcessError:
            print(f"Failed to close {app}. It may not be running.")
            return False

def System(command):
    system_name = platform.system().lower()

    if system_name == "windows":
        VK_VOLUME_MUTE = 0xAD
        VK_VOLUME_DOWN = 0xAE
        VK_VOLUME_UP = 0xAF

        def tap_key(vk_code, repeats=1):
            for _ in range(repeats):
                ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
                ctypes.windll.user32.keybd_event(vk_code, 0, 0x0002, 0)

        if command == "mute":
            tap_key(VK_VOLUME_MUTE)
        elif command == "unmute":
            tap_key(VK_VOLUME_MUTE)
        elif command == "volume up":
            tap_key(VK_VOLUME_UP, repeats=2)
        elif command == "volume down":
            tap_key(VK_VOLUME_DOWN, repeats=2)
        return True

    # macOS (original behavior)
    def mute():
        subprocess.run(["osascript", "-e", "set volume output muted true"])

    def unmute():
        subprocess.run(["osascript", "-e", "set volume output muted false"])

    def volume_up():
        subprocess.run(["osascript", "-e", "set volume output volume (output volume of (get volume settings) + 10)"])

    def volume_down():
        subprocess.run(["osascript", "-e", "set volume output volume (output volume of (get volume settings) - 10)"])

    if command == "mute":
        mute()
    elif command == "unmute":
        unmute()
    elif command == "volume up":
        volume_up()
    elif command == "volume down":
        volume_down()

    return True

def command_splitter(raw: str) -> list[str]:
    words = raw.split()
    cmds = []
    current = []

    keywords = ["open", "close", "play", "content", "google", "youtube", "system"]

    for word in words:
        if word in keywords:
            if current:
                cmds.append(" ".join(current))
                current = []
        current.append(word)

    if current:
        cmds.append(" ".join(current))

    return cmds


async def TranslateAndExecute(commands: list[str]):

    funcs = []
    for command in commands:
        if command.startswith("open "):
            fun = asyncio.to_thread(OpenApp, command.removeprefix("open "))
            funcs.append(fun)
        elif command.startswith("close "):
            fun = asyncio.to_thread(CloseApp, command.removeprefix("close "))
            funcs.append(fun)
        elif command.startswith("play "):
            fun = asyncio.to_thread(PlayYoutube, command.removeprefix("play "))
            funcs.append(fun)
        elif command.startswith("content "):
            fun = asyncio.to_thread(Content, command.removeprefix("content "))
            funcs.append(fun)
        elif command.startswith("google search "):
            fun = asyncio.to_thread(GoogleSearch, command.removeprefix("google search "))
            funcs.append(fun)
        elif command.startswith("youtube search "):
            fun = asyncio.to_thread(YoutubeSearch, command.removeprefix("youtube search "))
            funcs.append(fun)
        elif command.startswith("system "):
            fun = asyncio.to_thread(System, command.removeprefix("system "))
            funcs.append(fun)
        else:
            print(f"No Function found. For {command}")

    results = await asyncio.gather(*funcs)
    for result in results:
        yield result

async def Automation(commands: list[str]):
    async for result in TranslateAndExecute(commands):
        pass

    return True


if __name__ == "__main__":
    commands = [
        "open finder"
    ]

    asyncio.run(Automation(commands))


