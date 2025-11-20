import pyaudio
import wave
import audioop
import os
import subprocess
import asyncio
from pygame import mixer

# Parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
THRESHOLD = 10000  # Adjust based on testing, this value detects loud noises

# Function to open and run the Python file
async def open_file():
    file_path = "/Users/BPS/Documents/JARVIS-MK-IV/Main.py"
    mp3_path = "/Users/BPS/Documents/JARVIS-MK-IV/Frontend/Files/acdc.mp3"

    # Play MP3 file at 50% volume
    mixer.init()
    mixer.music.load(mp3_path)
    mixer.music.set_volume(0.25)  
    mixer.music.play()

    # Run Python script
    subprocess.call(['/Users/BPS/Documents/JARVIS-MK-IV/.venv/bin/python', file_path])  # Specify the file you want to open

# Function to listen for claps
async def listen_for_claps():
    audio = pyaudio.PyAudio()

    # Start streaming
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    print("Listening for claps...")

    try:
        while True:
            data = stream.read(CHUNK)
            rms = audioop.rms(data, 2)  # Gets the RMS of the audio chunk

            if rms > THRESHOLD:
                print("Clap detected")
                await open_file()  # Run open_file asynchronously
                break  # Exit after opening the file once, remove this if continuous detection is needed
    finally:
        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        audio.terminate()
        print("Terminated")

# Main function to start listening for claps
async def main():
    await listen_for_claps()

# Run the asyncio loop
if __name__ == "__main__":
    asyncio.run(main())
