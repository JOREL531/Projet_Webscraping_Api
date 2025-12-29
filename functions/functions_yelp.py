import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def extract_yelp_reviews(url: str, max_reviews: int = 50, headless: bool = False):
    """
    Extrait les avis depuis une page Yelp
    
    Args:
        url: URL de la page Yelp du restaurant
        max_reviews: Nombre maximum d'avis à récupérer
        headless: Mode sans interface graphique
    
    Returns:
        Liste de textes d'avis
    """
    options = uc.ChromeOptions()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = uc.Chrome(options=options)
    reviews = []
    
    try:
        print(f"🔍 Accès à Yelp: {url}")
        driver.get(url)
        time.sleep(3)
        
        # Attendre que les avis se chargent
        wait = WebDriverWait(driver, 10)
        
        # Sélecteur pour les avis Yelp
        review_elements = driver.find_elements(By.CSS_SELECTOR, "p.comment__09f24__D0cxf")
        
        print(f"✅ {len(review_elements)} avis trouvés")
        
        for element in review_elements[:max_reviews]:
            try:
                review_text = element.text.strip()
                if review_text:
                    reviews.append(review_text)
            except Exception as e:
                print(f"⚠️ Erreur extraction avis: {e}")
                continue
        
        print(f"✅ {len(reviews)} avis extraits de Yelp")
        return reviews
    
    except Exception as e:
        print(f"❌ Erreur scraping Yelp: {e}")
        return []
    
    finally:
        driver.quit()