from __future__ import annotations

from collections import Counter

from fastapi import FastAPI

from app.analyzer import analyze_comment
from app.balancer import balance_viewers
from app.schemas import (
    BatchCommentRequest,
    CommentRequest,
    HealthResponse,
    SessionOptimizationRequest,
    SessionOptimizationResponse,
    ViewerBalancingRequest,
)

app = FastAPI(
    title="AI Service",
    version="0.1.0",
    description="Comment analysis and viewer balancing service for livestream management.",
)


@app.get("/")
def root():
    return {
        "service": "ai-service",
        "status": "ok",
        "message": "AI Service is running.",
        "docs_url": "/docs",
        "health_url": "/health",
        "main_routes": [
            "/analyze-comment",
            "/analyze-comments/batch",
            "/balance-viewers",
            "/session-optimizer",
        ],
    }


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="ai-service")


@app.post("/analyze-comment")
def analyze_single_comment(payload: CommentRequest):
    return analyze_comment(payload)


@app.post("/analyze-comments/batch")
def analyze_comment_batch(payload: BatchCommentRequest):
    results = [analyze_comment(comment) for comment in payload.comments]
    summary = Counter(result.intent for result in results)
    return {
        "count": len(results),
        "summary": dict(summary),
        "results": results,
    }


@app.post("/balance-viewers")
def optimize_viewer_distribution(payload: ViewerBalancingRequest):
    return balance_viewers(payload)


@app.post("/session-optimizer", response_model=SessionOptimizationResponse)
def optimize_session(payload: SessionOptimizationRequest) -> SessionOptimizationResponse:
    comment_results = [analyze_comment(comment) for comment in payload.comments]
    hot_leads = [result for result in comment_results if result.priority == "high"]
    comment_summary = Counter(result.intent for result in comment_results)
    balancing = balance_viewers(
        ViewerBalancingRequest(
            accounts=payload.accounts,
            incoming_viewers=payload.incoming_viewers,
        )
    )
    return SessionOptimizationResponse(
        hot_leads=hot_leads,
        comment_summary=dict(comment_summary),
        balancing=balancing,
    )
