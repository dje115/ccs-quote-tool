# Lead Generation - Final Configuration

## Critical Rules
1. **ONLY GPT-5 MODELS**: Never use GPT-4, gpt-4o, gpt-4o-mini, or any GPT-4 variants
2. **Models allowed**: gpt-5, gpt-5-mini
3. **Web Search**: GPT-5-mini has web search capability via Responses API

## Current Configuration

### Primary Method: GPT-5-mini with Web Search
```python
model="gpt-5-mini"
tools=[{"type": "web_search_preview"}]
API: responses.create()
```

### Fallback Method: GPT-5 Chat Completions
```python
model="gpt-5"
API: chat.completions.create()
max_completion_tokens=4000
```

## What Was Fixed

### 1. Button State Issue
**Problem**: "Running Campaign..." button state was lost during page reload
**Solution**: 
- Campaign status set to RUNNING immediately after starting
- Status committed to database before long-running AI operation
- Button shows spinner during entire operation

### 2. Company Registration Removed
**Problem**: Requiring Companies House registration in initial search was slowing down and limiting results
**Solution**:
- Removed `company_registration` from required schema fields
- Removed from prompt instructions
- Can be fetched later during AI analysis of individual leads
- Makes initial lead generation faster and more flexible

## Schema Changes

### Before:
```json
{
  "company_registration": {"type": ["string", "null"]},
  "required": ["company_name", "website", "description", "address", "postcode", "lead_score"]
}
```

### After:
```json
{
  // company_registration removed
  "required": ["company_name", "website", "description", "postcode", "lead_score"]
}
```

## Prompt Changes

### Before:
```
- Find their Companies House registration number if possible
- Each business MUST be registered with Companies House
```

### After:
```
- Get their actual postcode from their website contact page
- Provide lead score (60-95) based on how good a prospect they are
```

## Business Type Filtering

### IT/MSP Expansion Campaign
**MUST INCLUDE:**
- ✓ IT Support Companies (MSP/Break-fix)
- ✓ Managed Service Providers
- ✓ Computer Repair Shops
- ✓ IT Consultancies
- ✓ Software Development Companies
- ✓ Web Design/Development Agencies
- ✓ Technology Resellers
- ✓ Network Support Companies
- ✓ Cybersecurity Firms

**MUST EXCLUDE:**
- ✗ Universities or Schools
- ✗ Hospitals or Healthcare
- ✗ Shopping Centers or Retail Stores
- ✗ Councils or Government Buildings
- ✗ Hotels or Hospitality
- ✗ Theatres or Entertainment Venues
- ✗ Libraries or Museums

## User Experience Flow

### 1. Click "Run Campaign"
```
Button changes to: "🔄 Running Campaign..."
Button becomes disabled
```

### 2. Campaign Starts
```
Status → RUNNING
Database committed
User can see campaign is in progress
```

### 3. AI Processing (1-3 minutes)
```
GPT-5-mini performs web search
Finds real UK IT/MSP businesses
Extracts contact information
Scores each lead
```

### 4. Completion
```
Page auto-refreshes
Shows: "Campaign completed successfully!"
Displays: X leads found, Y created
Status → COMPLETED
```

## Expected Results

### Good Campaign Run:
- **Time**: 1-3 minutes
- **Results**: 10-30 real IT/MSP businesses
- **Quality**: Actual UK companies with websites
- **Data**: Company name, website, postcode, phone, email
- **Scoring**: Lead scores 60-95 based on fit

### What to Verify:
1. ✅ All businesses are IT/MSP related
2. ✅ All have UK postcodes
3. ✅ Websites exist and are accessible
4. ✅ Contact information looks realistic
5. ✅ Lead scores are reasonable (60-95 range)

## Next Steps After Lead Generation

### 1. Review Leads
- Check lead list
- Verify business types are correct
- Look at lead scores

### 2. Convert to CRM
- Select high-scoring leads
- Click "Convert to Customer/Prospect"
- AI analysis will fetch Companies House data at this point
- Director information will be populated
- Financial data will be added

### 3. Follow Up
- Use contact information for outreach
- Track interactions
- Update lead status

## Performance Optimization

### Speed:
- ✅ Removed Companies House requirement (faster)
- ✅ Using gpt-5-mini (faster than gpt-5)
- ✅ Web search enabled (better results)
- ✅ Simplified schema (less processing)

### Quality:
- ✅ Clear business type requirements
- ✅ Explicit exclusion list
- ✅ Lead scoring included
- ✅ Source URLs for verification

## Troubleshooting

### No Leads Found:
- Postcode too specific → Try broader area (LE vs LE1)
- Distance too small → Increase to 30+ miles
- Wrong campaign type → Use IT/MSP expansion

### Wrong Business Types:
- Check terminal logs
- Verify GPT-5-mini is being used
- Check prompt includes exclusion list

### Slow Performance:
- Normal for 1-3 minutes
- Watch terminal for progress
- Don't click button multiple times

Last Updated: 2025-10-07


