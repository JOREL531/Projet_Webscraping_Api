from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd
import unicodedata
import re


def extract_review_from_gloogle_play_store(url, max):
    driver = webdriver.Chrome()
    driver.get(url)
    wait = WebDriverWait(driver, 10)

    bouton = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Afficher tous les avis')]")))
    bouton.click()

    # -------- PARAMETRE --------
    MAX_AVIS = max

    # -------- SELECTION DU CONTENEUR D'AVIS --------
    container = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//div[@jsname='bN97Pc']")  # conteneur scrollable
        )
    )

    avis_text_list = []
    last_height = 0  # la hauteur enregistrée au scroll précédent
    same_scroll_count = 0  # Compte combien de fois on a scrollé sans obtenir de nouveaux avis

    while len(avis_text_list) < MAX_AVIS and same_scroll_count < 5:
        
        # récupérer tous les avis actuellement visibles
        avis_elements = driver.find_elements(By.XPATH, "//div[contains(@class,'h3YV2d')]")

        for el in avis_elements:
            txt = el.text.strip()
            if txt and txt not in avis_text_list:
                avis_text_list.append(txt)

            if len(avis_text_list) >= MAX_AVIS:
                break
        
        # -------- SCROLL --------
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", container)
        time.sleep(2)

        # vérifier si ça charge encore
        new_height = driver.execute_script("return arguments[0].scrollHeight", container)
        if new_height == last_height:
            same_scroll_count += 1
        else:
            same_scroll_count = 0
            last_height = new_height
    driver.quit()
    return avis_text_list


def search_company_from_google_play_store(company):
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    driver.get("https://play.google.com/")

    # ---- Recherche ----

    first_card = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class='VfPpkd-Bz112c-LgbsSe yHy1rc eT1oJ mN1ivc']"))
    )
    driver.execute_script("arguments[0].click();", first_card)

    search = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Rechercher des applis et jeux']")))
    search.send_keys(company)
    search.send_keys(Keys.RETURN)

    time.sleep(5)
    #---- Premier résultat ----
    first_card = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@class,'Si6A0c Gy4nib') or contains(@class,'Qfxief')]"))
    )

    # # Option 1 : cliquer directement
    driver.execute_script("arguments[0].click();", first_card)

    # Option 2 : récupérer l'URL
    # url = first_card.get_attribute("href")
    # driver.get(url)

    return driver


def search_company_from_google_play_store_2(company):
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    driver.get("https://play.google.com/")

    # Ouvrir la recherche
    search_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.VfPpkd-Bz112c-LgbsSe"))
    )
    driver.execute_script("arguments[0].click();", search_btn)

    # Saisir la recherche
    search = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Rechercher des applis et jeux']"))
    )
    search.send_keys(company)
    search.send_keys(Keys.RETURN)

    # Attendre que les résultats apparaissent
    time.sleep(3)

    # Récupérer tous les liens apps
    cards = driver.find_elements(
        By.XPATH, "//a[contains(@href,'/store/apps/details?id=')]"
    )

    # Chercher le lien qui correspond le mieux à la recherche
    target_card = None
    company_lower = company.lower().replace(" ", "")
    for card in cards:
        href = card.get_attribute("href").lower().replace(" ", "")
        if company_lower in href:
            target_card = card
            break

    if not target_card:
        driver.quit()
        return print(f"Aucun résultat correspondant à '{company}' trouvé sur Google Play Store.")

    # Cliquer dessus
    driver.execute_script("arguments[0].click();", target_card)

    # Attendre que la page app soit chargée
    wait.until(EC.url_contains("/store/apps/details?id="))

    return driver


def extract_reviews_and_ratings_from_google_play_store(company, max_avis=30):
    driver = search_company_from_google_play_store_2(company)
    # driver.get(url)
    wait = WebDriverWait(driver, 10)

    # Bouton "Afficher tous les avis"
    bouton = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Afficher tous les avis')]"))
    )
    bouton.click()

    # Conteneur scrollable
    container = wait.until(
        EC.presence_of_element_located((By.XPATH, "//div[@jsname='bN97Pc']"))
    )

    results = []
    last_height = 0
    same_scroll_count = 0

    while len(results) < max_avis and same_scroll_count < 5:

        # Toutes les cartes d’avis visibles
        review_cards = driver.find_elements(By.XPATH, "//div[contains(@class,'RHo1pe')]")

        for card in review_cards:
            try:
                # ----- RATING -----
                rating_el = card.find_element(By.CSS_SELECTOR, "div[role='img'][aria-label]")
                aria_label = rating_el.get_attribute("aria-label")
                rating = int(re.search(r"\d+", aria_label).group())

                # ----- TEXTE -----
                review_el = card.find_element(By.CLASS_NAME, "h3YV2d")
                review_text = review_el.text.strip()

                item = {
                    "rating": rating,
                    "review": review_text
                }

                if item not in results:
                    results.append(item)

                if len(results) >= max_avis:
                    break

            except Exception:
                continue

        # ----- SCROLL -----
        driver.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollHeight", container
        )
        time.sleep(2)

        new_height = driver.execute_script(
            "return arguments[0].scrollHeight", container
        )

        if new_height == last_height:
            same_scroll_count += 1
        else:
            same_scroll_count = 0
            last_height = new_height

    driver.quit()
    return results
