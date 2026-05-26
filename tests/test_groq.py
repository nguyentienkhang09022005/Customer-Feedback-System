"""
Tests for GroqService - Groq API integration and sentiment analysis.
"""
import pytest
from unittest.mock import patch, MagicMock
import httpx
import json

from app.services.groqService import GroqService
from app.core.constants import SentimentLabel


class TestGroqServiceInit:
    """Tests for GroqService initialization."""

    def test_groq_service_raises_when_no_api_keys(self):
        """GroqService should raise ValueError when no API keys are configured."""
        # Test that service init checks for API keys
        with patch("app.services.groqService.settings") as mock_settings:
            mock_settings.GROQ_API_KEYS = []
            mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"

            with pytest.raises(ValueError, match="No Groq API keys configured"):
                GroqService()

    def test_groq_service_stores_multiple_api_keys(self):
        """GroqService should store and manage multiple API keys."""
        with patch("app.services.groqService.settings") as mock_settings:
            mock_settings.GROQ_API_KEYS = ["key1", "key2", "key3"]
            mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"

            service = GroqService()
            assert len(service.api_keys) == 3
            assert service.api_keys == ["key1", "key2", "key3"]


class TestGroqServiceKeyRotation:
    """Tests for API key rotation."""

    def test_get_current_key_returns_key(self):
        """_get_current_key should return the current key."""
        with patch("app.services.groqService.settings") as mock_settings:
            mock_settings.GROQ_API_KEYS = ["key1", "key2"]
            mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"

            service = GroqService()
            assert service._get_current_key() == "key1"

    def test_rotate_key_advances_index(self):
        """_rotate_key should advance to next key."""
        with patch("app.services.groqService.settings") as mock_settings:
            mock_settings.GROQ_API_KEYS = ["key1", "key2"]
            mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"

            service = GroqService()
            initial_index = service.current_key_index

            result = service._rotate_key()

            assert result is True
            assert service.current_key_index != initial_index

    def test_rotate_key_returns_false_when_single_key(self):
        """_rotate_key should return False when only one key is available."""
        with patch("app.services.groqService.settings") as mock_settings:
            mock_settings.GROQ_API_KEYS = ["only_key"]
            mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"

            service = GroqService()
            result = service._rotate_key()

            assert result is False

    def test_rotate_key_wraps_around(self):
        """_rotate_key should wrap around to first key after last."""
        with patch("app.services.groqService.settings") as mock_settings:
            mock_settings.GROQ_API_KEYS = ["key1", "key2"]
            mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"

            service = GroqService()
            service.current_key_index = 1  # Last key

            result = service._rotate_key()

            assert result is True
            assert service.current_key_index == 0


class TestGroqServiceChat:
    """Tests for chat functionality."""

    @patch("httpx.Client")
    def test_chat_returns_response_on_success(self, mock_client_class):
        """chat should return response text on successful API call."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello! How can I help you?"}}]
        }
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        with patch("app.services.groqService.settings") as mock_settings:
            mock_settings.GROQ_API_KEYS = ["test_key"]
            mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"

            service = GroqService()
            result = service.chat([{"role": "user", "content": "Hi"}])

            assert result == "Hello! How can I help you?"

    def test_chat_raises_when_messages_empty(self):
        """chat should raise ValueError when messages list is empty."""
        with patch("app.services.groqService.settings") as mock_settings:
            mock_settings.GROQ_API_KEYS = ["test_key"]
            mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"

            service = GroqService()

            with pytest.raises(ValueError, match="Messages list cannot be empty"):
                service.chat([])

    @patch("httpx.Client")
    def test_chat_raises_after_all_keys_fail(self, mock_client_class):
        """chat should raise exception when all API keys fail."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        with patch("app.services.groqService.settings") as mock_settings:
            mock_settings.GROQ_API_KEYS = ["key1", "key2"]
            mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"

            service = GroqService()

            with pytest.raises(Exception) as exc_info:
                service.chat([{"role": "user", "content": "Test"}])
            # After all keys fail, the final exception is raised
            assert "All Groq API keys exhausted" in str(exc_info.value)

    @patch("httpx.Client")
    def test_chat_handles_timeout(self, mock_client_class):
        """chat should handle timeout and rotate to next key."""
        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.TimeoutException("Request timeout")
        mock_client_class.return_value.__enter__.return_value = mock_client

        with patch("app.services.groqService.settings") as mock_settings:
            mock_settings.GROQ_API_KEYS = ["key1", "key2"]
            mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"

            service = GroqService()

            with pytest.raises(Exception) as exc_info:
                service.chat([{"role": "user", "content": "Test"}])
            # After both keys timeout, final exception is raised
            assert "All Groq API keys exhausted" in str(exc_info.value)

    @patch("httpx.Client")
    def test_chat_handles_http_error(self, mock_client_class):
        """chat should handle HTTP errors and rotate key."""
        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.HTTPError("Connection error")
        mock_client_class.return_value.__enter__.return_value = mock_client

        with patch("app.services.groqService.settings") as mock_settings:
            mock_settings.GROQ_API_KEYS = ["key1", "key2"]
            mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"

            service = GroqService()

            with pytest.raises(Exception):
                service.chat([{"role": "user", "content": "Test"}])


class TestGroqServiceSentiment:
    """Tests for sentiment analysis functionality."""

    def test_analyze_sentiment_returns_neutral_for_empty_text(self):
        """analyze_sentiment should return neutral for empty/whitespace text."""
        with patch("app.services.groqService.settings") as mock_settings:
            mock_settings.GROQ_API_KEYS = ["test_key"]
            mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"

            service = GroqService()

            result = service.analyze_sentiment("")
            assert result["label"] == SentimentLabel.NEUTRAL.value
            assert result["score"] == 0.0

            result = service.analyze_sentiment("   ")
            assert result["label"] == SentimentLabel.NEUTRAL.value

    @patch("httpx.Client")
    def test_analyze_sentiment_returns_positive_result(self, mock_client_class):
        """analyze_sentiment should return positive label for positive text."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"label": "positive", "score": 0.8}'}}]
        }
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        with patch("app.services.groqService.settings") as mock_settings:
            mock_settings.GROQ_API_KEYS = ["test_key"]
            mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"

            service = GroqService()
            result = service.analyze_sentiment("I am very happy with the service!")

            assert result["label"] == "positive"
            assert result["score"] == 0.8

    @patch("httpx.Client")
    def test_analyze_sentiment_returns_negative_result(self, mock_client_class):
        """analyze_sentiment should return negative label for negative text."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"label": "negative", "score": -0.7}'}}]
        }
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        with patch("app.services.groqService.settings") as mock_settings:
            mock_settings.GROQ_API_KEYS = ["test_key"]
            mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"

            service = GroqService()
            result = service.analyze_sentiment("This is terrible, I am very frustrated!")

            assert result["label"] == "negative"
            assert result["score"] == -0.7

    @patch("httpx.Client")
    def test_analyze_sentiment_normalizes_score_to_valid_range(self, mock_client_class):
        """analyze_sentiment should clamp score to -1.0 to 1.0 range."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"label": "positive", "score": 1.5}'}}]
        }
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        with patch("app.services.groqService.settings") as mock_settings:
            mock_settings.GROQ_API_KEYS = ["test_key"]
            mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"

            service = GroqService()
            result = service.analyze_sentiment("Test text")

            assert result["score"] == 1.0  # Clamped to max

    @patch("httpx.Client")
    def test_analyze_sentiment_handles_invalid_label(self, mock_client_class):
        """analyze_sentiment should default to neutral for invalid labels."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"label": "unknown", "score": 0.5}'}}]
        }
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        with patch("app.services.groqService.settings") as mock_settings:
            mock_settings.GROQ_API_KEYS = ["test_key"]
            mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"

            service = GroqService()
            result = service.analyze_sentiment("Test text")

            assert result["label"] == SentimentLabel.NEUTRAL.value

    @patch("httpx.Client")
    def test_analyze_sentiment_handles_malformed_json(self, mock_client_class):
        """analyze_sentiment should return neutral on JSON parse error."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "This is not JSON!"}}]
        }
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        with patch("app.services.groqService.settings") as mock_settings:
            mock_settings.GROQ_API_KEYS = ["test_key"]
            mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"

            service = GroqService()
            result = service.analyze_sentiment("Test text")

            assert result["label"] == SentimentLabel.NEUTRAL.value
            assert result["score"] == 0.0

    @patch("httpx.Client")
    def test_analyze_sentiment_handles_api_error(self, mock_client_class):
        """analyze_sentiment should return neutral on API error."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        with patch("app.services.groqService.settings") as mock_settings:
            mock_settings.GROQ_API_KEYS = ["key1", "key2"]
            mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"

            service = GroqService()
            result = service.analyze_sentiment("Test text")

            # Should return neutral on error (graceful degradation)
            assert result["label"] == SentimentLabel.NEUTRAL.value
            assert result["score"] == 0.0

    @patch("httpx.Client")
    def test_analyze_sentiment_truncates_long_text(self, mock_client_class):
        """analyze_sentiment should truncate text to 1000 characters."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"label": "neutral", "score": 0}'}}]
        }
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        with patch("app.services.groqService.settings") as mock_settings:
            mock_settings.GROQ_API_KEYS = ["test_key"]
            mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"

            service = GroqService()
            long_text = "A" * 2000
            service.analyze_sentiment(long_text)

            # Check that the text sent to API is truncated
            call_args = mock_client.post.call_args
            messages = call_args.kwargs["json"]["messages"]
            assert len(messages[1]["content"]) <= 1000


class TestGroqServiceRequestBuilding:
    """Tests for request building."""

    @patch("httpx.Client")
    def test_make_request_includes_authorization_header(self, mock_client_class):
        """_make_request should include Authorization header with API key."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        with patch("app.services.groqService.settings") as mock_settings:
            mock_settings.GROQ_API_KEYS = ["my_secret_key"]
            mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"

            service = GroqService()
            service._make_request([{"role": "user", "content": "test"}], 0)

            call_args = mock_client.post.call_args
            headers = call_args.kwargs["headers"]
            assert "Authorization" in headers
            assert headers["Authorization"] == "Bearer my_secret_key"

    @patch("httpx.Client")
    def test_make_request_uses_configured_model(self, mock_client_class):
        """_make_request should use the configured model."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        with patch("app.services.groqService.settings") as mock_settings:
            mock_settings.GROQ_API_KEYS = ["test_key"]
            mock_settings.GROQ_MODEL = "llama-3.3-70b-versatile"

            service = GroqService()
            service._make_request([{"role": "user", "content": "test"}], 0)

            call_args = mock_client.post.call_args
            payload = call_args.kwargs["json"]
            assert payload["model"] == "llama-3.3-70b-versatile"

    @patch("httpx.Client")
    def test_make_request_includes_messages_in_payload(self, mock_client_class):
        """_make_request should include messages in request payload."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        with patch("app.services.groqService.settings") as mock_settings:
            mock_settings.GROQ_API_KEYS = ["test_key"]
            mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"

            service = GroqService()
            messages = [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Hello"}
            ]
            service._make_request(messages, 0)

            call_args = mock_client.post.call_args
            payload = call_args.kwargs["json"]
            assert payload["messages"] == messages