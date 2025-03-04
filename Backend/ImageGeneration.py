# import asyncio
# from random import randint
# from PIL import Image
# import requests 
# from dotenv import get_key
# import os
# from time import sleep

# def open_images(prompt):
#     folder_path = r"Data"
#     prompt = prompt.replace(" ", "_")

#     Files = [f"{prompt}{i}.jpg" for i in range(1, 5)]

#     for jpg_file in Files:
#         image_path = os.path.join(folder_path, jpg_file)

#         try:
#             imag = Image.open(image_path)
#             print(f"Opening image: {image_path}")
#             imag.show()
#             sleep(1)
#         except IOError:
#             print(f"Unable to open {image_path}")

# API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
# headers = {"Authorization": f"Bearer {get_key('.env', 'HuggingFaceAPIKey')}"}

# async def query(payload):
#     response = await asyncio.to_thread(requests.post, API_URL, headers=headers, json=payload)
#     return response.content

# async def generate_images(prompt: str):
#     tasks = []

#     for _ in range(4):
#         payload = {
#             "inputs": f"{prompt}, quality=4k, sharpness=maximum, Ultra High details, high resolution, seed={randint(0, 1000000)}",
#         }
#         tasks.append(asyncio.create_task(query(payload)))

#     image_bytes_list = await asyncio.gather(*tasks)

#     for i, image_bytes in enumerate(image_bytes_list):
#         with open(fr"Data\{prompt.replace(' ', '_')}{i+1}.jpg", "wb") as f:
#             f.write(image_bytes)

# def GenerateImages(prompt: str):
#     asyncio.run(generate_images(prompt))
#     open_images(prompt)

# while True:
#     try:
#         with open(r"Frontend\Files\ImageGeneration.data", "r") as f:
#             Data: str = f.read()

#         Prompt, Status = Data.split(",")

#         if Status.strip() == "True":
#             print("Generating Images ...")
#             GenerateImages(prompt=Prompt)

#             with open(r"Frontend\Files\ImageGeneration.data", "w") as f:
#                 f.write("False,False")
#             break
#         else:
#             sleep(1)

#     except Exception as e:
#         print(f"Error: {e}")


import asyncio
import os
import requests
from random import randint
from PIL import Image
from time import sleep
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
HEADERS = {"Authorization": f"Bearer {os.getenv('HuggingFaceAPIKey')}"}

# Folder to store images
IMAGE_FOLDER = "Data"

def open_images(prompt):
    """Opens generated images based on the prompt."""
    prompt = prompt.replace(" ", "_")
    file_names = [f"{prompt}{i}.jpg" for i in range(1, 5)]

    for file in file_names:
        image_path = os.path.join(IMAGE_FOLDER, file)

        try:
            img = Image.open(image_path)
            print(f"Opening image: {image_path}")
            img.show()
            sleep(1)
        except IOError:
            print(f"Unable to open {image_path}")

async def query(payload):
    """Sends a request to the Hugging Face API."""
    try:
        response = await asyncio.to_thread(requests.post, API_URL, headers=HEADERS, json=payload)
        return response.content
    except Exception as e:
        print(f"API request failed: {e}")
        return None

async def generate_images(prompt):
    """Generates four AI images asynchronously."""
    tasks = []
    prompt_formatted = prompt.replace(" ", "_")

    for i in range(4):
        payload = {
            "inputs": f"{prompt}, quality=4k, sharpness=maximum, Ultra High details, high resolution, seed={randint(0, 1000000)}"
        }
        tasks.append(asyncio.create_task(query(payload)))

    image_bytes_list = await asyncio.gather(*tasks)

    for i, image_bytes in enumerate(image_bytes_list):
        if image_bytes:
            file_path = os.path.join(IMAGE_FOLDER, f"{prompt_formatted}{i+1}.jpg")
            with open(file_path, "wb") as f:
                f.write(image_bytes)

def GenerateImages(prompt):
    """Main function to generate and display images."""
    print("Generating Images ... ")
    asyncio.run(generate_images(prompt))
    open_images(prompt)

# def monitor_file():
#     """Monitors the file and generates images based on its content."""
#     file_path = os.path.join("Frontend", "Files", "ImageGeneration.data")

#     while True:
#         try:
#             with open(file_path, "r") as f:
#                 data = f.read().strip()

#             if data:
#                 prompt, status = data.split(",")

#                 if status.strip().lower() == "true":
#                     GenerateImages(prompt.strip())

#                     # Reset the file to prevent duplicate execution
#                     with open(file_path, "w") as f:
#                         f.write("False,False")

#             sleep(1)

#         except Exception as e:
#             print(f"Error: {e}")
#             sleep(1)

# def main():
#     """Runs the image generation process."""
#     GenerateImages("Tony Stark")

# if __name__ == "__main__":
#     main()
#     monitor_file()
