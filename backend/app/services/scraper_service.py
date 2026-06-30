import requests
import json
import os
import time
import traceback
import random
import re
import uuid
import concurrent.futures
from datetime import datetime
from dotenv import load_dotenv
from ..utils.logger import BeijingLogger
import hashlib
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from . import content_cache
from .content_cache import (
    CONTENT_CACHE_TTL,
    cache_content,
    delete_cached_content,
    get_cached_content,
    get_url_cache_key,
)

# Initialize logger
logger = BeijingLogger().get_logger()

# Load environment variables
load_dotenv()

# JigsawStack API configuration
JIGSAWSTACK_API_KEYS = os.getenv("JigsawStack_APIKEYs", "")
JIGSAWSTACK_KEYS_LIST = [key.strip() for key in JIGSAWSTACK_API_KEYS.split(",") if key.strip()]

# Firecrawl API configuration (fallback)
FIRECRAWL_API_TOKEN = os.getenv("FIRECRAWL_API_TOKEN", "").strip()
FIRECRAWL_BASE_URL = "https://api.firecrawl.dev/v1"

# JigsawStack quota failure cache TTL (1 hour) — avoids burning keys when project quota is exhausted
QUOTA_FAILURE_CACHE_TTL = 60 * 60
# Per-key exhaustion TTL (7 days) — individual keys that returned quota errors
KEY_EXHAUSTED_TTL = 7 * 24 * 60 * 60

def is_jigsawstack_quota_exhausted() -> bool:
    """Check if JigsawStack quota is known to be exhausted (cached flag)."""
    if not content_cache.redis_client:
        return False
    try:
        return content_cache.redis_client.get("jigsawstack:quota_exhausted") is not None
    except Exception:
        return False

def mark_jigsawstack_quota_exhausted() -> None:
    """Mark JigsawStack quota as exhausted for QUOTA_FAILURE_CACHE_TTL seconds."""
    if not content_cache.redis_client:
        return
    try:
        content_cache.redis_client.setex("jigsawstack:quota_exhausted", QUOTA_FAILURE_CACHE_TTL, "1")
        logger.info(f"JigsawStack quota marked exhausted, will skip for {QUOTA_FAILURE_CACHE_TTL}s")
    except Exception:
        pass

def _key_hash(api_key: str) -> str:
    return hashlib.md5(api_key.encode()).hexdigest()[:12]

def is_key_exhausted(api_key: str) -> bool:
    """Check if a specific JigsawStack key is marked as exhausted (7-day TTL)."""
    if not content_cache.redis_client or not api_key:
        return False
    try:
        return content_cache.redis_client.get(f"jigsawstack:key_exhausted:{_key_hash(api_key)}") is not None
    except Exception:
        return False

def mark_key_exhausted(api_key: str, reason: str = "") -> None:
    """Mark a specific JigsawStack key as exhausted for KEY_EXHAUSTED_TTL (7 days)."""
    if not content_cache.redis_client or not api_key:
        return
    try:
        content_cache.redis_client.setex(
            f"jigsawstack:key_exhausted:{_key_hash(api_key)}",
            KEY_EXHAUSTED_TTL,
            json.dumps({"exhausted_at": datetime.utcnow().isoformat(), "reason": reason})
        )
        logger.warning(f"Key {api_key[:10]}... marked exhausted for 7 days: {reason}")
    except Exception:
        pass

def clear_key_exhausted(api_key: str) -> None:
    """Manually clear exhaustion flag for a key."""
    if not content_cache.redis_client or not api_key:
        return
    try:
        content_cache.redis_client.delete(f"jigsawstack:key_exhausted:{_key_hash(api_key)}")
        logger.info(f"Key {api_key[:10]}... exhaustion flag cleared")
    except Exception:
        pass

def get_exhausted_keys_count() -> int:
    """Count how many keys are currently marked exhausted."""
    if not content_cache.redis_client:
        return 0
    try:
        return len(content_cache.redis_client.keys("jigsawstack:key_exhausted:*") or [])
    except Exception:
        return 0

# ----- JigsawStack Quota / Usage Tracking -----

# Redis key prefixes
_QUOTA_KEY_PREFIX = "jigsawstack:quota"
_ROUND_KEY_PREFIX = "jigsawstack:round"
_KEY_USAGE_PREFIX = "jigsawstack:key_usage"
_QUOTA_TTL = 7 * 24 * 60 * 60  # Keep quota data for 7 days
_ROUND_TTL = 7 * 24 * 60 * 60  # Keep round data for 7 days

# Active round ID — set per `batch_scrape_urls` call
_active_round_id: str | None = None

def start_usage_round() -> str:
    """Start a new usage tracking round. Returns round_id."""
    global _active_round_id
    _active_round_id = f"round:{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}:{uuid.uuid4().hex[:6]}"
    if content_cache.redis_client:
        try:
            content_cache.redis_client.setex(
                f"{_ROUND_KEY_PREFIX}:{_active_round_id}",
                _ROUND_TTL,
                json.dumps({
                    "started_at": datetime.utcnow().isoformat(),
                    "status": "active",
                    "keys_used": [],
                    "total_requests": 0,
                    "success_requests": 0,
                    "failed_requests": 0,
                })
            )
        except Exception:
            pass
    logger.info(f"[额度追踪] 开启新轮次: {_active_round_id}")
    return _active_round_id

def _get_active_round_id() -> str | None:
    global _active_round_id
    return _active_round_id

def track_jigsawstack_usage(api_key: str, resp_headers: dict, success: bool, url: str) -> dict:
    """
    Track quota usage from a JigsawStack API response.
    Extracts x-jigsaw-rate-limit-* headers and logs/persists quota info.

    Returns a dict with parsed quota info for inclusion in API responses.
    """
    quota_info = {
        "key_prefix": api_key[:10] + "...",
        "success": success,
        "url": url[:100],
    }

    # Extract rate-limit headers
    limit = resp_headers.get("x-jigsaw-rate-limit-limit")
    remaining = resp_headers.get("x-jigsaw-rate-limit-remaining")
    reset = resp_headers.get("x-jigsaw-rate-limit-reset")
    log_id = resp_headers.get("x-jigsaw-log-id", "")

    if limit is not None:
        quota_info["rate_limit_limit"] = int(limit)
    if remaining is not None:
        quota_info["rate_limit_remaining"] = int(remaining)
    if reset is not None:
        quota_info["rate_limit_reset"] = int(reset)
        quota_info["rate_limit_reset_iso"] = datetime.fromtimestamp(int(reset) / 1000).isoformat()
    if log_id:
        quota_info["log_id"] = log_id

    # Log structured quota line
    limit_str = quota_info.get("rate_limit_limit", "?")
    remaining_str = quota_info.get("rate_limit_remaining", "?")
    reset_str = quota_info.get("rate_limit_reset_iso", "?")
    status = "成功" if success else "失败"
    logger.info(
        f"[额度追踪] 密钥={quota_info['key_prefix']} | 状态={status} | "
        f"速率限制={remaining_str}/{limit_str} | 重置={reset_str} | "
        f"URL={url[:80]} | log_id={log_id}"
    )

    if not content_cache.redis_client:
        return quota_info

    # Persist per-key usage counters
    key_hash = hashlib.md5(api_key.encode()).hexdigest()[:12]
    try:
        usage_key = f"{_KEY_USAGE_PREFIX}:{key_hash}"
        raw = content_cache.redis_client.get(usage_key)
        key_data = json.loads(raw) if raw else {}
        key_data["last_prefix"] = api_key[:10] + "..."
        key_data["total_requests"] = key_data.get("total_requests", 0) + 1
        if success:
            key_data["success_requests"] = key_data.get("success_requests", 0) + 1
        else:
            key_data["failed_requests"] = key_data.get("failed_requests", 0) + 1
        key_data["last_rate_limit_remaining"] = quota_info.get("rate_limit_remaining")
        key_data["last_rate_limit_limit"] = quota_info.get("rate_limit_limit")
        key_data["last_used_at"] = datetime.utcnow().isoformat()
        content_cache.redis_client.setex(usage_key, _QUOTA_TTL, json.dumps(key_data))
    except Exception as e:
        logger.warning(f"Failed to persist key usage: {e}")

    # Update round summary
    round_id = _get_active_round_id()
    if round_id:
        try:
            raw = content_cache.redis_client.get(f"{_ROUND_KEY_PREFIX}:{round_id}")
            if raw:
                round_data = json.loads(raw)
                round_data["total_requests"] = round_data.get("total_requests", 0) + 1
                if success:
                    round_data["success_requests"] = round_data.get("success_requests", 0) + 1
                else:
                    round_data["failed_requests"] = round_data.get("failed_requests", 0) + 1
                if quota_info["key_prefix"] not in round_data.get("keys_used", []):
                    round_data.setdefault("keys_used", []).append(quota_info["key_prefix"])
                content_cache.redis_client.setex(f"{_ROUND_KEY_PREFIX}:{round_id}", _ROUND_TTL, json.dumps(round_data))
        except Exception:
            pass

    # Also persist latest quota snapshot for quick lookup
    try:
        content_cache.redis_client.setex(
            f"{_QUOTA_KEY_PREFIX}:latest",
            _QUOTA_TTL,
            json.dumps({
                "key_prefix": quota_info["key_prefix"],
                "rate_limit_remaining": quota_info.get("rate_limit_remaining"),
                "rate_limit_limit": quota_info.get("rate_limit_limit"),
                "rate_limit_reset": quota_info.get("rate_limit_reset"),
                "rate_limit_reset_iso": quota_info.get("rate_limit_reset_iso"),
                "log_id": log_id,
                "updated_at": datetime.utcnow().isoformat(),
            })
        )
    except Exception:
        pass

    return quota_info

def get_jigsawstack_quota_status() -> dict:
    """Get current JigsawStack quota status from Redis."""
    active_keys = [k for k in JIGSAWSTACK_KEYS_LIST if not is_key_exhausted(k)]
    status = {
        "quota_exhausted": is_jigsawstack_quota_exhausted(),
        "available_keys_count": len(JIGSAWSTACK_KEYS_LIST),
        "active_keys_count": len(active_keys),
        "exhausted_keys_count": get_exhausted_keys_count(),
        "latest_quota": None,
        "key_usages": [],
        "active_rounds": [],
    }

    if not content_cache.redis_client:
        return status

    try:
        raw = content_cache.redis_client.get(f"{_QUOTA_KEY_PREFIX}:latest")
        if raw:
            status["latest_quota"] = json.loads(raw)
    except Exception:
        pass

    try:
        for key in content_cache.redis_client.keys(f"{_KEY_USAGE_PREFIX}:*") or []:
            raw = content_cache.redis_client.get(key)
            if raw:
                status["key_usages"].append(json.loads(raw))
    except Exception:
        pass

    try:
        for key in content_cache.redis_client.keys(f"{_ROUND_KEY_PREFIX}:round:*") or []:
            raw = content_cache.redis_client.get(key)
            if raw:
                rd = json.loads(raw)
                rd["round_id"] = key.split(":")[-1]
                status["active_rounds"].append(rd)
        status["active_rounds"] = sorted(
            status["active_rounds"], key=lambda r: r.get("started_at", ""), reverse=True
        )[:10]
    except Exception:
        pass

    return status

def get_round_summary(round_id: str = None) -> dict | None:
    """Get summary for a specific round or the active round."""
    rid = round_id or _get_active_round_id()
    if not rid or not content_cache.redis_client:
        return None
    try:
        raw = content_cache.redis_client.get(f"{_ROUND_KEY_PREFIX}:{rid}")
        return json.loads(raw) if raw else None
    except Exception:
        return None

def get_random_jigsawstack_key() -> str:
    """Get a random JigsawStack API key from the available keys"""
    if not JIGSAWSTACK_KEYS_LIST:
        logger.error("No JigsawStack API keys configured")
        return None

    selected_key = random.choice(JIGSAWSTACK_KEYS_LIST)
    logger.info(f"Selected JigsawStack API key: {selected_key[:10]}...")
    return selected_key

JIGSAWSTACK_API_URL = "https://api.jigsawstack.com/v1"
# Per-request timeouts for JigsawStack HTTP call (seconds)
JIGSAWSTACK_CONNECT_TIMEOUT = 30   # TCP/SSL handshake
JIGSAWSTACK_READ_TIMEOUT = 240     # Wait for response after connected
JIGSAWSTACK_TOTAL_TIMEOUT = 240    # Future.result() overall timeout

# ----- Direct HTTP Scraper (free, no API key needed) -----

# Common headers to mimic a browser
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
}

def scrape_with_requests(url: str) -> dict:
    """
    Scrape a URL directly using requests + BeautifulSoup.
    Free, no API key needed. Works well for most static/SSR pages.
    """
    logger.info(f"使用直接HTTP爬取URL: {url}")
    try:
        resp = requests.get(url, headers=_BROWSER_HEADERS, timeout=(10, 30), allow_redirects=True)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "")
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            return {
                "success": False,
                "error": f"Non-HTML content type: {content_type}",
                "error_details": {"type": "non_html", "content_type": content_type, "url": url},
            }

        soup = BeautifulSoup(resp.text, "lxml")

        # Remove noise elements
        for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"]):
            tag.decompose()

        # Extract title
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        # Extract links
        links = []
        seen_hrefs = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue
            href = urljoin(url, href)
            if href not in seen_hrefs:
                seen_hrefs.add(href)
                text = a_tag.get_text(strip=True)
                links.append(f"- [{text}]({href})" if text else f"- {href}")

        # Extract main content — prefer <article> or <main>, fall back to <body>
        main_el = soup.find("article") or soup.find("main") or soup.find("body")
        if main_el is None:
            main_el = soup

        # Get text, collapse excessive whitespace
        text_content = main_el.get_text(separator="\n", strip=True)
        # Collapse 3+ consecutive newlines into 2
        text_content = re.sub(r"\n{3,}", "\n\n", text_content)

        # Build final markdown content
        parts = []
        if title:
            parts.append(f"# {title}")
        if links:
            parts.append("## Links\n" + "\n".join(links[:200]))  # cap links to avoid huge output
        if text_content:
            parts.append("## Content\n" + text_content)

        final_content = "\n\n".join(parts)

        if len(final_content.strip()) < 100:
            logger.warning(f"直接HTTP爬取内容过少 ({len(final_content)} 字符): {url}")
            return {
                "success": False,
                "error": "Content too short, page may require JavaScript rendering",
                "error_details": {
                    "type": "content_too_short",
                    "content_length": len(final_content),
                    "url": url,
                },
            }

        # Cache the content
        cache_content(url, final_content)

        logger.info(f"直接HTTP爬取成功，长度: {len(final_content)} 字符")
        return {
            "success": True,
            "url": url,
            "content": final_content,
            "metadata": {"title": title},
            "provider": "requests",
        }

    except requests.exceptions.Timeout:
        error_msg = "直接HTTP爬取超时"
        logger.warning(f"{error_msg}: {url}")
        return {"success": False, "error": error_msg, "error_details": {"type": "timeout", "url": url}}
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP {e.response.status_code}"
        logger.warning(f"直接HTTP爬取失败 {error_msg}: {url}")
        return {"success": False, "error": error_msg, "error_details": {"type": "http_error", "status_code": e.response.status_code, "url": url}}
    except Exception as e:
        error_msg = f"直接HTTP爬取异常: {str(e)}"
        logger.warning(f"{error_msg}: {url}")
        return {"success": False, "error": error_msg, "error_details": {"type": type(e).__name__, "message": str(e), "url": url}}

# ----- JigsawStack Scraper -----

def scrape_with_jigsawstack_single_key(url: str, api_key: str, use_element_prompts: bool = True) -> dict:
    """
    Scrape a single URL using a specific JigsawStack API key.
    Note: JigsawStack /v1/ai/scrape requires either 'selectors' or 'element_prompts'.
    We always send element_prompts since the API mandates one of them.
    """
    logger.info(f"使用JigsawStack (AI) 密钥 {api_key[:10]}... 爬取URL: {url}")

    scrape_params = {
        "url": url,
        "features": ["meta", "link"],
        "element_prompts": [
            "main content",
            "article text",
            "page content",
            "body text"
        ],
        "advance_config": {
            "goto_options": {
                "timeout": 30000,
                "wait_until": "domcontentloaded"
            },
            "wait_for": {
                "mode": "timeout",
                "value": 1000
            }
        }
    }

    def _do_request():
        return requests.post(
            f"{JIGSAWSTACK_API_URL}/ai/scrape",
            json=scrape_params,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "x-api-key": api_key,
            },
            timeout=(JIGSAWSTACK_CONNECT_TIMEOUT, JIGSAWSTACK_READ_TIMEOUT),
        )

    try:
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_do_request)
            try:
                resp = future.result(timeout=JIGSAWSTACK_TOTAL_TIMEOUT)
            except concurrent.futures.TimeoutError:
                error_msg = f"JigsawStack 整体超时 (>{JIGSAWSTACK_TOTAL_TIMEOUT}s)"
                logger.error(f"{error_msg} (密钥: {api_key[:10]}...)")
                qi = track_jigsawstack_usage(api_key, {}, False, url)
                return {
                    "success": False,
                    "error": error_msg,
                    "quota_info": qi,
                    "error_details": {
                        "type": "client_timeout",
                        "message": error_msg,
                        "url": url,
                        "api_key": api_key[:10] + "..."
                    }
                }
        response_time = time.time() - start_time
        resp_headers = {k.lower(): v for k, v in resp.headers.items()}
        logger.info(f"JigsawStack HTTP响应: {resp.status_code}, 耗时 {response_time:.2f}s (密钥: {api_key[:10]}...)")

        if resp.status_code != 200:
            error_msg = f"JigsawStack API返回HTTP {resp.status_code}"
            try:
                err_body = resp.json()
            except Exception:
                err_body = resp.text
            logger.error(f"{error_msg}: {err_body} (密钥: {api_key[:10]}...)")

            # Track failed usage (response headers available for 4xx/5xx)
            qi = track_jigsawstack_usage(api_key, resp_headers, False, url)

            # Detect project-level quota exhaustion
            is_quota_error = False
            if resp.status_code in (401, 403, 429):
                err_str = str(err_body).lower()
                if "exceed" in err_str or "limit" in err_str or "quota" in err_str or "upgrade" in err_str:
                    is_quota_error = True

            return {
                "success": False,
                "error": error_msg,
                "is_quota_error": is_quota_error,
                "quota_info": qi,
                "error_details": {
                    "type": "http_error",
                    "status_code": resp.status_code,
                    "body": err_body,
                    "url": url,
                    "api_key": api_key[:10] + "..."
                }
            }

        response = resp.json()

    except requests.exceptions.Timeout:
        error_msg = f"JigsawStack HTTP超时 (连接>{JIGSAWSTACK_CONNECT_TIMEOUT}s 或 读取>{JIGSAWSTACK_READ_TIMEOUT}s)"
        logger.error(f"{error_msg} (密钥: {api_key[:10]}...)")
        qi = track_jigsawstack_usage(api_key, {}, False, url)
        return {
            "success": False,
            "error": error_msg,
            "quota_info": qi,
            "error_details": {
                "type": "client_timeout",
                "message": error_msg,
                "url": url,
                "api_key": api_key[:10] + "..."
            }
        }
    except Exception as e:
        error_msg = f"JigsawStack爬取异常: {str(e)}"
        logger.error(f"{error_msg} (密钥: {api_key[:10]}...)", exc_info=True)
        qi = track_jigsawstack_usage(api_key, {}, False, url)
        return {
            "success": False,
            "error": error_msg,
            "quota_info": qi,
            "error_details": {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc(),
                "url": url,
                "api_key": api_key[:10] + "..."
            }
        }

    # Check if the response is successful
    if not response.get("success"):
        error_msg = "JigsawStack API返回失败状态"
        logger.error(f"{error_msg}: {response} (密钥: {api_key[:10]}...)")
        qi = track_jigsawstack_usage(api_key, resp_headers, False, url)
        return {
            "success": False,
            "error": error_msg,
            "quota_info": qi,
            "error_details": {
                "type": "api_response_error",
                "message": error_msg,
                "api_response": response,
                "api_key": api_key[:10] + "..."
            }
        }

    # Build readable content: links first, then text
    links = response.get("link", [])
    link_lines = []
    seen_hrefs = set()
    for l in links:
        href = l.get("href", "")
        text = (l.get("text") or "").strip()
        if href and href not in seen_hrefs:
            seen_hrefs.add(href)
            link_lines.append(f"- [{text}]({href})" if text else f"- {href}")

    context = response.get("context", {})
    text_parts = []
    for prompt, results in context.items():
        if results:
            text_parts.extend([r for r in results if isinstance(r, str)])

    # Also try to extract from data field (non-AI mode returns data)
    data_items = response.get("data", [])
    for item in data_items:
        if isinstance(item, dict):
            for result in item.get("results", []):
                text = result.get("text", "").strip()
                if text:
                    text_parts.append(text)

    meta = response.get("meta", {})
    title = meta.get("title", "")
    parts = []
    if title:
        parts.append(f"# {title}")
    if link_lines:
        parts.append("## Links\n" + "\n".join(link_lines))
    if text_parts:
        parts.append("## Content\n" + "\n\n".join(text_parts))
    final_content = "\n\n".join(parts)

    if not final_content.strip():
        error_msg = "JigsawStack未能提取到任何内容"
        logger.warning(f"{error_msg}: {url} (密钥: {api_key[:10]}...)")
        qi = track_jigsawstack_usage(api_key, resp_headers, False, url)
        return {
            "success": False,
            "error": error_msg,
            "quota_info": qi,
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

    meta = response.get("meta", {})
    logger.info(f"JigsawStack 成功爬取内容，长度: {len(final_content)} 字符 (密钥: {api_key[:10]}...)")

    qi = track_jigsawstack_usage(api_key, resp_headers, True, url)

    return {
        "success": True,
        "url": url,
        "content": final_content,
        "metadata": meta,
        "provider": "jigsawstack",
        "api_key": api_key[:10] + "...",
        "quota_info": qi
    }

def scrape_with_jigsawstack(url: str, use_element_prompts: bool = True, override_keys: list = None) -> dict:
    """
    Scrape a single URL using JigsawStack API with automatic key rotation.
    Short-circuits immediately on project-level quota errors (401 exceed limit).
    """
    logger.info(f"使用JigsawStack (AI) 爬取URL (支持密钥轮换): {url}")

    # Determine which keys to use
    keys_list = override_keys if override_keys else JIGSAWSTACK_KEYS_LIST

    # Check if quota is known to be exhausted (only for default keys)
    if not override_keys and is_jigsawstack_quota_exhausted():
        logger.warning("JigsawStack quota已知耗尽，跳过")
        return {
            "success": False,
            "error": "JigsawStack quota exhausted (cached)",
            "error_details": {
                "type": "quota_exhausted_cached",
                "message": "JigsawStack quota was recently exhausted, skipping to save time"
            }
        }

    if not keys_list:
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

    # Filter out exhausted keys (7-day ban)
    active_keys = [k for k in keys_list if not is_key_exhausted(k)]
    skipped_count = len(keys_list) - len(active_keys)
    if skipped_count > 0:
        logger.info(f"跳过 {skipped_count} 个已耗尽的key (7天内被标记)，剩余 {len(active_keys)} 个可用")
    if not active_keys:
        logger.warning("所有key都被标记为耗尽，回退使用全部key")
        active_keys = keys_list

    # Try up to 3 random keys (not all!) — they share the same project quota
    max_keys_to_try = min(3, len(active_keys))
    available_keys = random.sample(active_keys, max_keys_to_try)

    errors = []
    jigsawstack_start = time.time()
    JIGSAWSTACK_TOTAL_TIMEOUT = 420

    for i, api_key in enumerate(available_keys):
        elapsed = time.time() - jigsawstack_start
        if elapsed >= JIGSAWSTACK_TOTAL_TIMEOUT:
            logger.warning(f"JigsawStack总超时 ({JIGSAWSTACK_TOTAL_TIMEOUT}s)，已尝试 {i}/{len(available_keys)} 个密钥，停止轮换")
            break

        logger.info(f"尝试第 {i+1}/{len(available_keys)} 个API密钥: {api_key[:10]}... (已用时 {elapsed:.0f}s)")

        result = scrape_with_jigsawstack_single_key(url, api_key, use_element_prompts)

        if result.get("success"):
            logger.info(f"API密钥 {api_key[:10]}... 成功爬取内容")
            # Clear exhaustion flag on success (key might have recovered)
            if is_key_exhausted(api_key):
                clear_key_exhausted(api_key)
            return result

        error_msg = result.get("error", "Unknown error")
        logger.warning(f"API密钥 {api_key[:10]}... 失败: {error_msg}")

        # Short-circuit: project-level quota exhaustion — no point trying other keys
        if result.get("is_quota_error"):
            logger.error(f"项目级额度耗尽，停止轮换密钥: {error_msg}")
            mark_jigsawstack_quota_exhausted()
            mark_key_exhausted(api_key, f"quota error: {error_msg}")
            return {
                "success": False,
                "error": f"JigsawStack项目额度耗尽: {error_msg}",
                "error_details": {
                    "type": "quota_exhausted",
                    "message": error_msg,
                    "url": url,
                    "api_key": api_key[:10] + "..."
                }
            }

        # Short-circuit: page too large — won't help with another key
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

    final_error_msg = f"{len(available_keys)} 个JigsawStack API密钥都失败了"
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

def is_arxiv_html_error_page(content: str, url: str = "") -> bool:
    """Check if scraped content is an arXiv HTML error page, not actual paper content."""
    if not content:
        return True
    # arXiv error pages for missing HTML versions contain these specific strings
    indicators = [
        "HTML is not available for the source",
        "HTML is not available for",
        "currently not available in HTML",
        "arXiv平台目前无法为指定编号",
    ]
    content_lower = content.lower()
    for indicator in indicators:
        if indicator.lower() in content_lower:
            return True
    # arXiv HTML placeholders can be very short; do not apply this to other sites.
    if arxiv_html_to_abs_url(url) and len(content) < 3000:
        return True
    return False


def arxiv_html_to_abs_url(url: str) -> str | None:
    """Convert arXiv HTML URL to abs (abstract) URL. Returns None if not an arXiv HTML URL."""
    import re
    match = re.match(r'(https?://arxiv\.org)/html/(\d+\.\d+)(v\d+)?', url)
    if match:
        base = match.group(1)
        paper_id = match.group(2)
        return f"{base}/abs/{paper_id}"
    return None


def scrape_single_url(url: str, use_cache: bool = True, override_keys: list = None) -> dict:
    """
    Scrape a single URL with priority:
      1. Cache
      2. Direct HTTP (requests + BeautifulSoup) — free
      3. JigsawStack — API scraper (element_prompts required by the API)
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

    # 1. Check cache first
    if use_cache:
        cached_content = get_cached_content(url)
        if cached_content:
            # Check if cached content is an arXiv error page — if so, invalidate and re-scrape
            if is_arxiv_html_error_page(cached_content, url):
                logger.warning(f"缓存的arXiv内容为错误页 ({len(cached_content)} 字符), 清除缓存并重新爬取: {url}")
                delete_cached_content(url)
                # Fall through to re-scrape (don't return)
            else:
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
    best_result = None  # Keep the best result we've got so far

    def _check_result_and_fallback(result, original_url):
        """If result is an arXiv HTML error page, try scraping the /abs/ version instead."""
        if not result.get("success"):
            return result

        content = result.get("content", "")
        if not is_arxiv_html_error_page(content, original_url):
            return result

        abs_url = arxiv_html_to_abs_url(original_url)
        if not abs_url:
            return result

        logger.warning(f"arXiv HTML页面内容不足或为错误页 ({len(content)} 字符), 回退到摘要页: {abs_url}")

        # Try abs URL with the same providers, bypass cache for this retry
        # Direct HTTP first
        abs_direct = scrape_with_requests(abs_url)
        if abs_direct.get("success"):
            logger.info(f"arXiv摘要页回退成功 (直接HTTP): {abs_url}")
            # Invalidate the HTML URL cache so future requests won't serve the error page
            delete_cached_content(original_url)
            return abs_direct

        # JigsawStack
        keys_list = override_keys if override_keys else JIGSAWSTACK_KEYS_LIST
        if keys_list:
            abs_jigsaw = scrape_with_jigsawstack(abs_url, use_element_prompts=True, override_keys=override_keys)
            if abs_jigsaw.get("success"):
                logger.info(f"arXiv摘要页回退成功 (JigsawStack): {abs_url}")
                delete_cached_content(original_url)
                return abs_jigsaw

        logger.warning(f"arXiv摘要页回退也失败: {abs_url}")
        return result  # Return the original error-page result as last resort

    # 2. Try direct HTTP scraping first (free, no API key needed)
    logger.info("优先尝试直接HTTP爬取")
    direct_result = scrape_with_requests(url)
    if direct_result.get("success"):
        direct_result = _check_result_and_fallback(direct_result, url)
        if direct_result.get("success") and not is_arxiv_html_error_page(direct_result.get("content", ""), url):
            return {
                "success": True,
                "results": [direct_result]
            }
        best_result = direct_result
    else:
        logger.warning(f"直接HTTP爬取失败: {direct_result.get('error', '')}")
        errors.append({
            "provider": "requests",
            "error": direct_result.get("error", ""),
            "details": direct_result.get("error_details")
        })

    # 3. Try JigsawStack
    keys_list = override_keys if override_keys else JIGSAWSTACK_KEYS_LIST
    if keys_list:
        logger.info("尝试JigsawStack爬取")
        jigsaw_result = scrape_with_jigsawstack(url, use_element_prompts=True, override_keys=override_keys)

        if jigsaw_result.get("success"):
            jigsaw_result = _check_result_and_fallback(jigsaw_result, url)
            if jigsaw_result.get("success") and not is_arxiv_html_error_page(jigsaw_result.get("content", ""), url):
                return {
                    "success": True,
                    "results": [jigsaw_result]
                }
            if not best_result or jigsaw_result.get("success"):
                best_result = jigsaw_result
        else:
            error_msg = jigsaw_result.get("error", "")
            logger.warning(f"JigsawStack失败: {error_msg}")

            if "Page is too large" in error_msg:
                logger.error(f"页面过大，直接返回: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "error_details": jigsaw_result.get("error_details", {}),
                    "results": []
                }

            errors.append({
                "provider": "jigsawstack",
                "error": error_msg,
                "details": jigsaw_result.get("error_details")
            })
    else:
        logger.warning("JigsawStack API keys未配置，跳过")
        errors.append({
            "provider": "jigsawstack",
            "error": "API keys not configured",
            "details": {"message": "JigsawStack_APIKEYs environment variable not set"}
        })

    # Return best available result (even if it's an error page)
    if best_result and best_result.get("success"):
        logger.warning(f"返回降级结果（可能为摘要页或部分内容）: {url}")
        return {
            "success": True,
            "results": [best_result]
        }

    if FIRECRAWL_API_TOKEN:
        logger.info("尝试Firecrawl fallback爬取")
        firecrawl_result = scrape_with_firecrawl(url)
        if firecrawl_result.get("success"):
            return {
                "success": True,
                "results": [firecrawl_result]
            }
        errors.append({
            "provider": "firecrawl",
            "error": firecrawl_result.get("error", ""),
            "details": firecrawl_result.get("error_details")
        })
    else:
        logger.warning("Firecrawl API token未配置，跳过fallback")
        errors.append({
            "provider": "firecrawl",
            "error": "API token not configured",
            "details": {"message": "FIRECRAWL_API_TOKEN environment variable not set"}
        })

    # All providers failed
    error_msg = f"所有爬虫提供商都失败了: {url}"
    logger.error(error_msg)

    return {
        "success": False,
        "error": error_msg,
        "error_details": {
            "type": "all_providers_failed",
            "message": "Direct HTTP, JigsawStack, and Firecrawl fallback failed or were not configured",
            "url": url,
            "provider_errors": errors
        },
        "results": []
    }

def batch_scrape_urls(urls: list, use_cache: bool = True, override_keys: list = None) -> dict:
    """
    Batch scrape multiple URLs with priority: Cache -> Direct HTTP -> JigsawStack -> Firecrawl

    Args:
        urls (list): List of URLs to scrape
        use_cache (bool): Whether to check cache first

    Returns:
        dict: Scraped content or error information
    """
    round_id = start_usage_round()
    logger.info(f"[轮次 {round_id}] 开始批量爬取 {len(urls)} 个URLs")

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
    quota_infos = []  # Collect all quota_info from this round
    stop_on_failure = len(urls) > 1  # 多个URL时，遇到失败就停，避免浪费额度

    for url in urls:
        logger.info(f"[轮次 {round_id}] 处理URL: {url}")
        result = scrape_single_url(url, use_cache, override_keys=override_keys)

        if result.get("success") and result.get("results"):
            result_item = result["results"][0]
            results.append({
                "url": url,
                "content": result_item.get("content"),
                "success": True,
                "provider": result_item.get("provider", "unknown")
            })
            successful_count += 1
            # Collect quota_info from the inner result if present
            if "quota_info" in result_item:
                quota_infos.append(result_item["quota_info"])
        else:
            error_msg = result.get("error", "Unknown error")
            results.append({
                "url": url,
                "content": None,
                "success": False,
                "error": error_msg,
                "error_details": result.get("error_details", {})
            })
            if stop_on_failure:
                logger.warning(
                    f"[轮次 {round_id}] 爬取失败，停止后续URL以节省额度: {error_msg[:100]}"
                )
                break

    # Collect round summary
    round_summary = get_round_summary(round_id)

    # Log round summary
    logger.info(
        f"[轮次总结 {round_id}] 共 {len(urls)} 个URL | "
        f"成功={successful_count} 失败={len(urls)-successful_count} | "
        f"使用的Key={round_summary.get('keys_used', []) if round_summary else 'N/A'}"
    )

    return {
        "success": successful_count > 0,
        "results": results,
        "stats": {
            "total": len(urls),
            "success": successful_count,
            "failure": len(urls) - successful_count
        },
        "quota_summary": {
            "round_id": round_id,
            "round_summary": round_summary,
            "quota_infos": quota_infos
        }
    }
