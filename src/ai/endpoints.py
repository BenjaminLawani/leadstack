from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.groq import GroqModel

from src.core.config import settings
from src.core.utils import web_search_service, csv_service


# Pydantic models for API requests/responses
class LeadSearchRequest(BaseModel):
    """Request model for lead search"""
    industry: str = Field(..., description="Industry or business type to search for")
    location: Optional[str] = Field(None, description="Geographic location")
    job_title: Optional[str] = Field(None, description="Target job title")
    company_size: Optional[str] = Field(None, description="Company size filter")
    additional_criteria: Optional[str] = Field(None, description="Additional search criteria")


class LeadSearchResponse(BaseModel):
    """Response model for lead search"""
    leads: List[Dict[str, Any]]
    total_found: int
    search_query: str


class CSVProcessRequest(BaseModel):
    """Request model for CSV processing"""
    csv_content: str = Field(..., description="CSV content as string")
    field_mapping: Optional[Dict[str, str]] = Field(
        None,
        description="Mapping of CSV columns to lead fields"
    )
    filters: Optional[Dict[str, Any]] = Field(None, description="Filters to apply")


class CSVProcessResponse(BaseModel):
    """Response model for CSV processing"""
    leads: List[Dict[str, Any]]
    total_processed: int


class AgentQueryRequest(BaseModel):
    """Request model for agent queries"""
    query: str = Field(..., description="Natural language query for the agent")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class AgentQueryResponse(BaseModel):
    """Response model for agent queries"""
    response: str
    data: Optional[Dict[str, Any]] = None
    csv_content: Optional[str] = None
    is_csv: bool = False


# Initialize the Pydantic AI Agent
agent = Agent(
    "groq:llama-3.3-70b-versatile",
    system_prompt="""You are Steve, a lead generation assistant specialized in finding and processing business leads.

Your capabilities include:
1. Searching the web for potential leads based on industry, location, job titles, and other criteria
2. Processing and analyzing CSV files containing lead data
3. Extracting contact information from search results
4. Filtering and organizing lead data
5. Providing insights and recommendations for lead generation strategies

IMPORTANT: When the user asks for CSV, export, download, spreadsheet, or Excel output:
- Use the search tools to gather lead data
- Once you have the data, use the create_csv_from_leads tool to generate CSV content
- The system will automatically provide a download link to the user

When searching for leads, you should:
- Use specific search queries that include industry, location, and relevant keywords
- Look for contact information like emails and phone numbers
- Identify decision-makers and key contacts
- Provide structured data that can be easily imported

When processing CSV data, you should:
- Parse and normalize the data
- Apply filters as requested
- Extract relevant lead fields
- Identify data quality issues

For regular chat queries (not requesting CSV):
- Provide clear, conversational responses
- Offer actionable advice and insights
- Explain your reasoning and recommendations

Always be helpful, professional, and focused on helping users generate and manage leads effectively.""",
    retries=2,
)


# Tool functions for the agent
@agent.tool
async def search_web_for_leads(
    ctx: RunContext,
    industry: str,
    location: Optional[str] = None,
    job_title: Optional[str] = None,
    company_size: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search the web for potential leads based on criteria.
    
    Args:
        industry: Industry or business type
        location: Geographic location (optional)
        job_title: Target job title (optional)
        company_size: Company size filter (optional)
    
    Returns:
        Dictionary with search results
    """
    try:
        results = await web_search_service.search_for_leads(
            industry=industry,
            location=location,
            job_title=job_title,
            company_size=company_size,
        )
        
        return {
            "success": True,
            "results": results,
            "count": len(results),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": [],
            "count": 0,
        }


@agent.tool
async def perform_web_search(
    ctx: RunContext,
    query: str,
    num_results: int = 10,
) -> Dict[str, Any]:
    """
    Perform a general web search.
    
    Args:
        query: Search query string
        num_results: Number of results to return (default: 10)
    
    Returns:
        Dictionary with search results
    """
    try:
        results = await web_search_service.search_web(
            query=query,
            num_results=num_results,
        )
        
        return {
            "success": True,
            "results": results,
            "count": len(results),
            "query": query,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": [],
            "count": 0,
        }


@agent.tool
def process_csv_data(
    ctx: RunContext,
    csv_content: str,
    field_mapping: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Process CSV content and extract lead data.
    
    Args:
        csv_content: CSV content as string
        field_mapping: Optional mapping of CSV columns to lead fields
    
    Returns:
        Dictionary with processed leads
    """
    try:
        # Parse CSV
        data = csv_service.parse_csv_content(csv_content)
        
        # Extract lead fields
        leads = csv_service.extract_lead_fields(data, field_mapping)
        
        return {
            "success": True,
            "leads": leads,
            "count": len(leads),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "leads": [],
            "count": 0,
        }


@agent.tool
def filter_csv_leads(
    ctx: RunContext,
    csv_content: str,
    filters: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Filter leads from CSV data based on criteria.
    
    Args:
        csv_content: CSV content as string
        filters: Dictionary of filter criteria
    
    Returns:
        Dictionary with filtered leads
    """
    try:
        # Parse CSV
        data = csv_service.parse_csv_content(csv_content)
        
        # Apply filters
        filtered = csv_service.filter_leads(data, filters)
        
        return {
            "success": True,
            "leads": filtered,
            "count": len(filtered),
            "original_count": len(data),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "leads": [],
            "count": 0,
        }


@agent.tool
def create_csv_from_leads(
    ctx: RunContext,
    leads: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Create CSV content from lead data.
    
    Args:
        leads: List of lead dictionaries
    
    Returns:
        Dictionary with CSV content
    """
    try:
        csv_content = csv_service.create_csv_content(leads)
        
        return {
            "success": True,
            "csv_content": csv_content,
            "lead_count": len(leads),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "csv_content": "",
        }


# FastAPI Router
ai_router = APIRouter(prefix="/ai", tags=["AI Agent"])


@ai_router.post("/search-leads", response_model=LeadSearchResponse)
async def search_leads(request: LeadSearchRequest):
    """
    Search for leads using the AI agent with web search capabilities
    """
    try:
        # Build query for the agent
        query = f"Search for {request.industry} leads"
        if request.location:
            query += f" in {request.location}"
        if request.job_title:
            query += f" with job title {request.job_title}"
        if request.company_size:
            query += f" at {request.company_size} companies"
        if request.additional_criteria:
            query += f". Additional criteria: {request.additional_criteria}"
        
        # Run the agent
        result = await agent.run(
            query,
            message_history=[],
        )
        
        # Extract leads from the result
        leads = []
        # The result.data contains the final response from the agent
        response_data = getattr(result, 'data', None)
        
        if response_data:
            if isinstance(response_data, dict):
                if 'results' in response_data:
                    leads = response_data['results']
                elif 'leads' in response_data:
                    leads = response_data['leads']
            elif isinstance(response_data, list):
                leads = response_data
        
        return LeadSearchResponse(
            leads=leads,
            total_found=len(leads),
            search_query=query,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ai_router.post("/process-csv", response_model=CSVProcessResponse)
async def process_csv(request: CSVProcessRequest):
    """
    Process CSV data to extract and filter leads
    """
    try:
        # Build query for the agent
        query = "Process this CSV data and extract lead information"
        if request.filters:
            query += f" with filters: {request.filters}"
        
        # Add CSV content to context
        context = {
            "csv_content": request.csv_content,
            "field_mapping": request.field_mapping,
            "filters": request.filters,
        }
        
        # Run the agent
        result = await agent.run(
            query,
            message_history=[],
        )
        
        # Extract leads from the result
        leads = []
        # The result.data contains the final response from the agent
        response_data = getattr(result, 'data', None)
        
        if response_data:
            if isinstance(response_data, dict):
                if 'leads' in response_data:
                    leads = response_data['leads']
                elif 'results' in response_data:
                    leads = response_data['results']
            elif isinstance(response_data, list):
                leads = response_data
        
        return CSVProcessResponse(
            leads=leads,
            total_processed=len(leads),
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ai_router.post("/query", response_model=AgentQueryResponse)
async def query_agent(request: AgentQueryRequest):
    """
    Send a natural language query to the AI agent.
    Intelligently returns CSV content if requested, otherwise returns chat response.
    """
    try:
        # Detect if user is requesting CSV output
        query_lower = request.query.lower()
        csv_keywords = ['csv', 'export', 'download', 'spreadsheet', 'excel']
        wants_csv = any(keyword in query_lower for keyword in csv_keywords)
        
        # Run the agent with the query
        result = await agent.run(
            request.query,
            message_history=[],
        )
        
        # Extract the actual text response from the agent
        response_text = str(getattr(result, 'data', ''))
        
        # Check if the agent used tools and extract data
        csv_content = None
        leads_data = []
        
        # Try to extract structured data from tool calls
        try:
            if hasattr(result, 'all_messages'):
                for message in result.all_messages():
                    if hasattr(message, 'parts'):
                        for part in message.parts:
                            part_type = type(part).__name__
                            
                            # Check for ToolReturnPart which contains tool results
                            if part_type == 'ToolReturnPart':
                                tool_content = getattr(part, 'content', None)
                                tool_name = getattr(part, 'tool_name', '')
                                
                                if isinstance(tool_content, dict):
                                    # Check if this is CSV creation result
                                    if tool_name == 'create_csv_from_leads' and 'csv_content' in tool_content:
                                        csv_content = tool_content.get('csv_content')
                                    
                                    # Check for leads data from search tools
                                    if 'results' in tool_content and isinstance(tool_content['results'], list):
                                        leads_data.extend(tool_content['results'])
                                    elif 'leads' in tool_content and isinstance(tool_content['leads'], list):
                                        leads_data.extend(tool_content['leads'])
        except Exception:
            # If we can't extract tool data, continue with text response
            pass
        
        # If CSV was requested but not created, try to create it from any leads data
        if wants_csv and not csv_content and leads_data:
            from src.core.utils import csv_service
            csv_content = csv_service.create_csv_content(leads_data)
        
        # Return appropriate response
        if csv_content:
            return AgentQueryResponse(
                response="CSV file generated successfully",
                data={"lead_count": len(leads_data)},
                csv_content=csv_content,
                is_csv=True,
            )
        else:
            # Regular chat response - return the agent's natural language response
            return AgentQueryResponse(
                response=response_text,
                data=None,
                csv_content=None,
                is_csv=False,
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ai_router.get("/health")
async def health_check():
    """
    Check if the AI agent is properly configured
    """
    return {
        "status": "healthy",
        "groq_configured": bool(settings.GROQ_API_KEY),
        "serper_configured": bool(settings.SERPER_API_KEY),
        "agent_ready": True,
    }

# Made with Bob
