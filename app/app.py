import re
from flask import Flask, jsonify, render_template, send_from_directory, request
import os
from datetime import datetime
import json

app = Flask(__name__)

DATA_DIR = '/data'
initial_datetime = datetime.now().strftime('%Y%m%d%H%M%S')

def load_paper_info():
    paper_info = {}
    for root, dirs, files in os.walk(DATA_DIR):
        for file in files:
            if file.endswith('.json') and re.match(r'\d{8}\.json', file):
                json_file = os.path.join(root, file)
                with open(json_file, 'r') as f:
                    additional_info = json.load(f)
                    for key in additional_info:
                        key2 = key.replace('.txt', '')
                        paper_info[key2] = {'desc': additional_info[key]}
            elif 'papers_and_scores' in file and file.endswith('.json'):
                json_file = os.path.join(root, file)
                with open(json_file, 'r') as f:
                    papers = json.load(f)
                for paper in papers:
                    sanitized_title = sanitize_filename(paper['title']).replace('.txt', '')
                    if sanitized_title in paper_info:
                        paper_info[sanitized_title]['eval'] = paper
    return paper_info

@app.before_first_request
def initialize_cache():
    global paper_cache
    paper_cache = load_paper_info()

def get_pdf_files():
    pdf_files = []
    for root, dirs, files in os.walk(DATA_DIR):
        for file in files:
            if file.endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    pdf_files.sort()
    return pdf_files

def sanitize_filename(title):
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', title)

def get_paper_info(filename):
    paper_info = {}
    for root, dirs, files in os.walk(DATA_DIR):
        for file in files:

            if file.endswith('.json') and re.match(r'\d{8}\.json', file):
                json_file = os.path.join(root, file)
                with open(json_file, 'r') as f:
                    additional_info = json.load(f)
                    for key in additional_info:
                        key2 = key.replace('.txt','')
                        print(key2)
                        print(additional_info[key])
                        # adinfk = eval(additional_info[key])
                        # print(type(additional_info[key]))
                        paper_info[key2] = {'desc': additional_info[key]}
            elif 'papers_and_scores' in file and file.endswith('.json'):
                json_file = os.path.join(root, file)
                with open(json_file, 'r') as f:
                    papers = json.load(f)
                for paper in papers:
                    sanitized_title = sanitize_filename(paper['title']).replace('.txt','')
                    print(sanitized_title)
                    if sanitized_title in paper_info:
                        paper_info[sanitized_title]['eval'] = paper

                        # paper_info[key] = additional_info[key]
                # paper_info.update(additional_info)
    if filename in paper_info:
        return {filename: paper_info[filename]}
    return {}

@app.route('/')
def index():
    pdf_files = get_pdf_files()
    return render_template('index.html', pdf_files=pdf_files)

@app.route('/pdf/<path:filename>')
def get_pdf(filename):
    return send_from_directory(DATA_DIR, filename)

@app.route('/info/<filename>')
def get_info(filename):
    global paper_cache
    # paper_info = get_paper_info(filename)
    paper_info = paper_cache[filename]
    print(paper_info)
    print(jsonify(paper_info))
    return jsonify(paper_info)


@app.route('/get_vote/<paper_title>', methods=['GET'])
def get_vote(paper_title):
    global all_votes

    # filename = f'votes-{initial_datetime}.json'
    # filepath = os.path.join(DATA_DIR, filename)
    #
    # if os.path.exists(filepath):
    #     with open(filepath, 'r') as file:
    #         votes = json.load(file)
    vote = all_votes.get(paper_title, 0)

    return jsonify({'paper_title': paper_title, 'vote': vote})

@app.route('/get_all_votes', methods=['GET'])
def get_all_votes():
    global all_votes
    for root, dirs, files in os.walk(DATA_DIR):
        for file in files:
            if file.startswith('votes-') and file.endswith('.json'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    votes = json.load(f)
                    all_votes.update(votes)


@app.route('/save_vote', methods=['POST'])
def save_vote():
    data = request.json
    paper_title = data.get('paper_title')
    vote = data.get('vote')
    filename = f'votes-{initial_datetime}.json'
    filepath = os.path.join(DATA_DIR, filename)

    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            votes = json.load(file)
    else:
        votes = {}

    votes[paper_title] = vote

    with open(filepath, 'w') as file:
        json.dump(votes, file)

    return jsonify({'status': 'success'})

if __name__ == '__main__':
    paper_cache = {}
    all_votes = {}
    get_all_votes()
    app.run(host='0.0.0.0', port=5000)