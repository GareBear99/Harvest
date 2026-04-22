"""
API Error Handling with Retry Logic
Provides robust error handling for external API calls (Binance, etc.)
"""

import time
import logging
from functools import wraps
from typing import Callable, Any, Optional
from requests.exceptions import RequestException, Timeout, ConnectionError


logger = logging.getLogger("harvest.api")


class APIError(Exception):
    """Base exception for API errors"""
    pass


class RateLimitError(APIError):
    """Raised when API rate limit is hit"""
    pass


class AuthenticationError(APIError):
    """Raised when API authentication fails"""
    pass


class DataError(APIError):
    """Raised when API returns invalid or missing data"""
    pass


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (RequestException, ConnectionError, Timeout)
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"API call failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"API call failed after {max_retries + 1} attempts: {str(e)}"
                        )
                        raise APIError(f"API call failed after {max_retries + 1} attempts") from e
                        
                except Exception as e:
                    # Non-retryable exception
                    logger.error(f"Non-retryable error in API call: {str(e)}")
                    raise
            
            # Should not reach here, but just in case
            if last_exception:
                raise APIError(f"API call failed after {max_retries + 1} attempts") from last_exception
                
        return wrapper
    return decorator


def handle_rate_limit(func: Callable) -> Callable:
    """
    Decorator for handling API rate limits.
    Automatically sleeps when rate limit is hit.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        while True:
            try:
                return func(*args, **kwargs)
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check for rate limit indicators
                if '429' in error_msg or 'rate limit' in error_msg or 'too many requests' in error_msg:
                    wait_time = 60  # Default wait time
                    
                    # Try to extract wait time from error message
                    # Binance usually provides retry-after header
                    if hasattr(e, 'response') and e.response is not None:
                        retry_after = e.response.headers.get('Retry-After')
                        if retry_after:
                            try:
                                wait_time = int(retry_after)
                            except ValueError:
                                pass
                    
                    logger.warning(f"Rate limit hit. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise
                    
    return wrapper


def validate_api_response(response: Any, required_fields: Optional[list] = None) -> Any:
    """
    Validate API response data.
    
    Args:
        response: API response to validate
        required_fields: List of required fields in response
    
    Returns:
        Validated response
    
    Raises:
        DataError: If response is invalid
    """
    if response is None:
        raise DataError("API returned None response")
    
    if isinstance(response, dict):
        # Check for error indicators
        if 'error' in response:
            raise APIError(f"API error: {response['error']}")
        
        if 'code' in response and response['code'] != 200:
            raise APIError(f"API error code {response['code']}: {response.get('msg', 'Unknown error')}")
        
        # Check required fields
        if required_fields:
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                raise DataError(f"Missing required fields: {missing_fields}")
    
    elif isinstance(response, list):
        if len(response) == 0:
            raise DataError("API returned empty list")
    
    return response


# Usage examples and decorators for common patterns

@retry_with_backoff(max_retries=3, initial_delay=1.0)
@handle_rate_limit
def fetch_market_data_safe(api_client, symbol: str, interval: str, limit: int):
    """
    Safely fetch market data with retries and rate limit handling.
    
    Example usage:
        data = fetch_market_data_safe(client, "BTCUSDT", "1h", 100)
    """
    try:
        response = api_client.get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        
        # Validate response
        validate_api_response(response, required_fields=None)
        
        if not isinstance(response, list) or len(response) == 0:
            raise DataError(f"Invalid market data for {symbol}")
        
        logger.debug(f"Successfully fetched {len(response)} candles for {symbol}")
        return response
        
    except Exception as e:
        logger.error(f"Error fetching market data for {symbol}: {str(e)}")
        raise


@retry_with_backoff(max_retries=2, initial_delay=0.5)
def fetch_account_info_safe(api_client):
    """
    Safely fetch account information with retries.
    
    Example usage:
        account = fetch_account_info_safe(client)
    """
    try:
        response = api_client.get_account()
        
        # Validate response
        validate_api_response(response, required_fields=['totalWalletBalance', 'availableBalance'])
        
        logger.debug("Successfully fetched account information")
        return response
        
    except Exception as e:
        logger.error(f"Error fetching account information: {str(e)}")
        raise


def safe_api_call(func: Callable, *args, fallback_value: Any = None, **kwargs) -> Any:
    """
    Execute API call with error handling and optional fallback value.
    
    Args:
        func: Function to call
        *args: Positional arguments for function
        fallback_value: Value to return on error (if None, re-raises exception)
        **kwargs: Keyword arguments for function
    
    Returns:
        Function result or fallback value on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"API call failed: {str(e)}")
        if fallback_value is not None:
            logger.warning(f"Returning fallback value: {fallback_value}")
            return fallback_value
        raise


# Circuit breaker pattern for preventing cascading failures
class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures from repeated API errors.
    
    States:
        CLOSED: Normal operation, requests pass through
        OPEN: Too many failures, requests blocked
        HALF_OPEN: Testing if service recovered
    """
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker"""
        
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise APIError("Circuit breaker is OPEN - too many recent failures")
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
            
        except Exception as e:
            self.on_failure()
            raise
    
    def on_success(self):
        """Handle successful call"""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            logger.info("Circuit breaker returned to CLOSED state")
        self.failure_count = 0
    
    def on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(f"Circuit breaker OPENED after {self.failure_count} failures")


# Testing
if __name__ == '__main__':
    # Set up logging for testing
    logging.basicConfig(level=logging.DEBUG)
    
    # Test retry decorator
    @retry_with_backoff(max_retries=3, initial_delay=0.5)
    def flaky_function(fail_count: int = 0):
        """Simulates a flaky API call"""
        if not hasattr(flaky_function, 'attempts'):
            flaky_function.attempts = 0
        
        flaky_function.attempts += 1
        
        if flaky_function.attempts <= fail_count:
            raise ConnectionError(f"Simulated failure (attempt {flaky_function.attempts})")
        
        return "Success!"
    
    try:
        result = flaky_function(fail_count=2)
        print(f"✅ Retry test passed: {result}")
    except Exception as e:
        print(f"❌ Retry test failed: {e}")
    
    # Test circuit breaker
    breaker = CircuitBreaker(failure_threshold=3, timeout=5)
    
    def failing_function():
        raise APIError("Simulated API failure")
    
    print("\n Testing circuit breaker...")
    for i in range(5):
        try:
            breaker.call(failing_function)
        except APIError as e:
            print(f"Attempt {i+1}: {e}")
    
    print("\n✅ Error handling tests complete")
