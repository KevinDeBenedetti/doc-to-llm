import os

# Settings require an API key at import time; tests never reach the network.
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("OPENAI_MODEL", "test-model")
