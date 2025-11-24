"""Wiki crawler for internal wiki pages.

Uses requests + BeautifulSoup for HTML parsing, with support for authenticated sessions.
"""
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def _same_domain(a: str, b: str) -> bool:
    """Check if two URLs belong to the same domain."""
    return urlparse(a).netloc == urlparse(b).netloc

def extract_wiki_info(html: str, url: str) -> Dict:
    """Extract document information from wiki page HTML."""
    soup = BeautifulSoup(html, "html.parser")
    
    # Get title from either title tag or first h1
    title = None
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        title = h1.get_text(strip=True)

    # Collect all headings
    headings = []
    for level in range(1, 7):
        for tag in soup.find_all(f"h{level}"):
            text = tag.get_text(strip=True)
            if text:
                headings.append({"level": level, "text": text})

    # Get first paragraph as snippet
    snippet = ""
    for p in soup.find_all(["p", "div"]):
        t = p.get_text(strip=True)
        if t:
            snippet = t[:500]
            break

    # Get metadata from common wiki systems
    metadata = {}
    meta_tags = soup.find_all("meta")
    for tag in meta_tags:
        name = tag.get("name", "").lower()
        if name in ["author", "description", "keywords", "last-modified"]:
            metadata[name] = tag.get("content", "")

    return {
        "url": url,
        "title": title or "(no title)",
        "headings": headings,
        "snippet": snippet,
        "metadata": metadata,
        "type": "wiki"
    }

def crawl_wiki(root_url: str,
               session: Optional[requests.Session] = None,
               max_depth: int = 1,
               max_pages: int = 200,
               timeout: int = 10) -> List[Dict]:
    """Crawl wiki pages starting from root_url.
    
    Args:
        root_url: Starting URL to crawl
        session: Optional requests.Session for authentication
        max_depth: How many levels deep to crawl
        max_pages: Maximum number of pages to crawl
        timeout: Timeout for each request in seconds
    
    Returns:
        List of dictionaries containing page information
    """
    if session is None:
        session = requests.Session()

    to_visit = [(root_url, 0)]  # (url, depth)
    seen: Set[str] = set()
    results: List[Dict] = []

    while to_visit and len(results) < max_pages:
        url, depth = to_visit.pop(0)
        if url in seen:
            continue
        seen.add(url)

        try:
            resp = session.get(url, timeout=timeout)
            if resp.status_code in (401, 403):
                logger.warning(f"Access denied to {url}")
                results.append({
                    "url": url,
                    "title": None,
                    "headings": [],
                    "snippet": f"Access denied (HTTP {resp.status_code})",
                    "status": "forbidden",
                    "type": "wiki"
                })
                continue
            
            if not resp.ok:
                logger.error(f"HTTP {resp.status_code} for {url}")
                results.append({
                    "url": url,
                    "title": None,
                    "headings": [],
                    "snippet": f"Failed with HTTP {resp.status_code}",
                    "status": "error",
                    "type": "wiki"
                })
                continue

            info = extract_wiki_info(resp.text, url)
            info["status"] = "ok"
            results.append(info)

            # Find links to crawl if we haven't hit depth limit
            if depth < max_depth:
                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    child = urljoin(url, href)
                    
                    # Only follow http(s) links on same domain
                    parsed = urlparse(child)
                    if (parsed.scheme in ("http", "https") and
                        _same_domain(root_url, child) and
                        child not in seen):
                        to_visit.append((child, depth + 1))

        except Exception as e:
            logger.exception(f"Error crawling {url}")
            results.append({
                "url": url,
                "title": None,
                "headings": [],
                "snippet": f"Error: {str(e)}",
                "status": "error",
                "type": "wiki"
            })

    return results