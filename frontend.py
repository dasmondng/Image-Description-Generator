# frontend.py
import streamlit as st
import pandas as pd
import requests
import os
from io import BytesIO

# Page setup
st.set_page_config(page_title="Image Description Generator", layout="wide")
st.title("📷 Image Description Generator")
st.write("Upload images, and the AI will describe them.")

# Initialize or load DataFrame
@st.cache_data
def load_or_create_dataframe(filename='image_descriptions.csv'):
    if os.path.isfile(filename):
        return pd.read_csv(filename)
    return pd.DataFrame(columns=['image_file', 'description'])

df = load_or_create_dataframe()

# Settings
with st.expander("⚙️ Settings", expanded=True):
    backend_url = st.text_input(
        "Backend API URL:", 
        value="http://localhost:8000"  # Default FastAPI port
    )
    model = st.text_input("Model:", value="gemma-3-12b-it")
    prompt = st.text_input("Prompt:", value="Describe this image and take note of any text shown.")

# File uploader
uploaded_files = st.file_uploader(
    "Upload images:",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
)

def process_image(file):
    """Send image to backend for processing"""
    try:
        response = requests.post(
            f"{backend_url}/describe",
            files={"file": (file.name, file.getvalue())},
            params={"model": model, "prompt": prompt}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

# Process button
if st.button("🚀 Process Images", type="primary"):
    if not uploaded_files:
        st.error("Please upload images first!")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        results = []

        for i, file in enumerate(uploaded_files):
            filename = file.name
            if filename not in df['image_file'].values:
                status_text.text(f"Processing {filename}... ({i+1}/{len(uploaded_files)})")
                result = process_image(file)
                if result:
                    results.append(result)
                    with st.expander(f"Processed: {filename}", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.image(BytesIO(file.getvalue()), caption=filename, width=300)
                        with col2:
                            st.write(result["description"])
                progress_bar.progress((i + 1) / len(uploaded_files))

        if results:
            new_df = pd.DataFrame(results)
            df = pd.concat([df, new_df], ignore_index=True)
            df.to_csv('image_descriptions.csv', index=False)
            st.success(f"✅ Processed {len(results)} images!")

# Display results
st.subheader("📊 Existing Descriptions")
st.dataframe(df, use_container_width=True)

# Download button
if not df.empty:
    st.download_button(
        label="📥 Download CSV",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name='image_descriptions.csv',
        mime='text/csv',
    )