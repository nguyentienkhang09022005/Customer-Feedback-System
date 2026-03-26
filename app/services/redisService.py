import redis
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """
    Redis service singleton for connection management.
    Provides thread-safe Redis operations with error handling.
    """
    
    _instance: Optional['RedisService'] = None
    _client: Optional[redis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.host = settings.REDIS_HOST
        self.port = settings.REDIS_PORT
        self.db = settings.REDIS_DB
        self.password = settings.REDIS_PASSWORD
        self.enabled = settings.REDIS_ENABLED
        self._connect()
    
    def _connect(self):
        """Establish Redis connection"""
        if not self.enabled:
            logger.warning("⚠️ Redis is disabled")
            return
        
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self._client.ping()
            logger.info(f"✅ Redis connected to {self.host}:{self.port}")
        except redis.ConnectionError as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self._client = None
        except Exception as e:
            logger.error(f"❌ Redis error: {e}")
            self._client = None
    
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        if not self._client or not self.enabled:
            return False
        try:
            self._client.ping()
            return True
        except:
            return False
    
    def set_with_expiry(self, key: str, value: str, expiry_seconds: int) -> bool:
        """
        Set a key with TTL (Time To Live).
        Automatically cleans up after expiry.
        
        Args:
            key: Redis key
            value: Value to store
            expiry_seconds: TTL in seconds
        
        Returns:
            bool: True if successful
        """
        if not self.is_connected():
            logger.warning(f"⚠️ Redis not connected, skipping SET: {key}")
            return False
        
        try:
            self._client.setex(key, expiry_seconds, value)
            logger.debug(f"✅ SET {key} with TTL {expiry_seconds}s")
            return True
        except redis.RedisError as e:
            logger.error(f"❌ Redis SET error for {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[str]:
        """
        Get value by key.
        
        Args:
            key: Redis key
        
        Returns:
            Optional[str]: Value if exists, None otherwise
        """
        if not self.is_connected():
            logger.warning(f"⚠️ Redis not connected, skipping GET: {key}")
            return None
        
        try:
            value = self._client.get(key)
            return value
        except redis.RedisError as e:
            logger.error(f"❌ Redis GET error for {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        Delete a key.
        
        Args:
            key: Redis key
        
        Returns:
            bool: True if deleted, False otherwise
        """
        if not self.is_connected():
            logger.warning(f"⚠️ Redis not connected, skipping DELETE: {key}")
            return False
        
        try:
            self._client.delete(key)
            logger.debug(f"✅ DELETE {key}")
            return True
        except redis.RedisError as e:
            logger.error(f"❌ Redis DELETE error for {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists.
        
        Args:
            key: Redis key
        
        Returns:
            bool: True if exists
        """
        if not self.is_connected():
            return False
        
        try:
            return self._client.exists(key) > 0
        except redis.RedisError as e:
            logger.error(f"❌ Redis EXISTS error for {key}: {e}")
            return False
    
    def add_to_set(self, set_key: str, *values) -> bool:
        """
        Add values to a set.
        
        Args:
            set_key: Key of the set
            values: Values to add
        
        Returns:
            bool: True if successful
        """
        if not self.is_connected():
            return False
        
        try:
            self._client.sadd(set_key, *values)
            return True
        except redis.RedisError as e:
            logger.error(f"❌ Redis SADD error for {set_key}: {e}")
            return False
    
    def get_set_members(self, set_key: str) -> set:
        """
        Get all members of a set.
        
        Args:
            set_key: Key of the set
        
        Returns:
            set: Set members
        """
        if not self.is_connected():
            return set()
        
        try:
            return self._client.smembers(set_key)
        except redis.RedisError as e:
            logger.error(f"❌ Redis SMEMBERS error for {set_key}: {e}")
            return set()
    
    def remove_from_set(self, set_key: str, *values) -> bool:
        """
        Remove values from a set.
        
        Args:
            set_key: Key of the set
            values: Values to remove
        
        Returns:
            bool: True if successful
        """
        if not self.is_connected():
            return False
        
        try:
            self._client.srem(set_key, *values)
            return True
        except redis.RedisError as e:
            logger.error(f"❌ Redis SREM error for {set_key}: {e}")
            return False
    
    def close(self):
        """Close Redis connection"""
        if self._client:
            try:
                self._client.close()
                logger.info("✅ Redis connection closed")
            except:
                pass
            self._client = None


# Singleton instance
redis_service = RedisService()
