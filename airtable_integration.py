"""Integration module to send Greylitsearcher results to Airtable via data processor."""

import requests
import json
from typing import Dict, List, Any, Optional


class AirtableProcessorClient:
    """Client to send search results to data processor service."""
    
    def __init__(self, processor_url: str = "http://localhost:8001/process"):
        """
        Initialize client.
        
        Args:
            processor_url: URL of the data processor service endpoint
        """
        self.processor_url = processor_url
    
    def send_results(
        self,
        results: Dict[str, List[Dict[str, Any]]],
        search_queries: Dict[str, Dict[str, Any]],
        priority: int = 1
    ) -> Dict[str, Any]:
        """
        Send search results to processor.
        
        Args:
            results: Dictionary mapping website to list of search result items
            search_queries: Dictionary mapping website to search query details
            priority: Priority level (1-3)
        
        Returns:
            Response from processor service
        """
        all_results = []
        
        for website, items in results.items():
            query_info = search_queries.get(website, {})
            search_query = query_info.get("query", f"search on {website}")
            
            for item in items:
                # Add search context
                item_with_context = item.copy()
                item_with_context["search_query"] = search_query
                item_with_context["priority"] = priority
                all_results.append(item_with_context)
        
        payload = {
            "results": all_results,
            "search_query": "Greylitsearcher batch",
            "priority": priority
        }
        
        try:
            response = requests.post(
                self.processor_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error sending to processor: {e}")
            return {"error": str(e)}


def integrate_with_streamlit(st_session_state, processor_url: Optional[str] = None):
    """
    Integrate with Streamlit session state to send results.
    
    Usage in main.py:
        from airtable_integration import integrate_with_streamlit
        
        if search_button:
            # ... existing search code ...
            
            # After results are in st.session_state['results']
            if 'results' in st.session_state:
                client = AirtableProcessorClient(processor_url)
                # Send results
                response = client.send_results(
                    st.session_state['results'],
                    search_queries={},  # You may want to track queries
                    priority=1
                )
                st.success(f"Sent {len(st.session_state['results'])} results to Airtable!")
    """
    if processor_url is None:
        processor_url = "http://localhost:8001/process"
    
    client = AirtableProcessorClient(processor_url)
    
    if 'results' in st_session_state:
        # Extract search queries if available
        search_queries = st_session_state.get('search_queries', {})
        
        # Send all results
        response = client.send_results(
            st_session_state['results'],
            search_queries,
            priority=1
        )
        
        return response
    return None


# Example usage in main.py:
"""
# Add at the top of main.py:
from airtable_integration import AirtableProcessorClient

# Add processor URL to secrets or config:
PROCESSOR_URL = st.secrets.get('PROCESSOR_URL', 'http://localhost:8001/process')

# After search completes and results are in session_state:
if 'results' in st.session_state and st.button('Send to Airtable'):
    client = AirtableProcessorClient(PROCESSOR_URL)
    response = client.send_results(
        st.session_state['results'],
        search_queries={},  # Track your queries
        priority=1
    )
    if 'error' not in response:
        st.success(f"Successfully sent results to Airtable!")
    else:
        st.error(f"Error: {response.get('error')}")
"""



