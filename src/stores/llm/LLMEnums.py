from enum import Enum


class LLMEnums(Enum):
    
    OPENAI="OPENAI"
    COHERE="COHERE"
    GEMINI="GEMINI"
    GROQ="GROQ"
    
class OpenAIEnums(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT ="assistant"
    
    
class CoHereEnums(Enum):
    SYSTEM = "SYSTEM"
    USER = "USER"
    ASSISTANT ="CHATBOT"
    
    DOCUMENT = "search_document"
    QUERY = "search_query"
    
class GeminiEnums(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT ="assistant"
    
class GroqEnums(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT ="assistant"
class DocumentTypeEnum(Enum):
    Document = "document"
    QUERY = "query"