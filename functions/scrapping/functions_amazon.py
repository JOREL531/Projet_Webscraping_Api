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
import requests
import pickle


# Sauvegarder les cookies après une première connexion manuelle
def save_cookies(user_agent):

    chrome_options = Options()
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument("referer=https://www.amazon.fr/ap/signin?openid.pape.max_auth_age=900&openid.return_to=https%3A%2F%2Fwww.amazon.fr%2Fgp%2Fyourstore%2Fhome%3Fpath%3D%252Fgp%252Fyourstore%252Fhome%26useRedirectOnSuccess%3D1%26signIn%3D1%26action%3Dsign-out%26ref_%3Dnav_AccountFlyout_signout&openid.assoc_handle=frflex&openid.mode=checkid_setup&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0")


    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.amazon.fr/ap/signin?openid.pape.max_auth_age=900&openid.return_to=https%3A%2F%2Fwww.amazon.fr%2Fgp%2Fyourstore%2Fhome%3Fpath%3D%252Fgp%252Fyourstore%252Fhome%26useRedirectOnSuccess%3D1%26signIn%3D1%26action%3Dsign-out%26ref_%3Dnav_AccountFlyout_signout&openid.assoc_handle=frflex&openid.mode=checkid_setup&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0")
    
    # Connectez-vous MANUELLEMENT ici
    input("Connectez-vous manuellement puis appuyez sur Entrée...")
    
    # Sauvegarder les cookies
    with open("cookies.pkl", "wb") as file:
        pickle.dump(driver.get_cookies(), file)
    
    driver.quit()

# Recharger les cookies pour une session ultérieure
def load_cookies(url):
    driver = webdriver.Chrome()
    driver.get(url)
    
    # Charger les cookies sauvegardés
    with open("cookies.pkl", "rb") as file:
        cookies = pickle.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)
    
    # Recharger la page avec les cookies
    driver.refresh()
    
    return driver

def extract_review_from_amazon(url, max_reviews):
    driver = load_cookies(url)
    wait = WebDriverWait(driver, 5)
    bouton = wait.until(EC.element_to_be_clickable((By.XPATH,  "//a[contains(., 'Voir plus de commentaires')]")))
    bouton.click()

    reviews_text = []
    page = 1
    while len(reviews_text) < max_reviews:
        try:
                wait.until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, '//span[@data-hook="review-body"]')
                    )
                )

                reviews = driver.find_elements(
                        By.XPATH, 
                        '//span[@data-hook="review-body"]//span'
                    )
                
                for review in reviews:
                    text = review.text.strip()
                    reviews_text.append(text)
                    if len(reviews_text) >= max_reviews:
                        # return liste_review
                        break

                next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Suivant')]")))
                driver.execute_script("arguments[0].click();", next_btn)
                # maintenant on attend que l’ancienne page disparaisse
                wait.until(EC.staleness_of(reviews[0]))
                page += 1

        except TimeoutException:
            # print("\nPlus de page suivante")
            break
    driver.quit()
    return reviews_text
