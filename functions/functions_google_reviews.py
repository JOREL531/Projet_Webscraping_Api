import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def extract_google_reviews_full_best_effort(url: str, max_reviews: int = 50, headless: bool = False):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1400,900")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    def get_full_text_from_el(el):
       
        txt = (el.text or "").strip()

        aria = (el.get_attribute("aria-label") or "").strip()
        if len(aria) > len(txt):
            txt = aria

        
        js_txt = driver.execute_script("return arguments[0].textContent;", el)
        js_txt = (js_txt or "").strip()
        if len(js_txt) > len(txt):
            txt = js_txt

        return txt

    try:
        driver.get(url)
        time.sleep(3)

        # Cookies
        for xp in [
            "//button//*[contains(text(),'Tout accepter')]/..",
            "//button//*[contains(text(),'J’accepte')]/..",
            "//button//*[contains(text(),\"J'accepte\")]/..",
            "//button//*[contains(text(),'Accept all')]/..",
            "//button//*[contains(text(),'Accept')]/..",
        ]:
            try:
                btn = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.XPATH, xp)))
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(2)
                break
            except Exception:
                pass

        # Ouvrir "Avis / Reviews"
        for xp in [
            "//button[contains(@aria-label,'Avis')]",
            "//button[contains(@aria-label,'Reviews')]",
            "//*[@role='tab'][contains(.,'Avis')]",
            "//*[@role='tab'][contains(.,'Reviews')]",
        ]:
            try:
                wait.until(EC.element_to_be_clickable((By.XPATH, xp))).click()
                time.sleep(2)
                break
            except Exception:
                pass

        # Panel scroll 
        panel = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.m6QErb.DxyBCb.kA9KIf.dS8AEf"))
        )

        results = []
        seen = set()
        last_h = 0

        while len(results) < max_reviews:
            cards = driver.find_elements(By.CSS_SELECTOR, "div[data-review-id]")
            if not cards:
                break

            # Clique "More/Plus" sur les avis
            more_btns = driver.find_elements(By.CSS_SELECTOR, "button.w8nwRe.kyuRq")
            for b in more_btns:
                try:
                    driver.execute_script("arguments[0].click();", b)
                    time.sleep(0.05)
                except Exception:
                    pass

            # Extrait texte
            for c in cards:
                if len(results) >= max_reviews:
                    break
                try:
                    text_el = c.find_element(By.CSS_SELECTOR, "span.wiI7pd")
                    full = get_full_text_from_el(text_el)
                    # filtre basique
                    if full and len(full) > 30:
                        key = full[:180]
                        if key not in seen:
                            seen.add(key)
                            results.append(full)
                except Exception:
                    pass

            # scroll pour charger + avis
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", panel)
            time.sleep(2)

            new_h = driver.execute_script("return arguments[0].scrollHeight", panel)
            if new_h == last_h:
                break
            last_h = new_h

        return results

    finally:
        driver.quit()
