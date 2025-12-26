from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
import uvicorn

# Créer l'application FastAPI
app = FastAPI(
    title="WebScraping & Response Generator API",
    description="""
    API pour scraper des avis clients depuis différentes plateformes 
    et générer des réponses personnalisées automatiquement.
    
    ## Fonctionnalités
    
    * **Scraping** d'avis depuis Trustpilot (Google Reviews et TripAdvisor à venir)
    * **Génération de réponses** personnalisées avec templates ou IA (Ollama)
    * **Détection de sentiment** automatique
    * **3 tons** disponibles : formel, amical, empathique
    
    ## Workflow
    
    1. Scraper les avis depuis une URL
    2. Détecter le sentiment de chaque avis
    3. Générer une réponse adaptée au ton et sentiment
    """,
    version="1.0.0",
    contact={
        "name": "Victoria",
        "email": "victoria.viddal@gmail.com"
    }
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routes
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "API de Webscraping et Génération de Réponses",
        "docs": "/docs",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )