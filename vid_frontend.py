import streamlit as st
import pandas as pd
import requests
import os
import tempfile  # Add this with other imports at the top
from io import BytesIO
from PIL import Image

# Page setup
st.set_page_config(page_title="Media Description Generator", layout="wide")
st.title("📷🎥 Media Description Generator")
st.write("Upload images (PNG/JPG) or videos (MP4), and the AI will describe them.")

# Initialize or load DataFrame
@st.cache_data
def load_or_create_dataframe(filename='media_descriptions.csv'):
    if os.path.isfile(filename):
        return pd.read_csv(filename)
    return pd.DataFrame(columns=['media_file', 'description'])

df = load_or_create_dataframe()

# Settings
with st.expander("⚙️ Settings", expanded=True):
    backend_url = st.text_input(
        "Backend API URL:", 
        value="http://localhost:8000"
    )
    model = st.text_input("Model:", value="gemma-3-12b-it")
    prompt = st.text_input("Prompt:", value="What is this media about?")
    max_file_size = st.number_input("Max file size (MB)", min_value=1, value=50)

# File uploader
uploaded_files = st.file_uploader(
    "Upload media:",
    type=["png", "jpg", "jpeg", "mp4"],
    accept_multiple_files=True
)

def process_media(file):
    try:
        # Verify file size
        file_size = len(file.getvalue()) / (1024 * 1024)  # MB
        if file_size > max_file_size:
            raise ValueError(f"File too large ({file_size:.1f}MB > {max_file_size}MB limit)")
        
        # Verify MIME type
        if file.type not in ["image/png", "image/jpeg", "video/mp4"]:
            raise ValueError("Unsupported file type")

        with st.spinner(f"Processing {file.name}..."):
            response = requests.post(
                f"{backend_url}/describe",
                files={"file": (file.name, file.getvalue())},
                data={"model": model, "prompt": prompt},
                timeout=160  # Increased timeout
            )
            
            # Handle API errors
            if response.status_code != 200:
                error_detail = response.json().get("detail", "Unknown error")
                raise requests.exceptions.HTTPError(error_detail)
                
            return response.json()

    except requests.exceptions.RequestException as e:
        st.error(f"Connection failed: {str(e)}")
    except ValueError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"Processing failed: {str(e)}")
    return None

# Process button
if st.button("🚀 Process Media", type="primary"):
    if not uploaded_files:
        st.error("Please upload files first!")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        results = []

        for i, file in enumerate(uploaded_files):
            if file.name not in df['media_file'].values:
                result = process_media(file)
                if result:
                    results.append({
                        "media_file": file.name,
                        "description": result["description"]
                    })
                    with st.expander(f"Processed: {file.name}", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            if file.type.startswith("image/"):
                                try:
                                    file.seek(0)  # Reset file pointer
                                    st.image(file, caption=file.name, width=300)
                                except Exception as e:
                                    st.error(f"Couldn't display image: {str(e)}")
                            elif file.type == "video/mp4":
                                try:
                                    # Save to temp file for reliable playback
                                    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                                        file.seek(0)
                                        tmp.write(file.read())
                                        tmp_path = tmp.name
                
                                    # Display using absolute path
                                    st.video(tmp_path)
                
                                    # Clean up
                                    try:
                                        os.unlink(tmp_path)
                                    except:
                                        pass
                                except Exception as e:
                                    st.error(f"Couldn't display video: {str(e)}")
                        with col2:
                            st.write(result["description"])
                
                progress_bar.progress((i + 1) / len(uploaded_files))
                status_text.text(f"Processed {i+1}/{len(uploaded_files)} files")

        if results:
            new_df = pd.DataFrame(results)
            df = pd.concat([df, new_df], ignore_index=True)
            df.to_csv('media_descriptions.csv', index=False)
            st.success(f"✅ Processed {len(results)} new files!")
        else:
            st.info("No new files processed.")

# Display results
st.subheader("📊 Existing Descriptions")
st.dataframe(df, use_container_width=True)

# Download button
if not df.empty:
    st.download_button(
        label="📥 Download CSV",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name='media_descriptions.csv',
        mime='text/csv',
    )