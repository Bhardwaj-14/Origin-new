import asyncio
from random import randint
from PIL import Image
import requests
from dotenv import load_dotenv
import os
from time import sleep
import platform

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("HuggingFaceAPIKey")
if not API_KEY:
    raise ValueError("HuggingFaceAPIKey not found in .env file")

API_URL = "tencent/HunyuanImage-3.0"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

DATA_FOLDER = "Data"
os.makedirs(DATA_FOLDER, exist_ok=True)  # Ensure Data folder exists


async def query(payload, retries=3):
    """Send a request to the API and handle rate limits."""
    for attempt in range(retries):
        try:
            response = await asyncio.to_thread(requests.post, API_URL, headers=HEADERS, json=payload)
            if response.status_code == 200:
                return response.content  # Raw image bytes
            elif response.status_code == 429:
                print(f"Rate limit hit. Retrying in 60 seconds... (Attempt {attempt + 1}/{retries})")
                await asyncio.sleep(60)  # Wait before retrying
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Request failed: {e}")
    print("Max retries reached. Skipping this request.")
    return None


async def generate_images(prompt: str):
    """Generate 3 images asynchronously."""
    tasks = []

    for _ in range(3):  # Generate 3 images
        payload = {
            "inputs": f"{prompt}, quality=4k, sharpness=maximum, Ultra High details, high resolution, seed={randint(0, 1000000)}",
        }
        task = asyncio.create_task(query(payload))
        tasks.append(task)

    image_bytes_list = await asyncio.gather(*tasks)

    for i, image_bytes in enumerate(image_bytes_list):
        if image_bytes:  # Ensure the response is valid
            image_path = os.path.join(DATA_FOLDER, f"{prompt.replace(' ', '_')}{i + 1}.jpg")
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            print(f"Image saved: {image_path}")
        else:
            print(f"Image {i + 1} could not be generated.")


def open_images(prompt):
    """Open generated images using the default OS image viewer."""
    prompt = prompt.replace(" ", "_")
    Files = [f"{prompt}{i}.jpg" for i in range(1, 4)]

    for jpg_file in Files:
        image_path = os.path.join(DATA_FOLDER, jpg_file)

        try:
            # Check if the file exists before attempting to open it
            if os.path.exists(image_path):
                print(f"Opening image: {image_path}")

                # Open image with default OS viewer
                if platform.system() == "Windows":
                    os.startfile(image_path)  # Windows
                elif platform.system() == "Darwin":
                    os.system(f"open {image_path}")  # macOS
                else:
                    os.system(f"xdg-open {image_path}")  # Linux

                sleep(1)  # Wait for the image to open
            else:
                print(f"Image file does not exist: {image_path}")
        except Exception as e:
            print(f"Error opening image {image_path}: {e}")

def update_status():
    """Update the status in ImageGeneration.data."""
    try:
        with open(r"Frontend/Files/ImageGeneration.data", "w") as f:
            f.write("False,False")
            print("Status updated to False,False")
    except Exception as e:
        print(f"Error updating ImageGeneration.data: {e}")

def GenerateImages(prompt: str):
    asyncio.run(generate_images(prompt))
    open_images(prompt)
    update_status()  # Ensure the status is updated after processing


# Main loop to check for image generation requests
while True:
    try:
        with open(r"Frontend/Files/ImageGeneration.data", "r") as f:
            Data: str = f.read()

        Prompt, Status = Data.split(",")

        if Status.strip() == "True":
            print("Generating Images...")
            GenerateImages(prompt=Prompt.strip())

            with open(r"Frontend/Files/ImageGeneration.data", "w") as f:
                f.write("False,False")
                break
        else:
            sleep(1)

    except Exception as e:
        print(e)


generate_images("umbrellas")