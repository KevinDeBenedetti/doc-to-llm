from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate

# Add import for settings
from src.shared.config import config
from src.shared.ollama import translate_text, list_ollama_models

router = APIRouter()

# Pydantic models
class TranslationRequest(BaseModel):
    content: str = Field(..., description="Markdown content to translate")
    source_language: str = Field(..., description="Source language")
    target_language: str = Field(..., description="Target language")
    model_name: str = Field(default="gpt-oss", description="Model to use")

class TranslationResponse(BaseModel):
    translated_content: str
    source_language: str
    target_language: str
    model_used: str

# LangChain configuration
def get_translation_chain(model_name="gpt-oss"):
    llm = ChatOpenAI(
        temperature=0.4,
        model_name=model_name,
        openai_api_key=config.openai_api_key
    )
    
    system_template = """You are a professional translator specialized in technical documentation and Markdown."""
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
    
    human_template = """Translate the following Markdown content from {source_language} to {target_language}.
    Preserve all Markdown formatting, links and structure.
    
    Content:
    {content}
    """
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    
    chat_prompt = ChatPromptTemplate.from_messages([
        system_message_prompt,
        human_message_prompt
    ])
    
    chain = LLMChain(llm=llm, prompt=chat_prompt)
    return chain

@router.post("/translate", response_model=TranslationResponse)
async def translate(translation_req: TranslationRequest):
    try:
        # Use LangChain to translate the content
        chain = get_translation_chain(model_name=translation_req.model_name)
        translated_content = chain.invoke({
            "content": translation_req.content,
            "source_language": translation_req.source_language,
            "target_language": translation_req.target_language
        })
        
        # Extract the response content (format changed with ChatOpenAI)
        translated_text = translated_content.get("text", "")
        
        return TranslationResponse(
            translated_content=translated_text,
            source_language=translation_req.source_language,
            target_language=translation_req.target_language,
            model_used=translation_req.model_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during translation: {str(e)}")

@router.post("/translate-file", response_model=TranslationResponse)
async def translate_file(
    file: UploadFile = File(...),
    source_language: str = Form(...),
    target_language: str = Form(...),
    model_name: str = Form(default="gpt-oss")
):
    try:
        # Read the markdown file content
        content = await file.read()
        content_str = content.decode("utf-8")
        
        # Create a translation request
        translation_req = TranslationRequest(
            content=content_str,
            source_language=source_language,
            target_language=target_language,
            model_name=model_name
        )
        
        # Reuse the existing translate endpoint
        return await translate(translation_req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error translating file: {str(e)}")


from fastapi.responses import PlainTextResponse

from enum import Enum

DEFAULT_MODEL = "gemma3"

class StaticOllamaModels(str, Enum):
    gemma3 = "gemma3:latest"
    gemma3_1b = "gemma3:1b"

@router.post("/upload", response_class=PlainTextResponse)
async def translate_upload(
    file: UploadFile = File(...),
    target_lang: str = Form(...),
    model: StaticOllamaModels = Form(DEFAULT_MODEL)
):
    # Verify extension
    if not file.filename.endswith('.md'):
        raise HTTPException(status_code=400, detail="Only markdown files are supported")

    # Read the content
    content = (await file.read()).decode('utf-8')

    try:
        translated = translate_text(content, target_lang, model.value )
    except ConnectionError as ce:
        raise HTTPException(status_code=503, detail=str(ce))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {e}")

    return translated