from fastapi import FastAPI, Query
from typing import List
import requests
from PIL import Image
from io import BytesIO
from fastapi.responses import StreamingResponse
from urllib.parse import unquote
import json

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Perhaps, You're lost buddy"}

@app.get("/merge-images-to-pdf")
async def merge_images_to_pdf(urls: str = Query(...)):
  try:
      decoded_urls = json.loads(unquote(urls))
      images = []
      
      for url in decoded_urls:
          print("Downloading...", url)
          response = requests.get(url)
          img = Image.open(BytesIO(response.content))
          images.append(img.convert("RGB"))
      
      pdf_bytes = BytesIO()
      images[0].save(pdf_bytes, format='PDF', save_all=True, append_images=images[1:])
      pdf_bytes.seek(0)
      
      return StreamingResponse(pdf_bytes, media_type='application/pdf', headers={"Content-Disposition": "attachment; filename=merged_images.pdf"})
      
  except Exception as e:
      print(e)
      return {"error": "An error occurred while processing the images."}, 500
