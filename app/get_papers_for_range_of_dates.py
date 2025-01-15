import json
from datetime import datetime, timedelta
import argparse
import os
import sys
import traceback
from dotenv import load_dotenv
load_dotenv()


from get_research_digest import get_service, get_messages, get_message, parse_message
from score_papers import score_papers
from merge_papers_and_scores import merge_papers_and_scores
from download_pdfs import process_files

done_papers = []

def process_date(date, api_key, output_dir, score_threshold, downloaded_papers, docanalyzer_key):
    global driver
    all_papers = []
    to_download = []
    try:
        service = get_service()
        next_date = (datetime.strptime(date, '%Y/%m/%d') + timedelta(days=1)).strftime('%Y/%m/%d')
        previous_day = (datetime.strptime(date, '%Y/%m/%d') - timedelta(days=0)).strftime('%Y/%m/%d')

        query = f'from:digest@paperdigest.org subject:"Paper Digest" after:{previous_day} before:{next_date}'
        messages = get_messages(service, query=query)
        print('messages', len(messages))

        for msg in messages:
            message = get_message(service, 'me', msg['id'])

            if message:
                papers = parse_message(message)
                print('papers', len(papers))
                papers = [pape for pape in papers if pape['title'] not in done_papers]
                all_papers.extend(papers)
                done_papers.extend([pape['title'] for pape in papers])

        if not all_papers:
            print(f"No papers found for {date}")
            return
        dts = date.replace('/', '')
        papers_file = os.path.join(output_dir, f'papers-{dts}.json')
        with open(papers_file, 'w') as f:
            json.dump(all_papers, f, indent=2)


        scores_file = os.path.join(output_dir, f'scores-{dts}.json')
        score_papers(papers_file, api_key, scores_file)

        output_file = os.path.join(output_dir, f'papers_and_scores-{dts}.json')
        merge_papers_and_scores(papers_file, scores_file, output_file)

        print(f"Processed data for {date}")

        to_download = process_files(output_file, score_threshold, downloaded_papers, docanalyzer_key)

        return to_download
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print('[SignalControl] Exception in line: {}, type: {}, msg1: {}, msg2: {}'.format(exc_tb.tb_lineno, exc_type, traceback.format_exc(), e))
        return []

def main():
    parser = argparse.ArgumentParser(description='Process papers for a range of dates.')
    today = datetime.utcnow().strftime("%Y%m%d")
    parser.add_argument('-sd', '--start_date', type=str, default=today, help='Start date in YYYYMMDD format')
    parser.add_argument('-ed', '--end_date', type=str, default=today, help='End date in YYYYMMDD format')

    args = parser.parse_args()

    start_date = datetime.strptime(args.start_date, '%Y%m%d')
    end_date = datetime.strptime(args.end_date, '%Y%m%d')
    api_key = os.environ['openai_api_key']
    docanalyzer_key = os.environ['docanalyzer_token1']
    score_threshold = float(os.environ.get('score_threshold', 0.5))

    current_date = start_date
    downloaded_papers = []
    base_dir = '/data'
    while current_date <= end_date:
        date_str = current_date.strftime('%Y/%m/%d')
        dtshort = current_date.strftime('%Y%m%d')
        outf = os.path.join(base_dir, dtshort)
        if not os.path.exists(outf):
            os.makedirs(outf)
        print(date_str)
        downloaded_papers = process_date(date_str, api_key, outf, score_threshold, downloaded_papers, docanalyzer_key)
        print(dtshort)
        current_date += timedelta(days=1)

if __name__ == '__main__':
    main()