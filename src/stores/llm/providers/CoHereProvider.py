
import logging
import cohere
from ..LLMInterface import LLMInterface
from ..LLMEnums import CoHereEnums, DocumentTypeEnum

class CoHereProvider(LLMInterface):
    
    def __init__(self,api_key:str,
                 default_input_max_character: int=1000,
                 default_generation_max_output_tokens:int=1000,
                 default_generation_temperature:float=0.1
                ):
        self.api_key=api_key

        
        self.default_input_max_character=default_input_max_character
        self.default_generation_max_output_tokens=default_generation_max_output_tokens
        self.default_generation_temperature=default_generation_temperature
        
        
        self.generation_model_id =None
        self.embedding_model_id =None
        self.embedding_size =None
        
        self.client = cohere.ClientV2(
            api_key=self.api_key,
        )
        
        self.enum= CoHereEnums
        self.logger=logging.getLogger(__name__)    
        
    def  set_generation_model(self,model_id:str):
        self.generation_model_id=model_id
            
    def set_embedding_model(self,model_id:str,model_size:int):
        self.embedding_model_id=model_id
        self.embedding_size=model_size
            
    def process_text(self,text:str):
        return text[self.default_input_max_character].strip()
        
    def generate_text(self,prompt:str,chat_history:list ,max_output_token:int=None,temperature: float =None):
        if  not self.client:
            self.logger.error("Cohere client was not set")
            return None
        
        if not self.generation_model_id:
            self.logger.error("Generation model for Cohere was not set")
            return None
        
        
        max_output_token = max_output_token if max_output_token  else  self.default_generation_max_output_tokens
        temperature = temperature if temperature else self.default_generation_temperature
        
        # chat_history.append(
        #     self.contruct_prompt(
                
        #         prompt=prompt,
        #         role=CoHereEnums.USER.value()
        #     )
        # )
        
        response = self.client.chat(
            model=self.generation_model_id,
            messages=self.process_text(prompt),
            max_tokens=max_output_token,
            temperature=temperature
            )
        
        if not response or  not response.text :
            self.logger.error("Error while generation text with Cohere")
            return None
        return response.text
    
    
    def embed_text(self,text:str,documented_type:str=None):
        
        if  not self.client:
            self.logger.error("Cohere AI client was not set")
            return None

        if not self.embedding_model_id:
            self.logger.error("Embdedding model for Cohere was not set")
            return None    
        
        
        input_type = CoHereEnums.DOCUMENT
        if documented_type == DocumentTypeEnum.QUERY:
            input_type = CoHereEnums.QUERY
            
        
        response = self.client.embed(   
            model = self.embedding_model_id,
            texts= [self.process_text(text)],
            input_type= input_type,
            embedding_types=['float'],
        )
        
        if not  response or not response.embeddings  or not response.embeddings.float:
            self.logger.error("Error while embedding text with Cohere")
            return None
        
        return response.embeddings.float[0]
    
        
    def contruct_prompt(self,prompt:str,role:str):
        return {
            "role":role,
            "text":prompt
        }