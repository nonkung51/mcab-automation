from PIL import Image
import os

def pngs_to_pdf(png_folder, output_pdf):
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

# Example usage
if __name__ == "__main__":
    png_folder = r'D:\jean_factory\png_to_pdf_converter\images'  # Specify the folder containing your PNG files
    output_pdf = 'output.pdf'  # Specify the name of the output PDF file
    pngs_to_pdf(png_folder, output_pdf)

    print(f"PDF created successfully at {output_pdf}")
