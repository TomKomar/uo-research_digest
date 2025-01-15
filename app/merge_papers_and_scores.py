import json
from datetime import datetime

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def save_json(data, file_path):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

def merge_papers_and_scores(papers_path, scores_path, output_paths):
    papers = load_json(papers_path)
    scores = load_json(scores_path)
    if type(output_paths) == str: output_paths = [output_paths]
    scores_dict = {score['title']: score for score in scores}

    for paper in papers:
        title = paper['title']
        if title in scores_dict:
            paper['score'] = scores_dict[title]['score']
            paper['justification'] = scores_dict[title]['justification']

    for output_path in output_paths:
        save_json(papers, output_path)
    print("Papers updated with scores and justifications.")

def main():
    base_dir = '/app/data'
    date_str = datetime.utcnow().strftime("%Y%m%d")
    papers_path = f'{base_dir}/papers-{date_str}.json'
    scores_path = f'{base_dir}/scores-{date_str}.json'
    output_path = f'{base_dir}/papers_and_scores-{date_str}.json'

    merge_papers_and_scores(papers_path, scores_path, output_path)

if __name__ == '__main__':
    main()