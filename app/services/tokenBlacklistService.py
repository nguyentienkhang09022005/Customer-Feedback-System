import logging
from typing import Optional
from app.services.redisService import redis_service

logger = logging.getLogger(__name__)

# Key prefixes for Redis
BLACKLIST_ACCESS_PREFIX = "blacklist:access:"
BLACKLIST_REFRESH_PREFIX = "blacklist:refresh:"
BLACKLIST_USER_PREFIX = "blacklist:user:"


class TokenBlacklistService:
    """
    Service for managing JWT token blacklist in Redis.
    Handles logout functionality by invalidating tokens.
    """
    
    @staticmethod
    def blacklist_access_token(jti: str, user_id: str, expires_in: int) -> bool:
        """
        Add an access token to the blacklist.
        
        Args:
            jti: JWT ID (unique token identifier)
            user_id: User ID who owns the token
            expires_in: Seconds until token expires (TTL)
        
        Returns:
            bool: True if blacklisted successfully
        """
        if expires_in <= 0:
            logger.debug(f"⏭️ Token already expired, skipping blacklist: {jti}")
            return True
        
        key = f"{BLACKLIST_ACCESS_PREFIX}{jti}"
        success = redis_service.set_with_expiry(key, "1", expires_in)
        
        if success:
            # Also track in user's blacklist set for bulk invalidation
            user_key = f"{BLACKLIST_USER_PREFIX}{user_id}:access"
            redis_service.add_to_set(user_key, jti)
            logger.info(f"✅ Access token blacklisted: {jti}")
        else:
            logger.warning(f"⚠️ Failed to blacklist access token: {jti}")
        
        return success
    
    @staticmethod
    def blacklist_refresh_token(jti: str, user_id: str, expires_in: int) -> bool:
        """
        Add a refresh token to the blacklist.
        
        Args:
            jti: JWT ID (unique token identifier)
            user_id: User ID who owns the token
            expires_in: Seconds until token expires (TTL)
        
        Returns:
            bool: True if blacklisted successfully
        """
        if expires_in <= 0:
            logger.debug(f"⏭️ Refresh token already expired, skipping blacklist: {jti}")
            return True
        
        key = f"{BLACKLIST_REFRESH_PREFIX}{jti}"
        success = redis_service.set_with_expiry(key, "1", expires_in)
        
        if success:
            # Also track in user's blacklist set
            user_key = f"{BLACKLIST_USER_PREFIX}{user_id}:refresh"
            redis_service.add_to_set(user_key, jti)
            logger.info(f"✅ Refresh token blacklisted: {jti}")
        else:
            logger.warning(f"⚠️ Failed to blacklist refresh token: {jti}")
        
        return success
    
    @staticmethod
    def is_access_token_blacklisted(jti: str) -> bool:
        """
        Check if an access token is blacklisted.
        
        Args:
            jti: JWT ID to check
        
        Returns:
            bool: True if blacklisted (should be rejected)
        """
        if not jti:
            return False
        
        key = f"{BLACKLIST_ACCESS_PREFIX}{jti}"
        is_blacklisted = redis_service.exists(key)
        
        if is_blacklisted:
            logger.debug(f"🚫 Access token is blacklisted: {jti}")
        
        return is_blacklisted
    
    @staticmethod
    def is_refresh_token_blacklisted(jti: str) -> bool:
        """
        Check if a refresh token is blacklisted.
        
        Args:
            jti: JWT ID to check
        
        Returns:
            bool: True if blacklisted (should be rejected)
        """
        if not jti:
            return False
        
        key = f"{BLACKLIST_REFRESH_PREFIX}{jti}"
        is_blacklisted = redis_service.exists(key)
        
        if is_blacklisted:
            logger.debug(f"🚫 Refresh token is blacklisted: {jti}")
        
        return is_blacklisted
    
    @staticmethod
    def blacklist_all_user_tokens(user_id: str) -> int:
        """
        Blacklist all tokens for a specific user.
        Useful for "logout all devices" functionality.
        
        Args:
            user_id: User ID whose tokens should be invalidated
        
        Returns:
            int: Number of tokens blacklisted
        """
        count = 0
        
        # Get all access tokens for user
        access_key = f"{BLACKLIST_USER_PREFIX}{user_id}:access"
        access_tokens = redis_service.get_set_members(access_key)
        for jti in access_tokens:
            if not TokenBlacklistService.is_access_token_blacklisted(jti):
                TokenBlacklistService.blacklist_access_token(jti, user_id, 1)  # 1 second TTL
        
        # Get all refresh tokens for user
        refresh_key = f"{BLACKLIST_USER_PREFIX}{user_id}:refresh"
        refresh_tokens = redis_service.get_set_members(refresh_key)
        for jti in refresh_tokens:
            if not TokenBlacklistService.is_refresh_token_blacklisted(jti):
                TokenBlacklistService.blacklist_refresh_token(jti, user_id, 1)  # 1 second TTL
        
        logger.info(f"✅ All tokens blacklisted for user: {user_id}")
        return len(access_tokens) + len(refresh_tokens)
    
    @staticmethod
    def cleanup_user_blacklist(user_id: str) -> bool:
        """
        Clean up expired entries from user's blacklist set.
        Called periodically or after TTL expires.
        
        Args:
            user_id: User ID to clean up
        
        Returns:
            bool: True if successful
        """
        access_key = f"{BLACKLIST_USER_PREFIX}{user_id}:access"
        refresh_key = f"{BLACKLIST_USER_PREFIX}{user_id}:refresh"
        
        # Check if tokens in set are actually blacklisted, remove if not
        access_tokens = redis_service.get_set_members(access_key)
        for jti in access_tokens:
            if not TokenBlacklistService.is_access_token_blacklisted(jti):
                redis_service.remove_from_set(access_key, jti)
        
        refresh_tokens = redis_service.get_set_members(refresh_key)
        for jti in refresh_tokens:
            if not TokenBlacklistService.is_refresh_token_blacklisted(jti):
                redis_service.remove_from_set(refresh_key, jti)
        
        return True
