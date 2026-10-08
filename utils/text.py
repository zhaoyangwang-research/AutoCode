import tiktoken

def get_tokenizer(model:str):
    try:
        encoding = tiktoken.encoding_for_model(model)
        return encoding.encode

    except Exception:
        encoding = tiktoken.get_encoding("cl100k_base")
        return encoding,encode

def count_tokens(text: str, model: str) -> int:
    tokenizer = get_tokenizer(model)

    if tokenizer:
        return len(tokenizer(text))

    return estimate_tokens(text)

def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4 )

def truncate_text(text: str, 
                  model: str,
                  max_tokens: int, 
                  suffix: str = "\n...[truncated]",
):
    current_tokens = count_tokens(text, model)

    if current_tokens <= max_tokens:
        return text

    suffix_tokens = count_tokens(suffix, model)
    target_tokens = max_tokens - suffix_tokens 

    if target_tokens <= 0:
        return suffix.strip()

    


