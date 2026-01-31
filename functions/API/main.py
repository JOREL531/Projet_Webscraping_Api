from fastapi import FastAPI
from pydantic import BaseModel, Field
from functions.scrapping.functions_trustpilot import extract_reviews_and_ratings_from_trustpilot
from functions.scrapping.functions_yelp import extract_review_from_yelp, extract_reviews_and_ratings_from_yelp
from functions.scrapping.functions_play_store import extract_review_from_gloogle_play_store, extract_reviews_and_ratings_from_google_play_store
from functions.scrapping.functions_amazon import save_cookies, extract_review_from_amazon, extract_reviews_and_ratings_from_amazon
from functions.scrapping.functions_google_reviews import extract_google_reviews_full_best_effort
from functions.generator.response_generator import ResponseGenerator
from enum import Enum

app = FastAPI(
    title="Bot de réponse automatique aux avis clients",
    description=(
        "### 🇫🇷 Répondez automatiquement aux avis clients, à grande échelle\n\n"
        "Vous recevez trop d’avis pour répondre manuellement ? Cette API vous permet d’automatiser "
        "la gestion des avis clients en collectant des avis publics provenant de plateformes telles que "
        "Trustpilot, Yelp, Google, Play Store et Amazon.\n\n"
        "Grâce à des modèles de traitement du langage naturel, elle génère en quelques secondes "
        "des réponses pertinentes, cohérentes et adaptées au contexte de chaque avis, "
        "tout en respectant un ton professionnel et homogène.\n\n"
        "➡️ **Testez les endpoints directement via la documentation interactive (Swagger / OpenAPI).**\n\n"
        "---\n\n"
        "### 🇬🇧 Automatically respond to customer reviews, at scale\n\n"
        "Receiving too many reviews to reply manually? This API helps you automate customer review "
        "management by collecting public reviews from platforms such as Trustpilot, Yelp, Google, "
        "Play Store and Amazon.\n\n"
        "Using natural language processing models, it generates relevant and context-aware responses "
        "within seconds, ensuring a consistent and professional tone across all customer interactions.\n\n"
        "➡️ **Explore and test the endpoints via the interactive documentation (Swagger / OpenAPI).**"
    ),
)



# Initialiser le générateur
generator = ResponseGenerator(use_ai=True)

# Modèle pour la requête POST
class ReviewRequest(BaseModel):
    review_text: str
    rating: int = Field(..., ge=1, le=5, description="Note de 1 à 5")
    # tone: str | None = None

# @app.get("/reviews/trustpilot")
# def get_reviews(
#     url: str,
#     max_reviews:int
# ):
#     """
#     Récupère les avis Trustpilot depuis une URL donnée
#     """
#     reviews = extract_review_from_trustpilot(url, max_reviews)

#     return {
#         "url": url,
#         "requested_reviews": max_reviews,
#         # "returned_reviews": len(reviews),
#         "data": reviews
#     }

# @app.get("/reviews/yelp")
# def get_yelp_reviews(
#     url: str,
#     max_reviews: int
# ):
#     """
#     Récupère les avis Yelp depuis une URL donnée
#     """
#     reviews = extract_review_from_yelp(url, max_reviews)

#     return {
#         "url": url,
#         "requested_reviews": max_reviews,
#         # "returned_reviews": len(reviews),
#         "data": reviews
#     }

# @app.get("/reviews")
# def get_reviews(
#     source: str,  # trustpilot, yelp, google, appstore, amazon
#     url: str | None = None,
#     max_reviews: int = 50
# ):
#     if source == "trustpilot":
#         reviews = extract_review_from_trustpilot(url, max_reviews)

#     if source == "yelp":
#         reviews = extract_review_from_yelp(url, max_reviews)

#     if source == "google":
#         reviews = extract_google_reviews_full_best_effort(url, max_reviews)

#     if source == "playstore":
#         reviews = extract_review_from_gloogle_play_store(url, max_reviews)
    
#     if source == "amazon":
#         reviews = extract_review_from_amazon(url, max_reviews)

#     return {
#         "url": url,
#         "requested_reviews": max_reviews,
#         # "returned_reviews": len(reviews),
#         "data": reviews
#     }

# uvicorn functions.API.main:app

class ReviewSource(str, Enum):
    trustpilot = "trustpilot"
    yelp = "yelp"
    google = "google"
    playstore = "playstore"
    amazon = "amazon"

@app.get("/reviews")
def get_reviews(
    source: ReviewSource, 
    search: str | None = None,
    max_reviews: int = 50
):
    if source == ReviewSource.trustpilot:
        reviews = extract_reviews_and_ratings_from_trustpilot(search, max_reviews)

    elif source == ReviewSource.yelp:
        reviews = extract_reviews_and_ratings_from_yelp(search, max_reviews)

    elif source == ReviewSource.google:
        reviews = extract_google_reviews_full_best_effort(search, max_reviews)

    elif source == ReviewSource.playstore:
        reviews = extract_reviews_and_ratings_from_google_play_store(search, max_reviews)

    elif source == ReviewSource.amazon:
        reviews = extract_reviews_and_ratings_from_amazon(search, max_reviews)

    return {
        "search": search,
        "requested_reviews": max_reviews,
        "data": reviews
    }



@app.post("/generate-response")
def generate_response(request: ReviewRequest):
    """
    Génère une réponse pour UN avis
    """
    response = generator.generate_response(
        review_text=request.review_text,
        rating=request.rating,
        tone=request.tone
    )
    
    language = generator.detect_language(request.review_text)
    sentiment = generator.detect_sentiment(request.review_text)
    auto_tone = generator.auto_detect_tone(request.review_text, request.rating)
    
    return {
        "review": request.review_text,
        "rating": request.rating,
        "detected_language": language,
        "detected_sentiment": sentiment,
        "response_tone": auto_tone,
        # "used_tone": request.tone or auto_tone,
        "generated_response": response
    }



@app.get("/reviews-with-responses")
def get_reviews_with_responses(
    source: ReviewSource,
    search: str | None = None,
    max_reviews: int = 50,
):
    """
    Récupère les avis ET génère automatiquement les réponses
    """
    # Récupérer les avis
    if source == ReviewSource.trustpilot:
        reviews = extract_reviews_and_ratings_from_trustpilot(search, max_reviews)
    elif source == ReviewSource.yelp:
        reviews = extract_reviews_and_ratings_from_yelp(search, max_reviews)
    elif source == ReviewSource.google:
        reviews = extract_google_reviews_full_best_effort(search, max_reviews)
    elif source == ReviewSource.playstore:
        reviews = extract_reviews_and_ratings_from_google_play_store(search, max_reviews)
    elif source == ReviewSource.amazon:
        reviews = extract_reviews_and_ratings_from_amazon(search, max_reviews)
    else:
        return {"error": "Source invalide"}
    
    # FILTRER les avis vides (seulement ceux avec du texte)
    reviews = [r for r in reviews if r.get('review', '').strip()]
    
    # Générer les réponses pour chaque avis
    for review in reviews:
        review_text = review.get('review', '')
        rating = review.get('rating')
        
        if review_text:
            response = generator.generate_response(
                review_text=review_text,
                rating=rating,
            )
            review['generated_response'] = response
            review['detected_language'] = generator.detect_language(review_text)
            review['detected_sentiment'] = generator.detect_sentiment(review_text)
    
    return {
        "search": search,
        "requested_reviews": max_reviews,
        "returned_reviews": len(reviews),
        "data": reviews
    }