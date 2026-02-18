import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import time
from collections import deque

class WebsiteScraper:
    def __init__(self, base_url, max_pages=100, delay=1, exclude_patterns=None):
        """
        Initialize the scraper
        
        Args:
            base_url: The main page URL to start scraping
            max_pages: Maximum number of pages to scrape
            delay: Delay between requests in seconds
            exclude_patterns: List of URL patterns to exclude
        """
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited = set()
        self.to_visit = deque([base_url])
        self.max_pages = max_pages
        self.delay = delay
        self.scraped_docs = []
        self.exclude_patterns = exclude_patterns or []
        self.excluded_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', 
                                     '.ppt', '.pptx', '.zip', '.rar', '.jpg', 
                                     '.jpeg', '.png', '.gif', '.svg', '.mp4', 
                                     '.mp3', '.avi', '.mov']
        
    def is_valid_url(self, url):
        """Check if URL belongs to the same domain and is not excluded"""
        parsed = urlparse(url)
        
        # Check if same domain
        if parsed.netloc != self.domain:
            return False
        
        # Check if URL has excluded file extension
        url_lower = url.lower()
        for ext in self.excluded_extensions:
            if url_lower.endswith(ext):
                return False
        
        # Check if URL matches any exclude pattern
        for pattern in self.exclude_patterns:
            if pattern.lower() in url_lower:
                return False
        
        return True
    
    def extract_links(self, soup, current_url):
        """Extract all links from the page"""
        links = []
        for link in soup.find_all('a', href=True):
            url = urljoin(current_url, link['href'])
            # Remove fragments
            url = url.split('#')[0]
            if self.is_valid_url(url) and url not in self.visited:
                links.append(url)
        return links
    
    def extract_content(self, soup, url):
        """Extract main content from the page"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ""
        
        # Get main content
        # Try to find main content area
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup.body
        
        if main_content:
            text = main_content.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)
        
        # Clean up text
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        clean_text = '\n'.join(lines)
        
        return {
            'url': url,
            'title': title_text,
            'content': clean_text,
            'length': len(clean_text)
        }
    
    def scrape(self):
        """Main scraping function"""
        print(f"Starting to scrape: {self.base_url}")
        print(f"Max pages: {self.max_pages}")
        print(f"Excluding patterns: {self.exclude_patterns}")
        print(f"Excluding file types: {self.excluded_extensions}\n")
        
        skipped_count = 0
        
        while self.to_visit and len(self.scraped_docs) < self.max_pages:
            current_url = self.to_visit.popleft()
            
            if current_url in self.visited:
                continue
            
            # Check if URL should be excluded
            if not self.is_valid_url(current_url):
                skipped_count += 1
                self.visited.add(current_url)
                print(f"Skipping [{skipped_count}]: {current_url}")
                continue
            
            try:
                print(f"Scraping [{len(self.scraped_docs) + 1}]: {current_url}")
                
                # Make request
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(current_url, headers=headers, timeout=10)
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('Content-Type', '').lower()
                if 'text/html' not in content_type:
                    print(f"  → Skipping (not HTML): {content_type}")
                    self.visited.add(current_url)
                    skipped_count += 1
                    continue
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract content
                doc = self.extract_content(soup, current_url)
                
                # Only add if content is meaningful (more than 100 characters)
                if doc['length'] > 100:
                    self.scraped_docs.append(doc)
                else:
                    print(f"  → Skipping (too short)")
                    skipped_count += 1
                
                # Extract and queue new links
                new_links = self.extract_links(soup, current_url)
                self.to_visit.extend(new_links)
                
                # Mark as visited
                self.visited.add(current_url)
                
                # Be polite - delay between requests
                time.sleep(self.delay)
                
            except Exception as e:
                print(f"Error scraping {current_url}: {str(e)}")
                self.visited.add(current_url)
                continue
        
        print(f"\n✓ Scraping complete!")
        print(f"✓ Scraped {len(self.scraped_docs)} pages")
        print(f"✓ Skipped {skipped_count} pages")
        return self.scraped_docs
    
    def save_to_json(self, filename='scraped_docs.json'):
        """Save scraped documents to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_docs, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved to {filename}")
    
    def save_to_text(self, filename='scraped_docs.txt'):
        """Save scraped documents to text file"""
        with open(filename, 'w', encoding='utf-8') as f:
            for doc in self.scraped_docs:
                f.write(f"{'='*80}\n")
                f.write(f"URL: {doc['url']}\n")
                f.write(f"TITLE: {doc['title']}\n")
                f.write(f"{'='*80}\n\n")
                f.write(doc['content'])
                f.write(f"\n\n{'='*80}\n\n")
        print(f"✓ Saved to {filename}")


# Example usage
if __name__ == "__main__":
    # Replace with your target URL
    url = "https://www.emines-ingenieur.org"
    
    # Create scraper instance with exclusions
    scraper = WebsiteScraper(
        base_url=url,
        max_pages=100,  # Adjust as needed
        delay=1,  # 1 second delay between requests
        exclude_patterns=[
            'actualites',  # Excludes all news/actualites pages
            'agenda',      # Excludes agenda pages
            'faits-marquants',  # Excludes highlights
            'a-la-une'     # Excludes featured news
        ]
    )
    
    # Scrape the website
    docs = scraper.scrape()
    
    # Save results
    scraper.save_to_json('emines_docs.json')
    scraper.save_to_text('emines_docs.txt')
    
    # Print summary
    print(f"\nSummary:")
    print(f"Total pages scraped: {len(docs)}")
    print(f"Total content length: {sum(doc['length'] for doc in docs)} characters")