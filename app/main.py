import datetime
import subprocess
import os
from dotenv import load_dotenv
load_dotenv()

def main():
    start_date = os.environ.get('start_date',datetime.date.today().strftime("%Y%m%d"))
    end_date = start_date

    subprocess.run([
        "python", "/app/get_papers_for_range_of_dates.py",
        "-sd", start_date,
        "-ed", end_date
    ])
    subprocess.run(["python", "/app/interact_docanalyzer_unprocessed_folders.py"])

if __name__ == "__main__":
    main()