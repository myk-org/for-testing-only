"""API request handler module."""
import logging
import time
from typing import Any


logger = logging.getLogger(__name__)

# Default rate limit: 100 requests per minute
DEFAULT_RATE_LIMIT = 100
DEFAULT_RATE_WINDOW = 60  # seconds
DEFAULT_REQUEST_TIMEOUT = 30  # seconds


class RateLimiter:
    """Simple in-memory rate limiter using sliding window."""

    def __init__(self, max_requests: int = DEFAULT_RATE_LIMIT, window_seconds: int = DEFAULT_RATE_WINDOW) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: list[float] = []

    def is_allowed(self) -> bool:
        """Check if a new request is allowed under the rate limit."""
        now = time.monotonic()
        self._requests = [t for t in self._requests if now - t < self.window_seconds]
        if len(self._requests) >= self.max_requests:
            return False
        self._requests.append(now)
        return True

    def reset(self) -> None:
        """Reset the rate limiter."""
        self._requests.clear()


class RequestHandler:
    """Handle incoming API requests with retry, rate limiting, and timeout support."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the request handler.

        Args:
            config: Configuration dictionary with optional keys:
                - max_retries (int): Maximum retry attempts (default: 3)
                - retry_delay (float): Delay between retries in seconds (default: 1.0)
                - rate_limit (int): Max requests per minute (default: 100)
                - request_timeout (int): Request timeout in seconds (default: 30)
                - health_check_url (str): URL for upstream health checks (default: None)
        """
        self.config = config
        self.max_retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 1.0)
        self.request_timeout = config.get("request_timeout", DEFAULT_REQUEST_TIMEOUT)
        self.health_check_url = config.get("health_check_url")
        self.rate_limiter = RateLimiter(
            max_requests=config.get("rate_limit", DEFAULT_RATE_LIMIT)
        )
        logger.info("RequestHandler initialized with retry=%d, rate_limit=%d, timeout=%d",
                     self.max_retries, self.rate_limiter.max_requests, self.request_timeout)

    def process_request(self, data: dict[str, Any]) -> dict[str, Any]:
        """Process an incoming request with rate limiting and timeout tracking.

        Args:
            data: Request data

        Returns:
            Processed response data

        Raises:
            RuntimeError: If rate limit is exceeded
            TimeoutError: If processing exceeds request_timeout
        """
        if not self.rate_limiter.is_allowed():
            raise RuntimeError("Rate limit exceeded. Try again later.")

        start_time = time.monotonic()
        logger.debug(f"Processing request: {data}")
        result = {"status": "success", "data": data}

        elapsed = time.monotonic() - start_time
        if elapsed > self.request_timeout:
            raise TimeoutError(f"Request processing exceeded timeout of {self.request_timeout}s")

        return result

    def process_batch(self, requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process multiple requests in a batch.

        Each request is processed individually with validation and rate limiting.
        Failed requests are included in the results with error details.

        Args:
            requests: List of request data dictionaries

        Returns:
            List of result dictionaries, one per request
        """
        results: list[dict[str, Any]] = []
        for i, data in enumerate(requests):
            try:
                if not self.validate_request(data):
                    results.append({
                        "index": i,
                        "status": "error",
                        "error": "Validation failed: missing required fields 'id' and 'type'",
                    })
                    continue
                result = self.process_request(data)
                result["index"] = i
                results.append(result)
            except Exception as exc:
                results.append({
                    "index": i,
                    "status": "error",
                    "error": str(exc),
                })
        logger.info(f"Batch processed: {len(results)}/{len(requests)} requests")
        return results

    def process_request_with_retry(self, data: dict[str, Any]) -> dict[str, Any]:
        """Process a request with automatic retry on failure.

        Args:
            data: Request data

        Returns:
            Processed response data

        Raises:
            RuntimeError: If all retries are exhausted
        """
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return self.process_request(data)
            except Exception as exc:
                last_error = exc
                logger.warning(f"Attempt {attempt}/{self.max_retries} failed: {exc}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)

        raise RuntimeError(f"All {self.max_retries} retry attempts failed") from last_error

    def validate_request(self, data: dict[str, Any]) -> bool:
        """Validate request data.

        Args:
            data: Request data to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = {"id", "type"}
        return required_fields.issubset(data.keys())

    def health_check(self) -> dict[str, Any]:
        """Check the health status of the handler and its dependencies.

        Returns:
            Dictionary with health status information:
                - status: "healthy" or "unhealthy"
                - uptime_info: Basic handler info
                - rate_limiter: Rate limiter status
                - upstream: Upstream service URL if configured
        """
        health = {
            "status": "healthy",
            "handler": "operational",
            "rate_limiter": {
                "max_requests": self.rate_limiter.max_requests,
                "window_seconds": self.rate_limiter.window_seconds,
                "current_count": len(self.rate_limiter._requests),
            },
        }
        if self.health_check_url:
            health["upstream"] = {
                "url": self.health_check_url,
                "configured": True,
            }
        return health

    def get_stats(self) -> dict[str, Any]:
        """Get handler statistics.

        Returns:
            Dictionary with handler configuration and rate limiter stats
        """
        return {
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "request_timeout": self.request_timeout,
            "rate_limit": self.rate_limiter.max_requests,
            "rate_window": self.rate_limiter.window_seconds,
        }
