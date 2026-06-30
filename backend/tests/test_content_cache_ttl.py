import unittest

from app.services import content_cache, firecrawl_service, scraper_service


class ContentCacheTTLTest(unittest.TestCase):
    def test_scraped_content_cache_ttl_is_at_least_two_weeks(self):
        two_weeks_seconds = 14 * 24 * 60 * 60

        self.assertGreaterEqual(content_cache.CONTENT_CACHE_TTL, two_weeks_seconds)
        self.assertIs(scraper_service.cache_content, content_cache.cache_content)
        self.assertIs(scraper_service.get_cached_content, content_cache.get_cached_content)
        self.assertIs(scraper_service.get_url_cache_key, content_cache.get_url_cache_key)
        self.assertIs(firecrawl_service.cache_content, content_cache.cache_content)
        self.assertIs(firecrawl_service.get_cached_content, content_cache.get_cached_content)
        self.assertIs(firecrawl_service.get_url_cache_key, content_cache.get_url_cache_key)

    def test_content_cache_key_format_is_stable(self):
        self.assertEqual(
            "content:6eedbd4b7808dbf1da8e4dae8e50de47",
            content_cache.get_url_cache_key("https://example.com/cache-hit-check"),
        )

    def test_short_non_arxiv_cached_content_is_returned_from_cache(self):
        class FakeRedis:
            def __init__(self):
                self.values = {}

            def setex(self, key, _ttl, value):
                self.values[key] = value

            def get(self, key):
                return self.values.get(key)

            def delete(self, key):
                self.values.pop(key, None)

        def provider_failure(*_args, **_kwargs):
            return {
                "success": False,
                "error": "cache was bypassed",
                "error_details": {"type": "cache_bypassed"},
            }

        original_redis = content_cache.redis_client
        original_requests = scraper_service.scrape_with_requests
        original_jigsawstack = scraper_service.scrape_with_jigsawstack
        original_firecrawl = scraper_service.scrape_with_firecrawl
        original_firecrawl_token = scraper_service.FIRECRAWL_API_TOKEN

        try:
            content_cache.redis_client = FakeRedis()
            scraper_service.scrape_with_requests = provider_failure
            scraper_service.scrape_with_jigsawstack = provider_failure
            scraper_service.scrape_with_firecrawl = provider_failure
            scraper_service.FIRECRAWL_API_TOKEN = "configured"

            url = "https://example.com/cache-hit-check"
            cached_content = "short cached content"
            content_cache.cache_content(url, cached_content)

            result = scraper_service.scrape_single_url(url)

            self.assertTrue(result["success"])
            self.assertEqual("cache", result["results"][0]["provider"])
            self.assertEqual(cached_content, result["results"][0]["content"])
        finally:
            content_cache.redis_client = original_redis
            scraper_service.scrape_with_requests = original_requests
            scraper_service.scrape_with_jigsawstack = original_jigsawstack
            scraper_service.scrape_with_firecrawl = original_firecrawl
            scraper_service.FIRECRAWL_API_TOKEN = original_firecrawl_token


if __name__ == "__main__":
    unittest.main()
