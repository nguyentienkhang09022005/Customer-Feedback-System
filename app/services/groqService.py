import httpx
from typing import List, Optional, Dict, Any
from app.core.config import settings
from app.core.constants import SentimentLabel, SentimentConstants
import logging
import json

logger = logging.getLogger(__name__)


SENTIMENT_SYSTEM_PROMPT = """You are a customer sentiment analyzer. Analyze the following text and return a JSON object with:
- "label": "positive" if sentiment is positive, "neutral" if neutral, "negative" if negative
- "score": a float from -1.0 (very negative) to 1.0 (very positive)

Rules:
- Positive (label: "positive", score >= 0.3): happy, satisfied, grateful, compliment, solved
- Negative (label: "negative", score <= -0.3): angry, frustrated, disappointed, complaint, urgent problem
- Neutral (label: "neutral", -0.3 < score < 0.3): factual, informational, routine inquiry

Return ONLY the JSON object, no explanation."""


class GroqService:
    def __init__(self):
        self.api_keys = settings.GROQ_API_KEYS
        self.model = settings.GROQ_MODEL
        self.current_key_index = 0
        self.base_url = "https://api.groq.com/openai/v1"

        if not self.api_keys:
            raise ValueError("No Groq API keys configured. Set GROQ_API_KEY_1 (and optionally GROQ_API_KEY_2, GROQ_API_KEY_3) in environment.")

    def _get_current_key(self) -> str:
        return self.api_keys[self.current_key_index]

    def _rotate_key(self) -> bool:
        """Rotate to next key. Returns False if no more keys available."""
        if len(self.api_keys) <= 1:
            return False
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.warning(f"Rotating Groq API key to index {self.current_key_index}")
        return True

    def _make_request(self, messages: List[Dict[str, str]], key_index: int) -> Dict[str, Any]:
        """Make request to Groq API with specific key."""
        api_key = self.api_keys[key_index]
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            return response

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Send chat request to Groq API with automatic key rotation on failure.
        Returns the assistant's response text.
        Raises exception when all keys are exhausted.
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")

        keys_to_try = len(self.api_keys)
        start_index = self.current_key_index

        for _ in range(keys_to_try):
            try:
                response = self._make_request(messages, self.current_key_index)

                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]

                elif response.status_code in (401, 403, 429, 500, 502, 503, 504):
                    logger.warning(f"Groq API error {response.status_code} with key index {self.current_key_index}")
                    if not self._rotate_key():
                        raise Exception(f"All Groq API keys failed. Last error: {response.status_code}")
                    continue
                else:
                    raise Exception(f"Groq API returned unexpected status {response.status_code}: {response.text}")

            except httpx.TimeoutException:
                logger.warning(f"Groq API timeout with key index {self.current_key_index}")
                if not self._rotate_key():
                    raise Exception("All Groq API keys timed out")
                continue

            except httpx.HTTPError as e:
                logger.warning(f"Groq API HTTP error with key index {self.current_key_index}: {str(e)}")
                if not self._rotate_key():
                    raise Exception(f"All Groq API keys failed. Last error: {str(e)}")
                continue

        raise Exception("All Groq API keys exhausted")

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of given text using Groq API.
        Returns dict with label (positive/neutral/negative) and score (-1.0 to 1.0).
        """
        if not text or len(text.strip()) == 0:
            return {"label": SentimentLabel.NEUTRAL.value, "score": 0.0}

        try:
            messages = [
                {"role": "system", "content": SENTIMENT_SYSTEM_PROMPT},
                {"role": "user", "content": text[:1000]}
            ]
            response_text = self.chat(messages)
            result = json.loads(response_text)

            label = result.get("label", SentimentLabel.NEUTRAL.value)
            score = float(result.get("score", 0.0))

            if label not in [SentimentLabel.POSITIVE.value, SentimentLabel.NEUTRAL.value, SentimentLabel.NEGATIVE.value]:
                label = SentimentLabel.NEUTRAL.value

            score = max(-1.0, min(1.0, score))

            return {"label": label, "score": score}

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse sentiment response: {e}")
            return {"label": SentimentLabel.NEUTRAL.value, "score": 0.0}
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {"label": SentimentLabel.NEUTRAL.value, "score": 0.0}
