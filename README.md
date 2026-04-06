# YouTube Comments Generator

A Streamlit web application that generates YouTube-style comments for a given video using a fine-tuned GPT-2-large.

## Features

- Input via YouTube URL or manual channel/title entry
- Multiple generation strategies: Greedy, top-p, top-k, beam search
- Configurable generation parameters (temperature, tokens, etc.)

## Project Structure

```
├── app.py
├── src/
│   ├── generation.py       # GenerationCFG (pydantic), generation functions
│   ├── model.py            # Model loading with st.cache_resource
│   └── utils.py            # URL parsing, YouTube API, text utilities
├── images/
│   └── youtube_comments.jpg
├── .streamlit/
├── Dockerfile
├── requirements.txt
└── README.md
```

## Model

The app uses a fine-tuned on youtube-comments gpt2-large loaded from HuggingFace with the following prompt format:

```
<CHANNEL> {channel_title} <TITLE> {video_title} <COMMENT> {comment_to_generate}
```

## Setup

### With Docker (recommended)

```bash
docker build -t yt-comment-generator .
docker run -d -p 8000:8000 -e YOUTUBE_API_KEY=your_key_here yt-comment-generator
```

Then open [http://localhost:8000](http://localhost:8000).

### Without Docker

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file:
```
YOUTUBE_API_KEY=your_key_here
```

3. Run the app:
```bash
streamlit run app.py --server.port 8000
```