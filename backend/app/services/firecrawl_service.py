import requests
import json
import os
import time
import traceback
import sys
import psutil
import threading
import signal
from datetime import datetime
from dotenv import load_dotenv
from ..utils.logger import BeijingLogger
import redis
import hashlib

# Initialize logger
logger = BeijingLogger().get_logger()

# Load environment variables
load_dotenv()

# Firecrawl API configuration
FIRECRAWL_API_TOKEN = os.getenv("FIRECRAWL_API_TOKEN", "fc-f8947ce2c5aa457f9b311b7eff9d1da1")
FIRECRAWL_BASE_URL = "https://api.firecrawl.dev/v1"

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Content cache TTL (24 hours)
CONTENT_CACHE_TTL = 24 * 60 * 60

# Initialize Redis client
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True
    )
    # Test connection
    redis_client.ping()
    logger.info("Redis connection established successfully")
except Exception as e:
    logger.error(f"Redis connection failed: {e}")
    redis_client = None

def get_url_cache_key(url: str) -> str:
    """Generate cache key for URL content"""
    # Use MD5 hash of URL to create a clean cache key
    return f"content:{hashlib.md5(url.encode()).hexdigest()}"

def cache_content(url: str, content: str) -> None:
    """Cache scraped content in Redis"""
    if not redis_client:
        return
    
    try:
        cache_key = get_url_cache_key(url)
        redis_client.setex(cache_key, CONTENT_CACHE_TTL, content)
        logger.info(f"Cached content for URL: {url[:100]}...")
    except Exception as e:
        logger.warning(f"Failed to cache content: {e}")

def get_cached_content(url: str) -> str | None:
    """Get cached content from Redis"""
    if not redis_client:
        return None
    
    try:
        cache_key = get_url_cache_key(url)
        content = redis_client.get(cache_key)
        if content:
            logger.info(f"Retrieved cached content for URL: {url[:100]}...")
            return content
        return None
    except Exception as e:
        logger.warning(f"Failed to get cached content: {e}")
        return None

# Default request timeout (in seconds)
DEFAULT_REQUEST_TIMEOUT = 1200

# Circuit breaker for Firecrawl API
class CircuitBreaker:
    def __init__(self, name, failure_threshold=5, reset_timeout=300):
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.open_since = None
        self.lock = threading.Lock()
        
    def is_open(self):
        """Check if circuit breaker is open (API should not be called)"""
        with self.lock:
            if self.open_since is not None:
                # Check if reset timeout has elapsed
                if time.time() - self.open_since > self.reset_timeout:
                    logger.info(f"Circuit breaker {self.name}: 重置断路器状态")
                    self.reset()
                    return False
                return True
            return False
            
    def record_failure(self):
        """Record an API failure"""
        with self.lock:
            if self.open_since is None:  # Only count failures if circuit is closed
                self.failures += 1
                logger.warning(f"Circuit breaker {self.name}: 记录失败 {self.failures}/{self.failure_threshold}")
                if self.failures >= self.failure_threshold:
                    logger.error(f"Circuit breaker {self.name}: 已打开断路器，暂停API调用 {self.reset_timeout} 秒")
                    self.open_since = time.time()
    
    def record_success(self):
        """Record a successful API call"""
        with self.lock:
            if self.open_since is None and self.failures > 0:  # Only reset counter on success if circuit is closed
                self.failures = 0
                
    def reset(self):
        """Reset the circuit breaker"""
        with self.lock:
            self.failures = 0
            self.open_since = None

# Create circuit breaker for Firecrawl API
firecrawl_circuit = CircuitBreaker("Firecrawl")

class APITimeout(Exception):
    """Exception raised when an API call times out"""
    pass

# Timeout handler for SIGALRM
def timeout_handler(signum, frame):
    logger.error("Firecrawl API请求超时")
    raise APITimeout("Firecrawl API请求超时")

def safe_api_call(method, url, headers=None, json=None, timeout=DEFAULT_REQUEST_TIMEOUT):
    """
    Make a safe API call with timeout and circuit breaker
    
    Args:
        method (str): HTTP method ('get' or 'post')
        url (str): URL to call
        headers (dict): Request headers
        json (dict): JSON payload for POST requests
        timeout (int): Request timeout in seconds
        
    Returns:
        dict: API response or error information
    """
    if firecrawl_circuit.is_open():
        logger.error(f"Firecrawl API断路器打开，跳过API调用 {url}")
        return None
    
    # 使用请求库内置的超时机制，而不是信号处理
    start_time = time.time()
    try:
        if method.lower() == 'get':
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method.lower() == 'post':
            response = requests.post(url, headers=headers, json=json, timeout=timeout)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        # Record API call time
        response_time = time.time() - start_time
        logger.info(f"Firecrawl API响应时间 ({method.upper()} {url}): {response_time:.2f} 秒")
        
        if response.ok:
            firecrawl_circuit.record_success()
            return response
        else:
            firecrawl_circuit.record_failure()
            logger.error(f"Firecrawl API错误: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error(f"Firecrawl API调用超时 (超过 {timeout} 秒)")
        firecrawl_circuit.record_failure()
        return None
    except requests.RequestException as e:
        logger.error(f"Firecrawl API请求异常: {str(e)}")
        firecrawl_circuit.record_failure()
        return None
    except Exception as e:
        logger.error(f"Firecrawl API意外错误: {str(e)}", exc_info=True)
        firecrawl_circuit.record_failure()
        return None

def batch_scrape_urls(urls, output_format="markdown", timeout=30000, wait_time=2000):
    """
    Perform batch scraping of URLs using Firecrawl API
    
    Args:
        urls (list): List of URLs to scrape
        output_format (str): Output format (markdown, html, text)
        timeout (int): Timeout in milliseconds
        wait_time (int): Wait time in milliseconds
        
    Returns:
        dict: Scraped content or error information
    """
    logger.info(f"开始批量爬取 {len(urls)} 个URLs: {', '.join(urls[:3])}{'...' if len(urls) > 3 else ''}")
    
    # Basic input validation
    if not urls or not isinstance(urls, list):
        logger.error("批量爬取URLs参数无效: URLs必须是非空列表")
        return {
            "success": False,
            "error": "URLs must be a non-empty list",
            "error_details": {
                "type": "validation_error",
                "message": "URLs must be a non-empty list"
            },
            "results": []
        }
    
    try:
        # Create the request payload
        payload = {
            "urls": urls,
            "ignoreInvalidURLs": False,
            "formats": [output_format],
            "onlyMainContent": True,
            "headers": {},
            "waitFor": 0,
            "mobile": False,
            "skipTlsVerification": False,
            "timeout": timeout,
            "actions": [
                {
                    "type": "wait",
                    "milliseconds": wait_time
                }
            ],
            "location": {
                "country": "US", 
                "languages": ["en-US"]
            },
            "removeBase64Images": True,
            "blockAds": True,
            "proxy": "basic"
        }
        
        headers = {
            "Authorization": f"Bearer {FIRECRAWL_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Submit the batch scraping request
        logger.info(f"提交批量爬取请求到Firecrawl API")
        
        # Use safe_api_call instead of direct requests
        response = safe_api_call(
            'post',
            f"{FIRECRAWL_BASE_URL}/batch/scrape",
            headers=headers,
            json=payload, 
            timeout=60  # 60 seconds timeout for job submission
        )
        
        # Check if API call failed
        if response is None:
            error_msg = "Failed to submit batch scraping request: API call failed"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_details": {
                    "type": "api_failure",
                    "message": "Failed to submit batch scraping request",
                    "urls": urls
                },
                "results": []
            }
        
        logger.info(f"收到Firecrawl API响应: 状态码 {response.status_code}")
        
        job_data = response.json()
        logger.debug(f"Firecrawl批量爬取作业数据: {json.dumps(job_data)}")
        
        if not job_data.get("success"):
            error_msg = f"Batch scraping request error: {job_data}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_details": {
                    "type": "job_submission_error",
                    "message": "Failed to submit batch scraping job",
                    "api_response": job_data
                },
                "results": []
            }
        
        job_id = job_data.get("id")
        logger.info(f"成功提交批量爬取请求, 作业ID: {job_id}")
        return poll_batch_scrape_results(job_id, headers)
        
    except Exception as e:
        error_msg = f"Error in batch scraping: {str(e)}"
        logger.error(error_msg, exc_info=True)
        logger.error(f"异常堆栈: {traceback.format_exc()}")
        return {
            "success": False,
            "error": error_msg,
            "error_details": {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc(),
                "urls": urls
            },
            "results": []
        }

def poll_batch_scrape_results(job_id, headers, max_retries=10, initial_retry_interval=5):
    """
    Poll for results of a batch scrape job
    
    Args:
        job_id (str): Job ID to poll
        headers (dict): Request headers with authentication
        max_retries (int): Maximum number of retries
        initial_retry_interval (int): Initial retry interval in seconds (will increase exponentially)
        
    Returns:
        dict: Scraped content or error information
    """
    logger.info(f"开始轮询批量爬取作业结果: {job_id}")
    try:
        retry_interval = initial_retry_interval
        
        for attempt in range(max_retries):
            # Get batch scraping status
            status_url = f"{FIRECRAWL_BASE_URL}/batch/scrape/{job_id}"
            logger.info(f"轮询爬取状态, 尝试 {attempt+1}/{max_retries}")
            
            # Use safe_api_call instead of direct requests
            status_response = safe_api_call(
                'get',
                status_url,
                headers=headers,
                timeout=30  # 30 seconds timeout for status check
            )
            
            # Check if API call failed
            if status_response is None:
                # Continue to retry
                if attempt < max_retries - 1:
                    logger.info(f"将在 {retry_interval} 秒后重试")
                    time.sleep(retry_interval)
                    retry_interval = min(retry_interval * 1.5, 30)
                    continue
                else:
                    error_msg = f"Failed to get batch status after {max_retries} attempts"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "error": error_msg,
                        "error_details": {
                            "type": "polling_failure",
                            "message": f"Failed to get batch status after {max_retries} attempts",
                            "job_id": job_id
                        },
                        "results": []
                    }
            
            status_data = status_response.json()
            current_status = status_data.get("status")
            logger.info(f"当前爬取状态: {current_status}")
            
            # Check if completed
            if current_status == "completed":
                # Process and return the results
                results = []
                
                logger.info(f"批量爬取完成, 处理结果数据")
                data_items = status_data.get("data", [])
                logger.info(f"收到 {len(data_items)} 个结果项")
                
                for item in data_items:
                    url = item.get("metadata", {}).get("url", "unknown")
                    content = None
                    
                    # Get content in the specified format
                    content = item.get("markdown")
                    content_size = len(content) if content else 0
                    
                    if content:
                        logger.info(f"成功获取内容: {url}, 内容大小: {content_size} 字符")
                        
                        # Cache the content in Redis
                        cache_content(url, content)
                        
                        results.append({
                            "url": url,
                            "content": content,
                            "success": True
                        })
                    else:
                        error_info = {
                            "type": "content_extraction_failure",
                            "message": "No content found in the specified format"
                        }
                        
                        # Extract error information if available
                        if item.get("error"):
                            error_info.update({
                                "api_error": item.get("error"),
                                "status_code": item.get("statusCode")
                            })
                        
                        logger.warning(f"获取内容失败: {url}, 错误: {error_info}")
                        results.append({
                            "url": url,
                            "content": None,
                            "success": False,
                            "error": "No content found in the specified format",
                            "error_details": error_info
                        })
                
                success_count = sum(1 for r in results if r.get('success', False))
                logger.info(f"批量爬取完成, 成功获取 {success_count} 个内容, 总结果数 {len(results)}")
                
                # If we got no content at all and had URLs to scrape, record as API failure
                if len(results) > 0 and success_count == 0:
                    logger.error("所有URL爬取均失败，记录为API失败")
                    firecrawl_circuit.record_failure()
                    
                return {
                    "success": True,
                    "results": results,
                    "stats": {
                        "total": len(results),
                        "success": success_count,
                        "failure": len(results) - success_count
                    }
                }
            
            # If not completed, wait and retry
            if attempt < max_retries - 1:
                logger.info(f"爬取进行中, 状态: {current_status}, 尝试 {attempt+1}/{max_retries}, 等待 {retry_interval} 秒后重试")
                time.sleep(retry_interval)
                # Increase retry interval (with a cap)
                retry_interval = min(retry_interval * 1.5, 30)
            else:
                error_msg = f"Batch scraping not completed after {max_retries} attempts, final status: {current_status}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "error_details": {
                        "type": "timeout",
                        "message": f"Batch scraping not completed after {max_retries} attempts",
                        "job_id": job_id,
                        "final_status": current_status,
                        "status_data": status_data
                    },
                    "results": []
                }
        
        error_msg = "Batch scraping timed out"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "error_details": {
                "type": "timeout",
                "message": "Batch scraping timed out",
                "job_id": job_id
            },
            "results": []
        }
        
    except Exception as e:
        error_msg = f"Error polling batch scrape results: {str(e)}"
        logger.error(error_msg, exc_info=True)
        logger.error(f"异常堆栈: {traceback.format_exc()}")
        return {
            "success": False,
            "error": error_msg,
            "error_details": {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc(),
                "job_id": job_id
            },
            "results": []
        }

def scrape_single_url(url, output_format="markdown", timeout=30000):
    """
    Scrape a single URL using Firecrawl API
    
    Args:
        url (str): URL to scrape
        output_format (str): Output format (markdown, html, text)
        timeout (int): Timeout in milliseconds
        
    Returns:
        dict: Scraped content or error information
    """
    logger.info(f"开始爬取单个URL: {url}")
    
    # Basic input validation
    if not url or not isinstance(url, str):
        logger.error("爬取URL参数无效: URL必须是有效字符串")
        return {
            "success": False,
            "error": "URL must be a valid string",
            "error_details": {
                "type": "validation_error",
                "message": "URL must be a valid string",
                "provided_value": str(url)
            },
            "results": []
        }
    
    # Don't scrape obviously invalid URLs
    if not (url.startswith('http://') or url.startswith('https://')):
        logger.error(f"URL格式无效: {url}")
        return {
            "success": False, 
            "error": "URL must start with http:// or https://",
            "error_details": {
                "type": "invalid_url_format",
                "message": "URL must start with http:// or https://",
                "url": url
            },
            "results": []
        }
    
    return batch_scrape_urls([url], output_format, timeout) 