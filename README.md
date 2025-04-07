# Image-Description-Generator
Upload images to LLM (LM Studio) to generate a description

# How to start
Start the **backend**: 
```
python backend.py
```
Start the **frontend**: 
```
python -m streamlit run frontend.py
```
or
```
streamlit run frontend.py
```

# Progression Made
- ✅ Able to connect to llm
- ✅ Able to generate a description
- ✅ Creates an CSV file to upload the description
- ✅ Able to upload files instead of filepath
- ✅ Separate into frontend and backend files
- ✅ User can write their prompt

# Moving Forward
- videos

## Progression on Video Description
The current files, vid_backend.py & vid_frontend.py, are not the finished product.
# Currently Working on / Errors
- After uploading an MP4 file, the app takes a singular frame and sends it to the LLM to process. (Change it to send more frames instead)
- Streamlit is unable to play the processed video. (A white background is shown but audio is perfectly fine)
