"""SharePoint document crawler using Microsoft Graph API.

Requires Azure AD app registration for authentication. Can be configured with client
credentials (app-only) or delegated permissions (user context).
"""
from typing import List, Dict, Optional
import os
import msal
import requests
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SharePointCrawler:
    """Crawler for SharePoint document libraries using Microsoft Graph."""
    
    def __init__(self, 
                 tenant_id: str,
                 client_id: str,
                 client_secret: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None):
        """Initialize crawler with auth credentials.
        
        Args:
            tenant_id: Azure AD tenant ID
            client_id: Azure AD application (client) ID
            client_secret: Optional. For app-only auth
            username: Optional. For delegated auth
            password: Optional. For delegated auth
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        
        # Initialize MSAL app
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.app = msal.ConfidentialClientApplication(
            client_id,
            authority=authority,
            client_credential=client_secret
        ) if client_secret else msal.PublicClientApplication(
            client_id,
            authority=authority
        )
        
        self._token = None
    
    def _get_token(self) -> str:
        """Get access token for Microsoft Graph API."""
        scopes = ["https://graph.microsoft.com/.default"]
        
        if self.client_secret:
            # App-only auth
            result = self.app.acquire_token_for_client(scopes)
        else:
            # Delegated auth
            result = self.app.acquire_token_by_username_password(
                self.username,
                self.password,
                scopes
            )
            
        if "access_token" not in result:
            raise Exception(f"Failed to get token: {result.get('error_description')}")
            
        return result["access_token"]
    
    def _make_request(self, url: str) -> Dict:
        """Make authenticated request to Microsoft Graph API."""
        if not self._token:
            self._token = self._get_token()
            
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json"
        }
        
        resp = requests.get(url, headers=headers)
        if resp.status_code == 401:
            # Token expired, retry once
            self._token = self._get_token()
            headers["Authorization"] = f"Bearer {self._token}"
            resp = requests.get(url, headers=headers)
            
        resp.raise_for_status()
        return resp.json()

    def crawl_library(self, 
                     site_id: str,
                     library_id: str,
                     max_items: int = 1000) -> List[Dict]:
        """Crawl a SharePoint document library.
        
        Args:
            site_id: SharePoint site ID
            library_id: Document library ID
            max_items: Maximum number of items to return
            
        Returns:
            List of document metadata dictionaries
        """
        results = []
        next_link = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{library_id}/items"
        
        while next_link and len(results) < max_items:
            try:
                data = self._make_request(next_link)
                
                for item in data.get("value", []):
                    if len(results) >= max_items:
                        break
                        
                    # Skip folders
                    if "folder" in item:
                        continue
                        
                    doc_info = {
                        "id": item.get("id"),
                        "name": item.get("name"),
                        "title": item.get("title", item.get("name")),
                        "web_url": item.get("webUrl"),
                        "created": item.get("createdDateTime"),
                        "modified": item.get("lastModifiedDateTime"),
                        "size": item.get("size"),
                        "created_by": (item.get("createdBy", {})
                                     .get("user", {})
                                     .get("displayName")),
                        "modified_by": (item.get("lastModifiedBy", {})
                                      .get("user", {})
                                      .get("displayName")),
                        "file_type": item.get("file", {}).get("mimeType"),
                        "status": "ok",
                        "type": "sharepoint"
                    }
                    
                    results.append(doc_info)
                    
                next_link = data.get("@odata.nextLink")
                
            except Exception as e:
                logger.exception("Error crawling SharePoint library")
                break
                
        return results