# backend.py
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from io import BytesIO
import base64
from openai import OpenAI
import os

app = FastAPI()

# CORS setup (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client (configure via environment variables)
client = OpenAI(
    base_url=os.getenv("API_URL", "http://localhost:1234/v1"),
    api_key=os.getenv("API_KEY", "lm-studio")
)

def encode_image(uploaded_file):
    """Convert image to base64"""
    image = Image.open(BytesIO(uploaded_file))
    image_rgb = image.convert("RGB")
    img_byte_arr = BytesIO()
    image_rgb.save(img_byte_arr, format="JPEG")
    return base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")

@app.post("/describe")
async def describe_image(
    file: UploadFile,
    model: str = "gemma-3-12b-it",
    prompt: str = "What is this image about?"
):
    """API endpoint to generate image descriptions"""
    try:
        base64_image = encode_image(await file.read())
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
        )
        return {
            "image_file": file.filename,
            "description": completion.choices[0].message.content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)