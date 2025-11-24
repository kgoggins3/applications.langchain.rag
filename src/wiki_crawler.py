"""Simple wiki crawler utilities.

Provides crawl_wiki() to discover pages under a root wiki URL and extract
document information (titles, headings, snippets). Uses requests + BeautifulSoup.

Design notes / contract:
- Inputs: root_url (str), optional requests.Session, max_depth, max_pages
- Outputs: list[dict] with keys: url, title, headings(list), snippet, status
- Error modes: pages returning 401/403 will set status and note in snippet

This is intentionally minimal and synchronous so it works in restricted
internal environments. It follows same-domain links and limits pages to avoid
explosion.
"""
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup


def _same_domain(a: str, b: str) -> bool:
    return urlparse(a).netloc == urlparse(b).netloc


def extract_doc_info(html: str, url: str) -> Dict:
    soup = BeautifulSoup(html, "html.parser")
    title = None
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    # prefer h1 as title when present
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        title = h1.get_text(strip=True)

    # collect headings
    headings = []
    for level in range(1, 7):
        for tag in soup.find_all(f"h{level}"):
            text = tag.get_text(strip=True)
            if text:
                headings.append({"level": level, "text": text})

    # snippet: first paragraph-like text
    snippet = ""
    for p in soup.find_all(["p", "div"]):
        t = p.get_text(strip=True)
        if t:
            snippet = t[:500]
            break

    return {"url": url, "title": title or "(no title)", "headings": headings, "snippet": snippet}


def crawl_wiki(root_url: str,
               session: Optional[requests.Session] = None,
               max_depth: int = 1,
               max_pages: int = 200,
               timeout: int = 10,
               gather_headings_only: bool = True) -> List[Dict]:
    """Crawl pages starting from root_url and extract document info.

    The crawler only follows links on the same domain as root_url and will not
    visit more than max_pages pages. By default it only gathers headings and a
    short snippet; set gather_headings_only=False to return content for each
    page as well.

    Notes on internal wikis / permissions:
    - If the page returns 401/403, the result will include status and a note
      in the snippet. To access protected pages, pass a `session` configured
      with the necessary cookies/authentication.
    """
    if session is None:
        session = requests.Session()

    to_visit = [(root_url, 0)]
    seen: Set[str] = set()
    results: List[Dict] = []

    while to_visit and len(results) < max_pages:
        url, depth = to_visit.pop(0)
        if url in seen:
            continue
        seen.add(url)

        try:
            resp = session.get(url, timeout=timeout)
        except Exception as e:
            results.append({"url": url, "title": None, "headings": [], "snippet": f"error: {e}", "status": "error"})
            continue

        if resp.status_code in (401, 403):
            results.append({"url": url, "title": None, "headings": [], "snippet": f"access denied (status {resp.status_code})", "status": "forbidden"})
            continue

        if not resp.ok:
            results.append({"url": url, "title": None, "headings": [], "snippet": f"http {resp.status_code}", "status": "error"})
            continue

        html = resp.text
        info = extract_doc_info(html, url)
        info["status"] = "ok"
        if not gather_headings_only:
            info["content"] = html

        results.append(info)

        # enqueue same-domain links if depth allows
        if depth < max_depth:
            soup = BeautifulSoup(html, "html.parser")
            anchors = soup.find_all("a", href=True)
            for a in anchors:
                href = a["href"]
                # resolve relative URLs
                child = urljoin(url, href)
                # only same domain and http(s)
                parsed = urlparse(child)
                if parsed.scheme not in ("http", "https"):
                    continue
                if not _same_domain(root_url, child):
                    continue
                if child not in seen:
                    to_visit.append((child, depth + 1))

    return results


if __name__ == "__main__":
    # quick manual test
    import sys
    if len(sys.argv) > 1:
        root = sys.argv[1]
        res = crawl_wiki(root, max_depth=0, max_pages=10)
        for r in res:
            print(r["url"], r.get("title"))