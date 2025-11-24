# Document Crawler with Wiki and SharePoint Support

This application provides a web interface for crawling and exploring content from internal wikis and SharePoint document libraries. It's built with Python and Streamlit, offering an easy-to-use interface for accessing and viewing document metadata and content.

## Features

### Wiki Crawler
- Crawls internal wiki pages starting from a root URL
- Extracts headings, metadata, and content
- Handles authentication via cookies
- Configurable crawl depth and page limits
- Preview page content directly in the UI

### SharePoint Document Library Crawler
- Access SharePoint document libraries via Microsoft Graph API
- Supports both app-only and delegated authentication
- Extracts comprehensive document metadata
- Search and filter documents
- View full document properties

### Interactive UI (Streamlit)
- Easy authentication configuration
- Tabbed interface for different crawlers
- Expandable document previews
- Search/filter capabilities
- Clean metadata display

## Setup

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. For SharePoint access, you'll need:
   - Azure AD tenant ID
   - Client ID (App registration)
   - Either client secret (app-only) or username/password (delegated)

## Usage

1. Start the Streamlit app:
```bash
streamlit run src/streamlit_app.py
```

2. Configure authentication in the sidebar:
   - For wikis: Add any required cookies
   - For SharePoint: Add Azure AD credentials

3. Enter URLs/IDs and start crawling:
   - Wiki: Enter root URL, set depth and page limits
   - SharePoint: Provide site ID and library ID

## Authentication

### Wiki Access
For internal wikis that require authentication, you can:
1. Log in to the wiki in your browser
2. Copy the cookie header
3. Paste it in the Wiki Authentication section

### SharePoint Access
Two authentication methods are supported:
1. App-only (recommended for automation):
   - Requires Azure AD app registration with appropriate permissions
   - Uses client credentials (client ID + secret)

2. Delegated (user context):
   - Uses username/password
   - Requires user to have appropriate permissions

## Development

The project structure:
```
src/
  ├── crawlers/
  │   ├── wiki_crawler.py      # Wiki crawling functionality
  │   └── sharepoint_crawler.py # SharePoint document access
  ├── streamlit_app.py         # Web interface
  └── backend.py              # Core backend services
```

## Dependencies
- streamlit: Web interface
- requests: HTTP client
- beautifulsoup4: HTML parsing
- msal: Microsoft authentication
- python-dotenv: Environment management
