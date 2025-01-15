import os
from argparse import ArgumentParser
import base64
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client import file, client, tools
from google.oauth2 import service_account
from datetime import datetime
import re
import json
import requests
import sys


# Add the flag to sys.argv
# sys.argv.append('--noauth_local_webserver')

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
SERVICE_ACCOUNT_FILE = '../service.json'


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import arxiv
from bs4 import BeautifulSoup

def get_paper_info(url):
    # print(url)
    if 'arxiv' in url:
        return get_arxiv_paper_info(url)
    elif 'biorxiv' in url or 'medrxiv' in url:
        return get_biorxiv_medrxiv_paper_info(url)
    else:
        raise ValueError("Unsupported URL")

def get_arxiv_paper_info(arxiv_url):
    # print(arxiv_url)
    paper_id = arxiv_url.split('/')[-1]
    search = arxiv.Search(id_list=[paper_id])

    for result in search.results():
        abstract = result.summary
        pdf_link = result.pdf_url
        return abstract, pdf_link

def get_biorxiv_medrxiv_paper_info(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        abstract_div = soup.find('div', class_='abstract')
        if abstract_div:
            abstract = abstract_div.text.strip()
        else:
            abstract = "Abstract not found"

        pdf_link_tag = soup.find('a', class_='article-dl-pdf-link')
        if pdf_link_tag:
            pdf_link = f"https://{url.split('/')[2]}{pdf_link_tag['href']}"
        else:
            pdf_link = "PDF link not found"
    except:
        abstract, pdf_link = '',''
    return abstract, pdf_link

# def get_abstract(url: str) -> str:
#     abstract = "Abstract not found"
#     response = requests.get(url)
#     soup = BeautifulSoup(response.content, 'html.parser')
#
#     if 'arxiv' in url:
#         # Find the blockquote with 'abstract' in the class name
#         abstract_block = soup.find('blockquote', class_=lambda x: x and 'abstract' in x)
#         if abstract_block:
#             # Find the span with class 'descriptor' and get the text after it
#             descriptor = abstract_block.find('span', class_='descriptor')
#             if descriptor:
#                 abstract = descriptor.next_sibling.strip()
#
#     elif 'biorxiv' in url or 'medrxiv' in url:
#         # Find the meta tag with name containing 'Description'
#         meta_tag = soup.find('meta', attrs={'name': lambda x: x and 'Description' in x})
#         if meta_tag:
#             abstract = meta_tag.get('content', '').strip()
#     # print(abstract)
#     return abstract

def setup_driver():
    # Setup WebDriver
    options = Options()
    options.add_argument("--headless")  # Ensures Chrome launches in headless mode
    options.add_argument("--disable-gpu")  # Disables GPU hardware acceleration
    options.add_argument("--no-sandbox")  # Bypass OS security model (important for some Linux environments)
    options.add_argument("--window-size=1920,1080")  # Specify the window size

    # service = Service(executable_path=chromium)
    # driver = webdriver.Chrome(service=service, options=options)
    driver = webdriver.Chrome(options=options)
    return driver

# driver = setup_driver()
#
# def get_pdf_url(url):
#     global driver
#
#     # try:
#     if True:
#         # print(url)
#         pdf_link = None
#
#         # Check the domain in the URL
#         if 'medrxiv' in url:
#             driver.get(url)
#             # print('medrxiv')
#             pdf_link_element = WebDriverWait(driver, 10).until(
#                 EC.presence_of_element_located((By.XPATH, "//a[contains(@class, 'article-dl-pdf-link') and contains(@href, '.full.pdf')]"))
#             )
#             if pdf_link_element:
#                 pdf_link = pdf_link_element.get_attribute('href')
#
#         elif 'biorxiv' in url:
#             driver.get(url)
#             # print('biorxiv')
#             pdf_link_element = WebDriverWait(driver, 10).until(
#                 EC.presence_of_element_located((By.XPATH, "//a[contains(@class, 'article-dl-pdf-link') and contains(@href, '.full.pdf')]"))
#             )
#             if pdf_link_element:
#                 pdf_link = pdf_link_element.get_attribute('href')
#
#         elif 'arxiv' in url:
#             # print('arxiv')
#             driver.get(url)
#             print(url)
#             if 'arxiv' in url:
#                 pdf_link = url.replace('abs', 'pdf')
#             pdf_link_element = WebDriverWait(driver, 10).until(
#                 EC.presence_of_element_located((By.XPATH, "//a[contains(@class, 'mobile-submission-download')]"))
#             )
#             if pdf_link_element:
#                 pdf_link = pdf_link_element.get_attribute('href')
#
#         if pdf_link:
#             # print(pdf_link)
#             return pdf_link
#         else:
#             return None

    # except Exception as e:
    #     print(f"Error fetching URL: {e}")
    #     return None


def parse_email_content(content):
    papers = []
    url = ''
    # Split the content by "TITLE:" to get individual paper entries
    entries = re.split(r'TITLE:', content)[1:]

    for entry in entries:
        # Handle the last entry which ends with <div class="container">
        if '<div class="container"' in entry:
            entry = entry.split('<div class="container"')[0]

        # Extract the URL from the hyperlink above the HIGHLIGHTS field label
        url_match = re.search(r'<a href="([^"]+)"[^>]*>\s*<span[^>]*>\s*<u>\s*HIGHLIGHT\s*</u>\s*</span>\s*</a>', entry)
        if url_match:
            url = url_match.group(1)
            # Check if the URL contains "arxiv" and extract the ID
            if 'arxiv' in url:
                arxiv_id_match = re.search(r'arxiv-([0-9.]+)', url)
                if arxiv_id_match:
                    arxiv_id = arxiv_id_match.group(1)
                    url = f'https://arxiv.org/abs/{arxiv_id}'
            # Check if the URL contains "medrxiv" and extract the ID
            elif 'medrxiv' in url:
                medrxiv_id_match = re.search(r'medrxiv-([0-9.]+)', url)
                if medrxiv_id_match:
                    medrxiv_id = medrxiv_id_match.group(1)
                    parts = medrxiv_id.split('.', 2)
                    medrxiv_id = f'{parts[0]}.{parts[1]}/{parts[2]}'
                    url = f'https://www.medrxiv.org/content/{medrxiv_id}'
            # Check if the URL contains "biorxiv" and extract the ID
            elif 'biorxiv' in url:
                biorxiv_id_match = re.search(r'biorxiv-([0-9.]+)', url)
                if biorxiv_id_match:
                    biorxiv_id = biorxiv_id_match.group(1)
                    parts = biorxiv_id.split('.', 2)
                    biorxiv_id = f'{parts[0]}.{parts[1]}/{parts[2]}'
                    url = f'https://www.biorxiv.org/content/{biorxiv_id}'

        # Extract title
        title_match = re.search(r'<a[^>]+href="[^"]+"[^>]*>([^<]+)</a>', entry)
        if title_match:
            title = title_match.group(1).strip()
        else:
            continue

        # Extract authors
        authors_match = re.search(r'AUTHORS:\s*(.*?)<br>', entry)
        authors = authors_match.group(1).strip() if authors_match else ""

        # Extract category
        category_match = re.search(r'CATEGORY:\s*(.*?)<br>', entry)
        category = category_match.group(1).strip() if category_match else ""

        # Extract highlight
        highlight_match = re.search(r'HIGHLIGHT</u></span></a>:\s*(.*?)<br>', entry, re.DOTALL)
        highlight = highlight_match.group(1).strip() if highlight_match else ""

        pdf_url = ''
        abstract = ''
        try:
            if len(url) > 1:
                abstract, pdf_url = get_paper_info(url)
                # print(pdf_url)
            paper = {
                'title': title,
                'authors': authors,
                'category': category,
                'highlight': highlight,
                'url': url,
                'pdf_url': pdf_url,
                'abstract': abstract
            }
            # print(paper)
            papers.append(paper)
        except:
            continue

    return papers

def get_credentials():
    """Gets valid user credentials from storage."""
    if os.path.exists('/token.json'):
        print('token exists')
    if os.path.exists('/credentials.json'):
        print('creds exist')


    flags = tools.argparser.parse_args('--auth_host_name localhost --logging_level INFO --noauth_local_webserver'.split())
    try:
        credential_path = '../token.json'
        store = file.Storage(credential_path)
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets('/credentials.json', SCOPES)
            creds = tools.run_flow(flow, store, flags)
    except:
        print('exception')
        flow = client.flow_from_clientsecrets('/credentials.json', SCOPES)
        creds = tools.run_flow(flow, store, flags)
    return creds

def get_service():
    """Builds the Gmail API service."""
    creds = get_credentials()
    return build('gmail', 'v1', credentials=creds)

def get_messages(service, user_id='me', query='from:digest@paperdigest.org subject:"Paper Digest"'):
    """List all Messages of the user's mailbox matching the query."""
    try:
        print(query)
        # today = datetime.now().strftime('%Y/%m/%d')
        # query += f' after:{today}'
        response = service.users().messages().list(userId=user_id, q=query).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])
        return messages
    except HttpError as error:
        print(f'An error occurred: {error}')
        return []

def get_message(service, user_id, msg_id):
    """Get a Message with given ID."""
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id, format='full').execute()
        return message
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None


def parse_message(message):

    email_data = message["payload"]["headers"]
    # for values in email_data:
    #     name = values["name"]

    # I added the below script.
    for p in message["payload"]["parts"]:
        if p["mimeType"] in ["text/plain", "text/html"]:
            data = base64.urlsafe_b64decode(p["body"]["data"]).decode("utf-8")
            data = parse_email_content(data)
    return data


def main():
    service = get_service()
    messages = get_messages(service)
    all_papers = []

    for msg in messages:
        message = get_message(service, 'me', msg['id'])
        if message:
            papers = parse_message(message)
            all_papers.extend(papers)
            # print(all_papers)

    with open('papers-{}.json'.format(datetime.utcnow().strftime("%Y%m%d")), 'w') as f:
        json.dump(all_papers, f, indent=2)

if __name__ == '__main__':
    driver = setup_driver()
    main()

    driver.quit()