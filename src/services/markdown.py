import re
from datetime import datetime
from typing import Tuple, List, Dict
import httpx
import yaml
# FIXME : verify if marked is necessary
from .ollama import check_ollama_health, translate_text
# Import OLLAMA_URL, MODEL, DEFAULT_lANG, language_settings

FRONTMATTER = re.compile(r'^(---\n[\s\S]*?\n---)\n?', re.MULTILINE)

def get_current_date() -> str:
  return datetime.now(datetime.UTC).strftime("%d/%m/%Y")

def stringify_frontmatter(data: Dict) -> str:
  return "---\n" + yaml.safe_dump(data).strip() + "\n---\n\n"
