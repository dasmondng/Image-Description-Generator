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
from typing import List

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
    ext = os.path.splitext(filename)[1].lower()
    for mime_type, extensions in ALLOWED_TYPES.items():
        if ext in extensions:
            if mime_type.startswith('image'):
                try:
                    Image.open(BytesIO(content))
                    return mime_type
                except:
                    continue
            elif mime_type == 'video/mp4':
                if len(content) > 8 and content[4:8] == b'ftyp':
                    return mime_type
    raise ValueError("Unsupported or invalid file type")

def encode_image(image: Image.Image) -> str:
    """Convert PIL Image to base64"""
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format="JPEG", quality=85)
    return base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")

def extract_key_frames(video_path: str, num_frames: int = 3) -> List[Image.Image]:
    """Extract evenly spaced key frames from video"""
    frames = []
    cap = cv2.VideoCapture(video_path)
    try:
        if not cap.isOpened():
            raise ValueError("Could not open video file")
            
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames < 1:
            raise ValueError("Video has no frames")
            
        num_frames = min(num_frames, total_frames)
        
        for i in range(num_frames):
            frame_pos = int(total_frames * (i + 1) / (num_frames + 1))
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            ret, frame = cap.read()
            if ret:
                frames.append(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
            else:
                logger.warning(f"Failed to read frame at position {frame_pos}")
                
        if not frames:
            raise ValueError("No frames extracted")
            
    finally:
        cap.release()
    return frames

@app.post("/describe")
async def describe_media(
    file: UploadFile = File(...),
    model: str = Form("gemma-3-12b-it"),
    prompt: str = Form("What is this media about?"),
    num_frames: int = Form(3)
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
                frame_contents = [{
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                        "detail": "auto"
                    }
                }]
            except Exception as e:
                raise HTTPException(400, f"Invalid image file: {str(e)}")

        elif file_type == "video/mp4":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(content)
                tmp_path = tmp.name
                
            try:
                frames = extract_key_frames(tmp_path, num_frames)
                frame_contents = []
                for frame in frames:
                    base64_image = encode_image(frame)
                    frame_contents.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "low"
                        }
                    })
            except Exception as e:
                raise HTTPException(400, f"Video processing failed: {str(e)}")

        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            *frame_contents
                        ],
                    }
                ],
                max_tokens=500
            )
            description = completion.choices[0].message.content
        except Exception as e:
            raise HTTPException(502, f"AI service error: {str(e)}")

        return {
            "media_file": file.filename,
            "description": description,
            "processed_frames": len(frame_contents),
            "frame_base64": frame_contents[0]["image_url"]["url"] if frame_contents else None
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
