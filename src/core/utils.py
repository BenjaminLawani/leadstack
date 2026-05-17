import csv
import io
from typing import List, Dict, Any, Optional
import httpx
from slowapi import Limiter
from slowapi.util import get_ipaddr

from .config import settings


class EmailService:
    def __init__(self):
        self.api_key = settings.MAIL_PASSWORD
        self.from_email = settings.MAIL_FROM
        self.from_name = settings.MAIL_FROM_NAME

    async def send_email(
        self,
        subject: str,
        recipients: list[str],
        body: str,
    ):
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": f"{self.from_name} <{self.from_email}>",
                    "to": recipients,
                    "subject": subject,
                    "html": body,
                },
            )

            response.raise_for_status()
            return response.json()


fm = EmailService()

limiter = Limiter(key_func=get_ipaddr)


class WebSearchService:
    """Service for performing web searches to find leads"""
    
    def __init__(self):
        self.serper_api_key = settings.SERPER_API_KEY
        self.serper_url = "https://google.serper.dev/search"
    
    async def search_web(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "search"
    ) -> List[Dict[str, Any]]:
        """
        Search the web using Serper API (Google Search API)
        
        Args:
            query: Search query string
            num_results: Number of results to return (default: 10)
            search_type: Type of search - 'search', 'news', 'images' (default: 'search')
        
        Returns:
            List of search results with title, link, snippet
        """
        if not self.serper_api_key:
            raise ValueError("SERPER_API_KEY not configured")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.serper_url,
                headers={
                    "X-API-KEY": self.serper_api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "q": query,
                    "num": num_results,
                    "type": search_type,
                },
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract organic results
            results = []
            if "organic" in data:
                for item in data["organic"]:
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "position": item.get("position", 0),
                    })
            
            return results
    
    async def search_for_leads(
        self,
        industry: str,
        location: Optional[str] = None,
        job_title: Optional[str] = None,
        company_size: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for potential leads based on criteria
        
        Args:
            industry: Industry or business type
            location: Geographic location (optional)
            job_title: Target job title (optional)
            company_size: Company size filter (optional)
        
        Returns:
            List of potential leads with contact information
        """
        # Build search query
        query_parts = [industry]
        
        if location:
            query_parts.append(f"in {location}")
        if job_title:
            query_parts.append(job_title)
        if company_size:
            query_parts.append(f"{company_size} company")
        
        # Add contact info keywords
        query_parts.append("contact email phone")
        
        query = " ".join(query_parts)
        
        # Perform search
        results = await self.search_web(query, num_results=20)
        
        return results


class CSVService:
    """Service for handling CSV operations for lead data"""
    
    @staticmethod
    def parse_csv_content(content: str) -> List[Dict[str, Any]]:
        """
        Parse CSV content into a list of dictionaries
        
        Args:
            content: CSV content as string
        
        Returns:
            List of dictionaries representing rows
        """
        csv_file = io.StringIO(content)
        reader = csv.DictReader(csv_file)
        return list(reader)
    
    @staticmethod
    def parse_csv_file(file_path: str) -> List[Dict[str, Any]]:
        """
        Parse CSV file into a list of dictionaries
        
        Args:
            file_path: Path to CSV file
        
        Returns:
            List of dictionaries representing rows
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    
    @staticmethod
    def create_csv_content(data: List[Dict[str, Any]]) -> str:
        """
        Create CSV content from a list of dictionaries
        
        Args:
            data: List of dictionaries to convert to CSV
        
        Returns:
            CSV content as string
        """
        if not data:
            return ""
        
        output = io.StringIO()
        fieldnames = data[0].keys()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue()
    
    @staticmethod
    def write_csv_file(file_path: str, data: List[Dict[str, Any]]) -> None:
        """
        Write data to a CSV file
        
        Args:
            file_path: Path to output CSV file
            data: List of dictionaries to write
        """
        if not data:
            return
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(data)
    
    @staticmethod
    def filter_leads(
        data: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Filter lead data based on criteria
        
        Args:
            data: List of lead dictionaries
            filters: Dictionary of filter criteria
        
        Returns:
            Filtered list of leads
        """
        filtered = data
        
        for key, value in filters.items():
            if value is not None:
                filtered = [
                    item for item in filtered
                    if key in item and str(item[key]).lower() == str(value).lower()
                ]
        
        return filtered
    
    @staticmethod
    def extract_lead_fields(
        data: List[Dict[str, Any]],
        field_mapping: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract and normalize lead fields from CSV data
        
        Args:
            data: List of dictionaries from CSV
            field_mapping: Optional mapping of CSV columns to lead fields
                          e.g., {"Full Name": "name", "Email Address": "email"}
        
        Returns:
            List of normalized lead dictionaries
        """
        if not field_mapping:
            # Default field mapping
            field_mapping = {
                "name": "name",
                "company": "company",
                "email": "email",
                "phone": "phone_number",
                "phone_number": "phone_number",
            }
        
        leads = []
        for row in data:
            lead = {}
            for csv_field, lead_field in field_mapping.items():
                # Try exact match first
                if csv_field in row:
                    lead[lead_field] = row[csv_field]
                else:
                    # Try case-insensitive match
                    for key in row.keys():
                        if key.lower() == csv_field.lower():
                            lead[lead_field] = row[key]
                            break
            
            if lead:  # Only add if we found at least one field
                leads.append(lead)
        
        return leads


# Initialize services
web_search_service = WebSearchService()
csv_service = CSVService()