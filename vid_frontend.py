import streamlit as st
import pandas as pd
import requests
import os

# Page setup
st.set_page_config(page_title="Media Analysis", layout="wide")
st.title("🎥 Media Analyzer")
st.write("Upload images/videos to analyze with AI")

# Initialize or load DataFrame
@st.cache_data
def load_or_create_dataframe(filename='media_descriptions.csv'):
    if os.path.isfile(filename):
        return pd.read_csv(filename)
    return pd.DataFrame(columns=['media_file', 'description', 'frames_processed'])

df = load_or_create_dataframe()

# Settings
with st.expander("⚙️ Settings", expanded=True):
    backend_url = st.text_input(
        "Backend API URL:", 
        value="http://localhost:8000"
    )
    model = st.text_input("Model:", value="gemma-3-12b-it")
    prompt = st.text_input("Prompt:", value="Describe the key elements in this video")
    num_frames = st.slider("Frames to analyze", 3, 5, 4)
    max_file_size = 50

# File uploader
uploaded_files = st.file_uploader(
    "Upload media:",
    type=["png", "jpg", "jpeg", "mp4"],
    accept_multiple_files=True
)

def process_media(file):
    try:
        file_size = len(file.getvalue()) / (1024 * 1024)
        if file_size > max_file_size:
            raise ValueError(f"File too large ({file_size:.1f}MB > {max_file_size}MB limit)")
        
        if file.type not in ["image/png", "image/jpeg", "video/mp4"]:
            raise ValueError("Unsupported file type")

        with st.spinner(f"Processing {file.name}..."):
            response = requests.post(
                f"{backend_url}/describe",
                files={"file": (file.name, file.getvalue())},
                data={
                    "model": model,
                    "prompt": prompt,
                    "num_frames": num_frames
                },
                timeout=800
            )
            
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
if st.button("🚀 Analyze Media", type="primary"):
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
                        "description": result["description"],
                        "frames_processed": result.get("processed_frames", 1)
                    })
                    
                    with st.expander(f"Analyzed: {file.name} ({result.get('processed_frames', 1)} frames)", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            if file.type.startswith("image/"):
                                file.seek(0)
                                st.image(file, caption=file.name, width=300)
                            elif file.type == "video/mp4":
                                file.seek(0)
                                st.video(file)
                        with col2:
                            st.write(result["description"])
                
                progress_bar.progress((i + 1) / len(uploaded_files))
                status_text.text(f"Processed {i+1}/{len(uploaded_files)} files")

        if results:
            new_df = pd.DataFrame(results)
            df = pd.concat([df, new_df], ignore_index=True)
            df.to_csv('media_descriptions.csv', index=False)
            st.success(f"✅ Analyzed {len(results)} files!")
        else:
            st.info("No new files processed.")

# Display results
st.subheader("📊 Analysis History")
st.dataframe(df, use_container_width=True)

# Download button
if not df.empty:
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name='video_analysis.csv',
        mime='text/csv',
    )
