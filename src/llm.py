import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

def sentiment_score(lead):
    """
    Returns a float (0–1) representing the probability of positive sentiment
    for the lead’s snippet or (industry + location) fallback.
    """
    text = lead.get("snippet") or f"{lead.get('industry')} {lead.get('location')}"
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    prob = torch.softmax(logits, dim=1)[0][1].item()  # positive class prob
    return prob
