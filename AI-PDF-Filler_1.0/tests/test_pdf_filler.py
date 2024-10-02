import unittest
import os
from src.main import process_pdf
from src.ollama_utils import add_current_date_to_context, read_context_file
from src.pdf_utils import pdf_to_images, images_to_pdf

class TestPDFFiller(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.sample_pdf = os.path.join(self.test_dir, '..', 'sample_data', 'input_pdf.pdf')
        self.sample_context = os.path.join(self.test_dir, '..', 'sample_data', 'input_context.txt')
        self.output_dir = os.path.join(self.test_dir, 'test_output')
        os.makedirs(self.output_dir, exist_ok=True)

    def test_process_pdf(self):
        context = read_context_file(self.sample_context)
        context_with_date = add_current_date_to_context(context)
        output_filename = 'test_output.pdf'
        output_pdf = process_pdf(self.sample_pdf, self.output_dir, context_with_date, output_filename)
        self.assertTrue(os.path.exists(output_pdf))

    def test_pdf_to_images(self):
        images = pdf_to_images(self.sample_pdf, self.output_dir)
        self.assertTrue(len(images) > 0)
        for image_path in images:
            self.assertTrue(os.path.exists(image_path))

    def test_images_to_pdf(self):
        images = pdf_to_images(self.sample_pdf, self.output_dir)
        output_pdf = os.path.join(self.output_dir, 'test_combined.pdf')
        images_to_pdf(images, output_pdf)
        self.assertTrue(os.path.exists(output_pdf))

if __name__ == '__main__':
    unittest.main()
