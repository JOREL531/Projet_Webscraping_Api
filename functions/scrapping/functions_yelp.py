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

def search_company_from_yelp(company):
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    driver.get("https://www.yelp.fr/")

    # ---- Recherche ----
    search = wait.until(EC.presence_of_element_located((By.ID, "search_description")))
    search.send_keys(company)
    search.send_keys(Keys.RETURN)

    # ---- Premier résultat ----
    first_card = wait.until(
        # EC.element_to_be_clickable((By.CSS_SELECTOR, "a[class='y-css-9o0pq']")) #y-css-1887ssu
        EC.element_to_be_clickable((By.XPATH, f"//a[contains(@name,'{company}')]"))
    )

    # Option 1 : cliquer directement
    driver.execute_script("arguments[0].click();", first_card)

    wait.until(lambda d: len(d.window_handles) > 1)
    driver.switch_to.window(driver.window_handles[-1])

    # Option 2 : récupérer l'URL 
    # url = first_card.get_attribute("href")
    # driver.get(url)

    return driver

def extract_review_from_yelp(url, max_reviews):
    driver = webdriver.Chrome()
    driver.get(url)

    wait = WebDriverWait(driver, 10)
    
    liste_review = []
    page = 1
    while len(liste_review) < max_reviews:
        try:

                cards = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#reviews span.raw__09f24__T4Ezm")))
                for card in cards:
                        liste_review.append(card.text.strip())

                        # ---- arrêt si limite atteinte ----
                        if len(liste_review) >= max_reviews:
                            break

                next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@class,'navigation-button') and contains(@class,'next-link')]")))
                driver.execute_script("arguments[0].click();", next_btn)
                # maintenant on attend que l’ancienne page disparaisse
                wait.until(EC.staleness_of(cards[0]))
                page += 1

        except TimeoutException:
            # print("\nPlus de page suivante")
            break
    driver.quit()
    return liste_review



def extract_reviews_and_ratings_from_yelp(company, max_reviews):
    driver = search_company_from_yelp(company)
    # driver.get(url)

    wait = WebDriverWait(driver, 10)

    results = []
    page = 1

    while len(results) < max_reviews:
        try:
            # Attendre les blocs d'avis
            wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, '//li[@class=" y-css-19cyavo-styles"]') #y-css-1sqelp2
                )
            )

            reviews = driver.find_elements(By.XPATH, '//li[@class=" y-css-19cyavo-styles"]')

            for review in reviews:
                try:
                    # Texte de l'avis
                    text = review.find_element(
                        By.CSS_SELECTOR, "span.raw__09f24__PkHSg" # raw__09f24__T4Ezm
                    ).text.strip()

                    # Rating
                    rating_el = review.find_element(
                        By.XPATH,
                        ".//ancestor::div[contains(@class,'arrange-unit')]//div[@role='img']"
                    )
                    rating = float(
                        rating_el.get_attribute("aria-label").split()[0]
                    )

                    if text:
                        results.append({
                            "rating": rating,
                            "review": text
                        })

                    if len(results) >= max_reviews:
                        break

                except Exception:
                    # Avis incomplet → on ignore
                    continue

            # Bouton suivant
            next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@class,'navigation-button') and contains(@class,'next-link')]")))
            driver.execute_script("arguments[0].click();", next_btn)

            # maintenant on attend que l’ancienne page disparaisse
            wait.until(EC.staleness_of(reviews[0]))
            page += 1

        except TimeoutException:
            break

    driver.quit()
    return results
