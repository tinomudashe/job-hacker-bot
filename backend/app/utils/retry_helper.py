"""
Retry helper for handling API overload errors
"""
import asyncio
import logging
from typing import TypeVar, Callable, Any
from anthropic import InternalServerError

log = logging.getLogger(__name__)

T = TypeVar('T')

async def retry_with_backoff(
    func: Callable[..., T],
    *args,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    **kwargs
) -> T:
    """
    Retry a function with exponential backoff for overload errors.
    
    Args:
        func: The async function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Factor to multiply delay by after each retry
        *args, **kwargs: Arguments to pass to the function
    
    Returns:
        The result of the function call
    
    Raises:
        The last exception if all retries fail
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            # Call the function
            result = await func(*args, **kwargs)
            if attempt > 0:
                log.info(f"Successfully completed after {attempt + 1} attempts")
            return result
            
        except InternalServerError as e:
            # Check if it's an overload error (529)
            if '529' in str(e) or 'overloaded' in str(e).lower():
                last_exception = e
                if attempt < max_retries - 1:
                    log.warning(
                        f"API overloaded (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                    delay *= backoff_factor
                else:
                    log.error(f"API overloaded after {max_retries} retries")
                    raise Exception(
                        "The AI service is currently experiencing high traffic. "
                        "Please try again in a few moments."
                    ) from e
            else:
                # Not an overload error, re-raise immediately
                raise
                
        except Exception as e:
            # For any other exception, re-raise immediately
            log.error(f"Non-retryable error: {e}")
            raise
    
    # This shouldn't be reached, but just in case
    if last_exception:
        raise last_exception
    raise Exception("Retry failed with unknown error")