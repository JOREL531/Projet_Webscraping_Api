from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import pandas as pd
import unicodedata
import requests

# def extract_review_from_yelp(url):
#     driver = webdriver.Chrome()
#     driver.get(url)

#     wait = WebDriverWait(driver, 10)
    
#     liste_review = []
#     while True:
#         cards = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#reviews span.raw__09f24__T4Ezm")))
#         for card in cards:
#                 liste_review.append(card.text.strip())

#         # on garde le texte du 1er avis pour détecter changement
#         first_text = cards[0].text       

#         # ---- Page suivante ----
#         try:
#              # bouton "page suivante"
#             next_btn = wait.until(EC.element_to_be_clickable(
#                 (By.CSS_SELECTOR,
#                  "button[aria-label*='Next'], "
#                  "button[aria-label*='Suiv'], "
#                  "a[aria-label*='Next'], "
#                  "a[aria-label*='Suiv']")
#             ))

#             driver.execute_script("arguments[0].scrollIntoView();", next_btn)
#             driver.execute_script("arguments[0].click();", next_btn)

#             # ---- attendre nouvelle page ----
#             wait.until(lambda d: (
#                 len(d.find_elements(
#                     By.CSS_SELECTOR,
#                     "#reviews span.raw__09f24__T4Ezm"
#                 )) > 0
#                 and d.find_elements(
#                     By.CSS_SELECTOR,
#                     "#reviews span.raw__09f24__T4Ezm"
#                 )[0].text.strip() != first_text
#             ))

#         except TimeoutException:
#             #print("\nPlus de page suivante")
#             break

#     driver.quit()
#     return liste_review

def extract_review_from_yelp(url, max_reviews=20):
    driver = webdriver.Chrome()
    driver.get(url)

    wait = WebDriverWait(driver, 10)
    
    liste_review = []
    page = 0
    while True:
        cards = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#reviews span.raw__09f24__T4Ezm")))
        for card in cards:
                liste_review.append(card.text.strip())

                # ---- arrêt si limite atteinte ----
                if len(liste_review) >= max_reviews:
                    driver.quit()
                    return liste_review

        # on garde le texte du 1er avis pour détecter changement
        #first_text = cards[0].text       

        # ---- Page suivante ----
        page += 1
        next_url = url + f"&start={page*10}"
        driver.get(next_url)

        try:
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#reviews span.raw__09f24__T4Ezm")
            ))
        except TimeoutException:
            #print("Plus de page suivante")
            break

    driver.quit()
    return liste_review