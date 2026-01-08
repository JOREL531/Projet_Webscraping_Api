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


def extract_reviews_and_ratings_from_google_play_store(url, max_avis=30):
    driver = webdriver.Chrome()
    driver.get(url)
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
