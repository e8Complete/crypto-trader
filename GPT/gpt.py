# https://blog.rok.strnisa.com/2023/04/how-i-got-chatgpt-to-write-complete.html
import os
import requests
from bs4 import BeautifulSoup
import openai

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HN_API_BASE = "https://hacker-news.firebaseio.com/v0"

def get_top_stories():
    response = requests.get(f"{HN_API_BASE}/topstories.json")
    return response.json()

def get_story_details(story_id):
    response = requests.get(f"{HN_API_BASE}/item/{story_id}.json")
    return response.json()

def fetch_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    return soup.get_text()

def summarize_content(content):
    openai.api_key = OPENAI_API_KEY
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Summarize the following content in a single paragraph:\n```{content[:5000]}```\n",
        max_tokens=100,
        n=1,
        temperature=0.5,
    )
    return response.choices[0].text.strip()

def main():
    story_ids = get_top_stories()[:3]

    for story_id in story_ids:
        story = get_story_details(story_id)
        if "url" in story:
            content = fetch_content(story["url"])
            summary = summarize_content(content)
            print(f"Title: {story['title']}\nURL: {story['url']}\nSummary: {summary}\n")

if __name__ == "__main__":
    main()