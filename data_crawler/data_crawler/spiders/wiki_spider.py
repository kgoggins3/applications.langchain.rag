import scrapy
from urllib.parse import urljoin

class WikiSpider(scrapy.Spider):
    name = "wiki"
    allowed_domains = ["wikipedia.org/", "wiki.ith.intel.com"]
    start_urls = ["https://en.wikipedia.org/wiki/Sharpie_(marker)", "https://wiki.ith.intel.com/spaces/CASEAMR/pages/4257711614/TechNest+Copy"]

    # session cookie
    session_cookie = {"JSESSIONID": "DE04361939B092E6BB25B61943A5FC28"}

    def make_requests_from_url(self, url):
        # This ensures cookies are applied to start_urls
        return scrapy.Request(url, cookies=self.session_cookie, callback=self.parse)

    def parse(self, response):
        # Extract page title and text
        title = response.css("h1::text").get()
        paragraphs = response.css("p::text").getall()
        text = " ".join([p.strip() for p in paragraphs if p.strip()])

        yield {
            "url": response.url,
            "title": title,
            "text": text[:500]
        }

        # Follow internal links
        links = response.css("a::attr(href)").getall()
        for link in links:
            if link.startswith("/spaces/CASEAMR/pages/") and not any(prefix in link for prefix in [":", "#"]):
                next_page = urljoin(response.url, link)
                yield scrapy.Request(next_page, cookies=self.session_cookie, callback=self.parse)
