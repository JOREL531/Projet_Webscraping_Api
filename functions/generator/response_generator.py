"""Service de génération de réponses personnalisées aux avis"""
import re
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0
from transformers import pipeline

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
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="nlptown/bert-base-multilingual-uncased-sentiment"
        )
        
        if use_ai:
            print("Chargement du modèle GPT4All (première fois: téléchargement ~2GB)...")
            try:
                # Modèle léger et rapide
                #self.model = GPT4All("orca-mini-3b-gguf2-q4_0.gguf")
                self.model = GPT4All("mistral-7b-instruct-v0.1.Q4_0.gguf")
                print("Modèle GPT4All chargé avec succès")
            except Exception as e:
                print(f"Erreur chargement GPT4All: {e}")
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

    def detect_sentiment(self,text: str) -> str:
        result = self.sentiment_pipeline(text)[0]['label']

        # Labels: "1 star" → "5 stars"
        stars = int(result[0])

        if stars <= 2:
            return "negative"
        elif stars == 3:
            return "neutral"
        else:
            return "positive"
    
    
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
        
        # Header et footer adaptés à la langue
        greetings = {
            'fr': 'Cher client',
            'en': 'Dear customer',
            'es': 'Estimado cliente',
        }
        
        closings = {
            'fr': "Cordialement,\nL'équipe Service Client",
            'en': "Best regards,\nThe Customer Service Team",
            'es': "Atentamente,\nEl equipo de Atención al Cliente",
        }
        
        greeting = greetings.get(language, greetings['en'])
        closing = closings.get(language, closings['en'])
        
        # Si AI activée, utiliser GPT4All
        if self.use_ai:
            return self._generate_with_ai(review_text, tone, language, greeting, closing)
        
        # Sinon utiliser les templates
        sentiment = self.detect_sentiment(review_text)
        templates = self._get_templates(tone, sentiment, language)
        
        response_parts = [
            templates['greeting'],
            templates['acknowledgment'],
            templates['closing']
        ]
        
        response_body = ' '.join(response_parts)
        
        # Formater avec header et footer dans la bonne langue
        return f"{greeting},\n\n{response_body}\n\n{closing}"

    def _clean_ai_response(self, response: str) -> str:
        """Nettoie la réponse IA en supprimant les formules de politesse ajoutées automatiquement"""
        
        # Nettoyer le texte complet d'abord
        cleaned = response.strip()
    
        # Patterns à supprimer PARTOUT dans le texte
        patterns_to_remove = [
            r'Dear \[Client\],?\s*',
            r'Dear clients?,?\s*',           # ← Couvre "Dear client" ET "Dear clients"
            r'Dear valued customers?,?\s*',  # ← Couvre "customer" ET "customers"
            r'Dear valued guests?,?\s*',     # ← Couvre "guest" ET "guests"
            r'Dear customers?,?\s*',         # ← Couvre "customer" ET "customers"
            r'Chers? clients?,?\s*',         # ← Couvre "Cher client", "Chers clients"
            r'Chères? clientes?,?\s*',       # ← Couvre "Chère cliente", "Chères clientes"
            r'Estimados? clientes?,?\s*',    # ← Espagnol : "Estimado cliente", "Estimados clientes"
            r'\[Your name\]\s*',
            r'\[Votre nom\]\s*',
            r'\[Su nombre\]\s*',
            r'Merci de votre compréhension\s*',
            r'Sincerely,\s*Airbnb Customer Service\s*',
            r'Cordialement,\s*Service Client Airbnb\s*',
            r'Best regards,\s*Airbnb Customer Service\s*',
            r'Best regards,\s*',
            r'Cordialement,\s*', 
            r'Sincerely,\s*',
            r'Atentamente,\s*',
            # Auto-références à supprimer
            r'(?:^|\.\s+)As an?\s+[^.]+\.\s*',
            r'(?:^|\.\s+)As your\s+[^.]+\.\s*',
            r'(?:^|\.\s+)En tant qu[\'e]\s+[^.]+\.\s*',
        ]
        
        # Supprimer tous les patterns
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Nettoyer les espaces multiples et points en début
        cleaned = re.sub(r'^\.\s*', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Nettoyer ligne par ligne
        lines = cleaned.split('\n')
        final_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # Skip lignes vides
            if not line_lower:
                continue
            
            # Skip formules de politesse
            skip_patterns = [
                'dear customer',
                'dear valued',
                'cher client',
                'chère client',
                'estimado cliente',
                'sincerely',
                'best regards',
                'cordialement',
                'atentamente',
                'as an',
                'as a ',
                'as your',
                'en tant que',
                "en tant qu'",
            ]
            
            if any(line_lower.startswith(pattern) for pattern in skip_patterns):
                continue
            
            # Skip signatures
            if line_lower in ['the customer service team', "l'équipe service client", 'airbnb customer service', 'el equipo de atención al cliente']:
                continue
            
            final_lines.append(line_stripped)
        
        result = '\n'.join(final_lines).strip()

        # Failsafe
        if not result or len(result) < 20:
            print(f"⚠️ Nettoyage a tout supprimé, retour à l'original")
            result = response.strip()
            result = re.sub(r'^Dear \[Client\],?\s*', '', result, flags=re.IGNORECASE | re.MULTILINE)
            result = re.sub(r'\[Your name\]\s*$', '', result, flags=re.IGNORECASE | re.MULTILINE)
            result = re.sub(r'As an?\s+[^.]+\.\s*', '', result, flags=re.IGNORECASE)
        
        return result

    def _validate_response(self, response: str, original_review: str, expected_language: str) -> bool:
        """Valide que la réponse générée est acceptable"""
        
        # Trop courte ou trop longue
        if len(response) < 20 or len(response) > 800:  # ← Augmenté de 600 à 800
            return False
        
        # Patterns suspects (modèle qui délire)
        suspicious_patterns = [
            'génère uniquement',
            'formule de politesse',
            'ne pas inclure',
            'do not include',
            'réponds en',
            'respond in',
            'écris une réponse',
            'write a response',
            '[inst]',  # ← Ajouté pour Mistral
            '[/inst]',
        ]
        
        response_lower = response.lower()
        if any(pattern in response_lower for pattern in suspicious_patterns):
            return False
        
        # Vérifier que la langue est correcte (plus tolérant)
        try:
            detected_lang = self.detect_language(response)
            # Plus tolérant pour les langues proches
            if detected_lang != expected_language:
                similar_langs = {
                    'en': ['es', 'nl', 'no'],
                    'es': ['en', 'pt', 'ca'],
                    'fr': ['es', 'it']
                }
                if detected_lang not in similar_langs.get(expected_language, []):
                    print(f"⚠️ Langue détectée: {detected_lang}, attendue: {expected_language}")
                    return False
        except:
            pass
        
        return True  # ← Retiré la vérification de répétition qui est trop stricte
    
    def _generate_with_ai(self, review_text: str, tone: str, language: str = 'fr', greeting: str = 'Dear customer', closing: str = 'Best regards,\nThe Customer Service Team') -> str:
        """Génère une réponse avec GPT4All (LLM local) dans la langue détectée"""
        
        if not self.model:
            sentiment = self.detect_sentiment(review_text)
            templates = self._get_templates(tone, sentiment, language)
            response_body = ' '.join([templates['greeting'], templates['acknowledgment'], templates['closing']])
            return f"{greeting},\n\n{response_body}\n\n{closing}"
        
        tone_descriptions = {
            'formel': {
                'fr': 'professionnel',
                'en': 'professional',
                'es': 'profesional',
            },
            'amical': {
                'fr': 'amical',
                'en': 'friendly',
                'es': 'amigable',
            },
            'empathique': {
                'fr': 'empathique',
                'en': 'empathetic',
                'es': 'empático',
            }
        }
        
        tone_desc = tone_descriptions.get(tone, tone_descriptions['formel']).get(language, 'professional')
        
        # PROMPTS SIMPLIFIÉS PAR LANGUE
# PROMPTS ADAPTÉS POUR MISTRAL 7B
        if language == 'fr':
            prompt = f"""[INST] Tu es un assistant service client professionnel.

        Avis client : "{review_text}"

        Écris une réponse courte et professionnelle en français (maximum 80 mots).
        - Si l'avis est positif : remercie chaleureusement
        - Si l'avis est négatif : excuse-toi et propose une solution
        - Ton : {tone_desc}

        Réponds directement sans introduction ni signature. [/INST]

        """

        elif language == 'en':
            prompt = f"""[INST] You are a professional customer service assistant.

        Customer review: "{review_text}"

        Write a short professional response in English (maximum 80 words).
        - If positive review: thank warmly
        - If negative review: apologize and offer solution
        - Tone: {tone_desc}

        Respond directly without introduction or signature. [/INST]

        """

        else:
            prompt = f"""[INST] Eres un asistente profesional de servicio al cliente.

        Reseña del cliente: "{review_text}"

        Escribe una respuesta corta y profesional en español (máximo 80 palabras).
        - Si es positiva: agradece calurosamente
        - Si es negativa: discúlpate y ofrece solución
        - Tono: {tone_desc}

        Responde directamente sin introducción ni firma. [/INST]

        """
                
        # RETRY JUSQU'À 3 FOIS
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                with self.model.chat_session():
                    response = self.model.generate(
                    prompt,
                    max_tokens=120,  # Augmenté légèrement
                    temp=0.7,        # Mistral marche mieux à 0.7
                    top_k=40,
                    top_p=0.9
                )
                    
                    response_body = self._clean_ai_response(response)
                    
                    # VALIDATION STRICTE
                    is_valid = self._validate_response(response_body, review_text, language)
                    
                    if is_valid:
                        return f"{greeting},\n\n{response_body}\n\n{closing}"
                    else:
                        print(f"⚠️ Tentative {attempt + 1}/{max_attempts} : réponse invalide")
                        continue
            
            except Exception as e:
                print(f"Erreur génération (tentative {attempt + 1}): {e}")
                continue
        
        # Après 3 échecs → Fallback templates
        print(f"⚠️ GPT4All a échoué après {max_attempts} tentatives, utilisation des templates")
        sentiment = self.detect_sentiment(review_text)
        templates = self._get_templates(tone, sentiment, language)
        response_body = ' '.join([templates['greeting'], templates['acknowledgment'], templates['closing']])
        return f"{greeting},\n\n{response_body}\n\n{closing}"
    
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
                        'greeting': 'Merci beaucoup pour cet avis super !',
                        'acknowledgment': 'On est vraiment contents que tu aies eu une bonne expérience avec nous.',
                        'closing': 'On espère te revoir très bientôt !'
                    },
                    'negative': {
                        'greeting': 'Merci de nous avoir donné ton retour honnête.',
                        'acknowledgment': 'On est vraiment désolés que ça ne se soit pas bien passé.',
                        'closing': 'N\'hésite pas à nous contacter directement !'
                    },
                    'neutral': {
                        'greeting': 'Merci pour ton avis !',
                        'acknowledgment': 'Ton retour nous aide à nous améliorer.',
                        'closing': 'N\'hésite pas si besoin !'
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
                        'greeting': 'Thank you so much for this great review!',
                        'acknowledgment': 'We\'re really happy you had a good experience with us.',
                        'closing': 'Hope to see you again soon!'
                    },
                    'negative': {
                        'greeting': 'Thanks for your honest feedback.',
                        'acknowledgment': 'We\'re really sorry things didn\'t go well.',
                        'closing': 'Don\'t hesitate to contact us directly!'
                    },
                    'neutral': {
                        'greeting': 'Thanks for your review!',
                        'acknowledgment': 'Your feedback helps us improve.',
                        'closing': 'Feel free to reach out if needed!'
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