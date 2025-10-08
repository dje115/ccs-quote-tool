# Lead Generation - How to Use & What to Expect

## Overview
The lead generation system uses GPT-5's web search capability to find REAL UK businesses that match your campaign criteria.

## How It Works

### 1. Click "Run Campaign"
When you click the button:
- ✅ Button changes to "Running Campaign..." with spinner
- ✅ Page sends request to server
- ⚠️ **Page will appear to "hang" for 1-3 minutes** - this is NORMAL
- ✅ Watch terminal/console for detailed progress

### 2. GPT-5 Web Search Process (1-3 minutes)
The system performs these steps:

```
============================================================
STARTING GPT-5 WEB SEARCH FOR CAMPAIGN: MSP in Leicestershire
Postcode: LE1
Distance: 20 miles
Max Results: 50
Campaign Type: it_msp_expansion
============================================================

Making GPT-5 Responses API call with web search...
[GPT-5 searches UK business directories, Companies House, websites...]
[This takes 60-180 seconds depending on complexity]

✓ GPT-5 Responses API call successful!
✓ Extracted JSON response (XXXX characters)
✓ JSON is valid
✓ Found X businesses in response
```

### 3. Lead Creation & Deduplication
After GPT-5 returns results:
```
Creating lead: Example IT Ltd
✓ Created lead for Example IT Ltd
Checking for duplicates...
✓ X new leads created
✓ X duplicates skipped
```

### 4. Page Refreshes
- Flash message appears: "Campaign completed successfully!"
- Lead count updates
- Campaign status changes to "COMPLETED"

## Expected Wait Times

### By Campaign Size:
- **Small (5-10 results)**: 30-60 seconds
- **Medium (10-20 results)**: 60-120 seconds  
- **Large (20-50 results)**: 120-180 seconds

### Why So Long?
GPT-5 with web search:
1. Performs multiple web searches
2. Visits business websites
3. Checks Companies House database
4. Extracts and verifies contact information
5. Cross-references multiple sources
6. Formats results as structured JSON

This is REAL web research, not cached data!

## What to Watch in Terminal

### Successful Run:
```
============================================================
STARTING GPT-5 WEB SEARCH
============================================================

Making GPT-5 Responses API call with web search...

✓ GPT-5 Responses API call successful!
✓ Extracted JSON response (12500 characters)
✓ JSON is valid
✓ Found 15 businesses in response

Creating lead: ABC IT Services Ltd
Companies House verification for ABC IT Services Ltd
✓ Created lead for ABC IT Services Ltd

Creating lead: XYZ Technology Ltd  
Companies House verification for XYZ Technology Ltd
✓ Created lead for XYZ Technology Ltd

... [more leads] ...

Campaign completed: 15 found, 12 created, 3 duplicates
```

### If Using Fallback (No Web Search):
```
Responses API failed, falling back to chat completions: ...
Using GPT-5 knowledge base (no live web search)
```

## Common Issues

### Issue: Page "Hangs" or Appears Frozen
**Status**: ✅ NORMAL BEHAVIOR
**Why**: The request is synchronous - browser waits for server response
**Solution**: Be patient, watch terminal logs for progress
**Duration**: 1-3 minutes depending on campaign size

### Issue: "Responses API failed, falling back..."
**Status**: ⚠️ Using fallback method
**Why**: Responses API parameter error or timeout
**Result**: Uses GPT-5 knowledge base instead of live web search
**Quality**: Results may be less accurate/current

### Issue: No leads created (0 results)
**Possible causes**:
1. **Postcode too specific**: Try broader area or increase distance
2. **No matching businesses**: Try different campaign type
3. **API timeout**: Check terminal for error messages
4. **GPT-5 couldn't find verified businesses**: Increase max_results

### Issue: All results are duplicates
**Status**: ✅ Working correctly
**Why**: Businesses already exist in database
**Solution**: 
- Check existing leads before running
- Try different geographic area
- Use different campaign type

## Supported GPT-5 Responses API Parameters

### ✅ What Works:
```python
response = client.responses.create(
    model="gpt-5",
    tools=[{"type": "web"}],
    input=[...messages...]
)
```

### ❌ What Doesn't Work:
- ~~`response_format`~~ - Not supported
- ~~`max_completion_tokens`~~ - Not supported  
- ~~`temperature`~~ - Not supported
- ~~`timeout`~~ - Not supported (use client-level timeout)

## Results Quality

### What You Get:
- ✅ Real UK businesses with verified websites
- ✅ Companies House registration numbers (where found)
- ✅ Actual contact emails and phone numbers
- ✅ Valid UK postcodes
- ✅ Business descriptions and services
- ✅ Source URLs showing where data came from

### What to Verify:
- 📞 Phone numbers (may be outdated)
- 📧 Email addresses (may be generic info@ addresses)
- 💰 Project values (AI estimates)
- 📅 Timelines (AI predictions)

### Red Flags (Fake Results):
- ❌ No website URL
- ❌ Invalid postcode format
- ❌ No source URLs
- ❌ Generic/template company names
- ❌ "Example" or "Sample" in name

## Campaign Types

### it_msp_expansion
Finds IT/MSP businesses that might add cabling services:
- Managed service providers
- IT support companies
- Computer repair shops
- Software companies
- Tech startups

### education  
Finds educational institutions needing infrastructure:
- Schools (primary/secondary)
- Colleges
- Universities
- Training centers

### manufacturing
Finds industrial businesses modernizing:
- Manufacturing facilities
- Production plants
- Engineering companies
- Factory automation

### retail_office
Finds commercial properties needing cabling:
- Retail stores
- Office buildings
- Business centers
- Professional services firms

## Best Practices

### 1. Start Small
- Run campaign with 10-20 max_results first
- Verify quality of results
- Adjust parameters based on results

### 2. Geographic Strategy
- Use specific postcodes for focused search (LE1, LE17)
- Use postcode areas for broader search (LE)
- Increase distance for rural areas (30-50 miles)
- Decrease distance for cities (10-20 miles)

### 3. Campaign Management
- Review results before running again
- Check for duplicates in existing leads
- Try different campaign types for same area
- Use manual generation as backup

### 4. Lead Verification
After campaign completes:
- ✅ Check Companies House registration numbers
- ✅ Visit websites to verify businesses are real
- ✅ Call phone numbers to confirm active
- ✅ Review source URLs for credibility
- ✅ Check lead scores for prioritization

## Manual Generation (Backup Method)

If automatic generation fails:

1. Click "Manual Generation" button
2. Copy the AI prompt shown
3. Paste into ChatGPT, Claude, or Gemini
4. Copy the JSON results
5. Paste back into the application
6. System processes and creates leads

**Benefits**:
- More control over process
- Can use different AI engines
- Can iterate and refine results
- No timeouts or API limits

## Troubleshooting Steps

### If Campaign Fails:

1. **Check Terminal Logs**
   - Look for error messages
   - Check API call status
   - Verify JSON extraction

2. **Verify API Settings**
   - Admin → API Settings
   - Check OpenAI key is valid
   - Test connection

3. **Try Manual Generation**
   - Use as fallback method
   - Verify prompt works in ChatGPT
   - Check JSON format

4. **Reduce Campaign Size**
   - Start with max_results = 10
   - Increase gradually
   - Find optimal size

5. **Check Network**
   - Verify internet connection
   - Check firewall settings
   - Confirm OpenAI API accessible

## Performance Tips

### Speed Up Campaigns:
- ✅ Reduce max_results (10-20 instead of 50)
- ✅ Use specific postcodes (LE1 vs LE)
- ✅ Clear campaign before re-running
- ✅ Run during off-peak hours

### Improve Quality:
- ✅ Be specific in campaign type
- ✅ Use narrower geographic area  
- ✅ Verify with Companies House
- ✅ Review and manually score leads

## Next Steps After Generation

1. **Review Leads**
   - Go to "New Leads" or "All Campaigns"
   - Check lead details
   - Verify information

2. **Convert to CRM**
   - Select quality leads
   - Click "Convert to Customer/Prospect"
   - AI analysis runs automatically

3. **Prioritize Follow-up**
   - Sort by lead score
   - Check project value estimates
   - Review timeline predictions

4. **Track Interactions**
   - Log calls and emails
   - Update lead status
   - Add notes

Last Updated: 2025-10-07


