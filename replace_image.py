import os
import requests
import uuid
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv('.env.local')

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(url, key)

def replace_image(order_id: str, file_path: str):
    order_data = (
        supabase.from_("book_orders")
        .select("child_images, child_name, order_seq_number")
        .match({"order_seq_number": order_id})
        .single()
        .execute()
    )

    child_images = order_data.data.get("child_images", [])
    if len(child_images) == 0:
      raise "Image not found!"

    storage_path = child_images[0]

    try:
        # Upload the file to Supabase storage
        with open(file_path, "rb") as file:
            response = supabase.storage.from_("mychildartbook").update(
                file=file,
                path=storage_path,
                file_options={"content-type": "image/jpg"}
            )
        
        print(f"Image uploaded successfully to {storage_path}")
        return storage_path
    except Exception as e:
        print(f"Failed to upload image: {e}")
        return None

if __name__ == "__main__":
    book_id = input("input order id: ")
    replace_image(book_id, "img_to_replace.png")