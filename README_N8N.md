# LENR Collection System for n8n

**Automated LENR research paper collection with n8n workflow automation**

This system provides a REST API that n8n can use to automatically collect, process, and manage LENR (Low Energy Nuclear Reaction) research papers.

## 🚀 Quick Start (5 minutes)

### 1. Start the API

```bash
# Clone repository
cd LENR

# Create environment file
echo "DEEPSEEK_API_KEY=sk-your-key-here" > .env

# Start with Docker
docker-compose up -d

# Verify it's running
curl http://localhost:8000/health
```

### 2. Test the API

```bash
# Start a collection job
curl -X POST http://localhost:8000/collect \
  -H "Content-Type: application/json" \
  -d '{
    "sources": ["lenr-canr"],
    "max_papers": 5,
    "deepseek_verify": false
  }'

# Response:
# {
#   "job_id": "abc-123-def",
#   "status": "queued"
# }

# Check job status
curl http://localhost:8000/jobs/abc-123-def

# Query collected papers
curl "http://localhost:8000/papers?limit=10"
```

### 3. Import to n8n

1. Open n8n (http://localhost:5678)
2. Go to **Workflows** → **Import from File**
3. Select `n8n-workflows/collect-papers-workflow.json`
4. Update HTTP Request URLs to: `http://lenr-api:8000`
5. Activate workflow

Done! Papers will be collected daily at 2 AM.

## 📋 What This System Does

1. **Scrapes** LENR papers from:
   - LENR-CANR.org (2,300+ papers)
   - arXiv (physics papers)

2. **Downloads** PDFs with progress tracking

3. **Processes** PDFs to extract:
   - Title, authors, abstract
   - Full text content
   - Metadata (DOI, journal, date)

4. **Verifies** relevance using DeepSeek AI (optional)

5. **Stores** in Excel database with duplicate detection

6. **Provides** REST API for n8n automation

## 🔌 n8n Integration Methods

### Method 1: HTTP Request Nodes (Recommended)

Use n8n's built-in HTTP Request node:

```javascript
// Start collection
POST http://lenr-api:8000/collect
Body: {
  "sources": ["lenr-canr"],
  "max_papers": 10
}

// Query papers
GET http://lenr-api:8000/papers?author=Storms
```

### Method 2: Execute Command (CLI)

Use n8n's Execute Command node:

```bash
# Collect papers
python /app/cli.py collect --sources lenr-canr --max-papers 10

# Query papers
python /app/cli.py query --author "Storms" --output-format json

# Get statistics
python /app/cli.py stats
```

### Method 3: Webhook Integration

The API can call n8n webhooks when jobs complete:

```javascript
{
  "sources": ["lenr-canr"],
  "max_papers": 10,
  "webhook_url": "https://your-n8n.com/webhook/completion"
}
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/collect` | POST | Start collection job |
| `/jobs/{id}` | GET | Get job status |
| `/jobs` | GET | List all jobs |
| `/papers` | GET | Query papers |
| `/statistics` | GET | Get database stats |
| `/export` | GET | Export database |

Full documentation: http://localhost:8000/docs

## 🔧 Configuration

Configure via environment variables:

```bash
# .env file
DEEPSEEK_API_KEY=sk-your-key-here  # Optional
EXCEL_PATH=lenr_papers.xlsx
PDF_DIR=pdfs
MAX_PAPERS_PER_RUN=50
```

Or in `docker-compose.yml`:

```yaml
environment:
  - DEEPSEEK_API_KEY=sk-your-key
  - MAX_PAPERS_PER_RUN=50
```

## 📖 n8n Workflow Examples

### Example 1: Daily Collection

**Schedule Trigger** → **HTTP Request (POST /collect)** → **Wait** → **HTTP Request (GET /jobs/{id})** → **IF (completed?)** → **Send Email**

Import: `n8n-workflows/collect-papers-workflow.json`

### Example 2: Query on Demand

**Webhook** → **HTTP Request (GET /papers)** → **Respond to Webhook**

Import: `n8n-workflows/query-papers-webhook.json`

### Example 3: Weekly Report

**Schedule (Monday 9 AM)** → **HTTP Request (GET /statistics)** → **HTTP Request (GET /papers?min_score=0.8)** → **Format Email** → **Send Email**

### Example 4: Export to Google Sheets

**Schedule** → **HTTP Request (GET /papers)** → **Split in Batches** → **Google Sheets (Append)**

## 🐳 Docker Deployment

### Single Container

```bash
docker build -t lenr-api .
docker run -p 8000:8000 \
  -e DEEPSEEK_API_KEY=sk-your-key \
  -v $(pwd)/data:/data \
  lenr-api
```

### With n8n (docker-compose)

```bash
# Start both n8n and LENR API
docker-compose up -d

# Access
# n8n: http://localhost:5678
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

## 🔍 Querying Papers

### From n8n HTTP Request

```javascript
{
  "method": "GET",
  "url": "http://lenr-api:8000/papers",
  "qs": {
    "author": "Storms",
    "min_score": 0.8,
    "limit": 10
  }
}
```

### From CLI

```bash
# By author
python cli.py query --author "Storms" --output-format json

# High-score papers
python cli.py query --min-score 0.8 --output-format json

# By source
python cli.py query --source "arXiv" --limit 20
```

### Response Format

```json
{
  "total": 3,
  "papers": [
    {
      "Title": "Anomalous Heat in Palladium",
      "Authors": "Edmund Storms",
      "DeepSeek_Score": 0.95,
      "Source": "LENR-CANR",
      "URL": "https://...",
      "PDF_Path": "pdfs/...",
      "Abstract": "...",
      "Date_Published": "2010-05-15"
    }
  ]
}
```

## 📤 Exporting Data

### To CSV

```bash
curl "http://localhost:8000/export?format=csv" -o papers.csv
```

### To JSON

```bash
curl "http://localhost:8000/export?format=json" -o papers.json
```

### To Excel

```bash
curl "http://localhost:8000/export?format=excel" -o papers.xlsx
```

### From n8n

Use HTTP Request node with `responseType: file`

## 🧪 Testing

### Postman Collection

Import `LENR-API.postman_collection.json` to Postman

### cURL Examples

```bash
# Health check
curl http://localhost:8000/health

# Start small collection
curl -X POST http://localhost:8000/collect \
  -H "Content-Type: application/json" \
  -d '{"sources": ["lenr-canr"], "max_papers": 3}'

# Get statistics
curl http://localhost:8000/statistics

# Query papers
curl "http://localhost:8000/papers?limit=5"
```

## 🐛 Troubleshooting

### API not starting

```bash
# Check logs
docker logs lenr-api

# Common issues:
# - Missing DEEPSEEK_API_KEY (OK if not verifying)
# - Port 8000 already in use
# - Missing dependencies
```

### n8n can't reach API

```bash
# Use Docker service name
http://lenr-api:8000  # ✓ Correct
http://localhost:8000  # ✗ Won't work in Docker network

# Test from n8n container
docker exec n8n curl http://lenr-api:8000/health
```

### Jobs stuck in "queued"

```bash
# Restart API
docker-compose restart lenr-api

# Reduce max_papers
# Use fewer sources
```

### No papers found

```bash
# Check sources are accessible
curl https://lenr-canr.org

# Check database
curl http://localhost:8000/statistics

# Check logs
docker logs lenr-api
```

## 💰 Cost Estimation

### With DeepSeek Verification

- API cost: $0.001 per paper
- 1000 papers = $1
- Storage: ~100MB per 1000 papers

### Without Verification

- No API costs
- Just storage: ~100MB per 1000 papers

## 🔒 Security

### Production Deployment

1. **Enable authentication**:
   ```yaml
   environment:
     - API_KEY=your-secret-key
   ```

2. **Use HTTPS**:
   - Deploy behind nginx/Caddy
   - Use Let's Encrypt SSL

3. **Limit access**:
   - Firewall rules
   - VPN only
   - IP whitelist

4. **Secure API keys**:
   - Use Docker secrets
   - Rotate regularly
   - Never commit to git

## 📈 Performance

- **Throughput**: 50-100 papers/hour (with rate limiting)
- **Storage**: ~100KB per paper (PDF + metadata)
- **Memory**: ~500MB during collection
- **CPU**: Low (async I/O)

## 📚 Further Reading

- [Full Documentation](README.md)
- [n8n Integration Guide](N8N_INTEGRATION.md)
- [API Documentation](http://localhost:8000/docs)
- [Quick Start Guide](QUICKSTART.md)

## 🆘 Support

- **API Issues**: Check `/logs/` directory
- **n8n Issues**: n8n community forum
- **Integration Help**: See workflow examples

## 📝 License

MIT License - see LICENSE file
