import asyncio
import os
from random import randint
from PIL import Image
import requests
from dotenv import get_key
from time import sleep

# Set up constants
FOLDER_PATH = r"Data"
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
HEADERS = {"Authorization": f"Bearer {get_key('.env', 'HuggingFaceAPIKey')"}


def open_images(prompt):
    """Opens the generated images one by one."""
    sanitized_prompt = prompt.replace(" ", "_")
    files = [f"{sanitized_prompt}{i}.jpg" for i in range(1, 5)]

    for file_name in files:
        image_path = os.path.join(FOLDER_PATH, file_name)
        try:
            with Image.open(image_path) as img:
                print(f"Opening image: {image_path}")
                img.show()
                sleep(1)
        except IOError:
            print(f"Unable to open {image_path}")


async def query(payload):
    """Sends a request to the API and returns the generated image content."""
    try:
        response = await asyncio.to_thread(requests.post, API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()  # Raise error for failed requests
        return response.content
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return None


async def generate_images(prompt):
    """Generates four images based on the provided prompt."""
    sanitized_prompt = prompt.replace(" ", "_")
    tasks = []

    for i in range(4):
        payload = {
            "inputs": f"{prompt}, quality=4k, sharpness=maximum, Ultra High details, high resolution, seed={randint(0, 1000000)}",
        }
        tasks.append(asyncio.create_task(query(payload)))

    image_bytes_list = await asyncio.gather(*tasks)

    # Save images to disk
    for i, image_bytes in enumerate(image_bytes_list):
        if image_bytes:  # Only save if response is valid
            file_path = os.path.join(FOLDER_PATH, f"{sanitized_prompt}{i+1}.jpg")
            with open(file_path, "wb") as f:
                f.write(image_bytes)
        else:
            print(f"Skipping image {i+1} due to an API error.")


def generate_and_display_images(prompt):
    """Runs image generation and then displays the images."""
    asyncio.run(generate_images(prompt))
    open_images(prompt)


# Main loop for checking file status
IMAGE_GENERATION_FILE = r"Frontend\Files\ImageGeneration.data"

while True:
    try:
        # Read the status file
        with open(IMAGE_GENERATION_FILE, "r") as f:
            data = f.read().strip()

        if not data:
            sleep(1)
            continue

        prompt, status = data.split(",")

        if status.strip().lower() == "true":
            print("Generating Images ...")
            generate_and_display_images(prompt=prompt)

            # Reset the file status after generation
            with open(IMAGE_GENERATION_FILE, "w") as f:
                f.write("False,False")

            break  # Exit loop after completion
        else:
            sleep(1)

    except FileNotFoundError:
        print(f"File {IMAGE_GENERATION_FILE} not found. Retrying...")
        sleep(1)

    except Exception as e:
        print(f"Unexpected error: {e}")
        sleep(1)
