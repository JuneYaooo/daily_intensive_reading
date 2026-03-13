import requests
import json
import os
import time
import traceback
import threading
import random
from datetime import datetime
from dotenv import load_dotenv
from ..utils.logger import BeijingLogger
import redis
import hashlib
from jigsawstack import JigsawStack

# Initialize logger
logger = BeijingLogger().get_logger()

# Load environment variables
load_dotenv()

# JigsawStack API configuration
JIGSAWSTACK_API_KEYS = os.getenv("JigsawStack_APIKEYs", "")
JIGSAWSTACK_KEYS_LIST = [key.strip() for key in JIGSAWSTACK_API_KEYS.split(",") if key.strip()]

# Firecrawl API configuration (fallback)
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

def get_random_jigsawstack_key() -> str:
    """Get a random JigsawStack API key from the available keys"""
    if not JIGSAWSTACK_KEYS_LIST:
        logger.error("No JigsawStack API keys configured")
        return None
    
    selected_key = random.choice(JIGSAWSTACK_KEYS_LIST)
    logger.info(f"Selected JigsawStack API key: {selected_key[:10]}...")
    return selected_key

def scrape_with_jigsawstack_single_key(url: str, api_key: str) -> dict:
    """
    Scrape a single URL using a specific JigsawStack API key
    
    Args:
        url (str): URL to scrape
        api_key (str): Specific API key to use
        
    Returns:
        dict: Scraped content or error information
    """
    logger.info(f"使用JigsawStack API密钥 {api_key[:10]}... 爬取URL: {url}")
    
    try:
        # Initialize JigsawStack client
        jigsaw = JigsawStack(api_key=api_key)
        
        # Configure scraping parameters
        scrape_params = {
            "url": url,
            "element_prompts": [
                "main content",
                "article text",
                "page content",
                "body text"
            ],
            "features": ["meta", "link"],
            "advance_config": {
                "goto_options": {
                    "timeout": 60000,
                    "wait_until": "networkidle2"  # 等待网络基本空闲，适合动态加载的页面
                },
                "wait_for": {
                    "mode": "timeout",
                    "value": 3000
                }
            }
        }
        
        # Make the API call
        start_time = time.time()
        response = jigsaw.web.ai_scrape(scrape_params)
        response_time = time.time() - start_time
        
        logger.info(f"JigsawStack API响应时间: {response_time:.2f} 秒 (密钥: {api_key[:10]}...)")
        
        # Check if the response is successful
        if not response.get("success"):
            error_msg = "JigsawStack API返回失败状态"
            logger.error(f"{error_msg}: {response} (密钥: {api_key[:10]}...)")
            return {
                "success": False,
                "error": error_msg,
                "error_details": {
                    "type": "api_response_error",
                    "message": error_msg,
                    "api_response": response,
                    "api_key": api_key[:10] + "..."
                }
            }
        
        # Extract content from response
        content_parts = []
        
        # Get content from context (element prompts results)
        context = response.get("context", {})
        for prompt, results in context.items():
            if results:
                content_parts.extend(results)
        
        # Get content from data array
        data_items = response.get("data", [])
        for item in data_items:
            results = item.get("results", [])
            for result in results:
                text_content = result.get("text", "")
                if text_content:
                    content_parts.append(text_content)
        
        # Combine all content
        combined_content = "\n\n".join(content_parts) if content_parts else ""
        
        # Get metadata if available
        meta = response.get("meta", {})
        title = meta.get("title", "")
        description = meta.get("description", "")
        
        # Format final content with metadata
        final_content = ""
        if title:
            final_content += f"# {title}\n\n"
        if description:
            final_content += f"**Description:** {description}\n\n"
        
        # final_content += combined_content
        final_content = json.dumps(response)
        
        if not final_content.strip():
            error_msg = "JigsawStack未能提取到任何内容"
            logger.warning(f"{error_msg}: {url} (密钥: {api_key[:10]}...)")
            return {
                "success": False,
                "error": error_msg,
                "error_details": {
                    "type": "no_content_extracted",
                    "message": error_msg,
                    "url": url,
                    "api_response": response,
                    "api_key": api_key[:10] + "..."
                }
            }
        
        # Cache the content
        cache_content(url, final_content)
        
        logger.info(f"JigsawStack成功爬取内容，长度: {len(final_content)} 字符 (密钥: {api_key[:10]}...)")
        
        return {
            "success": True,
            "url": url,
            "content": final_content,
            "metadata": meta,
            "provider": "jigsawstack",
            "api_key": api_key[:10] + "..."
        }
        
    except Exception as e:
        error_msg = f"JigsawStack爬取异常: {str(e)}"
        logger.error(f"{error_msg} (密钥: {api_key[:10]}...)", exc_info=True)
        return {
            "success": False,
            "error": error_msg,
            "error_details": {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc(),
                "url": url,
                "api_key": api_key[:10] + "..."
            }
        }

def scrape_with_jigsawstack(url: str) -> dict:
    """
    Scrape a single URL using JigsawStack API with automatic key rotation
    
    Args:
        url (str): URL to scrape
        
    Returns:
        dict: Scraped content or error information
    """
    logger.info(f"使用JigsawStack爬取URL (支持密钥轮换): {url}")
    
    if not JIGSAWSTACK_KEYS_LIST:
        error_msg = "No JigsawStack API keys available"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "error_details": {
                "type": "configuration_error",
                "message": "JigsawStack API keys not configured"
            }
        }
    
    # 创建API密钥列表的副本，用于轮换
    available_keys = JIGSAWSTACK_KEYS_LIST.copy()
    random.shuffle(available_keys)  # 随机打乱顺序
    
    errors = []
    
    for i, api_key in enumerate(available_keys):
        logger.info(f"尝试第 {i+1}/{len(available_keys)} 个API密钥: {api_key[:10]}...")
        
        result = scrape_with_jigsawstack_single_key(url, api_key)
        
        if result.get("success"):
            logger.info(f"API密钥 {api_key[:10]}... 成功爬取内容")
            return result
        else:
            error_msg = result.get("error", "Unknown error")
            logger.warning(f"API密钥 {api_key[:10]}... 失败: {error_msg}")
            
            # 检查是否为"Page is too large"错误，如果是则直接返回，不再尝试其他密钥
            if "Page is too large" in error_msg:
                logger.error(f"页面过大错误，直接返回: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "error_details": {
                        "type": "page_too_large",
                        "message": error_msg,
                        "url": url,
                        "api_key": api_key[:10] + "...",
                        "original_error_details": result.get("error_details", {})
                    }
                }
            
            errors.append({
                "api_key": api_key[:10] + "...",
                "error": error_msg,
                "error_details": result.get("error_details", {})
            })
    
    # 所有API密钥都失败了
    final_error_msg = f"所有 {len(available_keys)} 个JigsawStack API密钥都失败了"
    logger.error(f"{final_error_msg}: {url}")
    
    return {
        "success": False,
        "error": final_error_msg,
        "error_details": {
            "type": "all_api_keys_failed",
            "message": final_error_msg,
            "url": url,
            "total_keys_tried": len(available_keys),
            "key_errors": errors
        }
    }

def scrape_with_firecrawl(url: str) -> dict:
    """
    Scrape a single URL using Firecrawl API (fallback)
    
    Args:
        url (str): URL to scrape
        
    Returns:
        dict: Scraped content or error information
    """
    logger.info(f"使用Firecrawl爬取URL: {url}")
    
    try:
        # Import firecrawl functions
        from .firecrawl_service import scrape_single_url as firecrawl_scrape
        
        result = firecrawl_scrape(url)
        
        if result.get('success') and result.get('results'):
            first_result = result['results'][0]
            if first_result.get('success') and first_result.get('content'):
                logger.info(f"Firecrawl成功爬取内容，长度: {len(first_result['content'])} 字符")
                return {
                    "success": True,
                    "url": url,
                    "content": first_result['content'],
                    "provider": "firecrawl"
                }
        
        return {
            "success": False,
            "error": "Firecrawl failed to scrape content",
            "error_details": result
        }
        
    except Exception as e:
        error_msg = f"Firecrawl爬取异常: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "error": error_msg,
            "error_details": {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc(),
                "url": url
            }
        }

def scrape_single_url(url: str, use_cache: bool = True) -> dict:
    """
    Scrape a single URL with priority: Cache -> JigsawStack -> Firecrawl
    
    Args:
        url (str): URL to scrape
        use_cache (bool): Whether to check cache first
        
    Returns:
        dict: Scraped content or error information
    """
    logger.info(f"开始爬取URL: {url}")
    
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
    
    # Check cache first if enabled
    if use_cache:
        cached_content = get_cached_content(url)
        if cached_content:
            logger.info(f"从缓存获取内容: {url}")
            return {
                "success": True,
                "results": [{
                    "success": True,
                    "url": url,
                    "content": cached_content,
                    "provider": "cache"
                }]
            }
    
    errors = []
    
    # Try JigsawStack first
    if JIGSAWSTACK_KEYS_LIST:
        logger.info("优先尝试使用JigsawStack")
        jigsawstack_result = scrape_with_jigsawstack(url)
        
        if jigsawstack_result.get("success"):
            return {
                "success": True,
                "results": [jigsawstack_result]
            }
        else:
            error_msg = jigsawstack_result.get("error", "")
            logger.warning(f"JigsawStack爬取失败: {error_msg}")
            
            # 检查是否为"Page is too large"错误，如果是则直接返回，不尝试其他提供商
            if "Page is too large" in error_msg:
                logger.error(f"页面过大错误，直接返回不尝试其他提供商: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "error_details": jigsawstack_result.get("error_details", {}),
                    "results": []
                }
            
            errors.append({
                "provider": "jigsawstack",
                "error": error_msg,
                "details": jigsawstack_result.get("error_details")
            })
    else:
        logger.warning("JigsawStack API keys未配置，跳过")
        errors.append({
            "provider": "jigsawstack",
            "error": "API keys not configured",
            "details": {"message": "JigsawStack_APIKEYs environment variable not set"}
        })
    
    # Fallback to Firecrawl
    logger.info("回退到Firecrawl")
    firecrawl_result = scrape_with_firecrawl(url)
    
    if firecrawl_result.get("success"):
        return {
            "success": True,
            "results": [firecrawl_result]
        }
    else:
        logger.error(f"Firecrawl爬取也失败: {firecrawl_result.get('error')}")
        errors.append({
            "provider": "firecrawl", 
            "error": firecrawl_result.get("error"),
            "details": firecrawl_result.get("error_details")
        })
    
    # Both providers failed
    error_msg = f"所有爬虫提供商都失败了: {url}"
    logger.error(error_msg)
    
    return {
        "success": False,
        "error": error_msg,
        "error_details": {
            "type": "all_providers_failed",
            "message": "Both JigsawStack and Firecrawl failed",
            "url": url,
            "provider_errors": errors
        },
        "results": []
    }

def batch_scrape_urls(urls: list, use_cache: bool = True) -> dict:
    """
    Batch scrape multiple URLs with priority: Cache -> JigsawStack -> Firecrawl
    
    Args:
        urls (list): List of URLs to scrape
        use_cache (bool): Whether to check cache first
        
    Returns:
        dict: Scraped content or error information
    """
    logger.info(f"开始批量爬取 {len(urls)} 个URLs")
    
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
    
    results = []
    successful_count = 0
    
    for url in urls:
        logger.info(f"处理URL: {url}")
        result = scrape_single_url(url, use_cache)
        
        if result.get("success") and result.get("results"):
            result_item = result["results"][0]
            results.append({
                "url": url,
                "content": result_item.get("content"),
                "success": True,
                "provider": result_item.get("provider", "unknown")
            })
            successful_count += 1
        else:
            results.append({
                "url": url,
                "content": None,
                "success": False,
                "error": result.get("error", "Unknown error"),
                "error_details": result.get("error_details", {})
            })
    
    logger.info(f"批量爬取完成，成功: {successful_count}/{len(urls)}")
    
    return {
        "success": successful_count > 0,
        "results": results,
        "stats": {
            "total": len(urls),
            "success": successful_count,
            "failure": len(urls) - successful_count
        }
    } 