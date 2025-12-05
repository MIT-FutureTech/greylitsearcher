"""
Direct Airtable integration - Alternative to processor service.

Use this if you want to skip the processor service and write directly to Airtable.
See ARCHITECTURE_DECISIONS.md for trade-offs.
"""

import time
from datetime import datetime
from typing import Dict, List, Any
from pyairtable import Table
import streamlit as st


class DirectAirtableIntegration:
    """Direct integration with Airtable from Streamlit."""
    
    def __init__(self, token: str, base_id: str, table_name: str = "raw_results"):
        """
        Initialize direct Airtable integration.
        
        Args:
            token: Airtable Personal Access Token
            base_id: Airtable Base ID
            table_name: Name of the table to write to
        """
        self.table = Table(token, base_id, table_name)
        self.token = token
        self.base_id = base_id
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return ""
    
    def normalize_record(self, item: Dict[str, Any], search_query: str, priority: int) -> Dict[str, Any]:
        """
        Normalize a search result item for Airtable.
        
        Note: Field names are case-sensitive and must match your Airtable table exactly.
        Default field names use lowercase with underscores (snake_case).
        
        Required fields (must exist in Airtable):
        - title
        - link
        
        Optional fields (will be written if they exist in Airtable):
        - snippet
        - source_domain
        - search_query
        - priority
        - scraped_at
        - status
        
        Extra fields in your Airtable table are fine - they'll just remain empty.
        """
        return {
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", ""),
            "source_domain": self.extract_domain(item.get("link", "")),
            "search_query": search_query,
            "priority": priority,
            "scraped_at": datetime.utcnow().date().isoformat(),
            "status": "Todo"
        }
    
    def save_results(
        self,
        results: Dict[str, List[Dict[str, Any]]],
        search_queries: Dict[str, str] = None,
        priority: int = 1,
        check_duplicates: bool = False,
        progress_callback=None
    ) -> Dict[str, int]:
        """
        Save results directly to Airtable.
        
        Args:
            results: Dictionary mapping website to list of search result items
            search_queries: Dictionary mapping website to search query string
            priority: Priority level (1-3)
            check_duplicates: Whether to check for duplicates before inserting
            progress_callback: Optional callback function(processed, total, created, errors)
        
        Returns:
            Dictionary with statistics: {created, duplicates, errors, processed}
        """
        if search_queries is None:
            search_queries = {}
        
        stats = {
            "processed": 0,
            "created": 0,
            "duplicates": 0,
            "errors": 0
        }
        
        all_items = []
        for website, items in results.items():
            query = search_queries.get(website, f"search on {website}")
            for item in items:
                # Use item's priority if available, otherwise use default priority
                item_priority = item.get('priority', priority)
                all_items.append((item, query, item_priority))
        
        total = len(all_items)
        
        for idx, (item, query, item_priority) in enumerate(all_items):
            try:
                link = item.get("link", "")
                if not link:
                    stats["errors"] += 1
                    stats["processed"] += 1
                    continue
                
                # Optional duplicate check (slower but prevents duplicates)
                if check_duplicates:
                    try:
                        from pyairtable.formulas import match
                        formula = match({"link": link})
                        existing = self.table.all(formula=formula, max_records=1)
                        if existing:
                            stats["duplicates"] += 1
                            stats["processed"] += 1
                            if progress_callback:
                                progress_callback(idx + 1, total, stats["created"], stats["errors"])
                            continue
                    except Exception as dup_error:
                        # If duplicate check fails (e.g., field doesn't exist), skip it and continue
                        # This allows the record to be created even if duplicate check fails
                        print(f"Warning: Duplicate check failed for {link}: {dup_error}")
                        # Continue to create the record anyway
                
                # Normalize and create record
                record = self.normalize_record(item, query, item_priority)
                
                # Airtable will automatically ignore fields that don't exist in the table
                # Extra fields in your table are fine - they'll just remain empty
                # Only required fields (title, link) must exist
                self.table.create(record)
                stats["created"] += 1
                stats["processed"] += 1
                
                # Rate limiting: Airtable allows 5 requests/second
                # Sleep 0.2 seconds = 5 requests/second max
                time.sleep(0.2)
                
                # Progress callback
                if progress_callback:
                    progress_callback(idx + 1, total, stats["created"], stats["errors"])
                
            except Exception as e:
                stats["errors"] += 1
                stats["processed"] += 1
                if progress_callback:
                    progress_callback(idx + 1, total, stats["created"], stats["errors"])
                # Log error but continue processing
                error_msg = str(e)
                print(f"Error saving record {link}: {error_msg}")
                
                # Provide helpful error messages
                if "403" in error_msg or "INVALID_PERMISSIONS" in error_msg:
                    print("  -> Check: Token has 'data.records:write' scope")
                    print("  -> Check: Token has access to this base and table")
                    print("  -> Check: Table name is correct")
                elif "NOT_FOUND" in error_msg or "model" in error_msg.lower():
                    print("  -> Check: Table name is correct")
                    print("  -> Check: Table exists in the base")
                    print("  -> Check: Field names match your Airtable schema")
        
        return stats


# Example usage in Streamlit main.py:
"""
# Add to top of main.py:
from direct_airtable_integration import DirectAirtableIntegration

# In your Streamlit app, after search completes:
if 'results' in st.session_state:
    if st.button('Save to Airtable'):
        # Get credentials from Streamlit secrets
        token = st.secrets.get('AIRTABLE_TOKEN')
        base_id = st.secrets.get('AIRTABLE_BASE_ID')
        
        if not token or not base_id:
            st.error("Airtable credentials not configured. Add AIRTABLE_TOKEN and AIRTABLE_BASE_ID to secrets.")
        else:
            # Initialize integration
            airtable = DirectAirtableIntegration(token, base_id)
            
            # Prepare search queries (optional)
            search_queries = {}
            for website in st.session_state['results']:
                search_queries[website] = f"{and1} {exact1}"  # Your search terms
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(processed, total, created, errors):
                progress = processed / total if total > 0 else 0
                progress_bar.progress(progress)
                status_text.text(f"Processing: {processed}/{total} | Created: {created} | Errors: {errors}")
            
            # Save results
            stats = airtable.save_results(
                st.session_state['results'],
                search_queries=search_queries,
                priority=1,
                check_duplicates=True,  # Set to False for faster processing
                progress_callback=update_progress
            )
            
            # Clear progress
            progress_bar.empty()
            status_text.empty()
            
            # Show results
            st.success(
                "**Save Complete!**\\n"
                f"- Created: {stats['created']} records\\n"
                f"- Duplicates: {stats['duplicates']} records\\n"
                f"- Errors: {stats['errors']} records"
            )
"""


