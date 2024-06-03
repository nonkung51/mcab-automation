import os
import requests
from dotenv import load_dotenv
from supabase import create_client, Client
from tqdm import tqdm

load_dotenv('.env.local')

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(url, key)

def download_pictures_by_book_id(book_id: str):
    order_data = (
        supabase.from_("book_orders")
        .select("child_images, child_name, order_seq_number")
        .match({"book": book_id})
        .single()
        .execute()
    )

    order_seq_number = str(order_data.data["order_seq_number"]).zfill(4)
    child_name = order_data.data["child_name"]
    order_number = f"{order_seq_number} {child_name}"

    # Create the directory if it doesn't exist
    if not os.path.exists(os.path.join("downloads", order_number)):
        os.makedirs(os.path.join("downloads", order_number))

    book_data = (
        supabase.from_("book_books").select("*").eq("id", book_id).single().execute()
    )

    pages = book_data.data["pages"]
    for page in tqdm(pages, desc="downloading pages", leave=False):
        page_data = (
            supabase.from_("book_pages")
            .select("page_number, status, output_url, comfy_storage_url, output_from")
            .eq("id", page)
            .single().execute()
        )

        page_number = page_data.data["page_number"]
        status = page_data.data["status"]
        output_url = page_data.data["output_url"]
        comfy_storage_url = page_data.data["comfy_storage_url"]
        output_from = page_data.data["output_from"]

        # Determine the URL to download from
        download_url = comfy_storage_url if comfy_storage_url else output_url
        # Define the file path
        file_path = os.path.join(os.path.join("downloads", order_number), f"page{page_number}.png")

        if comfy_storage_url:
            response = requests.get(comfy_storage_url)
            if response.status_code == 200:
                with open(file_path, 'wb') as file:
                    file.write(response.content)
        else:
            with open(file_path, 'wb+') as file:
                response = supabase.storage.from_('mychildartbook').download(output_url)
                file.write(response)


if __name__ == "__main__":
    book_ids = []
    print("input book ids (newline-separated). press \"enter\" twice to finish:")
    while True:
        book_id = input()
        if book_id == "":
            break
        book_ids.append(book_id)

    print("start downloading bruh!")
    for book_id in tqdm(book_ids, desc="downloading books", leave=True):
        book_id = book_id.strip()
        if book_id:
            download_pictures_by_book_id(book_id=book_id)

