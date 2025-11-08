"""
FastAPI REST API for LENR Collection System
n8n-compatible HTTP endpoints
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import asyncio
import uuid
import os
from datetime import datetime
from pathlib import Path

from lenr_collection.database import LENRDatabase
from lenr_collection.scrapers import LENRCANRScraper, ArXivScraper, ScraperConfig
from lenr_collection.downloader import PDFDownloader
from lenr_collection.processor import PDFProcessor
from lenr_collection.verifier import DeepSeekVerifier

app = FastAPI(
    title="LENR Research Collection API",
    description="REST API for automated LENR research paper collection",
    version="1.0.0"
)

# Job tracking
jobs = {}

# Configuration from environment variables
EXCEL_PATH = os.getenv("EXCEL_PATH", "lenr_papers.xlsx")
PDF_DIR = os.getenv("PDF_DIR", "pdfs")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
MAX_PAPERS = int(os.getenv("MAX_PAPERS_PER_RUN", "50"))


# Pydantic models
class CollectionRequest(BaseModel):
    sources: List[str] = ["lenr-canr"]
    max_papers: Optional[int] = 10
    deepseek_verify: bool = False
    webhook_url: Optional[str] = None


class PaperQuery(BaseModel):
    author: Optional[str] = None
    title: Optional[str] = None
    min_score: Optional[float] = None
    source: Optional[str] = None
    limit: int = 100


class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: Optional[Dict] = None
    result: Optional[Dict] = None
    error: Optional[str] = None


# Background job executor
async def run_collection_job(job_id: str, request: CollectionRequest):
    """Run collection job in background"""
    try:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["started_at"] = datetime.now().isoformat()

        # Initialize components
        db = LENRDatabase(EXCEL_PATH)
        downloader = PDFDownloader(PDF_DIR)
        processor = PDFProcessor()

        verifier = None
        if request.deepseek_verify and DEEPSEEK_API_KEY:
            verifier = DeepSeekVerifier(DEEPSEEK_API_KEY)

        all_papers = []

        # Collect from sources
        if "lenr-canr" in request.sources:
            scraper = LENRCANRScraper(ScraperConfig())
            async with scraper.session if hasattr(scraper, 'session') else None:
                papers = await scraper.scrape()
                all_papers.extend(papers)

        if "arxiv" in request.sources:
            scraper = ArXivScraper()
            papers = await scraper.search_lenr_papers(max_results=100)
            all_papers.extend(papers)

        # Filter duplicates
        new_papers = [p for p in all_papers if not db.is_duplicate_url(p.get('URL', ''))]
        new_papers = new_papers[:request.max_papers]

        jobs[job_id]["progress"] = {
            "total": len(new_papers),
            "processed": 0,
            "successful": 0,
            "failed": 0
        }

        # Process papers
        for i, paper in enumerate(new_papers):
            try:
                # Download PDF
                pdf_path = downloader.download(paper['URL'], paper['Title'])
                if pdf_path:
                    # Process PDF
                    extracted = processor.process_pdf(str(pdf_path))

                    # Update paper data
                    paper.update({
                        'PDF_Path': str(pdf_path),
                        'PDF_Hash': db.compute_pdf_hash(str(pdf_path)),
                        'Abstract': extracted.get('abstract') or paper.get('Abstract', ''),
                        'Status': 'processed'
                    })

                    # Verify if requested
                    if verifier:
                        verification = verifier.verify_content(
                            paper['Title'],
                            paper.get('Abstract', ''),
                            extracted.get('text', '')[:5000]
                        )
                        paper['Verified'] = True
                        paper['DeepSeek_Score'] = verification['score']
                        paper['DeepSeek_Summary'] = verification['summary']

                    # Add to database
                    db.add_paper(paper)
                    jobs[job_id]["progress"]["successful"] += 1
                else:
                    jobs[job_id]["progress"]["failed"] += 1

            except Exception as e:
                jobs[job_id]["progress"]["failed"] += 1

            jobs[job_id]["progress"]["processed"] = i + 1

        # Save database
        db.save(backup=True)

        # Get statistics
        stats = db.get_statistics()

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["result"] = {
            "papers_collected": len(new_papers),
            "successful": jobs[job_id]["progress"]["successful"],
            "failed": jobs[job_id]["progress"]["failed"],
            "database_stats": stats
        }

        # Call webhook if provided
        if request.webhook_url:
            import requests
            try:
                requests.post(request.webhook_url, json={
                    "job_id": job_id,
                    "status": "completed",
                    "result": jobs[job_id]["result"]
                })
            except:
                pass

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.now().isoformat()


# API Endpoints

@app.get("/")
async def root():
    """API information"""
    return {
        "name": "LENR Research Collection API",
        "version": "1.0.0",
        "endpoints": {
            "POST /collect": "Start collection job",
            "GET /jobs/{job_id}": "Get job status",
            "GET /papers": "Query papers",
            "GET /statistics": "Get database statistics",
            "GET /export": "Export database to CSV",
            "GET /health": "Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database_exists": Path(EXCEL_PATH).exists(),
        "deepseek_configured": bool(DEEPSEEK_API_KEY)
    }


@app.post("/collect")
async def start_collection(request: CollectionRequest, background_tasks: BackgroundTasks):
    """Start a new collection job"""
    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "created_at": datetime.now().isoformat(),
        "request": request.dict()
    }

    # Run in background
    background_tasks.add_task(run_collection_job, job_id, request)

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Collection job started",
        "check_status": f"/jobs/{job_id}"
    }


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a collection job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return jobs[job_id]


@app.get("/jobs")
async def list_jobs():
    """List all jobs"""
    return {
        "total": len(jobs),
        "jobs": list(jobs.values())
    }


@app.get("/papers")
async def query_papers(
    author: Optional[str] = None,
    title: Optional[str] = None,
    min_score: Optional[float] = None,
    source: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """Query papers from database"""
    try:
        db = LENRDatabase(EXCEL_PATH)
        results = db.df

        # Apply filters
        if author:
            results = results[results['Authors'].str.contains(author, na=False, case=False)]

        if title:
            results = results[results['Title'].str.contains(title, na=False, case=False)]

        if min_score is not None:
            results = results[results['DeepSeek_Score'] >= min_score]

        if source:
            results = results[results['Source'] == source]

        # Limit results
        results = results.head(limit)

        # Convert to dict
        papers = results.to_dict('records')

        return {
            "total": len(papers),
            "papers": papers
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/statistics")
async def get_statistics():
    """Get database statistics"""
    try:
        db = LENRDatabase(EXCEL_PATH)
        stats = db.get_statistics()

        return {
            "timestamp": datetime.now().isoformat(),
            "statistics": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/export")
async def export_database(
    format: str = Query(default="csv", regex="^(csv|json|excel)$")
):
    """Export database to file"""
    try:
        db = LENRDatabase(EXCEL_PATH)

        if format == "csv":
            export_path = "export.csv"
            db.df.to_csv(export_path, index=False)
        elif format == "json":
            export_path = "export.json"
            db.df.to_json(export_path, orient='records', indent=2)
        elif format == "excel":
            export_path = "export.xlsx"
            db.df.to_excel(export_path, index=False)

        return FileResponse(
            export_path,
            media_type="application/octet-stream",
            filename=export_path
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/papers/{paper_url:path}")
async def delete_paper(paper_url: str):
    """Delete a paper by URL"""
    try:
        db = LENRDatabase(EXCEL_PATH)
        initial_count = len(db.df)

        db.df = db.df[db.df['URL'] != paper_url]

        if len(db.df) < initial_count:
            db.save(backup=True)
            return {"message": "Paper deleted", "url": paper_url}
        else:
            raise HTTPException(status_code=404, detail="Paper not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
