from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import unicodedata

def enlever_accents(texte):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texte)
        if unicodedata.category(c) != 'Mn'
    )

def rechercher_elements(liste, recherche):
    # Normaliser et séparer les mots-clés
    mots = recherche.lower().split()
    resultat = []
    for element in liste:
        element_sans_accents = enlever_accents(element).lower()
        # Vérifier que tous les mots sont présents
        if all(enlever_accents(mot).lower() in element_sans_accents for mot in mots):
            resultat.append(element)
    return resultat

def search_company_from_trustpilot(company):
    driver = webdriver.Chrome()
    driver.get("https://www.trustpilot.com/")

    wait = WebDriverWait(driver, 6)

    # ---- Recherche ----
    search = wait.until(EC.presence_of_element_located((By.NAME, "query")))
    search.send_keys(company)
    search.send_keys(Keys.RETURN)

    page = 1
    liste_elem = []
    while True:
        # ---- Cartes de la page courante ----
        cards = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[name='business-unit-card']")))

        # lire les URLs
        for card in cards:
            ps = card.find_elements(By.TAG_NAME, "p")
            if len(ps) >= 2:
                # print(ps[1].text.strip())
                liste_elem.append(ps[1].text.strip())

        # ---- Page suivante ----
        try:
            next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[name='pagination-button-next']")))
            # on garde une référence à un élément de l’ancienne page
            old_first_card = cards[0]
            # clic (JS car Trustpilot bloque parfois les clics standards)
            driver.execute_script("arguments[0].click();", next_btn)
            # maintenant on attend que l’ancienne page disparaisse
            wait.until(EC.staleness_of(old_first_card))
            page += 1

        except TimeoutException:
            # print("\nPlus de page suivante 👍")
            break

    driver.quit()

    result = rechercher_elements(liste_elem, company)
    result
    return result


def extract_review_from_trustpilot(url):
    driver = webdriver.Chrome()
    driver.get(url)

    wait = WebDriverWait(driver, 6)

    page = 1
    liste_review = []
    while True:
        cards = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[class='styles_reviewContent__tuXiN']")))
        for card in cards:
            # Extraire le texte principal de l'avis
            review_text = None
            try:
                ps = card.find_elements(By.TAG_NAME, "p")
                if ps:
                    review_text = ps[0].text.strip()
            except Exception:
                review_text = None

            # Essayer d'extraire la note (ex: "5.0" ou "5 out of 5")
            rating = None
            try:
                # Trustpilot encode souvent la note dans un élément avec aria-label contenant "out of" ou "étoiles"
                # Cherche les éléments avec aria-label
                possible = card.find_elements(By.XPATH, ".//*[contains(@aria-label, 'out of')] | .//*[contains(@aria-label, 'étoile')]")
                if possible:
                    rating_label = possible[0].get_attribute('aria-label')
                    # extraire le chiffre au début
                    import re
                    m = re.search(r"([0-9]+(?:[\.,][0-9]+)?)", rating_label)
                    if m:
                        rating = float(m.group(1).replace(',', '.'))
                else:
                    # parfois la note est dans le titre d'une image
                    imgs = card.find_elements(By.TAG_NAME, 'img')
                    for im in imgs:
                        title = im.get_attribute('title') or ''
                        if title:
                            m = __import__('re').search(r"([0-9]+(?:[\.,][0-9]+)?)", title)
                            if m:
                                rating = float(m.group(1).replace(',', '.'))
                                break
            except Exception:
                rating = None

            # Essayer d'extraire le titre de l'avis (h2) qui indique le ressenti principal
            sentiment_label = None
            try:
                # Chercher le h2 avec l'attribut data-service-review-title-typography
                h2_elems = card.find_elements(By.CSS_SELECTOR, 'h2[data-service-review-title-typography="true"]')
                if h2_elems and len(h2_elems) > 0:
                    sentiment_label = h2_elems[0].text.strip()
                else:
                    # Fallback: chercher simplement le premier h2
                    h2_elems = card.find_elements(By.TAG_NAME, 'h2')
                    if h2_elems and len(h2_elems) > 0:
                        sentiment_label = h2_elems[0].text.strip()
            except Exception:
                sentiment_label = None

            # Construire l'objet review
            item = {
                'text': review_text if review_text else '',
                'rating': rating,
                'sentiment_label': sentiment_label
            }
            liste_review.append(item)

        # ---- Page suivante ----
        try:
            next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[name='pagination-button-next']")))
            # on garde une référence à un élément de l’ancienne page
            old_first_card = cards[0]
            # clic (JS car Trustpilot bloque parfois les clics standards)
            driver.execute_script("arguments[0].click();", next_btn)
            # maintenant on attend que l’ancienne page disparaisse
            wait.until(EC.staleness_of(old_first_card))
            page += 1

        except TimeoutException:
            # print("\nPlus de page suivante 👍")
            break

    driver.quit()
    return liste_review