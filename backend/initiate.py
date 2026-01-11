from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = "Qwen/Qwen2.5-7B-Instruct.gguf.q5_0"

tokenizer = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)

model = AutoModelForCausalLM.from_pretrained(
    MODEL,
    device_map="auto",
    load_in_4bit=True,
    torch_dtype="auto",
    trust_remote_code=True
)
