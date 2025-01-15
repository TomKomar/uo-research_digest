# uo-research_digest

## Motivation
The `uo-research_digest` application was developed to streamline the process of managing, analyzing, and summarizing research papers, addressing the needs of researchers overwhelmed by the growing volume of scientific literature. Personally, I often struggle to identify relevant papers amidst vast datasets, assess their importance, and integrate their findings efficiently. This tool consolidates various functionalities into a single pipeline, automating email retrieval, content extraction, scoring based on relevance, and document conversion. The application aims to save researchers significant time and effort while ensuring they stay updated with critical advancements in their fields.

## Functionality
The uo-research_digest application automates the end-to-end workflow for identifying and processing research papers. It begins by retrieving research-related emails from Gmail accounts and extracting metadata such as titles, authors, abstracts, and links. Papers are scored based on their relevance to a specified researcher's profile using the OpenAI API, allowing users to prioritize the most pertinent studies. The application also downloads PDFs of research papers, converts them into text, and analyzes them using the DocAnalyzer API. Furthermore, it includes utilities to convert JSON-formatted paper data into professionally styled Word documents, making it easier for researchers to review, present, and archive their findings. This comprehensive functionality minimizes manual intervention, allowing researchers to focus on analysis rather than administrative tasks.

## Use
To use the uo-research_digest application, start by preparing the required configuration files: an `.env` file containing API keys for OpenAI and DocAnalyzer, and a `credentials.json` file generated from your Google Cloud Platform account and your personal profile in plain text `profile.txt`. Build the Docker image with the command `docker build . -t tgk/uo-research_digest:1`, and run the application using the provided Docker command, mounting the required files and specifying an output folder. The application will retrieve emails, parse their content, and generate scored datasets of research papers. Processed papers are stored in JSON files, and PDFs are downloaded for conversion to text. The text files are uploaded to DocAnalyzer and summaries generated there are put into an MS Word document and saved for printing.

### Required setup

You will need an account with [OpenAI](http://openai.com) and [DocAnalyzer.ai](https://docanalyzer.ai). Email retrieval has been developed for working with [Gmail](https://gmail.google.com). You can join a premium research papers mailing list at [Paper Digest](https://www.paperdigest.org/).  
You will need an `.env` file (see `.env.example`), `credentials.json` and `profile.txt` (see `profile.txt.example`) files to run the script. The .env file should contain the following variables:

```
openai_api_key=YOUR_OPENAI_API_KEY
docanalyzer_token1=YOUR_DOCANALYZER_TOKEN1
docanalyzer_token2=YOUR_DOCANALYZER_TOKEN2
```

The crentials.json file needs to be generated in you Google Cloud Platform account.

profile.txt should contain information about the researcher's profile so that the OpenAI API can score the papers based on the profile.  

If you use different mailing list than Paper Digest, you can change sender and email title string in `.env`, but they may require different parsing than the one used in the scripts.

```
mailing_list_sender=MAILING_LIST_SENDER_ADDRESS
mailing_list_subject=PART_OF_SUBJECT_OF_EMAIL_FROM_MAILING_LIST
```

Build the project with the following command:

```
docker build -t tgk/uo-research_digest:1 .
```

Run the project with the following command:

```
docker run -it --rm -v your/.env:/.env -v your/credentials.json:/credentials.json -v your/profile.txt:/profile.txt -v output/folder:/data tgk/uo-research_digest:1
```
   
Optionally you can use environment variables to pass the fitness threshold (0-1, default 0.5) and date to target email received on a specific day:
```
-e score_threshold=0.5 -e target_date=20250101
```
Equally, you can set any of these in your .env file

### Email Retrieval and Parsing

The process begins with retrieving emails from a Gmail account using the Gmail API. The following functions are involved:

- **`get_credentials()`**: Retrieves user credentials for accessing the Gmail API.
- **`get_service()`**: Builds and returns the Gmail API service.
- **`get_messages(service, user_id, query)`**: Retrieves email messages matching the specified query.
- **`get_message(service, user_id, msg_id)`**: Retrieves a specific email message by its ID.
- **`parse_email_content(content)`**: Parses the email content to extract paper information such as title, authors, category, highlight, URL, PDF link, and abstract.

### Paper Information Extraction

Once the emails are parsed, the next step is to extract detailed information about each paper. This involves determining the source of the paper (e.g., arXiv, bioRxiv, medRxiv) and retrieving the abstract and PDF link:

- **`get_paper_info(url)`**: Determines the source of the paper and calls the appropriate function to get the paper's abstract and PDF link.
- **`get_arxiv_paper_info(arxiv_url)`**: Retrieves the abstract and PDF link for an arXiv paper.
- **`get_biorxiv_medrxiv_paper_info(url)`**: Retrieves the abstract and PDF link for bioRxiv or medRxiv papers.

### Paper Scoring

The extracted paper information is then scored based on its relevance to a specified researcher's profile using the OpenAI API. The following functions are used:

- **`load_papers(file_path)`**: Loads papers from a JSON file.
- **`combine_messages(papers)`**: Combines the title, highlight, and abstract of each paper into a single message.
- **`prepare_prompt(researcher_profile, batch_messages)`**: Prepares a prompt for the OpenAI API, including the researcher's profile and batch messages.
- **`call_openai_api(prompt, api_key)`**: Calls the OpenAI API with the prepared prompt and returns the response.
- **`parse_response(response_json)`**: Parses the JSON response from the OpenAI API.
- **`save_results(results, file_path)`**: Saves the results to a JSON file.
- **`score_papers(file_path, api_key, output_file)`**: Main function that loads papers, prepares prompts, calls the OpenAI API, parses responses, and saves results.

### Merging Papers and Scores

After scoring, the papers and their corresponding scores are merged into a single dataset:

- **`load_json(file_path)`**: Loads and returns the content of a JSON file from the specified file path.
- **`save_json(data, file_path)`**: Saves the given data to a JSON file at the specified file path.
- **`merge_papers_and_scores(papers_path, scores_path, output_path)`**: Loads papers and scores from their respective JSON files, merges them, and saves the updated papers to the output JSON file.

### PDF Download and Conversion

The next step involves downloading the PDFs of the research papers, converting them to text, and uploading the text to the DocAnalyzer API:

- **`sanitize_filename(title)`**: Sanitizes a title to create a valid filename.
- **`download_file(url, output_path)`**: Downloads a file from a URL and saves it to the specified path.
- **`pdf_to_text(pdf_path, text_path)`**: Converts a PDF file to a text file by extracting text from each page of the PDF and writing it to an output text file.

### Document Upload

The text files are then uploaded to the DocAnalyzer API for further analysis:

- **`upload_document(api_key, txt_path)`**: Uploads a text file to the DocAnalyzer API.

### Folder Processing

The script also includes functionality to process folders containing text files and identify those that need to be converted to Word documents:

- **`list_folders_with_txt_but_no_docx(root_folder)`**: Recursively scans the specified root folder, identifies folders containing `.txt` files but no `.docx` files, and returns a dictionary with folder paths as keys and lists of `.txt` file names as values.
- **`chat_document(API_KEY, doc_id, chat_string)`**: Sends a chat request to the DocAnalyzer API with a specified document ID and prompt, and returns the response from the API.
- **`list_documents(token)`**: Retrieves a list of documents from the DocAnalyzer API.

### JSON to DOCX Conversion

Finally, the script converts JSON data into a formatted Word document:

- **`read_json(file_path)`**: Reads a JSON file and returns the data.
- **`fix_json(text_to_fix, api_key)`**: Uses the OpenAI API to fix JSON formatting issues in a given text.
- **`create_word_document(data, output_path, openai_api_key)`**: Creates a Word document from the provided data, adding headings and content based on the JSON structure.
- **`main()`**: Main function that reads the JSON file, calls `create_word_document` to generate the Word document, and saves it to the specified path.