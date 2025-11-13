"""
Phase 4: Production & Scaling Optimizations

Implements:
1. KV Caching - Cache static prompts for cost/latency reduction
2. Model Tiering - Dynamic model selection based on task complexity
3. Prompt Optimization - Structure prompts to maximize cache hits
"""

from typing import Dict, Any, Optional, Callable
from enum import Enum
import hashlib
import json
import logging
from datetime import datetime, timedelta
import redis

logger = logging.getLogger(__name__)


class ModelTier(Enum):
    """Model tier for different task complexities"""
    FLASH = "gemini-1.5-flash-latest"  # Fast, cheap - for simple tasks
    PRO = "gemini-1.5-pro-latest"  # Powerful - for complex tasks


class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"  # User intent classification, quick validation
    MODERATE = "moderate"  # Code generation, chart generation
    COMPLEX = "complex"  # Narrative generation, macro planning


class KVCache:
    """
    Key-Value Cache for LLM responses.

    Implements caching with Redis backend to reduce costs and latency.
    Particularly effective for static prompts (system instructions, user preferences).
    """

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        ttl: int = 3600  # 1 hour default TTL
    ):
        """
        Initialize KV Cache.

        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            redis_db: Redis database number
            ttl: Time-to-live for cached entries (seconds)
        """
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True
            )
            self.redis_client.ping()
            self.enabled = True
            logger.info(f"KVCache initialized with Redis at {redis_host}:{redis_port}")

        except redis.ConnectionError:
            logger.warning("Redis not available, caching disabled")
            self.redis_client = None
            self.enabled = False

        self.ttl = ttl
        self.hit_count = 0
        self.miss_count = 0

    def _generate_cache_key(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.0
    ) -> str:
        """
        Generate cache key from prompt and parameters.

        Args:
            prompt: Input prompt
            model: Model name
            temperature: Generation temperature

        Returns:
            Cache key (hash)
        """
        # Create stable hash from inputs
        cache_input = f"{prompt}|{model}|{temperature}"
        return hashlib.sha256(cache_input.encode()).hexdigest()

    def get(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.0
    ) -> Optional[str]:
        """
        Get cached response for a prompt.

        Args:
            prompt: Input prompt
            model: Model name
            temperature: Generation temperature

        Returns:
            Cached response or None
        """
        if not self.enabled:
            return None

        cache_key = self._generate_cache_key(prompt, model, temperature)

        try:
            cached = self.redis_client.get(cache_key)

            if cached:
                self.hit_count += 1
                logger.debug(f"Cache HIT for key {cache_key[:12]}...")
                return cached
            else:
                self.miss_count += 1
                logger.debug(f"Cache MISS for key {cache_key[:12]}...")
                return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(
        self,
        prompt: str,
        model: str,
        response: str,
        temperature: float = 0.0,
        ttl: Optional[int] = None
    ) -> None:
        """
        Cache a response.

        Args:
            prompt: Input prompt
            model: Model name
            response: Model response to cache
            temperature: Generation temperature
            ttl: Custom TTL (uses default if None)
        """
        if not self.enabled:
            return

        cache_key = self._generate_cache_key(prompt, model, temperature)
        ttl = ttl or self.ttl

        try:
            self.redis_client.setex(cache_key, ttl, response)
            logger.debug(f"Cached response for key {cache_key[:12]}... (TTL: {ttl}s)")

        except Exception as e:
            logger.error(f"Cache set error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0

        return {
            "enabled": self.enabled,
            "hits": self.hit_count,
            "misses": self.miss_count,
            "hit_rate": f"{hit_rate:.1f}%",
            "total_requests": total_requests
        }


class ModelRouter:
    """
    Dynamic model selection based on task complexity.

    Routes tasks to appropriate model tier:
    - Gemini Flash: Simple, fast tasks
    - Gemini Pro: Complex reasoning tasks
    """

    # Task complexity mapping
    COMPLEXITY_MAP = {
        "user_intent_classification": TaskComplexity.SIMPLE,
        "quality_check": TaskComplexity.SIMPLE,
        "code_generation": TaskComplexity.MODERATE,
        "chart_generation": TaskComplexity.MODERATE,
        "macro_planning": TaskComplexity.COMPLEX,
        "narrative_generation": TaskComplexity.COMPLEX
    }

    # Model selection rules
    MODEL_RULES = {
        TaskComplexity.SIMPLE: ModelTier.FLASH,
        TaskComplexity.MODERATE: ModelTier.PRO,
        TaskComplexity.COMPLEX: ModelTier.PRO
    }

    @classmethod
    def select_model(cls, task_type: str) -> str:
        """
        Select optimal model for a task.

        Args:
            task_type: Type of task

        Returns:
            Model name
        """
        complexity = cls.COMPLEXITY_MAP.get(task_type, TaskComplexity.MODERATE)
        model_tier = cls.MODEL_RULES[complexity]

        logger.debug(f"Task '{task_type}' → {complexity.value} → {model_tier.value}")

        return model_tier.value

    @classmethod
    def estimate_cost(
        cls,
        task_type: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Estimate cost for a task.

        Gemini pricing (as of 2024):
        - Flash: $0.075/1M input, $0.30/1M output
        - Pro: $1.25/1M input, $5.00/1M output

        Args:
            task_type: Type of task
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        model = cls.select_model(task_type)

        if "flash" in model.lower():
            input_cost_per_1m = 0.075
            output_cost_per_1m = 0.30
        else:  # Pro
            input_cost_per_1m = 1.25
            output_cost_per_1m = 5.00

        cost = (
            (input_tokens / 1_000_000) * input_cost_per_1m +
            (output_tokens / 1_000_000) * output_cost_per_1m
        )

        return cost


class PromptOptimizer:
    """
    Optimize prompts for maximum cache hit rate.

    Strategy: Place static content (system instructions, user preferences)
    at the beginning of prompts to maximize prefix matching.
    """

    @staticmethod
    def structure_for_caching(
        system_instruction: str,
        user_preferences: Dict[str, Any],
        dynamic_context: str,
        task_instruction: str
    ) -> str:
        """
        Structure prompt to maximize cache hits.

        Prompt structure (static → dynamic):
        1. System instruction (static)
        2. User preferences (mostly static)
        3. Dynamic context (changes per query)
        4. Task instruction (varies)

        Args:
            system_instruction: Static system role
            user_preferences: User preferences
            dynamic_context: Query-specific context
            task_instruction: Specific task

        Returns:
            Optimized prompt
        """
        # Format preferences consistently for caching
        prefs_text = json.dumps(user_preferences, sort_keys=True)

        prompt = f"""[SYSTEM]
{system_instruction}

[USER PREFERENCES]
{prefs_text}

[CONTEXT]
{dynamic_context}

[TASK]
{task_instruction}
"""

        return prompt

    @staticmethod
    def extract_static_prefix(prompt: str) -> tuple[str, str]:
        """
        Extract static prefix from prompt for separate caching.

        Args:
            prompt: Full prompt

        Returns:
            Tuple of (static_prefix, dynamic_suffix)
        """
        # Find the [CONTEXT] marker
        if "[CONTEXT]" in prompt:
            parts = prompt.split("[CONTEXT]", 1)
            return parts[0], "[CONTEXT]" + parts[1]

        # If no marker, assume first 50% is static
        midpoint = len(prompt) // 2
        return prompt[:midpoint], prompt[midpoint:]


class RateLimiter:
    """
    Rate limiting for API calls to stay within quota.

    Implements token bucket algorithm.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        tokens_per_minute: int = 32000
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Max requests per minute
            tokens_per_minute: Max tokens per minute (Gemini limit)
        """
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = tokens_per_minute

        self.request_timestamps = []
        self.token_usage = []

    def can_make_request(
        self,
        estimated_tokens: int = 1000
    ) -> bool:
        """
        Check if request can be made within limits.

        Args:
            estimated_tokens: Estimated tokens for request

        Returns:
            True if within limits
        """
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)

        # Clean old timestamps
        self.request_timestamps = [
            ts for ts in self.request_timestamps
            if ts > one_minute_ago
        ]

        self.token_usage = [
            (ts, tokens) for ts, tokens in self.token_usage
            if ts > one_minute_ago
        ]

        # Check limits
        current_requests = len(self.request_timestamps)
        current_tokens = sum(tokens for _, tokens in self.token_usage)

        if current_requests >= self.requests_per_minute:
            logger.warning("Request limit exceeded")
            return False

        if current_tokens + estimated_tokens > self.tokens_per_minute:
            logger.warning("Token limit exceeded")
            return False

        return True

    def record_request(self, tokens_used: int) -> None:
        """Record a request"""
        now = datetime.now()
        self.request_timestamps.append(now)
        self.token_usage.append((now, tokens_used))


# Cached wrapper for Gemini calls
def cached_gemini_call(
    model_function: Callable,
    prompt: str,
    model: str,
    cache: Optional[KVCache] = None,
    temperature: float = 0.0,
    use_cache: bool = True
) -> str:
    """
    Wrapper for Gemini API calls with caching.

    Args:
        model_function: Function that calls Gemini model
        prompt: Input prompt
        model: Model name
        cache: KVCache instance
        temperature: Generation temperature
        use_cache: Whether to use cache

    Returns:
        Model response
    """
    if use_cache and cache and cache.enabled:
        # Try cache first
        cached_response = cache.get(prompt, model, temperature)
        if cached_response:
            logger.info("Using cached response")
            return cached_response

    # Call model
    response = model_function(prompt)

    # Cache response
    if use_cache and cache and cache.enabled:
        cache.set(prompt, model, response, temperature)

    return response
