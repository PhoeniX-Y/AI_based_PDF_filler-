import os
from pdf_utils import pdf_to_images, images_to_pdf
from image_processing import detect_and_mark_cells
from ollama_utils import add_current_date_to_context, read_context_file

def process_pdf(input_pdf, output_dir, context, output_filename):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Convert PDF to images
    print("Converting PDF to images...")
    image_paths = pdf_to_images(input_pdf, output_dir)

    # Process each page
    marked_image_paths = []
    for i, image_path in enumerate(image_paths):
        print(f"Processing page {i + 1}...")
        output_image_path = os.path.join(output_dir, f'marked_page_{i + 1}.png')
        detect_and_mark_cells(image_path, output_image_path, context)
        print(f"Marked image for page {i + 1} saved to: {output_image_path}")
        marked_image_paths.append(output_image_path)

        # Clean up temporary image file
        os.remove(image_path)

    # Convert marked images back to PDF
    output_pdf = os.path.join(output_dir, output_filename)
    images_to_pdf(marked_image_paths, output_pdf)
    print(f"Marked PDF saved to: {output_pdf}")

    print("PDF processing complete.")
    return output_pdf  # Return the path to the output PDF

# Remove or comment out the if __name__ == "__main__": block