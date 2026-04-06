import streamlit as st
from transformers import AutoModelForCausalLM, AutoTokenizer
from pathlib import Path



@st.cache_resource
def load_full_finetuned_model():
    model_path = "ivanhinz/gpt2-yt-comment-generator"
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        low_cpu_mem_usage=True,
        )
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    return model, tokenizer

