from transformers import GenerationConfig, TextIteratorStreamer
from threading import Thread
from pydantic import BaseModel, model_validator


class GenerationCFG(BaseModel):
    max_new_tokens: int = 128
    min_new_tokens: int = 2
    temperature: float = 1.2
    do_sample: bool = False
    top_p: float = 1.0
    top_k: int = 50
    repetition_penalty: float = 1.5
    no_repeat_ngram_size: int = 0
    num_return_sequences: int = 1
    num_beams: int = 1
    
    @model_validator(mode="after")
    def check_tokens_length(self):
        if self.min_new_tokens > self.max_new_tokens:
            raise ValueError("The value of max_new_tokens should be greater than for min_new_tokens!")
        if (self.min_new_tokens < 1) or (self.max_new_tokens < 1):
            raise ValueError("The value for max_new_tokens and min_new_tokens should be > 0!")
        return self

def simple_generate(model, tokenizer, formatted_text, generation_config_dct) -> list[str]:
    generation_config = GenerationConfig(**generation_config_dct)
    inputs = tokenizer(formatted_text, return_tensors="pt")
    resulted_comments = []
    
    output = model.generate(
        inputs=inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
        generation_config=generation_config,
        trust_remote_code=True,
    )
        
    for i, seq in enumerate(output):
        sequence_text = tokenizer.decode(seq, skip_special_tokens=False)
        comment = sequence_text.split("<COMMENT>")[-1].replace(tokenizer.eos_token, "").strip()
        resulted_comments.append(comment)
        
    return resulted_comments


def stream_one_comment(model, tokenizer, formatted_text, generation_config_dct):
    streamer = TextIteratorStreamer(
        tokenizer,
        skip_prompt=True,
        skip_special_tokens=True
    )
    
    inputs = tokenizer(formatted_text, return_tensors="pt")
    
    generation_kwargs = {
        "inputs": inputs["input_ids"],
        "attention_mask": inputs["attention_mask"],
        "generation_config": GenerationConfig(**generation_config_dct),
        "streamer": streamer,
    }
       
    inputs = tokenizer(formatted_text, return_tensors="pt")
    
    thread = Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()
    
    for new_text in streamer:
        yield new_text

