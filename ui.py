import streamlit as st
import os
import requests
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm


def download_pictures_by_book_id(order_id: str, indentification: str):
    # Call API to get order data
    url = "https://order.mychildartbook.com/api/books/admin/get-images-urls"
    querystring = {"orderId": order_id, "indentification": indentification}
    response = requests.get(url, params=querystring)
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}")
    data = response.json()

    order_number = data["orderNumber"]

    # Create the directory if it doesn't exist
    if not os.path.exists(os.path.join("downloads", order_number)):
        os.makedirs(os.path.join("downloads", order_number))

    for page in data["pages"]:
        page_number = page["pageNumber"]
        output_url = page["outputUrl"]

        file_path = os.path.join(
            os.path.join("downloads", order_number), f"page{page_number}.png"
        )

        try:
            # Download the image from the output URL
            response = requests.get(output_url)
            response.raise_for_status()
            
            with open(file_path, "wb+") as file:
                file.write(response.content)
        except Exception as e:
            print(f"Failed to download page {page_number}: {e}")


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

def mm_to_pixels(mm_value, dpi=300):
    """Convert millimeters to pixels at given DPI"""
    return int((mm_value / 25.4) * dpi)

def pngs_to_pdf_us(png_folder: str, output_pdf: str):
    try:
        # Create PDF with precise page sizes
        c = canvas.Canvas(output_pdf)

        # Process page1.png with special dimensions
        page1_path = os.path.join(png_folder, "page1.png")
        if os.path.exists(page1_path):
            # Calculate dimensions in points (1 point = 1/72 inch)
            width_pts = 478.0 * mm
            height_pts = 326.0 * mm
            c.setPageSize((width_pts, height_pts))
            
            # Calculate pixel dimensions for 300 DPI
            width_px = mm_to_pixels(478.0)
            height_px = mm_to_pixels(326.0)
            
            # Draw image at exact dimensions
            c.drawImage(page1_path, 0, 0, width=width_pts, height=height_pts)
            c.showPage()
            print(f"Processed: page1.png (478.0 x 326.0 mm @ 300 DPI)")
            print(f"Pixel dimensions: {width_px} x {height_px} px")
        
        # Process pages 2-35
        for page_num in range(2, 36):
            image_path = os.path.join(png_folder, f"page{page_num}.png")
            if os.path.exists(image_path):
                # Calculate dimensions in points
                width_pts = 216.0 * mm
                height_pts = 286.0 * mm
                c.setPageSize((width_pts, height_pts))
                
                # Calculate pixel dimensions for 300 DPI
                width_px = mm_to_pixels(216.0)
                height_px = mm_to_pixels(286.0)
                
                # Draw image at exact dimensions
                c.drawImage(image_path, 0, 0, width=width_pts, height=height_pts)
                c.showPage()
                print(f"Processed: page{page_num}.png (216.0 x 286.0 mm @ 300 DPI)")
                print(f"Pixel dimensions: {width_px} x {height_px} px")
            else:
                print(f"Warning: page{page_num}.png not found")
        
        # Save the PDF
        c.save()
        print(f"\nPDF created successfully with correct dimensions and 300 DPI: {output_pdf}")
        
    except Exception as e:
        print(f"Error creating PDF: {str(e)}")


def main():
    st.title("choose action:")

    indentification = st.text_input("enter indentification:")
    choices = ["download books", "convert to pdf (th)", "convert to pdf (us)"]
    choice = st.selectbox("select an action:", choices)

    if choice == choices[0]:
        order_id = st.text_input("enter order id, savvy:")
        if st.button("download books"):
            download_pictures_by_book_id(order_id=order_id, indentification=indentification)
            st.success("done")

    elif choice == choices[1]:
        download_folder = "downloads"
        png_folders = [
            f
            for f in os.listdir(download_folder)
            if os.path.isdir(os.path.join(download_folder, f))
        ]
        selected_file = st.selectbox("choose a folder to convert to pdf:", png_folders)
        if st.button("convert to pdf"):
            pngs_to_pdf(
                png_folder=f"downloads/{selected_file}", output_pdf=f"generated/{selected_file}.pdf"
            )
            st.success("pdf created")

    elif choice == choices[2]:
        download_folder = "downloads"
        png_folders = [
            f
            for f in os.listdir(download_folder)
            if os.path.isdir(os.path.join(download_folder, f))
        ]
        selected_file = st.selectbox("choose a folder to convert to pdf:", png_folders)
        if st.button("convert to pdf"):
            pngs_to_pdf_us(
                png_folder=f"downloads/{selected_file}",
                output_pdf=f"generated/{selected_file}.pdf",
            )
            st.success("pdf created")


if __name__ == "__main__":
    main()
