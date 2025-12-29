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


def extract_review_from_app_store(url, max):
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