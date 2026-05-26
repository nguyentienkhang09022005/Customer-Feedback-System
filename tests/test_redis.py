"""
Tests for RedisService - Redis connection and operations.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.services.redisService import RedisService


class TestRedisServiceSingleton:
    """Tests for RedisService singleton behavior."""

    def test_redis_service_is_singleton(self):
        """RedisService should return the same instance."""
        service1 = RedisService()
        service2 = RedisService()
        assert service1 is service2


class TestRedisServiceConnection:
    """Tests for Redis connection management."""

    def test_is_connected_returns_false_when_disabled(self):
        """is_connected should return False when Redis is disabled."""
        service = RedisService()
        service.enabled = False

        assert service.is_connected() is False

    def test_is_connected_returns_false_when_client_is_none(self):
        """is_connected should return False when client is None."""
        service = RedisService()
        service.enabled = True
        service._client = None

        assert service.is_connected() is False

    def test_is_connected_returns_false_when_client_cannot_ping(self):
        """is_connected should return False when ping fails."""
        service = RedisService()
        service.enabled = True

        mock_client = MagicMock()
        mock_client.ping.side_effect = Exception("Connection failed")
        service._client = mock_client

        assert service.is_connected() is False

    def test_close_sets_client_to_none(self):
        """Closing connection should set _client to None."""
        service = RedisService()
        service._client = MagicMock()

        service.close()

        assert service._client is None


class TestRedisServiceSetWithExpiry:
    """Tests for set_with_expiry operations."""

    def test_set_with_expiry_returns_false_when_not_connected(self):
        """set_with_expiry should return False when Redis is not connected."""
        service = RedisService()
        service.enabled = False
        service._client = None

        result = service.set_with_expiry("test_key", "test_value", 60)

        assert result is False

    def test_set_with_expiry_calls_setex_on_client(self):
        """set_with_expiry should call setex with correct parameters."""
        service = RedisService()
        service.enabled = True
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        service._client = mock_client

        result = service.set_with_expiry("my_key", "my_value", 120)

        assert result is True
        mock_client.setex.assert_called_once_with("my_key", 120, "my_value")

    def test_set_with_expiry_returns_false_on_redis_error(self):
        """set_with_expiry should return False on Redis error."""
        import redis

        service = RedisService()
        service.enabled = True
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.setex.side_effect = redis.RedisError("SET failed")
        service._client = mock_client

        result = service.set_with_expiry("test_key", "test_value", 60)

        assert result is False


class TestRedisServiceGet:
    """Tests for get operations."""

    def test_get_returns_none_when_not_connected(self):
        """get should return None when Redis is not connected."""
        service = RedisService()
        service.enabled = False
        service._client = None

        result = service.get("test_key")

        assert result is None

    def test_get_returns_value_on_success(self):
        """get should return the value on successful retrieval."""
        service = RedisService()
        service.enabled = True
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.get.return_value = "stored_value"
        service._client = mock_client

        result = service.get("test_key")

        assert result == "stored_value"
        mock_client.get.assert_called_with("test_key")

    def test_get_returns_none_on_redis_error(self):
        """get should return None on Redis error."""
        import redis

        service = RedisService()
        service.enabled = True
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.get.side_effect = redis.RedisError("GET failed")
        service._client = mock_client

        result = service.get("test_key")

        assert result is None


class TestRedisServiceDelete:
    """Tests for delete operations."""

    def test_delete_returns_false_when_not_connected(self):
        """delete should return False when Redis is not connected."""
        service = RedisService()
        service.enabled = False
        service._client = None

        result = service.delete("test_key")

        assert result is False

    def test_delete_returns_true_on_success(self):
        """delete should return True on successful deletion."""
        service = RedisService()
        service.enabled = True
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        service._client = mock_client

        result = service.delete("test_key")

        assert result is True
        mock_client.delete.assert_called_with("test_key")

    def test_delete_returns_false_on_redis_error(self):
        """delete should return False on Redis error."""
        import redis

        service = RedisService()
        service.enabled = True
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.delete.side_effect = redis.RedisError("DEL failed")
        service._client = mock_client

        result = service.delete("test_key")

        assert result is False


class TestRedisServiceExists:
    """Tests for exists operations."""

    def test_exists_returns_false_when_not_connected(self):
        """exists should return False when Redis is not connected."""
        service = RedisService()
        service._client = None

        result = service.exists("test_key")

        assert result is False

    def test_exists_returns_true_when_key_exists(self):
        """exists should return True when key exists."""
        service = RedisService()
        mock_client = MagicMock()
        mock_client.exists.return_value = 1
        service._client = mock_client

        result = service.exists("test_key")

        assert result is True

    def test_exists_returns_false_when_key_not_found(self):
        """exists should return False when key does not exist."""
        service = RedisService()
        mock_client = MagicMock()
        mock_client.exists.return_value = 0
        service._client = mock_client

        result = service.exists("missing_key")

        assert result is False


class TestRedisServiceSetOperations:
    """Tests for set operations (SADD, SMEMBERS, SREM)."""

    def test_add_to_set_returns_false_when_not_connected(self):
        """add_to_set should return False when not connected."""
        service = RedisService()
        service._client = None

        result = service.add_to_set("my_set", "value1", "value2")

        assert result is False

    def test_add_to_set_calls_sadd_on_client(self):
        """add_to_set should call sadd with values."""
        service = RedisService()
        mock_client = MagicMock()
        service._client = mock_client

        result = service.add_to_set("my_set", "value1", "value2")

        assert result is True
        mock_client.sadd.assert_called_with("my_set", "value1", "value2")

    def test_get_set_members_returns_empty_set_when_not_connected(self):
        """get_set_members should return empty set when not connected."""
        service = RedisService()
        service._client = None

        result = service.get_set_members("my_set")

        assert result == set()

    def test_get_set_members_returns_members_on_success(self):
        """get_set_members should return set members on success."""
        service = RedisService()
        mock_client = MagicMock()
        mock_client.smembers.return_value = {"member1", "member2"}
        service._client = mock_client

        result = service.get_set_members("my_set")

        assert result == {"member1", "member2"}

    def test_remove_from_set_returns_false_when_not_connected(self):
        """remove_from_set should return False when not connected."""
        service = RedisService()
        service._client = None

        result = service.remove_from_set("my_set", "value1")

        assert result is False

    def test_remove_from_set_calls_srem_on_client(self):
        """remove_from_set should call srem with values."""
        service = RedisService()
        mock_client = MagicMock()
        service._client = mock_client

        result = service.remove_from_set("my_set", "value1", "value2")

        assert result is True
        mock_client.srem.assert_called_with("my_set", "value1", "value2")


class TestRedisServiceIncrement:
    """Tests for increment operations."""

    def test_increment_returns_negative_one_when_not_connected(self):
        """increment should return -1 when not connected."""
        service = RedisService()
        service._client = None

        result = service.increment("counter_key")

        assert result == -1

    def test_increment_returns_new_value_on_success(self):
        """increment should return new value after increment."""
        service = RedisService()
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.incr.return_value = 5
        service._client = mock_client

        result = service.increment("counter_key")

        assert result == 5

    def test_increment_returns_negative_one_on_redis_error(self):
        """increment should return -1 on Redis error."""
        import redis

        service = RedisService()
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.incr.side_effect = redis.RedisError("INCR failed")
        service._client = mock_client

        result = service.increment("counter_key")

        assert result == -1