from fastapi import FastAPI, UploadFile, HTTPException, Form, File
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from io import BytesIO
import base64
from openai import OpenAI
import os
import cv2
import tempfile
import logging
import mimetypes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    base_url=os.getenv("API_URL", "http://localhost:1234/v1"),
    api_key=os.getenv("API_KEY", "lm-studio")
)

ALLOWED_TYPES = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'video/mp4': ['.mp4']
}

def validate_file_type(filename: str, content: bytes) -> str:
    """Validate file type using extension and content"""
    # Check extension first
    ext = os.path.splitext(filename)[1].lower()
    for mime_type, extensions in ALLOWED_TYPES.items():
        if ext in extensions:
            # Quick content validation
            if mime_type.startswith('image'):
                try:
                    Image.open(BytesIO(content))
                    return mime_type
                except:
                    continue
            elif mime_type == 'video/mp4':
                # Basic MP4 header check (0x00 0x00 0x00 0x20 0x66 0x74 0x79 0x70)
                if len(content) > 8 and content[4:8] == b'ftyp':
                    return mime_type
    raise ValueError("Unsupported or invalid file type")

def encode_image(image: Image.Image):
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format="JPEG", quality=85)
    return base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")

def extract_video_frame(video_path: str):
    """Extract middle frame from video with error handling"""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error("Failed to open video file")
            return None
            
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0:
            logger.error("Video has 0 frames")
            return None
            
        target_frame = total_frames // 2
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(frame)
        else:
            logger.error("Failed to read video frame")
            return None
    except Exception as e:
        logger.error(f"Video processing error: {str(e)}")
        return None

@app.post("/describe")
async def describe_media(
    file: UploadFile = File(...),
    model: str = Form("gemma-3-12b-it"),
    prompt: str = Form("What is this media about?")
):
    tmp_path = None
    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(400, "Empty file uploaded")

        try:
            file_type = validate_file_type(file.filename, content)
        except ValueError as e:
            raise HTTPException(400, str(e))

        if file_type.startswith("image/"):
            try:
                image = Image.open(BytesIO(content))
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                base64_image = encode_image(image)
            except Exception as e:
                raise HTTPException(400, f"Invalid image file: {str(e)}")

        elif file_type == "video/mp4":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            image = extract_video_frame(tmp_path)
            if not image:
                raise HTTPException(400, "Could not extract frame from video")
            base64_image = encode_image(image)

        # Generate description (same as before)
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                        ],
                    }
                ],
                max_tokens=300  # Added limit
            )
            description = completion.choices[0].message.content
        except Exception as e:
            raise HTTPException(502, f"AI service error: {str(e)}")

        return {
            "media_file": file.filename,  # Changed to match frontend
            "description": description
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(500, "Internal server error")

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except:
                pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)