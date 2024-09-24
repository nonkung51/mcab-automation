import streamlit as st
import os
import requests
from PIL import Image
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv(".env.local")

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
            .single()
            .execute()
        )

        page_number = page_data.data["page_number"]
        status = page_data.data["status"]
        output_url = page_data.data["output_url"]
        comfy_storage_url = page_data.data["comfy_storage_url"]
        output_from = page_data.data["output_from"]

        file_path = os.path.join(
            os.path.join("downloads", order_number), f"page{page_number}.png"
        )

        try:
            with open(file_path, "wb+") as file:
                response = supabase.storage.from_("mychildartbook").download(output_url)
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
                file=file, path=storage_path, file_options={"content-type": "image/jpg"}
            )

        print(f"Image uploaded successfully to {storage_path}")
        return storage_path
    except Exception as e:
        print(f"Failed to upload image: {e}")
        return None


def pngs_to_pdf(png_folder: str, output_pdf: str):
    png_files = [f for f in os.listdir(png_folder) if f.endswith(".png")]
    png_files.sort(key=lambda x: int(x.replace("page", "").replace(".png", "")))

    images = []

    for file in png_files:
        img_path = os.path.join(png_folder, file)
        img = Image.open(img_path)

        if img.mode == "RGBA":
            img = img.convert("RGB")

        images.append(img)

    if images:
        images[0].save(output_pdf, save_all=True, append_images=images[1:])


def main():
    st.title("choose yer action, matey")

    choices = ["download books", "replace young scallywag's image", "convert to pdf"]
    choice = st.selectbox("select an action, ye landlubber:", choices)

    if choice == choices[0]:
        order_id = st.text_input("enter order id, savvy:")
        if st.button("download books, arrr!"):
            download_pictures_by_book_id(order_id=order_id)
            st.success("download set sail!")

    elif choice == choices[1]:
        order_id = st.text_input("enter order id, savvy:")
        file_path = st.file_uploader(
            "choose the image file to replace, matey:", type=["jpg", "png"]
        )
        if st.button("replace image, aye!"):
            if file_path is not None:
                replace_image(order_id=order_id, file_path=file_path)
                st.success("image replaced, ho ho!")

    elif choice == choices[2]:
        download_folder = "downloads"
        png_folders = [
            f
            for f in os.listdir(download_folder)
            if os.path.isdir(os.path.join(download_folder, f))
        ]
        selected_file = st.selectbox("choose a folder to convert to pdf, matey:", png_folders)
        if st.button("convert to pdf, arrr!"):
            pngs_to_pdf(
                png_folder=f"downloads/{selected_file}", output_pdf=f"generated/{selected_file}.pdf"
            )
            st.success("pdf created, shiver me timbers!")


if __name__ == "__main__":
    main()
