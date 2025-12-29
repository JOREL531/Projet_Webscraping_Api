"""Service de génération de réponses personnalisées aux avis"""
import re
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0

# Import GPT4All
from gpt4all import GPT4All


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
            use_ai: Si True, utilise GPT4All pour générer des réponses personnalisées
        """
        self.use_ai = use_ai
        self.model = None
        
        if use_ai:
            print("🔄 Chargement du modèle GPT4All (première fois: téléchargement ~2GB)...")
            try:
                # Modèle léger et rapide
                self.model = GPT4All("orca-mini-3b-gguf2-q4_0.gguf")
                print("✅ Modèle GPT4All chargé avec succès")
            except Exception as e:
                print(f"⚠️ Erreur chargement GPT4All: {e}")
                print("→ Utilisation des templates à la place")
                self.use_ai = False
    
    def detect_language(self, text: str) -> str:
        """
        Détecte la langue du texte
        
        Args:
            text: Texte à analyser
        
        Returns:
            Code langue ISO 639-1 ('fr', 'en', 'es', etc.)
        """
        try:
            lang = detect(text)
            return lang
        except Exception:
            return 'fr'
    
    def detect_sentiment(self, text: str) -> str:
        """Détecte le sentiment du texte"""
        positive_words = [
            'excellent', 'super', 'fantastique', 'merveilleux', 'génial',
            'adoré', 'parfait', 'bravo', 'très bon', 'satisfait', 'content',
            'wonderful', 'amazing', 'great', 'perfect', 'love', 'formidable',
            'top', 'recommande', 'qualité', 'professionnel', 'rapide', 'efficace'
        ]
        negative_words = [
            'mauvais', 'horrible', 'décevant', 'nul', 'catastrophe', 'problème',
            'plainte', 'déçu', 'très mauvais', 'pire', 'refus', 'discrimination',
            'terrible', 'awful', 'bad', 'worst', 'disappointed', 'lent', 'incompétent',
            'arnaque', 'scandale', 'inadmissible', 'honte', 'frustré', 'horrific'
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
    
    def auto_detect_tone(self, review_text: str, rating: float = None) -> str:
        """
        Détecte automatiquement le ton approprié basé sur le rating et le sentiment
        
        Args:
            review_text: Texte de l'avis
            rating: Note sur 5 (optionnel)
        
        Returns:
            Ton recommandé ('formel', 'amical', 'empathique')
        """
        if rating is not None:
            if rating >= 4:
                return 'amical'
            elif rating <= 2:
                return 'empathique'
            else:
                return 'formel'
        
        sentiment = self.detect_sentiment(review_text)
        
        if sentiment == 'positive':
            return 'amical'
        elif sentiment == 'negative':
            return 'empathique'
        else:
            return 'formel'
    
    def generate_response(self, review_text: str, rating: float = None, tone: str = None) -> str:
        """
        Génère une réponse personnalisée pour un avis dans la langue de l'avis
        
        Args:
            review_text: Texte de l'avis
            rating: Note sur 5 (optionnel, pour auto-détecter le ton)
            tone: Ton souhaité ('formel', 'amical', 'empathique'). 
                  Si None, sera détecté automatiquement.
        
        Returns:
            Réponse générée dans la langue de l'avis
        """
        # Détecter la langue de l'avis
        language = self.detect_language(review_text)
        
        # Auto-détecter le ton si non spécifié
        if tone is None:
            tone = self.auto_detect_tone(review_text, rating)
        
        # Valider le ton
        if tone not in self.TONES:
            tone = 'formel'
        
        # Si AI activée, utiliser GPT4All
        if self.use_ai:
            return self._generate_with_ai(review_text, tone, language)
        
        # Sinon utiliser les templates
        sentiment = self.detect_sentiment(review_text)
        templates = self._get_templates(tone, sentiment, language)
        
        response_parts = [
            templates['greeting'],
            templates['acknowledgment'],
            templates['closing']
        ]
        
        return ' '.join(response_parts)
    
    def _generate_with_ai(self, review_text: str, tone: str, language: str = 'fr') -> str:
        """Génère une réponse avec GPT4All (LLM local) dans la langue détectée"""
        
        if not self.model:
            # Fallback sur templates si modèle non chargé
            sentiment = self.detect_sentiment(review_text)
            templates = self._get_templates(tone, sentiment, language)
            return ' '.join([templates['greeting'], templates['acknowledgment'], templates['closing']])
        
        tone_descriptions = {
            'formel': {
                'fr': 'professionnel et courtois',
                'en': 'professional and courteous',
                'es': 'profesional y cortés',
            },
            'amical': {
                'fr': 'chaleureux et amical',
                'en': 'warm and friendly',
                'es': 'cálido y amigable',
            },
            'empathique': {
                'fr': 'empathique et compréhensif',
                'en': 'empathetic and understanding',
                'es': 'empático y comprensivo',
            }
        }
        
        language_names = {
            'fr': 'français',
            'en': 'English',
            'es': 'español',
        }
        
        lang_name = language_names.get(language, 'français')
        tone_desc = tone_descriptions.get(tone, tone_descriptions['formel']).get(language, 'professional')
        
        closing_signatures = {
            'fr': "Cordialement, L'équipe Service Client",
            'en': "Best regards, The Customer Service Team",
            'es': "Atentamente, El equipo de atención al cliente",
        }
        
        signature = closing_signatures.get(language, closing_signatures['fr'])
        
        # Prompt pour GPT4All
        prompt = f"""Tu es un service client {tone_desc}.

Avis client : "{review_text}"

Réponds en {lang_name} (80-120 mots maximum).
Remercie le client. Si positif: reconnaissance. Si négatif: excuses et solution.
Signe: "{signature}".

Réponse:"""
        
        try:
            with self.model.chat_session():
                response = self.model.generate(
                    prompt,
                    max_tokens=200,
                    temp=0.7
                )
                return response.strip()
        
        except Exception as e:
            print(f"⚠️ Erreur génération GPT4All: {e}")
            # Fallback sur templates
            sentiment = self.detect_sentiment(review_text)
            templates = self._get_templates(tone, sentiment, language)
            return ' '.join([templates['greeting'], templates['acknowledgment'], templates['closing']])
    
    def _get_templates(self, tone: str, sentiment: str, language: str = 'fr') -> dict:
        """Retourne les templates selon le ton, le sentiment et la langue"""
        
        templates_db = {
            'fr': {
                'formel': {
                    'positive': {
                        'greeting': 'Nous vous remercions sincèrement pour cet avis positif.',
                        'acknowledgment': 'Nous sommes ravis que notre service ait répondu à vos attentes.',
                        'closing': 'Nous nous engageons à maintenir ce niveau d\'excellence.'
                    },
                    'negative': {
                        'greeting': 'Nous avons reçu votre avis et nous en prenons acte.',
                        'acknowledgment': 'Nous présentons nos sincères excuses pour la situation décrite.',
                        'closing': 'N\'hésitez pas à nous contacter directement.'
                    },
                    'neutral': {
                        'greeting': 'Nous vous remercions d\'avoir pris le temps de partager votre retour.',
                        'acknowledgment': 'Vos observations sont précieuses.',
                        'closing': 'Nous restons à votre disposition.'
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
                        'acknowledgment': 'On est vraiment désolés que ça ne se soit pas bien passé.',
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
            },
            'en': {
                'formel': {
                    'positive': {
                        'greeting': 'Thank you sincerely for your positive review.',
                        'acknowledgment': 'We are delighted that our service met your expectations.',
                        'closing': 'We are committed to maintaining this level of excellence.'
                    },
                    'negative': {
                        'greeting': 'We have received your feedback and take it seriously.',
                        'acknowledgment': 'We sincerely apologize for the situation described.',
                        'closing': 'Please do not hesitate to contact us directly.'
                    },
                    'neutral': {
                        'greeting': 'Thank you for taking the time to share your feedback.',
                        'acknowledgment': 'Your observations are valuable to us.',
                        'closing': 'We remain at your disposal.'
                    }
                },
                'amical': {
                    'positive': {
                        'greeting': 'Thank you so much for this great review! 😊',
                        'acknowledgment': 'We\'re really happy you had a good experience with us.',
                        'closing': 'Hope to see you again soon! 👋'
                    },
                    'negative': {
                        'greeting': 'Thanks for your honest feedback.',
                        'acknowledgment': 'We\'re really sorry things didn\'t go well.',
                        'closing': 'Don\'t hesitate to contact us directly! 💪'
                    },
                    'neutral': {
                        'greeting': 'Thanks for your review!',
                        'acknowledgment': 'Your feedback helps us improve.',
                        'closing': 'Feel free to reach out if needed! 😊'
                    }
                },
                'empathique': {
                    'positive': {
                        'greeting': 'We thank you deeply for this wonderful feedback.',
                        'acknowledgment': 'Your satisfaction touches us profoundly.',
                        'closing': 'We would be honored to welcome you again.'
                    },
                    'negative': {
                        'greeting': 'We deeply understand your frustration.',
                        'acknowledgment': 'We are truly sorry for disappointing your expectations.',
                        'closing': 'Your feedback is vital to us.'
                    },
                    'neutral': {
                        'greeting': 'We deeply appreciate you taking the time to share.',
                        'acknowledgment': 'Your observations help us better understand your needs.',
                        'closing': 'We remain at your service.'
                    }
                }
            }
        }
        
        # Si la langue n'est pas supportée, utiliser l'anglais ou le français
        if language not in templates_db:
            language = 'en' if language != 'fr' else 'fr'
        
        lang_templates = templates_db[language]
        return lang_templates.get(tone, lang_templates['formel']).get(sentiment, lang_templates['formel']['neutral'])