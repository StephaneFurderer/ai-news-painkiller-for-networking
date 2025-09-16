import os
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ReadwiseDocument:
    id: str
    url: str
    title: str
    author: str
    source: str
    category: str
    location: str
    tags: List[str]
    site_name: str
    word_count: int
    created_at: str
    updated_at: str
    notes: str
    summary: str
    image_url: str
    content: str
    html_content: str
    reading_progress: float
    first_opened_at: Optional[str]
    last_opened_at: Optional[str]
    saved_at: str
    last_moved_at: str


class ReadwiseClient:
    def __init__(self, api_token: Optional[str] = None):
        """Initialize Readwise API client."""
        # Try to get token from parameter, environment, or settings
        if api_token:
            self.api_token = api_token
        else:
            self.api_token = os.getenv("READWISE_TOKEN")

        if not self.api_token:
            try:
                from config.settings import settings
                self.api_token = settings.readwise_token
            except Exception:
                pass
        if not self.api_token:
            raise ValueError("READWISE_TOKEN environment variable is required")

        self.base_url = "https://readwise.io/api/v3"
        self.headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json"
        }

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make HTTP request to Readwise API."""
        url = f"{self.base_url}/{endpoint}"

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Readwise API request failed: {e}")
            return {}

    def list_documents(self, limit: int = 20, cursor: Optional[str] = None) -> Dict:
        """List documents from Readwise."""
        params = {"page_size": limit}
        if cursor:
            params["page_cursor"] = cursor

        print(f"DEBUG: Requesting {limit} documents from Readwise API")
        result = self._make_request("list/", params)
        if result and "results" in result:
            print(f"DEBUG: API returned {len(result['results'])} documents")
        return result

    def get_document_content(self, document_id: str, include_html: bool = False) -> Optional[ReadwiseDocument]:
        """Get full content of a specific document."""
        endpoint = "list/"
        params = {"id": document_id}
        if include_html:
            params["withHtmlContent"] = True

        data = self._make_request(endpoint, params)

        if not data or "results" not in data or not data["results"]:
            return None

        doc_data = data["results"][0]

        return ReadwiseDocument(
            id=doc_data.get("id", ""),
            url=doc_data.get("url", ""),
            title=doc_data.get("title", ""),
            author=doc_data.get("author", ""),
            source=doc_data.get("source", ""),
            category=doc_data.get("category", ""),
            location=doc_data.get("location", ""),
            tags=doc_data.get("tags", []),
            site_name=doc_data.get("site_name", ""),
            word_count=doc_data.get("word_count", 0),
            created_at=doc_data.get("created_at", ""),
            updated_at=doc_data.get("updated_at", ""),
            notes=doc_data.get("notes", ""),
            summary=doc_data.get("summary", ""),
            image_url=doc_data.get("image_url", ""),
            content=doc_data.get("content", ""),
            html_content=doc_data.get("html_content", ""),
            reading_progress=doc_data.get("reading_progress", 0.0),
            first_opened_at=doc_data.get("first_opened_at"),
            last_opened_at=doc_data.get("last_opened_at"),
            saved_at=doc_data.get("saved_at", ""),
            last_moved_at=doc_data.get("last_moved_at", "")
        )


def get_readwise_content(document_id: Optional[str] = None, limit: int = 10, api_token: Optional[str] = None) -> List[ReadwiseDocument]:
    """Tool function to get Readwise content."""
    try:
        client = ReadwiseClient(api_token=api_token)

        if document_id:
            # Get specific document
            doc = client.get_document_content(document_id)
            return [doc] if doc else []
        else:
            # List recent documents
            data = client.list_documents(limit=limit)
            documents = []

            for item in data.get("results", []):
                doc = ReadwiseDocument(
                    id=item.get("id", ""),
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    author=item.get("author", ""),
                    source=item.get("source", ""),
                    category=item.get("category", ""),
                    location=item.get("location", ""),
                    tags=item.get("tags", []),
                    site_name=item.get("site_name", ""),
                    word_count=item.get("word_count", 0),
                    created_at=item.get("created_at", ""),
                    updated_at=item.get("updated_at", ""),
                    notes=item.get("notes", ""),
                    summary=item.get("summary", ""),
                    image_url=item.get("image_url", ""),
                    content=item.get("content", ""),
                    reading_progress=item.get("reading_progress", 0.0),
                    first_opened_at=item.get("first_opened_at"),
                    last_opened_at=item.get("last_opened_at"),
                    saved_at=item.get("saved_at", ""),
                    last_moved_at=item.get("last_moved_at", "")
                )
                documents.append(doc)

            return documents

    except Exception as e:
        print(f"Error getting Readwise content: {e}")
        return []


if __name__ == "__main__":
    # Test the client
    documents = get_readwise_content(limit=5)
    print(f"Found {len(documents)} documents")

    for doc in documents:
        print(f"- {doc.title} ({doc.word_count} words)")