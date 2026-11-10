"""
Executive and Decision-Maker Extraction Engine.
Extracts names, designations, and public professional URLs from company leadership, team, and about pages.
"""

import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger("LeadershipExtractor")


class LeadershipExtractor:
    """Extracts authentic leadership details from company HTML pages."""

    DESIGNATION_PATTERNS = [
        (r"\bchief\s+executive\s+officer\b|\bceo\b", "CEO"),
        (r"\bco-?founder\b", "Co-Founder"),
        (r"\bfounder\b", "Founder"),
        (r"\bmanaging\s+director\b|\bmd\b", "Managing Director"),
        (r"\bchief\s+technology\s+officer\b|\bcto\b", "CTO"),
        (r"\bchief\s+operating\s+officer\b|\bcoo\b", "COO"),
        (r"\bchief\s+information\s+officer\b|\bcio\b", "CIO"),
        (r"\bhead\s+of\s+technology\b|\bvp\s+of\s+engineering\b", "Head of Technology"),
        (r"\bchief\s+financial\s+officer\b|\bcfo\b", "CFO"),
        (r"\bpresident\b", "President"),
        (r"\bchairman\b|\bchairperson\b", "Chairman"),
        (r"\bexecutive\s+director\b", "Executive Director"),
        (r"\bdirector\b", "Director"),
    ]

    INVALID_NAME_TOKENS = {
        "read", "more", "learn", "about", "us", "contact", "home", "our",
        "team", "leadership", "board", "directors", "view", "profile", "bio",
        "company", "mission", "vision", "services", "career", "careers", "join"
    }

    @classmethod
    def clean_name(cls, raw_name: str) -> Optional[str]:
        """Validates and formats executive name."""
        if not raw_name:
            return None
        name = " ".join(raw_name.split()).strip()
        # Remove honorifics
        name = re.sub(r"^(mr\.|mrs\.|ms\.|dr\.|engr\.|syed|sheikh|mian|choudhry|chaudhry)\s+", "", name, flags=re.IGNORECASE)
        # Check token count and validity
        tokens = name.split()
        if len(tokens) < 2 or len(tokens) > 5:
            return None
        for t in tokens:
            if t.lower() in cls.INVALID_NAME_TOKENS or not t.isalpha():
                return None
        return name.title()

    @classmethod
    def extract_executives_from_soup(cls, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """
        Parses HTML page looking for structured team cards, headers, and leadership markers.
        """
        executives: List[Dict[str, Any]] = []
        if not soup:
            return executives

        # Look for profile cards, team members, bio sections
        card_selectors = [
            ".team-member", ".team-card", ".leader", ".leadership-card",
            ".bio-card", ".member-card", ".director-card", ".team-item",
            ".executive-item", "article", ".person"
        ]

        found_cards = soup.select(", ".join(card_selectors))
        if found_cards:
            for card in found_cards:
                text = card.get_text(separator=" ", strip=True)
                for pattern, role in cls.DESIGNATION_PATTERNS:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        # Extract name candidates from headings inside this card
                        candidate_name = None
                        for h in card.find_all(["h2", "h3", "h4", "h5", "strong"]):
                            h_text = h.get_text(strip=True)
                            cleaned = cls.clean_name(h_text)
                            if cleaned:
                                candidate_name = cleaned
                                break

                        # Check for official public LinkedIn profile link inside card
                        linkedin_url = None
                        for a in card.find_all("a", href=True):
                            href = a["href"].strip()
                            if "linkedin.com/in/" in href:
                                linkedin_url = href.split("?")[0]
                                break

                        if candidate_name:
                            executives.append({
                                "name": candidate_name,
                                "designation": role,
                                "normalized_role": role,
                                "linkedin_url": linkedin_url,
                                "source_url": page_url,
                                "evidence_text": text[:300]
                            })
                            break

        # Fallback to text scanning if no structured cards found
        if not executives:
            page_text = soup.get_text(separator="\n", strip=True)
            lines = [line.strip() for line in page_text.splitlines() if line.strip()]
            for i, line in enumerate(lines):
                for pattern, role in cls.DESIGNATION_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE) and len(line) < 60:
                        # Check preceding line or succeeding line for name
                        potential_names = []
                        if i > 0:
                            potential_names.append(lines[i-1])
                        if i + 1 < len(lines):
                            potential_names.append(lines[i+1])

                        for pot in potential_names:
                            cleaned = cls.clean_name(pot)
                            if cleaned:
                                executives.append({
                                    "name": cleaned,
                                    "designation": line,
                                    "normalized_role": role,
                                    "linkedin_url": None,
                                    "source_url": page_url,
                                    "evidence_text": f"{cleaned} - {line}"
                                })
                                break
                    if len(executives) >= 5:
                        break

        # Deduplicate executives by name
        unique_execs = []
        seen = set()
        for e in executives:
            key = e["name"].lower()
            if key not in seen:
                seen.add(key)
                unique_execs.append(e)

        return unique_execs
