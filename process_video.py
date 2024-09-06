import requests
import subprocess
import re
import os
from datetime import datetime
from bs4 import BeautifulSoup
import yt_dlp
from transcribe import transcribe
import videogrep
from collections import Counter
import random
import json
import spacy

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

stopwords = ["i", "we're", "you're", "that's", "it's", "us", "i'm", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now", "like"]


def fetch_top_video_url():
    today = datetime.today().strftime('%m/%d/%Y')
    search_url = f"https://www.c-span.org/search/?sdate={today}&edate={today}&congressSelect=&yearSelect=&searchtype=Videos&sort=Most+Views&text=0"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    
    response = requests.get(search_url, headers=headers)
    html = response.text

    # Debugging: Print the first 1000 characters of HTML
    print("HTML content received from search URL:")
    print(html[:1000])

    soup = BeautifulSoup(html, 'html.parser')
    
    # Find the first <a> tag in the first <li> with class 'onevid'
    first_video = soup.select_one('.video-results .onevid a')
    if first_video and 'href' in first_video.attrs:
        video_url = first_video['href']
        # Ensure the URL is absolute
        if not video_url.startswith('http'):
            video_url = 'https:' + video_url
        print("Video URL found:", video_url)
        return video_url
    else:
        raise Exception("Top video URL not found")

def download_video(video_url):
    ydl_opts = {
        'outtmpl': 'video.%(ext)s',  # Save file as video.mp4
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
        video_url = info_dict.get('url', None)
        return 'video.mp4'


def transcribe_video(video_file):
    print(f"Transcribing video file: {video_file}")
    transcript = transcribe(video_file)
    
    if transcript:
        print("Transcription successful.")
        return transcript
        # Process the transcription as needed
    else:
        print("Transcription failed.")
        return []


## USING NOT SPACY, JUST MOST COMMON

# def extract_common_words(transcript, num_words=10):
#     # Adjust this based on the actual structure of your transcript
#     unigrams = []
#     for entry in transcript:
#         if "content" in entry:
#             unigrams.extend(entry["content"].lower().split())
#         elif "words" in entry:
#             unigrams.extend(word.lower() for word in entry["words"] if isinstance(word, str))
    
#     # Remove stop words
#     unigrams = [w for w in unigrams if w not in stopwords]
    
#     # Get the most common words
#     most_common = Counter(unigrams).most_common(num_words)


#     ##### SHOULD I GET LIKE JUST 5 MOST COMMON INSTEAD OF 10?? THIS SHIT GON BE SO LONG!!!!
    
#     # Extract the words
#     words = [w[0] for w in most_common]
    
#     # Randomize and select words
#     random.shuffle(words)
#     return words


## USING SPACY
def extract_common_words(transcript, num_words=5):
    # Combine transcript entries into a single text
    text = " ".join(entry["content"] for entry in transcript if "content" in entry)
    
    # Process text with spaCy
    doc = nlp(text)
    
    # Filter out stop words and punctuation
    words = [token.text.lower() for token in doc if not token.is_stop and not token.is_punct]
    
    # Get the most common words
    most_common = Counter(words).most_common(num_words)
    
    # Extract the words
    keywords = [w[0] for w in most_common]
    
    return keywords


def create_supercut(video_file, keywords):
    print(f"Creating supercut from video file: {video_file}")
    keywords_string = '|'.join(keywords)
    output_file = 'supercut.mp4'
    print(f"Keywords for supercut: {keywords_string}")

    result = subprocess.run(['videogrep', '--input', video_file, '--search', keywords_string, '--output', output_file], capture_output=True, text=True)

    # Print videogrep output and errors
    print("Videogrep stdout:")
    print(result.stdout)
    print("Videogrep stderr:")
    print(result.stderr)

    if result.returncode != 0:
        raise Exception("Videogrep failed to create the supercut")

    print(f"Supercut created successfully: {output_file}")
    return output_file

def run():
    try:
        video_page_url = fetch_top_video_url()
        video_file = download_video(video_page_url)
        transcript = transcribe_video(video_file)
        
        if transcript:
            # Extract common words from the transcript
            keywords = extract_common_words(transcript)
            if keywords:
                # Create a supercut based on the extracted keywords
                supercut_file = create_supercut(video_file, keywords)
                print(f'Supercut created: {supercut_file}')
            else:
                print("No keywords extracted for supercut.")
        else:
            print("No transcript available to extract keywords.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    run()
