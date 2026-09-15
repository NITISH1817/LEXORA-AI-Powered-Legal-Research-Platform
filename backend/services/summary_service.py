import google.generativeai as genai
from backend.config import settings

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash')

def generate_summary(text: str, summary_type: str = "short") -> str:
    prompts = {
        "short": "Provide a brief 3-sentence summary of this legal text.",
        "detailed": "Provide a structured summary of this legal text including: Case Overview, Facts, Legal Issues, Decision, and Reasoning.",
        "research": "Provide a comprehensive research summary of this text, extracting all key legal principles, specific precedents cited, and the core ratio decidendi."
    }
    
    prompt = prompts.get(summary_type, prompts["short"]) + "\n\nText:\n" + text
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return str(e)
