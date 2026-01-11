import os

class Config:
    # Flask
    JSON_AS_ASCII = False

    # LLM (позже подключим)
    GIGACHAT_TOKEN = os.getenv("GIGACHAT_TOKEN", "")

    # Safety
    MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "20"))
    REQUEST_TIMEOUT_SEC = int(os.getenv("REQUEST_TIMEOUT_SEC", "60"))
