"""Confluence API client for fetching page content."""
import requests
import json
import os
import argparse
from ..config import Config


class ConfluenceClient:
    """Client for interacting with Confluence API."""
    
    def __init__(self):
        """Initialize Confluence client with configuration."""
        # Derive Confluence base URL from JIRA server URL
        jira_server = Config.JIRA_SERVER
        if jira_server.endswith('/browse'):
            self.base_url = jira_server.replace('/browse', '/wiki')
        else:
            self.base_url = jira_server.rstrip('/') + '/wiki'
        
        self.api_token = Config.JIRA_API_TOKEN
        self.username = Config.JIRA_EMAIL
        self.output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'output', 'confluence')
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
    
    def get_page_id_by_title(self, page_title: str) -> str:
        """
        Fetch the page ID of a Confluence page using its title.
        
        Args:
            page_title: Title of the Confluence page to search for
            
        Returns:
            Page ID if found, None otherwise
        """
        url = f"{self.base_url}/rest/api/content?title={page_title}"
        headers = {"Accept": "application/json"}
        auth = (self.username, self.api_token)
        
        response = requests.get(url, headers=headers, auth=auth)
        
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                return results[0].get("id")
            else:
                print("No page found with the given title.")
                return None
        else:
            print(f"Failed to fetch page ID. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    def get_page_content(self, page_id: str) -> dict:
        """
        Fetch the content of a Confluence page using the REST API.
        
        Args:
            page_id: ID of the Confluence page to fetch
            
        Returns:
            Content of the page in JSON format
        """
        url = f"{self.base_url}/rest/api/content/{page_id}?expand=body.storage"
        headers = {"Accept": "application/json"}
        auth = (self.username, self.api_token)
        
        response = requests.get(url, headers=headers, auth=auth)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch page content. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    def get_page_by_title(self, page_title: str) -> dict:
        """
        Fetch a Confluence page by its title.
        
        Args:
            page_title: Title of the page to fetch
            
        Returns:
            Page content dictionary
        """
        page_id = self.get_page_id_by_title(page_title)
        if page_id:
            return self.get_page_content(page_id)
        return None
    
    def save_page_content(self, page_title: str, content: str, filename: str = None) -> str:
        """
        Save page content to a file in the output directory.
        
        Args:
            page_title: Title of the page (for default filename)
            content: HTML content to save
            filename: Optional custom filename
            
        Returns:
            Path to the saved file
        """
        if filename is None:
            # Generate filename from page title
            safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in page_title)
            safe_title = safe_title.replace(' ', '_')
            filename = f"{safe_title}.html"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath


def main():
    """Command-line interface for Confluence client."""
    parser = argparse.ArgumentParser(description="Fetch Confluence page content by title.")
    parser.add_argument("page_title", type=str, help="The title of the Confluence page to fetch.")
    parser.add_argument("--output", "-o", type=str, help="Output filename (optional)")
    args = parser.parse_args()
    
    # Create client
    client = ConfluenceClient()
    
    # Fetch page content
    page_data = client.get_page_by_title(args.page_title)
    
    if page_data:
        # Extract content
        body_storage = page_data.get("body", {}).get("storage", {}).get("value", "")
        print("Page Content:")
        print(body_storage)
        
        # Save to file
        filepath = client.save_page_content(args.page_title, body_storage, args.output)
        print(f"\nPage content saved to: {filepath}")


if __name__ == "__main__":
    main()
