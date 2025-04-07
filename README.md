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
- ✅ User can upload either image or video files
- ✅ User can write their prompt
- ✅ Able to generate a description
- ✅ Creates an CSV file to upload the description
- ✅ Separate into frontend and backend files

# Limitations
- Only up to 5 frames of the video will be used for processing

## Notes
The files *vid_backend.py* and *vid_frontend.py* are the finished products. They consist of both image and video description functions. <br/>
The original files, *frontend.py* & *backend.py*, only have the image description function.
