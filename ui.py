import easygui
import os
import requests
from PIL import Image
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv('.env.local')

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(url, key)

def download_pictures_by_book_id(order_id: str):
    order_data = (
        supabase.from_("book_orders")
        .select("child_images, child_name, book")
        .match({"order_seq_number": order_id})
        .single()
        .execute()
    )

    order_seq_number = str(order_id).zfill(4)
    book_id = order_data.data["book"]
    child_name = order_data.data["child_name"]
    order_number = f"{order_seq_number} {child_name}"

    # Create the directory if it doesn't exist
    if not os.path.exists(os.path.join("downloads", order_number)):
        os.makedirs(os.path.join("downloads", order_number))

    book_data = (
        supabase.from_("book_books").select("*").eq("id", book_id).single().execute()
    )

    pages = book_data.data["pages"]
    for page in pages:
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

        file_path = os.path.join(os.path.join("downloads", order_number), f"page{page_number}.png")

        try:
            with open(file_path, 'wb+') as file:
                response = supabase.storage.from_('mychildartbook').download(output_url)
                file.write(response)
        except Exception as e:
            print(f"Failed to download page {page_number}: {e}")

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

def pngs_to_pdf(png_folder: str, output_pdf: str):
    png_files = [f for f in os.listdir(png_folder) if f.endswith('.png')]
    png_files.sort(key=lambda x: int(x.replace('page', '').replace('.png', '')))

    images = []

    for file in png_files:
        img_path = os.path.join(png_folder, file)
        img = Image.open(img_path)
        
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        images.append(img)

    if images:
        images[0].save(output_pdf, save_all=True, append_images=images[1:])

def main():
    choices = ["download books", "replace children's image", "convert to pdf"]
    choice = easygui.buttonbox("choose an action:", choices=choices)

    if choice == choices[0]:
        order_id = easygui.enterbox("enter order id:")
        download_pictures_by_book_id(order_id=order_id)

    elif choice == choices[1]:
        order_id = easygui.enterbox("enter order id:")
        file_path = easygui.fileopenbox("select the image file to replace:")
        replace_image(order_id=order_id, file_path=file_path)

    elif choice == choices[2]:
        folder_path = easygui.diropenbox("select a folder:")
        book_name = easygui.enterbox("enter book name:")
        pngs_to_pdf(png_folder=folder_path, output_pdf=book_name)
    
    easygui.msgbox("Finish!", title="Complete")

if __name__ == "__main__":
    main()