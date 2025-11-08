# n8n Integration Guide for LENR Collection System

This guide shows how to use the LENR Collection System with n8n workflow automation.

## Quick Start

### 1. Deploy the API

**Option A: Docker Compose (Recommended)**

```bash
# Create .env file
cp .env.example .env
# Edit .env and add your DEEPSEEK_API_KEY

# Start the API
docker-compose up -d

# Check health
curl http://localhost:8000/health
```

**Option B: Direct Python**

```bash
# Install dependencies
pip install -r requirements.txt -r requirements-api.txt

# Set environment variables
export DEEPSEEK_API_KEY="sk-your-key"
export EXCEL_PATH="lenr_papers.xlsx"
export PDF_DIR="pdfs"

# Run API
uvicorn api:app --host 0.0.0.0 --port 8000
```

### 2. Import n8n Workflows

In n8n:
1. Go to **Workflows** → **Import from File**
2. Import workflows from `n8n-workflows/` folder:
   - `collect-papers-workflow.json` - Scheduled daily collection
   - `query-papers-webhook.json` - Query papers via webhook

### 3. Configure Workflows

Update the HTTP Request nodes to point to your API:
- If running locally: `http://localhost:8000`
- If using Docker: `http://lenr-api:8000`
- If deployed elsewhere: `http://your-domain:8000`

## API Endpoints

### Start Collection Job

```bash
POST http://localhost:8000/collect

Body:
{
  "sources": ["lenr-canr", "arxiv"],
  "max_papers": 20,
  "deepseek_verify": true,
  "webhook_url": "https://your-n8n-webhook-url"
}

Response:
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Collection job started",
  "check_status": "/jobs/550e8400-e29b-41d4-a716-446655440000"
}
```

### Check Job Status

```bash
GET http://localhost:8000/jobs/{job_id}

Response:
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": {
    "total": 20,
    "processed": 5,
    "successful": 4,
    "failed": 1
  }
}
```

### Query Papers

```bash
GET http://localhost:8000/papers?author=Storms&min_score=0.8&limit=10

Response:
{
  "total": 3,
  "papers": [
    {
      "Title": "Anomalous Heat in Palladium",
      "Authors": "Edmund Storms",
      "DeepSeek_Score": 0.95,
      "Source": "LENR-CANR",
      "URL": "https://...",
      "PDF_Path": "pdfs/..."
    }
  ]
}
```

### Get Statistics

```bash
GET http://localhost:8000/statistics

Response:
{
  "timestamp": "2025-11-08T12:00:00",
  "statistics": {
    "total_papers": 156,
    "verified": 120,
    "pending": 10,
    "failed": 2,
    "avg_score": 0.85,
    "sources": {
      "LENR-CANR": 100,
      "arXiv": 56
    }
  }
}
```

### Export Database

```bash
# CSV export
GET http://localhost:8000/export?format=csv

# JSON export
GET http://localhost:8000/export?format=json

# Excel export
GET http://localhost:8000/export?format=excel
```

## n8n Workflow Examples

### Example 1: Daily Scheduled Collection

**Nodes:**
1. **Schedule Trigger** - Every day at 2 AM
2. **HTTP Request** - POST to `/collect`
3. **Wait** - Wait 5 minutes
4. **HTTP Request** - GET job status
5. **IF** - Check if completed
6. **Email** - Send notification

**Configuration:**

```javascript
// HTTP Request node body
{
  "sources": ["lenr-canr"],
  "max_papers": 10,
  "deepseek_verify": true
}
```

### Example 2: Query Papers on Demand

**Nodes:**
1. **Webhook** - Receive query request
2. **HTTP Request** - GET from `/papers`
3. **Respond to Webhook** - Return results

**Usage:**

```bash
curl -X POST https://your-n8n-webhook-url \
  -H "Content-Type: application/json" \
  -d '{
    "author": "Storms",
    "min_score": 0.8,
    "limit": 10
  }'
```

### Example 3: Weekly Report

**Nodes:**
1. **Schedule Trigger** - Every Monday at 9 AM
2. **HTTP Request** - GET statistics
3. **HTTP Request** - GET high-scoring papers (min_score=0.8)
4. **Code** - Format report
5. **Email** - Send weekly summary

### Example 4: Real-time Collection with Webhook

**Nodes:**
1. **Webhook** - Trigger collection
2. **HTTP Request** - POST to `/collect` with webhook_url
3. **Webhook Wait** - Wait for completion callback
4. **HTTP Request** - GET final statistics
5. **Slack** - Post to channel

## Advanced n8n Integrations

### Integration with Google Sheets

Export papers to Google Sheets automatically:

```
Schedule Trigger → Get Papers → Split In Batches → Google Sheets (Append)
```

### Integration with Notion

Save papers to Notion database:

```
Webhook → Query Papers → Notion (Create Page)
```

### Integration with Airtable

Sync papers to Airtable:

```
Schedule Trigger → Get Papers → Airtable (Create Record)
```

### Integration with Slack

Get paper notifications:

```
Schedule Trigger → Query High-Score Papers → Slack (Send Message)
```

## Environment Variables

Configure the API using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DEEPSEEK_API_KEY` | DeepSeek API key for verification | (optional) |
| `EXCEL_PATH` | Path to Excel database | `lenr_papers.xlsx` |
| `PDF_DIR` | Directory for PDF storage | `pdfs` |
| `MAX_PAPERS_PER_RUN` | Maximum papers per collection | `50` |

## Docker Deployment with n8n

### docker-compose.yml (Combined)

```yaml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=changeme
    volumes:
      - n8n_data:/home/node/.n8n
    depends_on:
      - lenr-api

  lenr-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - EXCEL_PATH=/data/lenr_papers.xlsx
      - PDF_DIR=/data/pdfs
    volumes:
      - ./data:/data
      - ./logs:/app/logs

volumes:
  n8n_data:
```

Start both services:

```bash
docker-compose up -d
```

Access:
- n8n: http://localhost:5678
- LENR API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Troubleshooting

### API not reachable from n8n

If n8n can't reach the API:

1. **Check network**: Use `http://lenr-api:8000` (Docker service name)
2. **Check health**: `docker exec lenr-api curl http://localhost:8000/health`
3. **Check logs**: `docker logs lenr-api`

### Jobs stuck in "queued" status

Background tasks may not be running:

1. Check API logs for errors
2. Restart API: `docker-compose restart lenr-api`
3. Reduce `max_papers` in request

### Webhook not triggering

1. Verify webhook URL is accessible from API
2. Check n8n webhook settings (should be production URL)
3. Use polling instead (Wait node + Loop)

## API Documentation

Interactive API documentation available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Example n8n HTTP Request Configurations

### Start Collection Job

```javascript
{
  "method": "POST",
  "url": "http://lenr-api:8000/collect",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "sources": ["lenr-canr"],
    "max_papers": 10,
    "deepseek_verify": true,
    "webhook_url": "{{ $workflow.webhook }}"
  }
}
```

### Query Papers by Author

```javascript
{
  "method": "GET",
  "url": "http://lenr-api:8000/papers",
  "qs": {
    "author": "{{ $json.author }}",
    "min_score": 0.7,
    "limit": 50
  }
}
```

### Export to CSV

```javascript
{
  "method": "GET",
  "url": "http://lenr-api:8000/export",
  "qs": {
    "format": "csv"
  },
  "responseType": "file"
}
```

## Best Practices

1. **Rate Limiting**: Don't start multiple collection jobs simultaneously
2. **Monitoring**: Set up health check workflows
3. **Error Handling**: Use IF nodes to handle failed jobs
4. **Webhooks**: Use webhooks for long-running jobs instead of polling
5. **Scheduling**: Run collection during off-peak hours (2-6 AM)
6. **Limits**: Start with small `max_papers` values (10-20) for testing
7. **Backups**: Export database regularly to external storage

## Support

- API Issues: Check `logs/` directory
- n8n Issues: Check n8n community forum
- Integration Help: See workflow examples in `n8n-workflows/`
