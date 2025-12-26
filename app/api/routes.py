from fastapi import APIRouter, HTTPException, status
from typing import List, Any
import sys
sys.path.append('..')

from app.models.schemas import (
    ScrapeRequest, Review, GenerateResponseRequest, 
    GeneratedResponse, ScrapeAndRespondRequest
)

from functions.functions_trustpilot import extract_review_from_trustpilot
from functions.functions_google_reviews import extract_google_reviews_full_best_effort  # ← AJOUTE ÇA
from functions.response_generator import ResponseGenerator

router = APIRouter()
response_generator = ResponseGenerator()


@router.post("/scrape", tags=["Scraping"])
async def scrape_reviews(request: ScrapeRequest) -> Any:
    """Scrape les avis depuis une plateforme"""
    try:
        if request.platform == "trustpilot":
            reviews = extract_review_from_trustpilot(str(request.url))
            reviews = reviews[:request.max_reviews]
            
            return {
                "success": True,
                "count": len(reviews),
                "reviews": reviews
            }
        
        elif request.platform == "google":
            # ← AJOUTE CE BLOC
            reviews_raw = extract_google_reviews_full_best_effort(
                str(request.url), 
                max_reviews=request.max_reviews,
                headless=True  # Sans interface graphique
            )
            
            # Convertir en format dict
            reviews = [{"text": r} for r in reviews_raw]
            
            return {
                "success": True,
                "count": len(reviews),
                "reviews": reviews
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plateforme non supportée"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur: {str(e)}"
        )

@router.get("/", tags=["Root"])
async def root():
    """Point d'entrée de l'API"""
    return {
        "message": "API de Webscraping et Génération de Réponses",
        "version": "1.0.0",
        "endpoints": {
            "scrape": "/api/v1/scrape",
            "generate": "/api/v1/generate-response",
            "scrape_and_respond": "/api/v1/scrape-and-respond"
        }
    }


@router.post("/generate-response", tags=["Génération"])
async def generate_response(request: GenerateResponseRequest):
    """Génère une réponse personnalisée pour un avis"""
    try:
        generator = ResponseGenerator(use_ai=request.use_ai)
        response_text = generator.generate_response(
            review_text=request.review_text,
            tone=request.tone
        )
        sentiment = generator.detect_sentiment(request.review_text)
        
        return {
            "response": response_text,
            "tone": request.tone,
            "sentiment": sentiment,
            "used_ai": request.use_ai
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur: {str(e)}"
        )


@router.post("/scrape-and-respond", tags=["Workflow Complet"])
async def scrape_and_respond(request: ScrapeAndRespondRequest):
    """Workflow complet: Scrape + génère des réponses"""
    try:
        # 1. Scraper les avis
        if request.platform == "trustpilot":
            reviews = extract_review_from_trustpilot(str(request.url))
            reviews = reviews[:request.max_reviews]
        
        elif request.platform == "google":
            # ← AJOUTE CE BLOC
            reviews_raw = extract_google_reviews_full_best_effort(
                str(request.url), 
                max_reviews=request.max_reviews,
                headless=True
            )
            reviews = [{"text": r} for r in reviews_raw]
        
        else:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=f"Plateforme {request.platform} pas encore implémentée"
            )
        
        # 2. Générer des réponses (reste identique)
        generator = ResponseGenerator(use_ai=request.use_ai)
        results = []
        
        for review in reviews:
            text = review.get('text', '') if isinstance(review, dict) else review
            rating = review.get('rating', None) if isinstance(review, dict) else None
            
            if rating:
                if rating >= 4:
                    tone_auto = "amical"
                elif rating <= 2:
                    tone_auto = "empathique"
                else:
                    tone_auto = request.tone
            else:
                tone_auto = request.tone
            
            response_text = generator.generate_response(text, tone=tone_auto)
            sentiment = generator.detect_sentiment(text)
            
            results.append({
                "review": review,
                "generated_response": response_text,
                "tone": tone_auto,
                "sentiment": sentiment
            })
        
        return results
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur: {str(e)}"
        )

@router.get("/health", tags=["Monitoring"])
async def health_check():
    """Vérifier l'état de l'API"""
    return {"status": "healthy"}