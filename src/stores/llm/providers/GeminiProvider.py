from google.genai import Client
import logging
from typing import List, Union
from ..LLMInterface import LLMInterface
from ..LLMEnums import GeminiEnums

class GeminiProvider(LLMInterface):

    def __init__(
        self,
        api_key: str,
        default_input_max_character: int = 1000,
        default_generation_max_output_tokens: int = 1000,
        default_generation_temperature: float = 0.1
    ):
        self.api_key = api_key
        self.default_input_max_character = default_input_max_character
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature
        self.enums = GeminiEnums

        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None

        self.client = Client(api_key=self.api_key)

        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, model_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = model_size

    def process_text(self, text: str):
        return text[:self.default_input_max_character].strip()

    def generate_text(
    self,
    prompt: str,
    chat_history: list,
    max_output_token: int = None,
    temperature: float = None
    ):
        if not self.generation_model_id:
            self.logger.error("Generation model for Gemini was not set")
            return None

        max_output_token = max_output_token or self.default_generation_max_output_tokens
        temperature = temperature or self.default_generation_temperature

        try:
            # Combine chat history into one string + user prompt
            full_prompt = ""
            for msg in chat_history:
                full_prompt += f"{msg['role']}: {msg['content']}\n"
            full_prompt += f"user: {prompt}"

            # Correct Gemini text generation call
            response = self.client.models.generate_content(
                model=self.generation_model_id,
                contents=full_prompt,
            )

            # Extract text from response
            if response and hasattr(response, "text"):
                return response.text
            else:
                self.logger.error("Gemini did not return text")
                return None

        except Exception as e:
            self.logger.error(f"Gemini generation error: {e}")
            return None
        
    def embed_text(self, text: Union[str, List[str]], documented_type: str = None):
        if isinstance(text, str):
            text = [text]

        if not self.embedding_model_id:
            self.logger.error("Embedding model for Gemini was not set")
            return None

        try:
            embeddings = []
            for t in text:
                result = self.client.embed_content(
                    model=self.embedding_model_id,
                    content=t
                )
                embeddings.append(result["embedding"])
            return embeddings

        except Exception as e:
            self.logger.error(f"Gemini embedding error: {e}")
            return None

    def construct_prompt(self, prompt: str, role: str):
        return {"role": role, "content": prompt}