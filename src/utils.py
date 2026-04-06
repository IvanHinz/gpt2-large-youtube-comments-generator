import os
import streamlit as st
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs 
from googleapiclient.discovery import build
from fast_langdetect import detect


load_dotenv()


def create_youtube_client():
    return build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))


def get_video_id(url: str) -> str | None:
    # print(url)
    parsed = urlparse(url)
    
    if parsed.path.startswith("/shorts"):
        return parsed.path.split("/")[-1]
        
    if parsed.hostname == "youtu.be":
        return parsed.path[1:]
    
    if parsed.hostname in ("www.youtube.com", "youtube.com"):
        return parse_qs(parsed.query).get("v", [None])[0]
    
    return None

@st.cache_data
def get_video_info(video_id: str) -> dict | None:
    youtube_client = create_youtube_client()
    
    
    response = youtube_client.videos().list(
        part="snippet", id=video_id
    ).execute()


    if not response:
        return None
    
    if not response.get("items"):
        return None
    
    snippet = response["items"][0]["snippet"]

    return {
        "channel": snippet["channelTitle"],
        "title": snippet["title"],
        "video_id": video_id
    }
    

def is_english_language_video(channel_title: str, title: str) -> bool:
    # Define the language of the channel name
    # channel_title_lang = detect(channel_title)[0]["lang"]
    
    # Define the language of the title
    title_lang = detect(title)[0]["lang"]
    
    # Define if the language of the name of the video is English
    return title_lang == "en"
  
    
def format_text(channel_title: str, title: str) -> str:
    return f"<CHANNEL> {channel_title} <TITLE> {title} <COMMENT>"


