# LENR Collection - Direct n8n Setup (No External Services)

**Get LENR papers directly in n8n - No Python, No API, No Docker needed!**

This guide shows you how to collect LENR research papers using **only n8n's built-in nodes**. Everything runs directly in your n8n instance.

## 🎯 What You'll Get

- ✅ Automatic daily collection of LENR papers
- ✅ Save to Airtable, Google Sheets, or any database
- ✅ No external services required
- ✅ Works in n8n cloud or self-hosted
- ✅ 100% inside n8n

## 🚀 Quick Start (5 Minutes)

### Step 1: Import Workflow

1. Open your n8n instance
2. Click **Workflows** → **Import from File**
3. Select one of these workflows:
   - `lenr-scraper-minimal.json` - **Start here!** (Test & see results)
   - `lenr-to-airtable-complete.json` - Save to Airtable
   - `simple-scraper-google-sheets.json` - Save to Google Sheets

### Step 2: Test It

1. Click **Execute Workflow** button
2. Wait 5-10 seconds
3. See LENR papers appear! 🎉

### Step 3: Configure Storage (Optional)

Choose where to save papers:

#### Option A: Airtable (Easiest)

1. Create free Airtable account: https://airtable.com
2. Create a base called "LENR Papers"
3. Add table with columns:
   - Title (Single line text)
   - Authors (Long text)
   - Date (Date)
   - Journal (Single line text)
   - URL (URL)
   - Source (Single select)
   - Date Added (Date)
4. In n8n:
   - Add Airtable credential
   - Update workflow with your Base ID and Table ID
5. Done!

#### Option B: Google Sheets

1. Create Google Sheet with headers:
   ```
   Title | Authors | Date | Journal | URL | Source | Date Added
   ```
2. Share with your n8n Google account
3. In n8n:
   - Add Google Sheets credential
   - Update workflow with Sheet ID
4. Done!

#### Option C: Notion

1. Create Notion database
2. Add Notion integration
3. Use Notion node in n8n

#### Option D: Local Database

Use n8n's SQLite, PostgreSQL, or MySQL nodes

## 📋 Workflow Explanation

### Workflow 1: Minimal Tester

```
Manual Trigger
  ↓
HTTP Request (Get LENR-CANR page)
  ↓
Code (Parse HTML → Extract papers)
  ↓
Show Results
```

**What it does:**
- Fetches LENR-CANR library page
- Parses HTML to extract paper info
- Shows you the first 10 papers

**Use this to:** Test and see what data you get

### Workflow 2: Airtable Auto-Collector

```
Schedule (Daily at 2 AM)
  ↓
HTTP Request (Get LENR-CANR page)
  ↓
Code (Parse HTML)
  ↓
Check if paper exists in Airtable
  ↓
IF new → Add to Airtable
  ↓
Rate limit (2 second delay)
  ↓
Loop to next paper
```

**What it does:**
- Runs every night at 2 AM
- Collects new LENR papers
- Checks for duplicates
- Saves to Airtable automatically

**Use this for:** Production automation

## 🔧 Customization

### Change How Many Papers to Collect

In the "Parse Papers" Code node:

```javascript
// Find this line at the end:
return papers.slice(0, 20).map(p => ({ json: p }));

// Change 20 to any number:
return papers.slice(0, 100).map(p => ({ json: p }));  // Get 100 papers
```

### Change Schedule

In the Schedule Trigger node:

```javascript
// Daily at 2 AM
"0 2 * * *"

// Every 6 hours
"0 */6 * * *"

// Weekly on Monday at 9 AM
"0 9 * * 1"
```

### Add More Sources

After the LENR-CANR scraper, add another HTTP Request node for arXiv:

```
HTTP Request
URL: https://export.arxiv.org/api/query?search_query=all:LENR&max_results=100
```

Then parse the XML response.

## 🎨 Example Workflows

### Example 1: Simple Collector

**Goal:** Get papers and see them

```javascript
// Manual Trigger → HTTP Request → Code → Respond

// Code node:
const html = $input.item.json.data;
// ... parsing code ...
return papers.slice(0, 10).map(p => ({ json: p }));
```

**Try it:** Import `lenr-scraper-minimal.json`

### Example 2: Save to Spreadsheet

**Goal:** Auto-collect to Google Sheets

```
Schedule → HTTP Request → Parse → Google Sheets (Append)
```

**Try it:** Import `simple-scraper-google-sheets.json`

### Example 3: Advanced with Deduplication

**Goal:** Smart collection with duplicate checking

```
Schedule → HTTP Request → Parse → Check Airtable → IF new → Add to Airtable
```

**Try it:** Import `lenr-to-airtable-complete.json`

### Example 4: With Email Notifications

**Goal:** Get notified when new papers are found

```
Schedule → Scrape → Parse → Airtable → Send Email Summary
```

Add an Email node at the end:

```javascript
Subject: {{ $json.length }} new LENR papers collected
Body: Papers added today:
{{ $json.map(p => `- ${p.Title} by ${p.Authors}`).join('\n') }}
```

## 🔍 Understanding the Code Node

The Code node parses the LENR-CANR HTML page. Here's how it works:

```javascript
// Get the HTML
const html = $input.item.json.data;

// Find table rows with regex
const rowRegex = /<tr[^>]*>(.*?)<\/tr>/gis;

// For each row...
while ((match = rowRegex.exec(html)) !== null) {
  // Extract cells
  const cells = [];
  const cellRegex = /<td[^>]*>(.*?)<\/td>/gis;

  // Get cell text
  while ((cellMatch = cellRegex.exec(row)) !== null) {
    const text = cellMatch[1].replace(/<[^>]*>/g, '').trim();
    cells.push(text);
  }

  // Extract PDF URL
  const urlMatch = row.match(/href=["'](.*?\.pdf)["']/i);
  let pdfUrl = urlMatch ? urlMatch[1] : '';

  // Build paper object
  papers.push({
    Title: cells[5],
    Authors: cells[4],
    Date: cells[2],
    Journal: cells[6],
    URL: pdfUrl,
    Source: 'LENR-CANR'
  });
}

// Return papers
return papers.map(p => ({ json: p }));
```

**You can modify this to:**
- Extract different fields
- Filter papers (by date, author, etc.)
- Format data differently

## 📊 Data Structure

Each paper has these fields:

```javascript
{
  "Title": "Anomalous Heat in Palladium",
  "Authors": "Edmund Storms",
  "Date": "2010-05-15",
  "Journal": "Journal of CMNS",
  "URL": "https://lenr-canr.org/acrobat/StormsEanomalousb.pdf",
  "Source": "LENR-CANR",
  "Recnum": "1234",
  "Date Added": "2025-11-08"
}
```

## 🛠️ Troubleshooting

### "Cannot read property 'data' of undefined"

**Fix:** The HTTP Request node isn't returning data

1. Check URL is correct
2. Add `.data` to access response: `$input.item.json.data`
3. Try "Response Format: text" in HTTP Request options

### "No papers found"

**Fix:** LENR-CANR website might have changed

1. Open https://lenr-canr.org/wordpress/?page_id=3009 in browser
2. View page source
3. Update the parsing regex in Code node

### "Airtable/Google Sheets error"

**Fix:** Check credentials

1. Verify API key is correct
2. Check base/sheet ID
3. Test with a simple write operation first

### "Workflow too slow"

**Fix:** Reduce number of papers

```javascript
// Change from:
return papers.map(p => ({ json: p }));

// To:
return papers.slice(0, 10).map(p => ({ json: p }));  // Only 10 papers
```

## 🎯 Best Practices

### 1. Start Small

Begin with 10-20 papers, then increase:

```javascript
return papers.slice(0, 10).map(p => ({ json: p }));
```

### 2. Add Rate Limiting

Between Airtable/Sheets writes, add a Wait node (2 seconds)

### 3. Use Duplicate Checking

Always check if paper exists before adding:

```
Airtable Search → IF not found → Airtable Create
```

### 4. Schedule During Off-Peak Hours

Run at 2-6 AM to respect LENR-CANR server:

```javascript
"0 2 * * *"  // 2 AM daily
```

### 5. Handle Errors

Enable "Continue on Fail" for HTTP Request nodes

### 6. Log Results

Add a final node to log statistics:

```javascript
return [{
  json: {
    total_found: $input.all().length,
    total_added: $input.all().filter(p => p.added).length,
    date: new Date().toISOString()
  }
}];
```

## 📈 Scaling Up

### Collect More Sources

Add nodes for:
- arXiv: `https://export.arxiv.org/api/query?search_query=all:LENR`
- JCMNS: Custom scraper
- Google Scholar: Use SerpAPI

### Add AI Verification

Use n8n's AI nodes:

```
Parse Papers → OpenAI (Verify relevance) → Filter by score → Save
```

### Build a Dashboard

Save to database, then:
1. Connect Metabase/Grafana
2. Or build custom web app
3. Or use Airtable's interface builder

## 🆓 Cost

Everything in this guide is **free**:

- ✅ n8n (5 workflows free on cloud, unlimited on self-hosted)
- ✅ Airtable (Free tier: 1,200 records)
- ✅ Google Sheets (Free: unlimited rows)
- ✅ LENR-CANR (Free public access)

**Total cost: $0/month**

## ✅ Checklist

Before going live:

- [ ] Import workflow to n8n
- [ ] Test with "Execute Workflow" button
- [ ] See papers in output
- [ ] Connect Airtable/Sheets
- [ ] Test saving one paper
- [ ] Enable duplicate checking
- [ ] Set schedule (daily at 2 AM)
- [ ] Activate workflow
- [ ] Check next day that it ran

## 📞 Need Help?

**Check these in order:**

1. **Run the minimal workflow first**
   - Import `lenr-scraper-minimal.json`
   - Click "Execute Workflow"
   - See if you get paper data

2. **Check n8n execution logs**
   - Click "Executions" tab
   - Find failed workflows
   - See error messages

3. **Verify HTTP Request works**
   - Test URL in browser first
   - Make sure LENR-CANR is accessible

4. **Test Code node independently**
   - Copy/paste HTML directly
   - Test parsing logic

5. **Ask in n8n community**
   - https://community.n8n.io

## 🎉 You're Ready!

You now have a complete LENR paper collection system running **entirely inside n8n**!

**Quick Start:**
```
1. Import lenr-scraper-minimal.json
2. Click "Execute Workflow"
3. See papers!
```

**Next Steps:**
- Connect to Airtable/Sheets
- Enable scheduling
- Add more sources
- Share with your research team!

---

**No Python. No Docker. No API. Just n8n.** 🚀
