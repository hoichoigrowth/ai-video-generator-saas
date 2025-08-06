import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

class BaseAgent(ABC):
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        google_api_key: Optional[str] = None,
        model_name_openai: str = "gpt-3.5-turbo",
        model_name_anthropic: str = "claude-3-opus-20240229",
        model_name_gemini: str = "gemini-pro",
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        logging.basicConfig(level=logging.INFO)
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.llms = {}
        if openai_api_key:
            self.llms["openai"] = ChatOpenAI(api_key=openai_api_key, model=model_name_openai)
        if anthropic_api_key:
            self.llms["claude"] = ChatAnthropic(api_key=anthropic_api_key, model=model_name_anthropic)
        if google_api_key:
            self.llms["gemini"] = ChatGoogleGenerativeAI(api_key=google_api_key, model=model_name_gemini)

    @abstractmethod
    def process(self, *args, **kwargs) -> Any:
        """
        Main method to be implemented by subclasses for agent logic.
        Should use self._run_with_retries for LLM calls.
        """
        pass

    def _run_with_retries(self, func, *args, **kwargs):
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                self.logger.info(f"Attempt {attempt} for {func.__name__}")
                return func(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Error on attempt {attempt}: {e}")
                last_exception = e
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
        self.logger.error(f"All {self.max_retries} attempts failed.")
        raise last_exception