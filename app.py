import streamlit as st
from googleapiclient.errors import HttpError
from src.utils import (
    get_video_id,
    get_video_info,
    is_english_language_video,
    format_text,
)
from src.generation import (
    GenerationCFG, 
    simple_generate, 
    stream_one_comment
)
from src.model import load_full_finetuned_model


# ------ Title, app_image and header ------
st.title("YouTube Comments Generator")
st.image("./images/youtube_comments.jpg")
st.header("Choose desirable input type: URL or text")


# ------ Choose the way, how to enter channel name and video title

# Function to reset url after we change our option: by url or text input
def reset_url():
    st.session_state.youtube_video_url = ""
   
st.selectbox(
    "How would you like to enter the channel_name and video_name?",
    ["With URL", "Text on my own"],
    key="option",
    on_change=reset_url,
)

channel_title, title = None, None
is_valid = True

if st.session_state.option == "With URL":
    st.text_input("Enter URL to YouTube video in English", key="youtube_video_url")

    video_id = None
    if st.session_state.youtube_video_url:
        try:
            video_id = get_video_id(st.session_state.youtube_video_url)
        except:
            st.error("""Possibly there is problem with API or video is 
            not available (possibly video is not from YouTube)!""")

        if video_id is not None:
            try:
                video_info = get_video_info(video_id)
                channel_title, title = video_info["channel"], video_info["title"]
            except HttpError as h:
                st.error(f"HTTP {h.resp_status}: {h.content}")
                st.error("Failed to fetch video info. Check if video is available.")
        else:
            st.error("You probably have invalid URL - not from YouTube!")
else:
    col1, col2 = st.columns(2)
    
    with col1:
        channel_title = st.text_input("Enter Channel Name")
        
    with col2:
        title = st.text_input("Enter Video Title")

if (channel_title is None) and (title is None) and (st.session_state.option == "With URL"):
    st.text("Wait for the channel title and video title to be parsed!")
    
if channel_title and title and (not is_english_language_video(channel_title, title)):
    st.error("Enter video with English Title (ex: Trump foreign politics)!")
    is_valid = False
 
# Display which channel_title and video title we have now       
col1, col2 = st.columns(2)

with col1:
    if channel_title:
        st.success(f"✅ As channel title you have chosen: {channel_title}")
    else:
        st.error(f"🚨 You have not chosen channel title yet!")
        
with col2:
    if title:
        st.success(f"✅ As title you have chosen: '{title}'")
    else:
        st.error(f"🚨 You have not chosen title yet!")

if (not channel_title) or (not title) or (not is_valid):
    st.stop()
    
st.divider()


# ------ Generation configuration ------

st.header("Choose generation parameters")

generation_strategy = st.radio(
    "Generation Strategy",
    ["Greedy", "Top-p sampling", "Top-k sampling", "Beam Search"]
)

# GenerationCFG instance (uses pydantic BaseModel) for data types validation
generation_config = GenerationCFG() # model.dump()

if generation_strategy != "Greedy":
    generation_config.num_return_sequences = int(st.number_input(
        "Quantity of sequences to generate",
        min_value=1,
        max_value=10,
        value=1,
    ))

# Specific optional parameters for each strategy
if generation_strategy == "Top-p sampling":
    generation_config.top_p = float(st.number_input(
        "Enter the top-p probability threshold (0.0 - 1.0)",
        min_value=0.0,
        max_value=1.0,
        value=0.9,
        step=0.01
    ))
elif generation_strategy == "Top-k sampling":
    generation_config.top_k = int(st.number_input(
        "Enter the number of K (most probable tokens to use every iteration) (NO MORE THAN 100)",
        min_value=1,
        max_value=100,
        step=1
    ))
elif generation_strategy == "Beam Search":
    st.info(
        "Beam search finds the most probable sequences\n\n"
        "For diverse comments use top-p or top-k options of generation"
    )    
    # previous num beams, if we have not previously entered it is 1
    previous_num_beams = st.session_state.get("num_beams", 1)
    
    generation_config.num_beams = int(st.number_input(
        "Number of beams",
        min_value=generation_config.num_return_sequences,
        max_value=20, 
        # value=max(2, num_seqs + 1),  # need to make independent from num_seqs later
        value=max(previous_num_beams, generation_config.num_return_sequences),
        key="num_beams"
    ))
    # we can make early stopping

if generation_strategy in ("Top-p sampling", "Top-k sampling"):
    generation_config.temperature = float(st.slider(
        "Temperature value: HIGHER -> more creative and random",
        min_value=0.000001,
        max_value=3.0,
        value=1.2,
        format="plain"
    ))
    
    generation_config.do_sample = True
  
# Options to choose for every algorithm  
generation_config.max_new_tokens = int(st.slider(
    "Maximum quantity of new tokens to generate",
    min_value=2,
    max_value=256,
    value=150,
    format="plain",
))

generation_config.min_new_tokens = int(st.slider(
    "Minimum quantity of new tokens to generate",
    min_value=1,
    max_value=generation_config.max_new_tokens - 1,
    value=1,
    format="plain",
))

generation_config.repetition_penalty = float(st.slider(
    "How much do we penalize our model for repetitions?",
    min_value=1.0,
    max_value=2.0,
    value=1.3,
    format="plain"
))

generation_config.no_repeat_ngram_size = int(
    st.slider(
        "Ngrams of which length we do not want to repeat?",
        # min_value=generation_config.min_new_tokens,
        min_value=0,
        max_value=5,
        value=0,
        format="plain"
    )
)

st.divider()


# ------ Generation process ------

st.header("Generate comments")
st.text("Click this button to generate comments with your generation parameters ->")


if st.button("Generate comments"):
    if not st.session_state.get("model_loaded", False):
        st.text("Wait for the model to be loaded!")
    # Load model and tokenizer
    model, tokenizer = load_full_finetuned_model()
    
    st.session_state.model_loaded = True
    
    # Formatted text
    formatted_text = format_text(channel_title, title)
    
    if generation_strategy == "Beam Search":
        st.warning(f"⚠️ Resulted comments will be shown after full generation!")
                
        new_comments = simple_generate(model, tokenizer, formatted_text, generation_config.model_dump())
        
        #  Write comments to display them
        for idx, comment in enumerate(new_comments):
            with st.container(border=True):
                st.write(f"""**Comment {idx}:** \n\n{comment}""")
    else:
        num_comments = generation_config.num_return_sequences
        
        generation_config = generation_config.model_copy(update={"num_return_sequences": 1})
        
        for idx in range(num_comments):
            st.write(f"""**Comment {idx}:** \n\n""")
            
            st.write_stream(stream_one_comment(
                model, 
                tokenizer, 
                formatted_text, 
                generation_config.model_dump()
                # generation_config_dct
                )
            )

