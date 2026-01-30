from os import getenv
from typing import Dict, List

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

load_dotenv()


class YahooFinanceCrawler:
    BASE_URL = getenv('BASE_URL')

    def __init__(self, region: str):
        self.region = region
        self.data: List[Dict[str, str]] = []
        self.driver = self._setup_driver()

    def _setup_driver(self) -> webdriver.Chrome:
        """Configure and return an instance of the Chrome WebDriver."""
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 '
            'Safari/537.36'
        )

        # Estratégia 'eager': libera o script assim que o HTML carregar
        chrome_options.page_load_strategy = 'eager'

        driver = webdriver.Chrome(options=chrome_options)
        return driver

    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()

    def run(self):
        """Main method that orchestrates the execution."""
        try:
            print(f'Initializing crawler for region: {self.region}')
            self.driver.get(self.BASE_URL)

            self._apply_region_filter()

            print('Script finished. Press Enter to close the browser...')
            input()
        except Exception as e:
            print(f'An error occurred: {e}')
            print('An error occurred. Press Enter to close the browser...')
            input()
            raise
        finally:
            self.close()

    def _apply_region_filter(self) -> None:
        """Apply the region filter."""
        print(f'Trying to select region: {self.region}')

        # 1. Try to close the initial "Explore..." popup
        try:
            initial_done = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    '//div[contains(text(), "Explore")]//following::button[contains(., "Done")]',
                ))
            )
            initial_done.click()
            print('Initial popup closed.')
        except Exception:
            pass

        # 2. Click on the Region button
        print('Looking for Region button...')
        region_btn = WebDriverWait(self.driver, 15).until(
            EC.element_to_be_clickable((
                By.XPATH,
                '//button[contains(@class, "menuBtn") and contains(., "Region")]',
            ))
        )
        region_btn.click()
        print('Region button clicked.')

        # 3. Wait for the search field and type the region
        search_input = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((
                By.CSS_SELECTOR,
                'input[placeholder="Search..."]',
            ))
        )
        search_input.clear()
        search_input.send_keys(self.region)
        print(f"Typed '{self.region}' in the search field.")

        # 4. Click on the specific checkbox for the region
        # Search for the input checkbox that is inside a label with the region title
        # or next to the region text
        try:
            checkbox = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    f'//label[contains(., "{self.region}")]//input[@type="checkbox"] | //span[contains(., "{self.region}")]/following-sibling::input[@type="checkbox"]',
                ))
            )
            # Force the click on the checkbox via JS
            self.driver.execute_script('arguments[0].click();', checkbox)
            print(f"Checkbox for region '{self.region}' marked via JS.")
        except Exception as e:
            print(f'Error trying to mark checkbox: {e}')
            raise

        # 5. Click on the Apply button
        try:
            apply_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    '//button[contains(., "Apply")]',
                ))
            )
            self.driver.execute_script('arguments[0].click();', apply_btn)
            print('Apply button clicked.')
        except Exception:
            print('Apply button not found.')

        # 6. Wait for the menu to close
        WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located((
                By.CSS_SELECTOR,
                'input[placeholder="Search..."]',
            ))
        )
        print('Filter applied (menu closed).')


if __name__ == '__main__':
    crawler = YahooFinanceCrawler(region='Argentina')
    crawler.run()
