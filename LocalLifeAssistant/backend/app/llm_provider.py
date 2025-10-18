import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import openai
import anthropic
from openai import OpenAI
from anthropic import Anthropic

class LLMProvider(ABC):
    @abstractmethod
    async def generate_response(self, prompt: str, context: str = "") -> str:
        pass

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    async def generate_response(self, prompt: str, context: str = "") -> str:
        try:
            full_prompt = f"{context}\n\n{prompt}" if context else prompt
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful local life assistant that provides personalized recommendations for events and restaurants."},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    async def generate_response(self, prompt: str, context: str = "") -> str:
        try:
            full_prompt = f"{context}\n\n{prompt}" if context else prompt
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": full_prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")

class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        self.base_url = base_url
        self.model = model

    async def generate_response(self, prompt: str, context: str = "") -> str:
        try:
            import httpx
            full_prompt = f"{context}\n\n{prompt}" if context else prompt
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "stream": False
                    }
                )
                response.raise_for_status()
                return response.json()["response"]
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")

class LLMProviderFactory:
    @staticmethod
    def create_provider(provider_name: str, **kwargs) -> LLMProvider:
        if provider_name == "openai":
            api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found")
            return OpenAIProvider(api_key=api_key, model=kwargs.get("model", "gpt-3.5-turbo"))
        
        elif provider_name == "anthropic":
            api_key = kwargs.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("Anthropic API key not found")
            return AnthropicProvider(api_key=api_key, model=kwargs.get("model", "claude-3-sonnet-20240229"))
        
        elif provider_name == "ollama":
            return OllamaProvider(
                base_url=kwargs.get("base_url", "http://localhost:11434"),
                model=kwargs.get("model", "llama2")
            )
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")

class MultiLLMProvider:
    def __init__(self, default_provider: str = "openai"):
        self.default_provider = default_provider
        self._providers: Dict[str, LLMProvider] = {}

    def get_provider(self, provider_name: str = None) -> LLMProvider:
        provider_name = provider_name or self.default_provider
        
        if provider_name not in self._providers:
            self._providers[provider_name] = LLMProviderFactory.create_provider(provider_name)
        
        return self._providers[provider_name]

    async def generate_response(self, prompt: str, context: str = "", provider_name: str = None) -> str:
        provider = self.get_provider(provider_name)
        return await provider.generate_response(prompt, context)
