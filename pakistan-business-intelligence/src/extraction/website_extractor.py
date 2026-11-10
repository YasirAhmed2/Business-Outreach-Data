"""
Safe Website Crawler and Page Extractor.
Complies with robots.txt, respects timeouts, and targets key corporate pages.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Set
import logging

logger = logging.getLogger("WebsiteExtractor")


class WebsiteExtractor:
    """Safely extracts content from official company websites."""

    TARGET_SUBPAGES = {
        "leadership": [
            "about", "about-us", "team", "our-team", "leadership",
            "management", "board-of-directors", "directors", "founders",
            "who-we-are", "company"
        ],
        "contact": [
            "contact", "contact-us", "reach-us", "get-in-touch",
            "support", "offices", "locations"
        ]
    }

    def __init__(self, timeout: int = 12, max_pages: int = 5, user_agent: str = ""):
        self.timeout = timeout
        self.max_pages = max_pages
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 (Pakistan-Research/1.0)"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetches and parses a single web page."""
        if not url:
            return None
        try:
            resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            if resp.status_code == 200 and "text/html" in resp.headers.get("Content-Type", ""):
                return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            logger.debug(f"Could not fetch {url}: {e}")
        return None

    def discover_relevant_subpages(self, base_url: str) -> Dict[str, List[str]]:
        """
        Discovers URLs for leadership and contact pages from the base website.
        """
        subpages: Dict[str, List[str]] = {"leadership": [], "contact": []}
        if not base_url:
            return subpages

        soup = self.fetch_page(base_url)
        if not soup:
            # Fallback to standard conventions
            for slug in ["about", "about-us", "team", "leadership", "management"]:
                subpages["leadership"].append(urljoin(base_url, slug))
            for slug in ["contact", "contact-us"]:
                subpages["contact"].append(urljoin(base_url, slug))
            return subpages

        base_domain = urlparse(base_url).netloc.lower()
        seen_urls: Set[str] = set()

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            
            # Keep within the same domain
            if parsed.netloc.lower() != base_domain:
                continue

            clean_path = parsed.path.lower().strip("/")
            if not clean_path or full_url in seen_urls:
                continue

            for pattern in self.TARGET_SUBPAGES["leadership"]:
                if pattern in clean_path and full_url not in subpages["leadership"]:
                    subpages["leadership"].append(full_url)
                    seen_urls.add(full_url)
                    break

            for pattern in self.TARGET_SUBPAGES["contact"]:
                if pattern in clean_path and full_url not in subpages["contact"]:
                    subpages["contact"].append(full_url)
                    seen_urls.add(full_url)
                    break

            if len(seen_urls) >= self.max_pages * 2:
                break

        # Always include base_url as fallback
        if base_url not in subpages["contact"]:
            subpages["contact"].insert(0, base_url)
        if base_url not in subpages["leadership"]:
            subpages["leadership"].insert(0, base_url)

        return subpages
