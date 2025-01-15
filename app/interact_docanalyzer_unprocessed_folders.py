import os
from dotenv import load_dotenv
load_dotenv()
token = os.environ['docanalyzer_token1']
token2 = os.environ['docanalyzer_token2']
openai_api_key = os.environ['openai_api_key']
import time
import requests
import json
import logging
from json_to_docx import create_word_document, read_json
import os

def list_folders_with_txt_but_no_docx(root_folder):
    folders_with_txt_no_docx = {}

    for subdir, _, files in os.walk(root_folder):
        txt_files = [file for file in files if file.endswith('.txt')]
        txt_files = [file[:-4] for file in txt_files]
        has_docx = any(file.endswith('.docx') for file in files)

        if txt_files and not has_docx:
            folders_with_txt_no_docx[subdir] = txt_files

    return folders_with_txt_no_docx

def chat_document(API_KEY, doc_id, chat_string):
    url = "https://api.docanalyzer.ai/api/v1/doc/" + doc_id + "/chat"

    payload = {"prompt": chat_string}
    headers = {"Authorization": f"Bearer {API_KEY}"}

    response = requests.request("POST", url, headers=headers, json=payload)

    if response.status_code == 200:
        try:
            response_json = json.loads(response.text)
            # Fetch docid from the nested 'data' property
            return response_json.get('data', {})
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON: {e}")
            return None
    else:
        logging.error(f"API call error: {response.status_code}")
        logging.error(f"API Response: {response.text}")
        return None

def list_documents(token, offset=0, limit=1000):
    all_docs = []
    while True:
        url = f"https://api.docanalyzer.ai/api/v1/doc?offset={offset}&limit={limit}"
        payload = {}
        headers = {
            'Authorization': f'Bearer {token}'
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        resp_json = response.json()
        docs = resp_json.get('data', [])
        if not docs:
            break
        all_docs.extend(docs)
        offset += limit
    return all_docs

if __name__ == '__main__':
    root_folder = r'/data'
    result = list_folders_with_txt_but_no_docx(root_folder)
    processed = []
    for folder, batch in result.items():
        print(f"Folder: {folder}")

        time.sleep(1)
        conclusions = {}
        failed = []
        while len(processed) < len(batch):
            time.sleep(5)
            docs = list_documents(token)
            for enum, doc in enumerate(docs):
                if doc['name'] in processed: continue
                if ' ' in doc['name']: continue
                if '.pdf' in doc['name']: continue
                # print(doc['name'])
                # print(doc['name'][:-4], batch)
                if doc['name'][:-4] not in batch:
                    continue
                # print(doc)
                time.sleep(1)
                try:
                    answer = chat_document(token2, str(doc['docid']), 'Summarize paper background, list research motivations, identified research gap, applications, contribution, tools and techniques, scaling limits. Present method as a step by step process. Describe Top-3 findings from research. List highlights from conclusions and discussion. Find 3 positives and 3 negatives. Provide your answer in json format without any annotations nor formatting, use section title as key and content as value, e.g. {"background": "summary of detected research background information", ...}')

                    conclusions[doc['name']] = answer['answer']
                except:
                    failed.append(doc['docid'])
                    time.sleep(5)
                processed.append(doc['name'])

        if len(conclusions) > 0:
            dest_json1 = os.path.join(root_folder,os.path.basename(folder), os.path.basename(folder)+'.json')
            # dest_json2 = os.path.join('/data', os.path.basename(folder)+'.json')
            with open(dest_json1,'w') as oj:
                json.dump(conclusions,oj)
            # with open(dest_json2,'w') as oj:
            #     json.dump(conclusions,oj)
            dest_docx =  (dest_json1)[:-5]+'.docx'
            data = read_json(dest_json1)
            create_word_document(data, dest_docx, openai_api_key)
            print(dest_docx)

        print(failed)
        time.sleep(5)
