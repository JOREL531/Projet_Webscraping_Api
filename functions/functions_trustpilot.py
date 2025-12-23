from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import pandas as pd
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
                ps = card.find_elements(By.TAG_NAME, "p")
                if ps:  # si la liste n'est pas vide
                    liste_review.append(ps[0].text.strip())

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