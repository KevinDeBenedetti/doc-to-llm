import requests
import ollama
from typing import Optional

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "gemma3"
DEFAULT_LANGUAGE = "en"

language_settings = {
    "fr": {
        "name": "French",
        "precision": "Translate to French in a technical and clear style without any introductory commentary or additional explanation"
    }
}

def check_ollama_health() -> bool:
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/", timeout=2)    
        return response.status_code == 200
    except requests.RequestException:
        return False

def get_ollama_version() -> Optional[str]:
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/version", timeout=2)
        if response.status_code == 200:
            return response.json().get("version")
    except requests.RequestException:
        return None

def model_exists(model_name: str) -> bool:
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return any(model["name"] == model_name for model in models)
    except requests.RequestException:
        pass
    return False

def list_ollama_models():
    try:
        return ollama.list()["models"]
    except Exception as e:
        raise ConnectionError(f"Error retrieving Ollama models: {e}")
    
def translate_text(
        text: str,
        target_language: str,
        model: str = DEFAULT_MODEL
    ) -> str:
    if not check_ollama_health():
        raise ConnectionError("Ollama service is not reachable.")
    
    if not model_exists(model):
        raise ValueError(f"Model '{model}' does not exist on the Ollama instance.")
    
    setting = language_settings.get(target_language)
    if not setting:
        raise ValueError(f"Unsupported language: {target_language}")

    prompt = (
        f"Translate the following markdown text from {DEFAULT_LANGUAGE} to {setting['name']}. "
        f"{setting['precision']}. Preserve exactly all markdown formatting, including headers, code blocks, and paragraphs, "
        f"and do not include any extra commentary:\n\n{text}"
    )

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.9,
            "repeat_penalty": 1.0
        },
        "raw": False,
        "keep_alive": "5m"
    }

    response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
    response.raise_for_status()
    return response.json()["response"]
