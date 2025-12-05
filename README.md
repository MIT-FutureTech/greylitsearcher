# Greylitsearcher

A Streamlit-based web application for finding grey literature on the web using Google Custom Search API. Greylitsearcher helps researchers discover and collect relevant documents from specific websites with advanced search capabilities.

## Overview

Greylitsearcher is designed to systematically search for grey literature (reports, white papers, technical documents, etc.) across multiple websites. It supports up to three priority-based search queries per website and can retrieve up to 40 results per site, making it ideal for comprehensive literature reviews and research data collection.

## Features

- **Multi-Query Search**: Up to 3 different search queries with priority levels (1-3)
- **Multi-Website Support**: Search across multiple websites simultaneously
- **Advanced Search Options**:
  - All these words (AND operator)
  - Exact phrase matching
  - Any of these words (OR operator)
  - Exclude words (NOT operator)
- **Rate Limit Handling**: Automatic fallback across multiple Google Search API keys
- **CSV Export**: Download search results as CSV files
- **Airtable Integration**: Optional integration to send results directly to Airtable via data processor
- **Priority-Based Results**: Results are tagged with priority levels for easy filtering

## Requirements

- Python 3.8+
- Google Custom Search API keys (at least 1, recommended 3 for rate limit handling)
- Google Custom Search Engine IDs (CX)

## Installation

1. **Clone or navigate to the Greylitsearcher directory:**
```bash
cd Greylitsearcher
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up Google Custom Search API:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Custom Search API
   - Create API keys (recommended: 3 keys for rate limit handling)
   - Create Custom Search Engines at [Google Programmable Search](https://programmablesearchengine.google.com/)
   - Note your Search Engine IDs (CX)

4. **Configure Streamlit secrets:**
   
   Create a `.streamlit/secrets.toml` file in your project root:
```toml
# App Password (required for access)
APP_PASSWORD = "your_secure_password_here"

# Google Custom Search API
GS1_CX = "your_search_engine_id_1"
GS1_KEY = "your_google_api_key_1"
GS2_KEY = "your_google_api_key_2"
GS3_KEY = "your_google_api_key_3"

# Airtable Integration (optional)
AIRTABLE_TOKEN = "your_airtable_personal_access_token"
AIRTABLE_BASE_ID = "your_base_id"
AIRTABLE_TABLE_NAME = "raw_results"  # Optional: table name or table ID
```

   **Note:** The `.streamlit` directory should be in your project root, and `secrets.toml` should not be committed to git (add it to `.gitignore`).

   Or if using Streamlit Cloud, add these as secrets in your app settings.

## Usage

### Running the Application

```bash
streamlit run main.py
```

The application will open in your default web browser at `http://localhost:8501`.

### Authentication

When you first open the app, you'll be prompted to enter a password. This password is set in your `secrets.toml` file as `APP_PASSWORD`. Once authenticated, you can use the app normally. A logout button is available in the sidebar if you need to log out.

### Basic Workflow

1. **Configure Search Queries:**
   - **Search 1** (Priority 1): Primary search query (expanded by default)
   - **Search 2** (Priority 2): Secondary search query (optional)
   - **Search 3** (Priority 3): Tertiary search query (optional)

2. **Enter Websites:**
   - Add one website per line in the "Websites to search" text area
   - Example:
     ```
     example.com
     another-site.org
     research-institute.edu
     ```

3. **Execute Search:**
   - Click the "Search" button
   - The application will:
     - First try Search 1 queries (up to 4 pages = 40 results)
     - If fewer than 40 results, try Search 2 queries (up to 8 pages)
     - If still fewer than 40 results, try Search 3 queries (up to 10 pages)
     - Automatically deduplicate results by URL

4. **View and Export Results:**
   - Results are displayed in an interactive table
   - Download results as CSV using the download button
   - Each website's results are shown separately

### Search Query Options

Each search query supports four types of search terms:

- **All these words**: Documents must contain all specified terms (AND)
- **This exact word or phrase**: Documents must contain the exact phrase
- **Any of these words**: Documents must contain at least one term (OR)
- **None of these words**: Documents must not contain these terms (NOT)

### Priority System

Results are automatically tagged with priority levels:
- **Priority 1**: Results from Search 1 queries
- **Priority 2**: Results from Search 2 queries
- **Priority 3**: Results from Search 3 queries

This helps you identify which search strategy found each result.

## Airtable Integration

Greylitsearcher uses direct Airtable integration to save search results. The integration is built into the app and works automatically once configured.

### Setup

1. **Create an Airtable Personal Access Token:**
   - Go to [Airtable Account Settings](https://airtable.com/create/tokens)
   - Click "Create new token"
   - Give it a name (e.g., "Greylitsearcher")
   - Grant the following scopes:
     - `data.records:read`
     - `data.records:write`
   - Grant access to your base
   - Copy the token

2. **Get your Airtable Base ID and Table ID/Name:**
   - Open your Airtable base
   - Go to [Airtable API Documentation](https://airtable.com/api)
   - Select your base
   - The Base ID is shown at the top (starts with `app...`)
   - You can use either:
     - **Table Name**: The display name of your table (e.g., "raw_results")
     - **Table ID**: The unique identifier (starts with `tbl...`) - more reliable if table name might change

3. **Add credentials to Streamlit secrets:**
   
   Create or edit `.streamlit/secrets.toml`:
```toml
AIRTABLE_TOKEN = "your_personal_access_token"
AIRTABLE_BASE_ID = "your_base_id"  # e.g., "appHrhJQHkZz4c82U"
AIRTABLE_TABLE_NAME = "raw_results"  # Optional: table name or table ID (e.g., "tblb9eEVPpV4Qqo4u")
```

   Or if using Streamlit Cloud, add these as secrets in your app settings.

### Airtable Table Schema

Your Airtable table should have the following fields:

**Required Fields (must exist):**
- `title` - Single line text
- `link` - URL

**Optional Fields (will be populated if they exist):**
- `snippet` - Long text
- `source_domain` - Single line text
- `search_query` - Single line text
- `priority` - Number (1, 2, or 3)
- `scraped_at` - Date (date only, no time)
- `status` - Single select (must include "Todo" as an option)

**Note:** Field names are case-sensitive and must match exactly (lowercase with underscores).

### Usage

Once configured, the app will automatically show a "Save All Results to Airtable" button after you perform a search. The integration:

- ✅ Saves all search results to Airtable
- ✅ Checks for duplicates (optional, can be toggled)
- ✅ Preserves priority levels (1, 2, 3)
- ✅ Tracks search queries
- ✅ Shows real-time progress during save
- ✅ Provides detailed statistics (created, duplicates, errors)
- ✅ Sets status to "Todo" for new records
- ✅ Sets scraped_at to current date (YYYY-MM-DD format)
- ✅ Handles rate limiting (5 requests/second)

### Data Format

Records are saved with the following structure:
- `title`: Document title from search results
- `link`: Full URL to the document
- `snippet`: Search result snippet/description
- `source_domain`: Extracted domain from URL
- `search_query`: The search query that found this result
- `priority`: Priority level (1, 2, or 3)
- `scraped_at`: Current date in YYYY-MM-DD format
- `status`: Set to "Todo"

### Alternative: Using Data Processor Service

If you prefer to use the data processor service instead of direct integration, see `airtable_integration.py` for the processor-based approach.

## API Rate Limits

### Google Custom Search API Limits

- **Free tier**: 100 queries per day per API key
- **Paid tier**: Up to 10,000 queries per day per API key

### Rate Limit Handling

Greylitsearcher automatically handles rate limits by:
1. Trying the first API key
2. If rate limited, trying the second key
3. If rate limited, trying the third key
4. If all keys are exhausted, displaying an error message

**Recommendation**: Use 3 API keys to maximize daily query capacity.

### Best Practices

- Start with fewer websites to test your setup
- Monitor your API usage in Google Cloud Console
- Consider scheduling searches during off-peak hours
- Use multiple API keys for higher volume searches

## Result Format

Each search result contains:
- `title`: Document title
- `link`: URL to the document
- `snippet`: Brief description/snippet
- `priority`: Priority level (1, 2, or 3)
- Additional Google Search API metadata

## Troubleshooting

### "All keys have exceeded the rate limit"

**Solution**: 
- Wait 24 hours for daily limits to reset
- Upgrade to paid Google API tier
- Add more API keys
- Reduce the number of websites or search queries

### No results returned

**Possible causes**:
- Search query too specific
- Website doesn't have matching content
- Google Search Engine not indexing the website
- API key or CX incorrect

**Solution**:
- Try broader search terms
- Verify website is accessible and indexed by Google
- Check API keys and CX values in secrets

### Streamlit secrets not loading

**Solution**:
- Ensure `.streamlit/secrets.toml` exists in project root
- For Streamlit Cloud, add secrets via app settings
- Restart Streamlit after changing secrets

### Password authentication issues

**Solution**:
- Ensure `APP_PASSWORD` is set in your `secrets.toml` file
- Password is case-sensitive
- If you forget the password, check your `secrets.toml` file
- To log out, use the logout button in the sidebar
- After changing the password in secrets, restart Streamlit

### Connection errors with Airtable integration

**Solution**:
- Verify Airtable token is valid and not expired
- Check Base ID is correct (starts with `app...`)
- Ensure table name or table ID matches your Airtable table
- Verify token has `data.records:read` and `data.records:write` scopes
- Check token has access to the base
- Verify Airtable API rate limits (5 requests/second)
- Ensure `status` field has "Todo" as a select option
- Ensure `scraped_at` field is a Date field (not Date with time)

### "INVALID_VALUE_FOR_COLUMN" error for scraped_at

**Solution**:
- Ensure `scraped_at` field in Airtable is a Date field (not Date with time)
- The field should accept date format: YYYY-MM-DD

### "INVALID_MULTIPLE_CHOICE_OPTIONS" error for status

**Solution**:
- Ensure your `status` field in Airtable has "Todo" as one of the select options
- You cannot create new select options via API without proper permissions
- Add "Todo" as an option in your Airtable table settings

## Project Structure

```
Greylitsearcher/
├── main.py                        # Main Streamlit application
├── direct_airtable_integration.py  # Direct Airtable integration (default, built-in)
├── airtable_integration.py         # Processor-based integration (optional alternative)
├── requirements.txt                # Python dependencies
├── .streamlit/
│   └── secrets.toml               # Configuration file (not in git)
└── README.md                       # This file
```

## Dependencies

- `streamlit==1.31.0` - Web application framework
- `requests==2.31.0` - HTTP library for API calls
- `pandas` - Data manipulation and CSV export
- `beautifulsoup4==4.12.3` - HTML parsing (for future enhancements)
- `pyairtable>=2.3.0` - Airtable API client for direct integration

## Future Enhancements

Potential improvements:
- [ ] Save search configurations for reuse
- [ ] Export to other formats (JSON, Excel)
- [ ] Content extraction from result URLs
- [ ] Scheduled/automated searches
- [ ] Search history and saved results
- [ ] Advanced filtering options
- [ ] Batch processing for large-scale searches

## Integration with Data Pipeline

Greylitsearcher is part of a larger data pipeline system:

```
Greylitsearcher → Data Processor → Airtable → LLM Screener → Human Review → Vector DB → Chatbot
```

See `../ARCHITECTURE.md` for the complete system architecture.

## License

[Add your license here]

## Support

For issues or questions:
1. Check this README for common solutions
2. Review Google Custom Search API documentation
3. Check Streamlit documentation for UI issues
4. See `../ARCHITECTURE.md` for system integration questions

## Contributing

[Add contribution guidelines if applicable]

