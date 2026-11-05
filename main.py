"""
FastAPI backend for location, weather, news, and AI summarization.
Run: uvicorn main:app --reload
"""

from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from api_services.ai_summary_service import generate_ai_news_summary
from api_services.location_service import format_location_info, get_location_by_ip
from api_services.news_service import fetch_live_news, scrape_full_article_content
from api_services.weather_service import get_live_weather

app = FastAPI(
    title="City/Region News Summarizer REST API",
    description="IP location, live news, weather context, and Gemini summarization.",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>City/Region News Summarization API</title>
        <style>
            body { font-family: Segoe UI, sans-serif; background: #0f172a; color: #f8fafc; padding: 2rem; }
            .card { background: #1e293b; padding: 2rem; border-radius: 12px; max-width: 800px; margin: 0 auto; }
            h1 { color: #38bdf8; }
            code { background: #0f172a; color: #38bdf8; padding: 0.2rem 0.5rem; border-radius: 4px; }
            .btn { display: inline-block; background: #0284c7; color: white; padding: 0.75rem 1.5rem; text-decoration: none; border-radius: 8px; margin-top: 1rem; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>City/Region News Summarization System API</h1>
            <ul>
                <li>Location API: <code>GET /api/location</code></li>
                <li>Weather API: <code>GET /api/weather</code></li>
                <li>News API: <code>GET /api/news</code></li>
                <li>AI Summarizer: <code>POST /api/summarize</code></li>
            </ul>
            <a class="btn" href="/docs">Open Swagger docs</a>
        </div>
    </body>
    </html>
    """


@app.get("/api/location")
async def get_location(request: Request, user_ip: Optional[str] = None):
    client_ip = user_ip or (request.client.host if request.client else None)
    if client_ip in ("127.0.0.1", "::1"):
        client_ip = None
    raw_loc = get_location_by_ip(client_ip)
    return format_location_info(raw_loc)


@app.get("/api/weather")
async def get_weather(location: str = "Ahmedabad", lat: Optional[float] = None, lon: Optional[float] = None):
    return get_live_weather(lat, lon, location)


@app.get("/api/news")
async def get_news(
    location: str = Query("Rajkot", description="City or region name"),
    search_type: str = Query("city", description="'city' or 'region'"),
    region: Optional[str] = Query("Gujarat", description="State or region name"),
    category: str = Query("All", description="News category (All, Political, Sports, Technology, Business, Entertainment, Education, Local News)"),
    limit: int = Query(6, ge=1, le=20),
):
    articles = fetch_live_news(
        query_location=location,
        search_type=search_type,
        region_state=region,
        category=category,
        limit=limit,
    )
    return {
        "location": location,
        "region": region,
        "search_type": search_type,
        "category": category,
        "total_articles": len(articles),
        "articles": articles,
    }


@app.post("/api/summarize")
async def summarize_article(payload: Dict[str, Any]):
    if "title" not in payload:
        raise HTTPException(status_code=400, detail="Payload must include at least 'title'")
    if payload.get("link"):
        payload["full_text"] = scrape_full_article_content(
            payload["link"], payload.get("full_text", payload.get("title"))
        )
    return {
        "article_title": payload.get("title"),
        "source": payload.get("source"),
        "location": payload.get("location"),
        "ai_summary": generate_ai_news_summary(payload),
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
