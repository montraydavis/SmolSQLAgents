"""OpenAI embeddings wrapper for SQL documentation."""

from typing import List, Callable, Any
import os
import re
import openai
import tiktoken
from tenacity import retry, stop_after_attempt, wait_exponential

class OpenAIEmbeddingsClient:
    """Handles OpenAI embeddings generation with error handling and batching."""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))
        self.max_retries = int(os.getenv("EMBEDDING_MAX_RETRIES", "3"))
        self._encoder = tiktoken.encoding_for_model(self.model)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_embedding(self, text: str) -> List[float]:
        """Generate single embedding for text.
        
        Args:
            text: The text to generate embedding for
            
        Returns:
            List[float]: The embedding vector
            
        Raises:
            Exception: If the API call fails after retries
        """
        prepared_text = self._prepare_text_for_embedding(text)
        response = self.client.embeddings.create(
            input=prepared_text,
            model=self.model
        )
        return response.data[0].embedding

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List[List[float]]: List of embedding vectors
            
        Raises:
            Exception: If the API call fails after retries
        """
        prepared_texts = [self._prepare_text_for_embedding(text) for text in texts]
        embeddings = []
        
        # Process in batches
        for i in range(0, len(prepared_texts), self.batch_size):
            batch = prepared_texts[i:i + self.batch_size]
            response = self._retry_with_backoff(
                self.client.embeddings.create,
                input=batch,
                model=self.model
            )
            batch_embeddings = [data.embedding for data in response.data]
            embeddings.extend(batch_embeddings)
        
        return embeddings

    def _prepare_text_for_embedding(self, text: str) -> str:
        """Clean and prepare text for embedding generation.
        
        Args:
            text: Raw text to prepare
            
        Returns:
            str: Cleaned and prepared text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Truncate if needed
        if self._count_tokens(text) > 8000:
            text = self._truncate_text(text)
            
        return text

    def _count_tokens(self, text: str) -> int:
        """Count tokens to ensure we don't exceed OpenAI limits.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            int: Number of tokens
        """
        return len(self._encoder.encode(text))

    def _truncate_text(self, text: str, max_tokens: int = 8000) -> str:
        """Truncate text to fit within token limits.
        
        Args:
            text: Text to truncate
            max_tokens: Maximum number of tokens allowed
            
        Returns:
            str: Truncated text
        """
        tokens = self._encoder.encode(text)
        if len(tokens) <= max_tokens:
            return text
            
        truncated_tokens = tokens[:max_tokens]
        return self._encoder.decode(truncated_tokens)

    def _retry_with_backoff(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Retry failed requests with exponential backoff.
        
        Args:
            func: Function to retry
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Any: Result from the function
            
        Raises:
            Exception: If all retries fail
        """
        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=4, max=10)
        )
        def _wrapped_func():
            return func(*args, **kwargs)
            
        return _wrapped_func()
