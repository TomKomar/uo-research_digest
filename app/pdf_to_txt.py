import imutils.paths
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError

def pdf_to_text(pdf_path, text_path):
    try:
        # Open the PDF file
        with open(pdf_path, 'rb') as pdf_file:
            reader = PdfReader(pdf_file)
            text = ""

            # Iterate over each page
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()

        # Write the text to the output file
        with open(text_path, 'w', encoding='utf-8', errors='ignore') as text_file:
            text_file.write(text)
    except PdfReadError as e:
        print(f"Error reading {pdf_path}: {e}")

if __name__ == '__main__':
    folder = r'/data'
    for path in imutils.paths.list_files(folder, validExts=(".pdf")):
        pdf_to_text(path, path[:-4]+'-1.txt')