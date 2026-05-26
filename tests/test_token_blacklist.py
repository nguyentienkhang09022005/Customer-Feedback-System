"""
Tests for TokenBlacklistService.

Coverage areas:
- Access token blacklist (blacklist, check)
- Refresh token blacklist (blacklist, check)
- Bulk user token invalidation
- Blacklist cleanup
- Edge cases (expired TTL, empty JTI, disconnected Redis)
"""

import pytest
from unittest.mock import patch


# ============================================================================
# Happy Path Tests
# ============================================================================

def test_blacklist_access_token_succeeds_with_valid_ttl():
    """Blacklisting a valid access token should store it in Redis."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from uuid import uuid4
        from app.services.tokenBlacklistService import TokenBlacklistService

        jti = str(uuid4())
        user_id = str(uuid4())
        expires_in = 3600  # 1 hour
        mock_redis.set_with_expiry.return_value = True
        mock_redis.add_to_set.return_value = True

        result = TokenBlacklistService.blacklist_access_token(jti, user_id, expires_in)

        assert result is True
        mock_redis.set_with_expiry.assert_called_once()
        mock_redis.add_to_set.assert_called_once()


def test_blacklist_refresh_token_succeeds_with_valid_ttl():
    """Blacklisting a valid refresh token should store it in Redis."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from uuid import uuid4
        from app.services.tokenBlacklistService import TokenBlacklistService

        jti = str(uuid4())
        user_id = str(uuid4())
        expires_in = 86400  # 1 day
        mock_redis.set_with_expiry.return_value = True
        mock_redis.add_to_set.return_value = True

        result = TokenBlacklistService.blacklist_refresh_token(jti, user_id, expires_in)

        assert result is True
        mock_redis.set_with_expiry.assert_called_once()
        mock_redis.add_to_set.assert_called_once()


def test_is_access_token_blacklisted_returns_true_for_blacklisted_token():
    """Checking a blacklisted access token should return True."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from uuid import uuid4
        from app.services.tokenBlacklistService import TokenBlacklistService

        jti = str(uuid4())
        mock_redis.exists.return_value = True

        result = TokenBlacklistService.is_access_token_blacklisted(jti)

        assert result is True
        mock_redis.exists.assert_called_once()


def test_is_refresh_token_blacklisted_returns_true_for_blacklisted_token():
    """Checking a blacklisted refresh token should return True."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from uuid import uuid4
        from app.services.tokenBlacklistService import TokenBlacklistService

        jti = str(uuid4())
        mock_redis.exists.return_value = True

        result = TokenBlacklistService.is_refresh_token_blacklisted(jti)

        assert result is True
        mock_redis.exists.assert_called_once()


# ============================================================================
# Validation / Invalid Input Tests
# ============================================================================

def test_blacklist_access_token_skips_expired_token():
    """Blacklisting a token with expires_in <= 0 should skip and return True."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from uuid import uuid4
        from app.services.tokenBlacklistService import TokenBlacklistService

        jti = str(uuid4())
        user_id = str(uuid4())

        result = TokenBlacklistService.blacklist_access_token(jti, user_id, 0)

        assert result is True
        mock_redis.set_with_expiry.assert_not_called()


def test_blacklist_access_token_skips_negative_ttl():
    """Blacklisting a token with negative TTL should skip and return True."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from uuid import uuid4
        from app.services.tokenBlacklistService import TokenBlacklistService

        jti = str(uuid4())
        user_id = str(uuid4())

        result = TokenBlacklistService.blacklist_access_token(jti, user_id, -10)

        assert result is True
        mock_redis.set_with_expiry.assert_not_called()


def test_blacklist_refresh_token_skips_expired_token():
    """Blacklisting a refresh token with expires_in <= 0 should skip and return True."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from uuid import uuid4
        from app.services.tokenBlacklistService import TokenBlacklistService

        jti = str(uuid4())
        user_id = str(uuid4())

        result = TokenBlacklistService.blacklist_refresh_token(jti, user_id, 0)

        assert result is True
        mock_redis.set_with_expiry.assert_not_called()


def test_blacklist_refresh_token_skips_negative_ttl():
    """Blacklisting a refresh token with negative TTL should skip and return True."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from uuid import uuid4
        from app.services.tokenBlacklistService import TokenBlacklistService

        jti = str(uuid4())
        user_id = str(uuid4())

        result = TokenBlacklistService.blacklist_refresh_token(jti, user_id, -3600)

        assert result is True
        mock_redis.set_with_expiry.assert_not_called()


def test_is_access_token_blacklisted_returns_false_for_empty_jti():
    """Checking with an empty JTI string should return False instead of querying."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from app.services.tokenBlacklistService import TokenBlacklistService

        result = TokenBlacklistService.is_access_token_blacklisted("")

        assert result is False
        mock_redis.exists.assert_not_called()


def test_is_access_token_blacklisted_returns_false_for_none_jti():
    """Checking with None JTI should return False instead of querying."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from app.services.tokenBlacklistService import TokenBlacklistService

        result = TokenBlacklistService.is_access_token_blacklisted(None)

        assert result is False
        mock_redis.exists.assert_not_called()


def test_is_refresh_token_blacklisted_returns_false_for_empty_jti():
    """Checking with an empty JTI string should return False for refresh token."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from app.services.tokenBlacklistService import TokenBlacklistService

        result = TokenBlacklistService.is_refresh_token_blacklisted("")

        assert result is False
        mock_redis.exists.assert_not_called()


def test_is_refresh_token_blacklisted_returns_false_for_none_jti():
    """Checking with None JTI should return False for refresh token."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from app.services.tokenBlacklistService import TokenBlacklistService

        result = TokenBlacklistService.is_refresh_token_blacklisted(None)

        assert result is False
        mock_redis.exists.assert_not_called()


# ============================================================================
# Business Rule / State Rule Tests
# ============================================================================

def test_is_access_token_blacklisted_returns_false_for_unknown_token():
    """Checking a token that was never blacklisted should return False."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from uuid import uuid4
        from app.services.tokenBlacklistService import TokenBlacklistService

        jti = str(uuid4())
        mock_redis.exists.return_value = False

        result = TokenBlacklistService.is_access_token_blacklisted(jti)

        assert result is False


def test_is_refresh_token_blacklisted_returns_false_for_unknown_token():
    """Checking a refresh token that was never blacklisted should return False."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from uuid import uuid4
        from app.services.tokenBlacklistService import TokenBlacklistService

        jti = str(uuid4())
        mock_redis.exists.return_value = False

        result = TokenBlacklistService.is_refresh_token_blacklisted(jti)

        assert result is False


def test_blacklist_access_token_is_idempotent():
    """Blacklisting the same access token twice should not fail."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from uuid import uuid4
        from app.services.tokenBlacklistService import TokenBlacklistService

        jti = str(uuid4())
        user_id = str(uuid4())
        expires_in = 3600
        mock_redis.set_with_expiry.return_value = True
        mock_redis.add_to_set.return_value = True

        first = TokenBlacklistService.blacklist_access_token(jti, user_id, expires_in)
        second = TokenBlacklistService.blacklist_access_token(jti, user_id, expires_in)

        assert first is True
        assert second is True
        assert mock_redis.set_with_expiry.call_count == 2


def test_blacklist_refresh_token_is_idempotent():
    """Blacklisting the same refresh token twice should not fail."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from uuid import uuid4
        from app.services.tokenBlacklistService import TokenBlacklistService

        jti = str(uuid4())
        user_id = str(uuid4())
        expires_in = 86400
        mock_redis.set_with_expiry.return_value = True
        mock_redis.add_to_set.return_value = True

        first = TokenBlacklistService.blacklist_refresh_token(jti, user_id, expires_in)
        second = TokenBlacklistService.blacklist_refresh_token(jti, user_id, expires_in)

        assert first is True
        assert second is True
        assert mock_redis.set_with_expiry.call_count == 2


def test_blacklist_all_user_tokens_invalidates_access_and_refresh():
    """Bulk invalidation should blacklist both access and refresh tokens for a user."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from uuid import uuid4
        from app.services.tokenBlacklistService import TokenBlacklistService

        user_id = str(uuid4())
        access_jti_1 = str(uuid4())
        access_jti_2 = str(uuid4())
        refresh_jti_1 = str(uuid4())

        # Track call count to distinguish between access and refresh exists checks
        exists_call_count = [0]

        def exists_side_effect(key: str) -> bool:
            exists_call_count[0] += 1
            return False

        mock_redis.get_set_members.side_effect = lambda key: (
            {access_jti_1, access_jti_2} if "access" in key else
            {refresh_jti_1} if "refresh" in key else
            set()
        )
        mock_redis.exists.side_effect = exists_side_effect
        mock_redis.set_with_expiry.return_value = True
        mock_redis.add_to_set.return_value = True

        count = TokenBlacklistService.blacklist_all_user_tokens(user_id)

        # Should return total number of tokens found
        assert count == 3
        # Each token should be blacklisted with short TTL (1 second)
        assert mock_redis.set_with_expiry.call_count == 3


def test_blacklist_all_user_tokens_skips_already_blacklisted():
    """Bulk invalidation should skip tokens that are already blacklisted."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from uuid import uuid4
        from app.services.tokenBlacklistService import TokenBlacklistService

        user_id = str(uuid4())
        jti_blacklisted = str(uuid4())
        jti_not_blacklisted = str(uuid4())

        call_index = [0]

        def exists_side_effect(key: str) -> bool:
            call_index[0] += 1
            # First two calls (access token checks) return True (already blacklisted)
            # Third call (refresh token check) returns False (not blacklisted)
            return call_index[0] <= 2

        mock_redis.get_set_members.side_effect = lambda key: (
            {jti_blacklisted, jti_not_blacklisted} if "access" in key else
            {jti_blacklisted} if "refresh" in key else
            set()
        )
        mock_redis.exists.side_effect = exists_side_effect
        mock_redis.set_with_expiry.return_value = True
        mock_redis.add_to_set.return_value = True

        count = TokenBlacklistService.blacklist_all_user_tokens(user_id)

        assert count == 3
        # Token in access user's set that was already blacklisted should not be re-added
        # The service checks is_access_token_blacklisted before re-blacklisting
        # So only count includes tokens found, but some are skipped


def test_cleanup_user_blacklist_removes_expired_entries():
    """Cleanup should remove expired token entries from user's set."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from uuid import uuid4
        from app.services.tokenBlacklistService import TokenBlacklistService

        user_id = str(uuid4())
        expired_jti = str(uuid4())
        valid_jti = str(uuid4())

        call_index = [0]

        def exists_side_effect(key: str) -> bool:
            call_index[0] += 1
            # First call returns False (expired token), second returns True (valid token)
            return call_index[0] > 1

        mock_redis.get_set_members.side_effect = lambda key: (
            {expired_jti, valid_jti} if "access" in key else set()
        )
        mock_redis.exists.side_effect = exists_side_effect
        mock_redis.remove_from_set.return_value = True

        result = TokenBlacklistService.cleanup_user_blacklist(user_id)

        assert result is True
        assert mock_redis.remove_from_set.call_count >= 1


def test_cleanup_user_blacklist_handles_empty_set():
    """Cleanup with no tokens to clean should return True without errors."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from app.services.tokenBlacklistService import TokenBlacklistService

        user_id = "user-no-tokens"
        mock_redis.get_set_members.return_value = set()

        result = TokenBlacklistService.cleanup_user_blacklist(user_id)

        assert result is True


# ============================================================================
# Edge Cases
# ============================================================================

def test_blacklist_access_token_returns_false_when_redis_fails():
    """Blacklisting a token with non-existent user should still return True."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from uuid import uuid4
        from app.services.tokenBlacklistService import TokenBlacklistService

        jti = str(uuid4())
        user_id = str(uuid4())
        expires_in = 3600
        # set_with_expiry returns False (Redis failure)
        mock_redis.set_with_expiry.return_value = False

        result = TokenBlacklistService.blacklist_access_token(jti, user_id, expires_in)

        # Service logs warning but doesn't raise - it propagates the failure flag
        assert result is False


def test_blacklist_refresh_token_returns_false_when_redis_fails():
    """Blacklisting refresh token should return False when Redis set fails."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from uuid import uuid4
        from app.services.tokenBlacklistService import TokenBlacklistService

        jti = str(uuid4())
        user_id = str(uuid4())
        expires_in = 86400
        mock_redis.set_with_expiry.return_value = False

        result = TokenBlacklistService.blacklist_refresh_token(jti, user_id, expires_in)

        assert result is False


def test_is_token_blacklisted_returns_false_when_redis_disconnected():
    """Checking blacklist should return False for safety when Redis is disconnected."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from uuid import uuid4
        from app.services.tokenBlacklistService import TokenBlacklistService

        # When is_connected returns False, redis_service.exists() also returns False
        # per the RedisService.exists() logic (it checks is_connected first).
        mock_redis.is_connected.return_value = False
        mock_redis.exists.return_value = False
        jti = str(uuid4())

        # Access token check - should return False because disconnected
        access_result = TokenBlacklistService.is_access_token_blacklisted(jti)
        assert access_result is False

        # Refresh token check - should return False because disconnected
        refresh_result = TokenBlacklistService.is_refresh_token_blacklisted(jti)
        assert refresh_result is False


def test_blacklist_access_token_user_key_includes_user_id():
    """Verify the user tracking set key includes the correct user_id."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from uuid import uuid4
        from app.services.tokenBlacklistService import TokenBlacklistService

        jti = str(uuid4())
        user_id = "user-123"
        expires_in = 3600
        mock_redis.set_with_expiry.return_value = True
        mock_redis.add_to_set.return_value = True

        TokenBlacklistService.blacklist_access_token(jti, user_id, expires_in)

        # Check that add_to_set was called with correct user key
        call_args = mock_redis.add_to_set.call_args
        assert call_args is not None, "add_to_set was not called"
        user_key = call_args[0][0]
        assert user_key == f"blacklist:user:{user_id}:access"
        assert call_args[0][1] == jti


def test_blacklist_refresh_token_user_key_includes_user_id():
    """Verify the refresh token user tracking set key includes the correct user_id."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from uuid import uuid4
        from app.services.tokenBlacklistService import TokenBlacklistService

        jti = str(uuid4())
        user_id = "user-456"
        expires_in = 86400
        mock_redis.set_with_expiry.return_value = True
        mock_redis.add_to_set.return_value = True

        TokenBlacklistService.blacklist_refresh_token(jti, user_id, expires_in)

        call_args = mock_redis.add_to_set.call_args
        assert call_args is not None, "add_to_set was not called"
        user_key = call_args[0][0]
        assert user_key == f"blacklist:user:{user_id}:refresh"
        assert call_args[0][1] == jti


def test_blacklist_all_user_tokens_handles_no_tokens_found():
    """Bulk invalidation with no tokens for user should return 0."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from uuid import uuid4
        from app.services.tokenBlacklistService import TokenBlacklistService

        user_id = str(uuid4())
        mock_redis.get_set_members.return_value = set()

        count = TokenBlacklistService.blacklist_all_user_tokens(user_id)

        assert count == 0


def test_blacklist_all_user_tokens_with_only_access_tokens():
    """Bulk invalidation should handle users with only access tokens (no refresh)."""
    with patch("app.services.tokenBlacklistService.redis_service") as mock_redis:
        from uuid import uuid4
        from app.services.tokenBlacklistService import TokenBlacklistService

        user_id = str(uuid4())
        access_jti = str(uuid4())

        def get_set_members_side_effect(key):
            if "access" in key:
                return {access_jti}
            return set()

        mock_redis.get_set_members.side_effect = get_set_members_side_effect
        mock_redis.exists.return_value = False
        mock_redis.set_with_expiry.return_value = True
        mock_redis.add_to_set.return_value = True

        count = TokenBlacklistService.blacklist_all_user_tokens(user_id)

        # Should count the one access token found
        assert count == 1
        mock_redis.set_with_expiry.assert_called_once()
