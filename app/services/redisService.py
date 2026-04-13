import redis
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    from upstash_redis import Redis as UpstashRedis
    UPSTASH_AVAILABLE = True
except ImportError:
    UPSTASH_AVAILABLE = False
    UpstashRedis = None


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
        self.enabled = settings.REDIS_ENABLED
        self._connect()
    
    def _connect(self):
        """Establish Redis connection"""
        if not self.enabled:
            logger.warning("⚠️ Redis is disabled")
            return

        if settings.REDIS_UPSTASH_MODE and UPSTASH_AVAILABLE:
            self._connect_upstash()
        else:
            self._connect_local()

    def _connect_upstash(self):
        """Connect to Upstash Redis Cloud"""
        try:
            if not settings.UPSTASH_REDIS_REST_URL or not settings.UPSTASH_REDIS_REST_TOKEN:
                logger.error("❌ Upstash mode enabled but credentials not found")
                self._client = None
                return

            self._client = UpstashRedis(
                url=settings.UPSTASH_REDIS_REST_URL,
                token=settings.UPSTASH_REDIS_REST_TOKEN
            )
            # Test connection
            self._client.ping()
            logger.info("✅ Upstash Redis connected")
        except Exception as e:
            logger.error(f"❌ Upstash Redis connection failed: {e}")
            self._client = None

    def _connect_local(self):
        """Connect to local Redis (legacy)"""
        try:
            # Check if local Redis settings exist
            if not hasattr(settings, 'REDIS_HOST'):
                logger.warning("⚠️ Local Redis settings not found. Install upstash-redis and set REDIS_UPSTASH_MODE=true")
                self._client = None
                return

            self._client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self._client.ping()
            logger.info(f"✅ Redis connected to {settings.REDIS_HOST}:{settings.REDIS_PORT}")
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
    
    def increment(self, key: str) -> int:
        """
        Increment a counter atomically.
        
        Args:
            key: Redis key
        
        Returns:
            int: New value after increment, -1 if failed
        """
        if not self.is_connected():
            logger.warning(f"⚠️ Redis not connected, skipping INCR: {key}")
            return -1
        
        try:
            result = self._client.incr(key)
            logger.debug(f"✅ INCR {key} -> {result}")
            return result
        except redis.RedisError as e:
            logger.error(f"❌ Redis INCR error for {key}: {e}")
            return -1
    
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
