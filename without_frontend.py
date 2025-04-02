import requests

import glob
import pandas as pd
from PIL import Image

import os
from io import BytesIO
import json
import base64  

from pathlib import Path
from PIL import Image

from openai import OpenAI
from rich import print

# encode the image to base64
import base64
import io

URL="http://localhost:1234/v1"
API_KEY="lm-studio"

# Load the DataFrame from a CSV file, or create a new one if the file doesn't exist
def load_or_create_dataframe(filename):
    if os.path.isfile(filename):
        df = pd.read_csv(filename)
    else:
        df = pd.DataFrame(columns=['image_file', 'description'])
    return df

df = load_or_create_dataframe('image_descriptions.csv')

# get the list of image files in the folder yopu want to process
image_files = list(Path(r"C:\Users\dasmo\OneDrive\Documents\OSIX\DC25\imgs").glob("Screenshot*.png"))
image_files.sort()

print(image_files[:3])
print(df.head())

def generate_description(base64_image):
    client = OpenAI(base_url=URL, api_key=API_KEY)
    completion = client.chat.completions.create(
        model="gemma-3-12b-it",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What is this image about?",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            },
        ],
    )
    return completion.choices[0].message.content
    
# processing the images 
def process_image(image_file):
    print(f"\nProcessing {image_file}\n")
    image = Image.open(image_file)
    # Convert PIL Image to RGB mode
    image_rgb = image.convert("RGB")

    # Convert PIL Image to bytes
    img_byte_arr = io.BytesIO()
    image_rgb.save(img_byte_arr, format="JPEG")
    image_bytes = img_byte_arr.getvalue()

    # Encode to base64
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    full_response = generate_description(base64_image)
    print(f"this is the response: {full_response}")

    # Add a new row to the DataFrame
    df.loc[len(df)] = [image_file, full_response]


for image_file in image_files:
    # Get list of filenames already in the DataFrame (extract basenames)
    existing_files = [os.path.basename(path) for path in df['image_file'].values]
    filename = os.path.basename(image_file)
    if filename not in existing_files:
        try:
            process_image(image_file)
        except Exception as e:
            print(f"Failed to process {image_file}: {e}")

# Save the DataFrame to a CSV file
df.to_csv('image_descriptions.csv', index=False)

