"""Service de génération de réponses personnalisées aux avis"""
import re
import requests


class ResponseGenerator:
    """Génère des réponses automatiques personnalisées aux avis"""
    
    TONES = {
        'formel': 'formel',
        'amical': 'amical',
        'empathique': 'empathique'
    }
    
    def __init__(self, use_ai=False):
        """
        Args:
            use_ai: Si True, utilise Ollama pour générer des réponses personnalisées
        """
        self.use_ai = use_ai
    
    def detect_sentiment(self, text: str) -> str:
        """Détecte le sentiment du texte"""
        positive_words = [
            'excellent', 'super', 'fantastique', 'merveilleux', 'génial',
            'adoré', 'parfait', 'bravo', 'très bon', 'satisfait', 'content',
            'wonderful', 'amazing', 'great', 'perfect', 'love'
        ]
        negative_words = [
            'mauvais', 'horrible', 'décevant', 'nul', 'catastrophe', 'problème',
            'plainte', 'déçu', 'très mauvais', 'pire', 'refus', 'discrimination',
            'terrible', 'awful', 'bad', 'worst', 'disappointed'
        ]
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def generate_response(self, review_text: str, tone: str = 'formel') -> str:
        """Génère une réponse personnalisée pour un avis"""
        if tone not in self.TONES:
            tone = 'formel'
        
        # Si AI activée, utiliser Ollama
        if self.use_ai:
            return self._generate_with_ai(review_text, tone)
        
        # Sinon utiliser les templates
        sentiment = self.detect_sentiment(review_text)
        templates = self._get_templates(tone, sentiment)
        
        response_parts = [
            templates['greeting'],
            templates['acknowledgment'],
            templates['closing']
        ]
        
        return ' '.join(response_parts)
    
    def _generate_with_ai(self, review_text: str, tone: str) -> str:
        """Génère une réponse avec Ollama (LLM local)"""
        
        tone_descriptions = {
            'formel': 'professionnel et courtois',
            'amical': 'chaleureux et amical',
            'empathique': 'empathique et compréhensif'
        }
        
        prompt = f"""Tu es un service client {tone_descriptions.get(tone, 'professionnel')} de BNP Paribas.

Avis client : "{review_text}"

Génère une réponse {tone} en français (100-150 mots maximum). 
Remercie le client. Si positif : reconnaissance. Si négatif : excuses et solution.
Signe "Cordialement, L'équipe BNP Paribas".
Réponds UNIQUEMENT en français, sans préambule."""
        
        try:
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'mistral',
                    'prompt': prompt,
                    'stream': False
                },
                timeout=60
            )
            return response.json()['response']
        except Exception as e:
            # En cas d'erreur, fallback sur les templates
            print(f"⚠️ Erreur AI (Ollama pas lancé ?), utilisation des templates")
            sentiment = self.detect_sentiment(review_text)
            templates = self._get_templates(tone, sentiment)
            return ' '.join([templates['greeting'], templates['acknowledgment'], templates['closing']])
    
    def _get_templates(self, tone: str, sentiment: str) -> dict:
        """Retourne les templates selon le ton et le sentiment"""
        
        templates_db = {
            'formel': {
                'positive': {
                    'greeting': 'Nous vous remercions sincèrement pour cet avis positif.',
                    'acknowledgment': 'Nous sommes ravi que notre service ait répondu à vos attentes et dépassé vos espérances.',
                    'closing': 'Nous nous engageons à maintenir ce niveau d\'excellence et vous souhaite une excellente journée.'
                },
                'negative': {
                    'greeting': 'Nous avons reçu votre avis et nous en prenons acte.',
                    'acknowledgment': 'Nous présentons nos sincères excuses pour la situation décrite et comprenons votre frustration.',
                    'closing': 'Nous serions honorés de l\'opportunité de remédier à cette situation. N\'hésitez pas à nous contacter directement.'
                },
                'neutral': {
                    'greeting': 'Nous vous remercions d\'avoir pris le temps de partager votre retour.',
                    'acknowledgment': 'Vos observations sont précieuses et nous aident à identifier les domaines d\'amélioration.',
                    'closing': 'Nous restons à votre disposition pour discuter de toute préoccupation supplémentaire.'
                }
            },
            'amical': {
                'positive': {
                    'greeting': 'Merci beaucoup pour cet avis super ! 😊',
                    'acknowledgment': 'On est vraiment contents que tu aies eu une bonne expérience avec nous.',
                    'closing': 'On espère te revoir très bientôt ! 👋'
                },
                'negative': {
                    'greeting': 'Merci de nous avoir donné ton retour honnête.',
                    'acknowledgment': 'On est vraiment désolé que ça ne se soit pas bien passé.',
                    'closing': 'N\'hésite pas à nous contacter directement ! 💪'
                },
                'neutral': {
                    'greeting': 'Merci pour ton avis !',
                    'acknowledgment': 'Ton retour nous aide à nous améliorer.',
                    'closing': 'N\'hésite pas si besoin ! 😊'
                }
            },
            'empathique': {
                'positive': {
                    'greeting': 'Nous vous remercions infiniment pour ce magnifique retour.',
                    'acknowledgment': 'Votre satisfaction nous touche profondément.',
                    'closing': 'Nous serions honorés de vous accueillir à nouveau.'
                },
                'negative': {
                    'greeting': 'Nous comprenons profondément votre frustration.',
                    'acknowledgment': 'Nous sommes vraiment désolés d\'avoir déçu vos attentes.',
                    'closing': 'Votre retour est vital pour nous.'
                },
                'neutral': {
                    'greeting': 'Nous apprécions profondément votre partage.',
                    'acknowledgment': 'Vos observations nous aident à mieux comprendre vos besoins.',
                    'closing': 'Nous restons à votre écoute.'
                }
            }
        }
        
        return templates_db.get(tone, templates_db['formel']).get(sentiment, templates_db['formel']['neutral'])