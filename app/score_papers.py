import os
import json
import requests
from datetime import datetime

def load_papers(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def combine_messages(papers):
    messages = []
    for paper in papers:
        message = f"Title: {paper['title']}\nHighlight: {paper['highlight']}\nAbstract: {paper['abstract']}"
        messages.append(message)
    return messages

def prepare_prompt(researcher_profile, batch_messages):
    return f"""
    Researcher Profile: {researcher_profile}

    How related is each of the listed works to the provided researcher profile? Provide a numerical score in the range 0-1 and justification for each item. Respond in the following JSON format:
    [
      {{
        "title": "Title of the paper",
        "score": numerical_score,
        "justification": "Justification text"
      }},
      ...
    ]

    {batch_messages}
    """

def call_openai_api(prompt, api_key):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    data = {
        "model": "gpt-4o-mini",
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that helps in making comparisons and associations between research outputs and personas responding with JSON."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1500,
        "n": 1,
        "stop": None,
        "temperature": 0.0
    }
    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
    return response.json()

def parse_response(response_json):
    return json.loads(response_json['choices'][0]['message']['content'].strip())

def save_results(results, file_path):
    with open(file_path, 'w') as file:
        json.dump(results, file, indent=2)

def read_researcher_profile(file_path):
    with open(file_path, 'r') as file:
        return file.read().strip()

def score_papers(file_path, api_key, output_file):
    papers = load_papers(file_path)
    messages = combine_messages(papers)

    researcher_profile = read_researcher_profile('../profile.txt')

    results = []
    for i in range(0, len(messages), 10):
        try:
            batch_messages = "\n\n".join(messages[i:i + 10])
            prompt = prepare_prompt(researcher_profile, batch_messages)
            response_json = call_openai_api(prompt, api_key)
            res = parse_response(response_json)
            results.extend(res['results'])
        except Exception as e:
            print(e)
            pass
    save_results(results, output_file)
    print(f"Results saved to {output_file}")

def main():
    file_path = '../get_mail/papers-20241220.json'
    api_key = os.environ['openai_api_key']
    output_file = 'scores-{}.json'.format(datetime.utcnow().strftime("%Y%m%d"))

    score_papers(file_path, api_key, output_file)

if __name__ == '__main__':
    main()