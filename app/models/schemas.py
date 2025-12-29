from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from enum import Enum

class Platform(str, Enum):
    trustpilot = "trustpilot"
    google = "google"
    tripadvisor = "tripadvisor"
    yelp = "yelp"


class Tone(str, Enum):
    """Tons de réponse disponibles"""
    formel = "formel"
    amical = "amical"
    empathique = "empathique"


class ScrapeRequest(BaseModel):
    """Requête pour scraper des avis"""
    url: HttpUrl
    platform: Platform
    max_reviews: Optional[int] = 10
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.trustpilot.com/review/mabanque.bnpparibas",
                "platform": "trustpilot",
                "max_reviews": 10
            }
        }


class Review(BaseModel):
    """Modèle d'un avis"""
    text: str
    rating: Optional[float] = None
    sentiment_label: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    
    class Config:
        # Permet d'accepter des champs supplémentaires sans erreur
        extra = "allow"

class GenerateResponseRequest(BaseModel):
    """Requête pour générer une réponse"""
    review_text: str
    use_ai: Optional[bool] = True  # ← True par défaut
    
    class Config:
        json_schema_extra = {
            "example": {
                "review_text": "Excellent service, très satisfait!",
                "use_ai": True
            }
        }


class GeneratedResponse(BaseModel):
    """Réponse générée"""
    review: Review
    generated_response: str
    tone: str
    sentiment: Optional[str] = None


class ScrapeAndRespondRequest(BaseModel):
    """Requête pour scraper ET générer des réponses"""
    url: HttpUrl
    platform: Optional[Platform] = None  # ← Rendre optionnel
    max_reviews: Optional[int] = 10
    use_ai: Optional[bool] = True