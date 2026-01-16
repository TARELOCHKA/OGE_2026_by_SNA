import os

class Config:
    # Flask
    JSON_AS_ASCII = False

    # GigaChat
    GIGACHAT_TOKEN = os.getenv("GIGACHAT_TOKEN", "")
    GIGACHAT_MODEL = os.getenv("GIGACHAT_MODEL", "GigaChat")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))
    PROMPT_VERSION = os.getenv("PROMPT_VERSION", "v1.1")
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "900"))

    # Safety
    MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "20"))
    REQUEST_TIMEOUT_SEC = int(os.getenv("REQUEST_TIMEOUT_SEC", "60"))
