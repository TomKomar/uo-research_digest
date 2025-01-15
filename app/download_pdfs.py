# import imutils.paths
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
import os
import json
import re
import requests
import argparse

from interact_docanalyzer_unprocessed_folders import list_documents
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.options import Options

# def setup_driver():
#     options = Options()
#     options.add_argument("--headless")
#     options.add_argument("--disable-gpu")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--window-size=1920,1080")
#     driver = webdriver.Chrome(options=options)
#     return driver

def sanitize_filename(title):
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', title)

# def find_pdf_link(driver, url):
#     driver.get(url)
#     # print(url)
#     pdf_link_element = WebDriverWait(driver, 10).until(
#         EC.presence_of_element_located((By.XPATH, "//a[contains(@class, 'mobile-submission-download')]"))
#     )
#     pdf_link = pdf_link_element.get_attribute('href')
#     return pdf_link

def download_file(url, output_path):
    response = requests.get(url)
    with open(output_path, 'wb') as file:
        file.write(response.content)

def pdf_to_text(pdf_path, text_path):
    """
    Converts a PDF file to a text file.

    Parameters:
    pdf_path (str): The path to the PDF file.
    text_path (str): The path to the output text file.
    """
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

def upload_document(api_key, txt_path):
    """
    Uploads a document to the DocAnalyzer API.

    Parameters:
    api_key (str): The API key for authentication.
    pdf_path (str): The path to the PDF to be uploaded.

    Returns:
    dict: The response from the API.
    """
    url = "https://api.docanalyzer.ai/api/v1/doc/upload/"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    files = {
        "file": open(txt_path, "rb")
    }

    response = requests.post(url, headers=headers, files=files)
    response.raise_for_status()  # Raise an exception for HTTP errors
    print(f'Uploaded {txt_path}')
    return response.json()


def process_files(filename, score_threshold, downloaded_papers, docanalyzer_key):
    # driver = setup_driver()
    to_download = []
    fn = os.path.basename(filename)
    if fn.startswith('papers_and_scores-') and fn.endswith('.json'):
        file_path = filename
        with open(file_path, 'r') as file:
            papers = json.load(file)
        documents_exist = [doc['name'].replace('.txt','') for doc in list_documents(docanalyzer_key)]
        for paper in papers:
            if 'score' not in paper:
                continue
            try:
                if paper['score'] >= score_threshold:
                    if paper['title'] in downloaded_papers: continue
                    sanitized_title = sanitize_filename(paper['title'])

                    pdf_url = paper['pdf_url']
                    if not 'http' in pdf_url: continue

                    output_file_path = os.path.join(os.path.dirname(filename), sanitized_title + '.pdf')
                    output_file_path = output_file_path.replace('\\','/')
                    if not os.path.exists(output_file_path):
                        download_file(pdf_url, output_file_path)
                        print(f"Downloaded: {output_file_path} from {pdf_url}")
                    else:
                        print(f"File exists: {output_file_path}")

                    txtpth = output_file_path[:-4]+'.txt'
                    to_download.append(os.path.basename(txtpth))
                    if os.path.exists(txtpth):
                        print(f"Txt file exists: {txtpth}")
                    else:
                        pdf_to_text(output_file_path, txtpth)
                        print('Transformed',txtpth)
                    if sanitized_title.replace('.pdf', '').replace('.txt', '') in documents_exist:
                        print('Document already exists in DocAnalyzer')
                    else:
                        upload_document(docanalyzer_key, txtpth)
                        print('Uploaded to DocAnalyzer')

            except Exception as e:
                print('Exception:', e)
    # driver.quit()
    return to_download

def main():
    parser = argparse.ArgumentParser(description='Process and download papers based on score threshold.')
    parser.add_argument('-i', '--input_file', default=r'd:\t\pycharm\mygpt\get_mail\20240805\papers_and_scores-20240805.json', help='Input folder containing JSON files')
    parser.add_argument('-s', '--score_threshold', type=float, default=0.5, help='Score threshold for filtering papers')
    parser.add_argument('-o', '--output_folder', default=r'd:\t\pycharm\mygpt\get_mail\20240805', help='Output folder to save downloaded PDFs')
    args = parser.parse_args()

    downloaded_papers = []
    docanalyzer_key = os.environ['docanalyzer_token1']
    downloaded_papers = process_files(args.input_file, args.score_threshold, downloaded_papers, docanalyzer_key)

if __name__ == '__main__':
    main()