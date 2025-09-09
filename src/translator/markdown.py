import re
from datetime import datetime
from typing import Dict
import yaml
from src.services.ollama import check_ollama_health, translate_text

FRONTMATTER = re.compile(r'^(---\n[\s\S]*?\n---)\n?', re.MULTILINE)

def get_current_date() -> str:
  return datetime.now(datetime.UTC).strftime("%d/%m/%Y")

def stringify_frontmatter(data: Dict) -> str:
  return "---\n" + yaml.safe_dump(data).strip() + "\n---\n\n"
