import pymupdf
from PIL import Image
import io
import os
import sys

def extract_images_with_transparency_handling(pdf_path):
    output_folder = os.path.dirname(os.path.abspath(pdf_path))
    pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
    prefix = f"output_images_{pdf_basename}_"

    doc = pymupdf.open(pdf_path)
    img_count = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)

        for img in image_list:
            base_xref = img[0]
            smask_xref = img[1]

            print(f"Processing: Page {page_num+1}, XREF {base_xref}, SMask XREF {smask_xref}")

            try:
                base_image_dict = doc.extract_image(base_xref)
                base_pixmap = pymupdf.Pixmap(doc, base_xref)
                
                if base_pixmap.alpha:
                    pil_base = Image.frombytes("RGBA", [base_pixmap.width, base_pixmap.height], base_pixmap.samples)
                    
                else:
                    pil_base = Image.frombytes("RGB", [base_pixmap.width, base_pixmap.height], base_pixmap.samples)
                    
                if smask_xref > 0:
                    smask_pixmap = pymupdf.Pixmap(doc, smask_xref)
                    
                    if smask_pixmap.colorspace.n == 1:
                        pil_mask = Image.frombytes("L", [smask_pixmap.width, smask_pixmap.height], smask_pixmap.samples)
                        final_image = Image.new("RGBA", (base_pixmap.width, base_pixmap.height))
                        
                        if pil_base.size != pil_mask.size:
                            print(f"Warning: XREF {base_xref} and SMask {smask_xref} : non consistent dimensions, cannot apply mask. Saving base image without transparency.")
                            pil_base.save(os.path.join(output_folder, prefix + f"image_p{page_num+1}_xref{base_xref}.png"))
                            img_count += 1
                            continue
                        
                        final_image.paste(pil_base, (0, 0))
                        final_image.putalpha(pil_mask)

                        filename = os.path.join(output_folder, prefix + f"image_p{page_num+1}_xref{base_xref}_rgba.png")
                        final_image.save(filename)
                        print(f"Saved RGBA image: {filename}")

                    else:
                        print(f"Warning: XREF {smask_xref} is not a standard grayscale mask, cannot composite. Saving base image only.")
                        pil_base.save(os.path.join(output_folder, prefix + f"image_p{page_num+1}_xref{base_xref}.png"))

                else:
                    ext = base_image_dict["ext"]
                    filename = os.path.join(output_folder, prefix + f"image_p{page_num+1}_xref{base_xref}.{ext}")
                    pil_base.save(filename)
                    print(f"Saved image without transparency: {filename}")

                img_count += 1

            except Exception as e:
                print(f"Processing image xref {base_xref} failed: {e}")

    print(f"Extraction completed. Total images processed: {img_count}. Output directory: {output_folder}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: Drag and drop a PDF file onto the script file icon, or specify the PDF path via command line.")
        print("Example: python PDF_Image_Extractor_Lossless.py C:\\path\\to\\file.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file does not exist: {pdf_path}")
        sys.exit(1)

    extract_images_with_transparency_handling(pdf_path)