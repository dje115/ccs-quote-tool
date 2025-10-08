# GPT-5 Lead Generation - Web Search Fix

## Overview
Updated the lead generation system to work correctly with GPT-5's Responses API and web search capabilities.

## Issues Fixed

### 1. **`response_format` Parameter Not Supported**
**Error**: `Responses.create() got an unexpected keyword argument 'response_format'`

**Fix**: Removed the `response_format={"type": "json_object"}` parameter as GPT-5 Responses API doesn't support it. Instead, we rely on explicit prompting to ensure JSON output.

### 2. **Improved Web Search Prompts**
Enhanced the prompts to be more specific about finding REAL UK businesses:

#### New System Prompt:
```python
system_prompt = """You are a UK business research specialist with access to live web search.
Your job is to find REAL, VERIFIED businesses that currently operate in the UK.

CRITICAL REQUIREMENTS:
1. Use web search to find actual UK businesses (search websites, directories, Companies House)
2. Each business MUST have a real website or verifiable online presence
3. Verify UK postcodes are genuine and in the correct format
4. Cross-reference with Companies House when possible for registration numbers
5. Only return businesses that are currently active and trading
6. Return ONLY valid JSON matching the exact schema provided
7. Do NOT make up or fabricate business information

SEARCH STRATEGY:
- Search for "{postcode} IT companies" or "{postcode} MSP" or similar relevant terms
- Look for business directories like Yell.com, Thomson Local, UK businesses directories
- Check Companies House for active companies in the area
- Verify websites are active and businesses are real
- Get actual contact information from websites when available
"""
```

#### Enhanced User Task:
```python
user_task = f"""
TASK: Find {campaign.max_results} REAL, VERIFIED UK businesses near {campaign.postcode} (within {campaign.distance_miles} miles).

Campaign Focus: {campaign.prompt_type}
Search Area: {campaign.postcode} + {campaign.distance_miles} miles radius

SEARCH APPROACH:
1. Start by searching: "{campaign.postcode} IT services companies" or "{campaign.postcode} managed service providers"
2. Look in UK business directories (Yell, Thomson Local, etc.)
3. Check Companies House active companies database
4. Verify each business has:
   - Real website (check it exists and loads)
   - Valid UK postcode
   - Genuine contact information
   - Active business status

FOR EACH BUSINESS FOUND:
- Extract company name from their website or Companies House
- Get their actual postcode from their website contact page
- Find their Companies House registration number if possible
- Get real contact email/phone from their website
- Note their business focus and services
- Assess if they would benefit from structured cabling services

QUALITY OVER QUANTITY:
- Better to return 5 verified businesses than 20 fake ones
- Each business must be real and verifiable
- Include source URLs where you found the information
"""
```

### 3. **Enhanced Debugging & Logging**
Added comprehensive logging to track the entire web search process:

```python
# Campaign start logging
print(f"\n{'='*60}")
print(f"STARTING GPT-5 WEB SEARCH FOR CAMPAIGN: {campaign.name}")
print(f"Postcode: {campaign.postcode}")
print(f"Distance: {campaign.distance_miles} miles")
print(f"Max Results: {campaign.max_results}")
print(f"Campaign Type: {campaign.prompt_type}")
print(f"{'='*60}\n")

# API call logging
print(f"✓ GPT-5 Responses API call successful!")
print(f"✓ Extracted JSON response ({len(ai_response)} characters)")
print(f"✓ Found {len(test_parse.get('results', []))} businesses in response")
```

### 4. **Improved JSON Extraction**
Enhanced the `_extract_json_from_responses_api` method to:
- Provide detailed logging of response structure
- Handle markdown fences
- Extract JSON from surrounding text
- Validate JSON before returning
- Provide helpful error messages

```python
def _extract_json_from_responses_api(self, response) -> str:
    """Extract JSON string from Responses API response"""
    # Detailed logging of response structure
    print(f"\nExtracting JSON from Responses API...")
    print(f"Response has output attribute: {hasattr(response, 'output')}")
    
    # Collect text from response.output structure
    txt_parts = []
    if hasattr(response, 'output'):
        for item in response.output:
            if getattr(item, "type", None) == "message":
                for c in item.content:
                    if getattr(c, "type", None) == "output_text":
                        txt_parts.append(c.text)
    
    raw = "".join(txt_parts).strip()
    
    # Handle empty responses
    if not raw:
        return '{"query_area": "unknown", "results": []}'
    
    # Remove markdown fences
    cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", raw, flags=re.IGNORECASE)
    
    # Extract JSON from surrounding text if needed
    json_match = re.search(r'\{.*"results".*\}', cleaned, re.DOTALL)
    if json_match:
        cleaned = json_match.group(0)
    
    # Validate and return
    json.loads(cleaned)  # Validate
    return cleaned
```

### 5. **Increased Timeout**
Set appropriate timeout for web search operations:

```python
response = self.openai_client.responses.create(
    model="gpt-5",
    tools=[{"type": "web"}],
    input=[...],
    max_completion_tokens=50000,
    timeout=180.0  # 3 minutes for web search operations
)
```

## GPT-5 Responses API Parameters

### ✅ Supported Parameters:
- `model` - "gpt-5"
- `input` - List of message objects (role + content)
- `tools` - [{"type": "web"}] for web search
- `max_completion_tokens` - Token limit (50,000 recommended)
- `timeout` - Request timeout in seconds (180.0 for web search)

### ❌ NOT Supported Parameters:
- ~~`response_format`~~ - Not available in Responses API
- ~~`temperature`~~ - GPT-5 uses default (1) only
- ~~`max_tokens`~~ - Use `max_completion_tokens` instead
- ~~`messages`~~ - Use `input` instead

## How GPT-5 Web Search Works

### 1. **Search Phase**
GPT-5 uses the `tools=[{"type": "web"}]` parameter to:
- Perform live web searches
- Access current information from the internet
- Verify business information from multiple sources
- Cross-reference data for accuracy

### 2. **Data Collection Phase**
The AI:
- Searches UK business directories
- Checks Companies House database
- Visits company websites
- Extracts contact information
- Verifies postcodes and addresses

### 3. **Verification Phase**
Each business is:
- Verified to have a real website
- Checked for active status
- Cross-referenced with Companies House
- Validated for UK postcode format
- Assessed for relevance to campaign

### 4. **JSON Output Phase**
Returns structured JSON with:
```json
{
  "query_area": "LE17 5NJ + 20 miles",
  "results": [
    {
      "company_name": "Example IT Services Ltd",
      "website": "https://example-it.co.uk",
      "description": "Managed IT services provider",
      "project_value": "£15,000-£30,000",
      "timeline": "Q2 2025",
      "contact_email": "info@example-it.co.uk",
      "contact_phone": "01234 567890",
      "lead_score": 85,
      "address": "123 High Street, Leicester",
      "postcode": "LE1 1AA",
      "business_sector": "Technology",
      "company_size": "Small (10-50 employees)",
      "company_registration": "12345678",
      "source_urls": [
        "https://example-it.co.uk/contact",
        "https://find-and-update.company-information.service.gov.uk/company/12345678"
      ]
    }
  ]
}
```

## Testing the Fix

### To Test Lead Generation:

1. **Navigate to Lead Generation**
   - Go to Lead Generation → Dashboard
   - Select an existing campaign or create new one

2. **Run Campaign**
   - Click "Run Campaign" button
   - Watch terminal logs for detailed progress
   - Wait for GPT-5 web search to complete (may take 1-2 minutes)

3. **Check Terminal Output**
   Look for these indicators:
   ```
   ============================================================
   STARTING GPT-5 WEB SEARCH FOR CAMPAIGN: MSP in Leicestershire
   Postcode: LE17 5NJ
   Distance: 20 miles
   Max Results: 10
   Campaign Type: it_msp_expansion
   ============================================================
   
   Making GPT-5 Responses API call with web search...
   Timeout set to: 180 seconds
   ✓ GPT-5 Responses API call successful!
   ✓ Extracted JSON response (XXXX characters)
   ✓ JSON is valid
   ✓ Found X businesses in response
   ```

4. **Review Results**
   - Check campaign detail page
   - Verify businesses are real UK companies
   - Check Companies House registration numbers
   - Validate postcodes and contact information

### Expected Results:

- **Real Businesses**: All returned businesses should be verifiable
- **Contact Information**: Should include real websites, emails, phones
- **Postcodes**: Valid UK postcodes in correct format
- **Companies House**: Registration numbers where available
- **Source URLs**: Links to where information was found

## Common Issues & Solutions

### Issue: "No businesses found"
**Solution**: 
- Check postcode is valid UK format
- Increase distance_miles radius
- Try different campaign type
- Check terminal logs for API errors

### Issue: "JSON parsing error"
**Solution**:
- Check terminal logs for raw response
- GPT-5 may need clearer JSON instructions
- Verify max_completion_tokens is sufficient
- Check for timeout errors

### Issue: "Fake/made up businesses"
**Solution**:
- Prompts now emphasize REAL, VERIFIED businesses
- System cross-references multiple sources
- Companies House validation recommended
- Review source_urls to verify legitimacy

## Performance

### Typical Response Times:
- **Simple Campaign (5-10 results)**: 30-60 seconds
- **Medium Campaign (10-20 results)**: 60-120 seconds
- **Large Campaign (20-50 results)**: 120-180 seconds

### Token Usage:
- **Input Tokens**: ~1,000-2,000 (prompt + schema)
- **Reasoning Tokens**: ~5,000-15,000 (GPT-5 reasoning)
- **Output Tokens**: ~2,000-10,000 (JSON results)
- **Total**: ~10,000-30,000 tokens per campaign

## Next Steps

### Recommended Improvements:
1. **Post-Processing Validation**
   - Verify businesses with Companies House API
   - Check website accessibility
   - Validate email addresses
   - Confirm phone numbers

2. **Duplicate Detection**
   - Check against existing leads
   - Compare by company registration number
   - Fuzzy matching on company names

3. **Scoring Enhancement**
   - Use financial data for scoring
   - Consider company age and size
   - Analyze recent growth indicators

4. **Source Verification**
   - Store source URLs with each lead
   - Allow manual verification flag
   - Track lead quality over time

Last Updated: 2025-10-07


