import streamlit as st
import requests
import glob
import pandas as pd
from PIL import Image
import os
from io import BytesIO
import json
import base64  
from pathlib import Path
from openai import OpenAI
from rich import print

# Set up the page
st.set_page_config(page_title="Image Description Generator", layout="wide")
st.title("📷 Image Description Generator")
st.write("Upload a folder of images, and the AI will describe them.")

# Initialize or load the DataFrame
@st.cache_data
def load_or_create_dataframe(filename='image_descriptions.csv'):
    if os.path.isfile(filename):
        df = pd.read_csv(filename)
    else:
        df = pd.DataFrame(columns=['image_file', 'description'])
    return df

df = load_or_create_dataframe()

# Settings expander
with st.expander("⚙️ Settings", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        folder_path = st.text_input("Folder path with images:", 
                                  value=r"C:\Users\dasmo\OneDrive\Documents\OSIX\DC25\imgs")
    with col2:
        api_url = st.text_input("API URL:", value="http://localhost:1234/v1")
        api_key = st.text_input("API Key:", value="lm-studio", type="password")
        lm_model = st.text_input("API Key:", value="gemma-3-12b-it")

# Function to encode image to base64
def encode_image(image_file):
    image = Image.open(image_file)
    image_rgb = image.convert("RGB")
    img_byte_arr = BytesIO()
    image_rgb.save(img_byte_arr, format="JPEG")
    return base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")

# Function to generate description
def generate_description(base64_image, api_url, api_key):
    client = OpenAI(base_url=api_url, api_key=api_key)
    completion = client.chat.completions.create(
        model = lm_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What is this image about?"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            },
        ],
    )
    return completion.choices[0].message.content

# Process button
if st.button("🚀 Process Images", type="primary"):
    if not folder_path or not os.path.exists(folder_path):
        st.error("Please enter a valid folder path!")
    else:
        # Get image files
        image_files = list(Path(folder_path).glob("Screenshot*.png"))
        image_files.sort()
        
        if not image_files:
            st.warning("No Screenshot*.png files found in the folder!")
        else:
            st.info(f"Found {len(image_files)} images to process...")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            results = []
            
            for i, image_file in enumerate(image_files):
                # Skip if already processed
                filename = os.path.basename(image_file)
                existing_files = [os.path.basename(path) for path in df['image_file'].values]
                
                if filename not in existing_files:
                    status_text.text(f"Processing {filename}... ({i+1}/{len(image_files)})")
                    
                    try:
                        base64_image = encode_image(image_file)
                        description = generate_description(base64_image, api_url, api_key)
                        results.append({"image_file": str(image_file), "description": description})
                        
                        # Display preview
                        with st.expander(f"Processed: {filename}", expanded=False):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.image(image_file, caption=filename, width=300)
                            with col2:
                                st.write(description)
                    except Exception as e:
                        st.error(f"Failed to process {filename}: {str(e)}")
                        continue
                    
                    progress_bar.progress((i + 1) / len(image_files))
            
            # Update DataFrame
            if results:
                new_df = pd.DataFrame(results)
                df = pd.concat([df, new_df], ignore_index=True)
                df.to_csv('image_descriptions.csv', index=False)
                st.success(f"✅ Successfully processed {len(results)} new images!")
            else:
                st.info("No new images to process.")

# Show existing data
st.subheader("📊 Existing Descriptions")
st.dataframe(df, use_container_width=True)

# Download button
if not df.empty:
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name='image_descriptions.csv',
        mime='text/csv',
    )