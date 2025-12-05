import pandas as pd
import streamlit as st
import requests
from direct_airtable_integration import DirectAirtableIntegration


# Password authentication
def check_password():
    """Check if user is authenticated."""
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    if not st.session_state['authenticated']:
        # Get password from secrets or use default
        correct_password = st.secrets.get('APP_PASSWORD', '')
        
        if not correct_password:
            st.error("Password not configured. Please set APP_PASSWORD in secrets.toml")
            st.stop()
        
        # Show password input form
        st.title("Greylitsearcher - Authentication Required")
        password = st.text_input("Enter password", type="password", key="password_input")
        
        if st.button("Login"):
            if password == correct_password:
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("Incorrect password. Please try again.")
        
        st.stop()
    
    return True


# Check authentication before proceeding
check_password()


# Initialize Airtable integration if credentials are available
airtable_configured = False
airtable_client = None

try:
    airtable_token = st.secrets.get('AIRTABLE_TOKEN')
    airtable_base_id = st.secrets.get('AIRTABLE_BASE_ID')
    airtable_table_name = st.secrets.get('AIRTABLE_TABLE_NAME', 'raw_results')
    
    if airtable_token and airtable_base_id:
        airtable_client = DirectAirtableIntegration(
            airtable_token,
            airtable_base_id,
            airtable_table_name
        )
        airtable_configured = True
except Exception as e:
    # Airtable not configured, continue without it
    pass


# Search engine CXs
GS_CX = [
    st.secrets['GS1_CX'],
    st.secrets['GS1_CX'],
    st.secrets['GS1_CX']
]

# API keys
GS_KEYS = [
    st.secrets['GS1_KEY'],
    st.secrets['GS2_KEY'],
    st.secrets['GS3_KEY'],
]


def google_search(page, site, **kwargs):
    url = 'https://www.googleapis.com/customsearch/v1'
    params = {
        'q': '',
        'key': '',
        'cx': '',
        'num': 10,
        'start': page * 10 + 1,
        'siteSearch': site
    }
    params.update(kwargs)
    for cx, key in zip(GS_CX, GS_KEYS):
        params['cx'] = cx
        params['key'] = key
        # return {'items': [{'link': 'https://www.google.com'}]}
        response = requests.get(url, params=params).json()
        # Check if the response is successful or if the rate limit has been exceeded
        if not response.get('error') or 'rateLimitExceeded' not in response['error']['errors'][0]['reason']:
            return response
    # If all keys exceeded the rate limit, print an error message
    print("All keys have exceeded the rate limit.")
    return None


st.set_page_config(layout="wide", page_title="Greylitsearcher",
                   page_icon="🔍️",)
st.title('Greylitsearcher')

# Logout button in sidebar
with st.sidebar:
    if st.button("Logout"):
        st.session_state['authenticated'] = False
        st.rerun()
st.write("""
Greylitsearcher is a tool that helps you find grey literature on the web.\n
You can get up to 40 results from each website. If the first search doesn't give you enough results, it will keep searching until it finds up to 40.
""")


with st.expander("Search 1", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        and1 = st.text_input(
            "All these words", help="Appends the specified query terms to the query, as if they were combined with a logical AND operator.", key='and1')
        exact1 = st.text_input("This exact word or phrase",
                               help="Identifies a phrase that all documents in the search results must contain.", key='exact1')
    with col2:
        any1 = st.text_input(
            "Any of these words", help="Provides additional search terms to check for in a document, where each document in the search results must contain at least one of the additional search terms.", key='any1')
        none1 = st.text_input(
            "None of these words", help="Identifies a word or phrase that should not appear in any documents in the search results.", key='none1')

with st.expander("Search 2"):
    col3, col4 = st.columns(2)
    with col3:
        and2 = st.text_input(
            "All these words", help="Appends the specified query terms to the query, as if they were combined with a logical AND operator.", key='and2')
        exact2 = st.text_input("This exact word or phrase",
                               help="Identifies a phrase that all documents in the search results must contain.", key='exact2')
    with col4:
        any2 = st.text_input(
            "Any of these words", help="Provides additional search terms to check for in a document, where each document in the search results must contain at least one of the additional search terms.", key='any2')
        none2 = st.text_input(
            "None of these words", help="Identifies a word or phrase that should not appear in any documents in the search results.", key='none2')

with st.expander("Search 3"):
    col5, col6 = st.columns(2)
    with col5:
        and3 = st.text_input(
            "All these words", help="Appends the specified query terms to the query, as if they were combined with a logical AND operator.", key='and3')
        exact3 = st.text_input("This exact word or phrase",
                               help="Identifies a phrase that all documents in the search results must contain.", key='exact3')
    with col6:
        any3 = st.text_input(
            "Any of these words", help="Provides additional search terms to check for in a document, where each document in the search results must contain at least one of the additional search terms.", key='any3')
        none3 = st.text_input(
            "None of these words", help="Identifies a word or phrase that should not appear in any documents in the search results.", key='none3')

websites = st.text_area("Websites to search",
                        key='websites',
                        help="Enter one website per line",
                        placeholder="example.com\nexample2.com"
                        )


search_button = st.button('Search')


limitExceeded = False

if search_button:
    st.session_state['results'] = {}
    st.session_state['search_queries'] = {}  # Track search queries for Airtable
    websites = websites.split('\n')
    for website in websites:
        if website:
            st.session_state['results'][website] = []
            # Build search query string for tracking
            query_parts = []
            if and1:
                query_parts.append(f"AND: {and1}")
            if exact1:
                query_parts.append(f'EXACT: "{exact1}"')
            if any1:
                query_parts.append(f"OR: {any1}")
            if none1:
                query_parts.append(f"NOT: {none1}")
            search_query_1 = " | ".join(query_parts) if query_parts else f"search on {website}"
            
            for page in range(4):
                current_results = google_search(
                    page, website, q=and1, exactTerms=exact1, orTerms=any1, excludeTerms=none1)
                if current_results == None:
                    limitExceeded = True
                    break
                for item in current_results.get('items', []):
                    item['priority'] = 1

                st.session_state['results'][website].extend(
                    current_results.get('items', []))
                if len(st.session_state['results'][website]) >= 40 or len(current_results.get('items', [])) < 10:
                    break
            
            # Store search query for this website
            st.session_state['search_queries'][website] = search_query_1
            
            if len(st.session_state['results'][website]) < 40 and (and2 or exact2 or any2 or none2):
                # Build search query 2
                query_parts_2 = []
                if and2:
                    query_parts_2.append(f"AND: {and2}")
                if exact2:
                    query_parts_2.append(f'EXACT: "{exact2}"')
                if any2:
                    query_parts_2.append(f"OR: {any2}")
                if none2:
                    query_parts_2.append(f"NOT: {none2}")
                search_query_2 = " | ".join(query_parts_2) if query_parts_2 else f"search 2 on {website}"
                st.session_state['search_queries'][website] = f"{search_query_1}; {search_query_2}"
                for page in range(8):
                    current_results = google_search(
                        page, website, q=and2, exactTerms=exact2, orTerms=any2, excludeTerms=none2)
                    if current_results == None:
                        limitExceeded = True
                        break
                    for item in current_results.get('items', []):
                        item['priority'] = 2

                    st.session_state['results'][website].extend([item for item in current_results.get(
                        'items', []) if item['link'] not in [i['link'] for i in st.session_state['results'][website]]])

                    if len(st.session_state['results'][website]) >= 40 or len(current_results.get('items', [])) < 10:
                        break
            
            if len(st.session_state['results'][website]) < 40 and (and3 or exact3 or any3 or none3):
                # Build search query 3
                query_parts_3 = []
                if and3:
                    query_parts_3.append(f"AND: {and3}")
                if exact3:
                    query_parts_3.append(f'EXACT: "{exact3}"')
                if any3:
                    query_parts_3.append(f"OR: {any3}")
                if none3:
                    query_parts_3.append(f"NOT: {none3}")
                search_query_3 = " | ".join(query_parts_3) if query_parts_3 else f"search 3 on {website}"
                current_query = st.session_state['search_queries'].get(website, search_query_1)
                st.session_state['search_queries'][website] = f"{current_query}; {search_query_3}"
                for page in range(10):
                    current_results = google_search(
                        page, website, q=and3, exactTerms=exact3, orTerms=any3, excludeTerms=none3)
                    if current_results == None:
                        limitExceeded = True
                        break
                    for item in current_results.get('items', []):
                        item['priority'] = 3
                    st.session_state['results'][website].extend([item for item in current_results.get(
                        'items', []) if item['link'] not in [i['link'] for i in st.session_state['results'][website]]])

                    if len(st.session_state['results'][website]) >= 40 or len(current_results.get('items', [])) < 10:
                        break
            st.session_state['results'][website] = st.session_state['results'][website][:40]



if 'results' in st.session_state.keys():
    # Calculate total results
    total_results = sum(len(items) for items in st.session_state['results'].values())
    
    # Show Airtable integration section if configured
    if airtable_configured:
        st.divider()
        st.subheader("Save to Airtable")
        
        col_save1, col_save2 = st.columns([2, 1])
        with col_save1:
            st.write(f"**{total_results}** total results ready to save")
        with col_save2:
            check_duplicates = st.checkbox("Check for duplicates", value=True, help="Slower but prevents duplicate records")
        
        if st.button("Save All Results to Airtable", type="primary", use_container_width=True):
            if airtable_client:
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(processed, total, created, errors):
                    progress = processed / total if total > 0 else 0
                    progress_bar.progress(progress)
                    status_text.text(f"Processing: {processed}/{total} | Created: {created} | Errors: {errors}")
                
                try:
                    # Get search queries from session state
                    search_queries = st.session_state.get('search_queries', {})
                    
                    # Prepare results with priority from each item
                    # The save_results function will use priority=1 as default,
                    # but we'll ensure each item's priority is preserved
                    results_with_priority = {}
                    for website, items in st.session_state['results'].items():
                        results_with_priority[website] = items
                    
                    # Save results (priority from items will be used)
                    stats = airtable_client.save_results(
                        results_with_priority,
                        search_queries=search_queries,
                        priority=1,  # Default, but items have their own priority
                        check_duplicates=check_duplicates,
                        progress_callback=update_progress
                    )
                    
                    # Clear progress
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Show results
                    st.success(f"""
                        **Save Complete!**
                        - **Created:** {stats['created']} records
                        - **Duplicates:** {stats['duplicates']} records (skipped)
                        - **Errors:** {stats['errors']} records
                    """)
                    
                    if stats['created'] > 0:
                        st.info(f"{stats['created']} new records added to Airtable. They will be screened by the LLM screener service.")
                    
                except Exception as e:
                    st.error(f"Error saving to Airtable: {str(e)}")
                    st.exception(e)
            else:
                st.error("Airtable client not initialized. Please check your configuration.")
    else:
        # Show info if Airtable not configured
        with st.expander("Want to save results to Airtable?"):
            st.info("""
            To enable Airtable integration, add these to your Streamlit secrets (`.streamlit/secrets.toml`):
            
            ```toml
            AIRTABLE_TOKEN = "your_airtable_personal_access_token"
            AIRTABLE_BASE_ID = "your_airtable_base_id"
            AIRTABLE_TABLE_NAME = "raw_results"  # Optional, defaults to "raw_results"
            ```
            
            **Note:** Airtable uses Personal Access Tokens (not API keys). 
            Create one at: https://airtable.com/create/tokens
            
            See `Greylitsearcher/README.md` for more details.
            """)
    
    st.divider()
    
    # Display results for each website
    for website in st.session_state['results']:
        cols = st.columns([3, 1])
        with cols[0]:
            st.write(f"### {website}")
            st.write(f"**{len(st.session_state['results'][website])}** results")
        with cols[1]:
            df = pd.DataFrame(st.session_state['results'][website])
            csv = df.to_csv(index=False)
            btn = st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"{website.replace('.', '_')}_results.csv",
                mime="text/csv",
                key=f"download_{website}"
            )
        
        st.dataframe(
            st.session_state['results'][website],
            use_container_width=True,
            hide_index=True
        )
        
        if limitExceeded:
            st.warning('Rate limit exceeded. Please try again later.')
