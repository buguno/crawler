import csv
import datetime
import logging
import time
from os import makedirs, path
from typing import Dict, List

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


class YahooFinanceCrawler:
    def __init__(self, region: str, base_url: str, headless: bool = True):
        self.region = region
        self.base_url = base_url
        self.headless = headless
        self.data: List[Dict[str, str]] = []
        self.driver = self._setup_driver()

    def _setup_driver(self) -> webdriver.Chrome:
        """Configure and return an instance of the Chrome WebDriver."""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument('--headless')

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 '
            'Safari/537.36'
        )

        # 'eager' strategy: releases script as soon as HTML loads
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
            logger.info(f'Initializing crawler for region: {self.region}')
            self.driver.get(self.base_url)

            self._apply_region_filter()
            self._set_rows_per_page_to_100()
            self._scrape_all_pages()
            self._save_to_csv()
            logger.info(f'Done. Saved {len(self.data)} rows to CSV.')

        except Exception as error:
            logger.error(f'An error occurred: {error}', exc_info=True)
            raise error
        finally:
            self.close()

    def _apply_region_filter(self) -> None:
        """Robustly applies the region filter."""
        logger.info(f'Attempting to select region: {self.region}')

        # 1. Try to close initial "Explore..." popup if present
        try:
            initial_done = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    '//div[contains(text(), "Explore")]//following::button[contains(., "Done")]',
                ))
            )
            initial_done.click()
            logger.info('Initial popup closed.')
        except Exception:
            pass

        logger.info('Looking for Region button...')
        region_btn = WebDriverWait(self.driver, 15).until(
            EC.element_to_be_clickable((
                By.XPATH,
                '//button[contains(@class, "menuBtn") and contains(., "Region")]',
            ))
        )
        region_btn.click()
        logger.info('Region button clicked.')

        logger.info('Clearing previous selections...')
        try:
            # Wait for list to load
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((
                    By.CSS_SELECTOR,
                    'input[placeholder="Search..."]',
                ))
            )

            # Find all checked checkboxes within the menu
            checked_boxes = self.driver.find_elements(
                By.XPATH,
                '//div[contains(@class,"menu-surface-dialog")]//input[@type="checkbox"]',
            )

            for box in checked_boxes:
                if box.is_selected():
                    self.driver.execute_script('arguments[0].click();', box)
                    logger.info('Previous checkbox unchecked.')
                    time.sleep(0.5)
        except Exception as error:
            logger.warning(f'Error while clearing selection: {error}')

        # 4. Search and select the desired region
        search_input = self.driver.find_element(
            By.CSS_SELECTOR, 'input[placeholder="Search..."]'
        )
        search_input.clear()
        search_input.send_keys(self.region)
        logger.info(f"Typed '{self.region}' in search box.")

        # Click the specific checkbox for the region
        try:
            checkbox = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    f'//label[contains(., "{self.region}")]//input[@type="checkbox"] | //span[contains(., "{self.region}")]/following-sibling::input[@type="checkbox"]',
                ))
            )
            self.driver.execute_script('arguments[0].click();', checkbox)
            logger.info(f"Region '{self.region}' checkbox checked via JS.")
        except Exception as error:
            logger.error(f'Error checking checkbox: {error}')
            raise

        # 5. Click APPLY button
        try:
            apply_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    '//button[contains(., "Apply")]',
                ))
            )
            self.driver.execute_script('arguments[0].click();', apply_btn)
            logger.info('Apply button clicked.')
        except Exception:
            logger.warning('Apply button not found.')

        # 6. Wait for menu to close
        WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located((
                By.CSS_SELECTOR,
                'input[placeholder="Search..."]',
            ))
        )
        logger.info('Filter applied (menu closed).')

    def _set_rows_per_page_to_100(self) -> None:
        """Changes the rows per page from default (25) to 100."""
        logger.info('Changing rows per page to 100...')
        try:
            # 1. Click on the dropdown "25"
            rows_dropdown = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    '//span[contains(text(), "Rows per page")]/following::button[1] | //button[@title="25"]',
                ))
            )
            self.driver.execute_script('arguments[0].click();', rows_dropdown)
            logger.info('Rows dropdown clicked.')

            # 2. Click on the option "100"
            option_100 = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    'div[role="option"][data-value="100"]',
                ))
            )
            self.driver.execute_script('arguments[0].click();', option_100)
            logger.info('Selected 100 rows per page via JS.')

            # 3. Wait for the table to update (the button should change the title to "100")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    '//button[@title="100"]',
                ))
            )
            logger.info('Table updated to 100 rows.')
            time.sleep(3)  # Extra pause to ensure data is loaded

        except Exception as error:
            logger.warning(
                f'Could not change rows per page (sticking to default): {error}'
            )

    def _scrape_all_pages(self) -> None:
        """Loops through all pages and scrapes data."""
        page_num = 1
        while True:
            logger.info(f'Scraping page {page_num}...')
            self._extract_current_page()

            try:
                # Find Next button by data-testid
                next_btn = self.driver.find_elements(
                    By.CSS_SELECTOR, '[data-testid="next-page-button"]'
                )

                # Check if exists and enabled
                if next_btn and next_btn[0].is_enabled():
                    if next_btn[0].get_attribute('disabled') is not None:
                        logger.info('Next button is disabled. End of pages.')
                        break

                    # JS click to be safe
                    self.driver.execute_script(
                        'arguments[0].click();', next_btn[0]
                    )
                    logger.info(
                        f'Next button clicked. Going to page {page_num + 1}...'
                    )

                    # Wait for table reload
                    time.sleep(3)
                    page_num += 1
                else:
                    logger.info(
                        'No more pages (Next button not found or disabled).'
                    )
                    break
            except Exception as error:
                logger.error(f'Pagination stopped: {error}')
                break

    def _extract_current_page(self) -> None:
        """Extracts data from the currently visible table."""
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                'table, [role="table"], [data-testid="data-table"]',
            ))
        )

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        table = (
            soup.find('table')
            or soup.find(attrs={'role': 'table'})
            or soup.find(attrs={'data-testid': 'data-table'})
        )

        if not table:
            return

        headers = []
        header_row = table.find('thead')
        if header_row:
            headers = [
                th.get_text(strip=True).lower()
                for th in header_row.find_all(['th', 'td'])
            ]
        if not headers:
            first_row = table.find('tr')
            if first_row:
                headers = [
                    th.get_text(strip=True).lower()
                    for th in first_row.find_all(['th', 'td'])
                ]

        idx_symbol = 0
        idx_name = 1
        idx_price = 2
        for index, header in enumerate(headers):
            if 'symbol' in header:
                idx_symbol = index
            elif 'name' in header:
                idx_name = index
            elif 'price' in header:
                idx_price = index

        tbody = table.find('tbody') or table
        rows = tbody.find_all('tr')

        count_before = len(self.data)
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if cells and cells[0].get_text(strip=True).lower() == 'symbol':
                continue
            if len(cells) > max(idx_symbol, idx_name, idx_price):
                symbol = cells[idx_symbol].get_text(strip=True)
                name = cells[idx_name].get_text(strip=True)
                price = cells[idx_price].get_text(strip=True).replace(',', '')

                # Avoid duplicates
                if symbol and not any(
                    data['symbol'] == symbol for data in self.data
                ):
                    self.data.append({
                        'symbol': symbol,
                        'name': name,
                        'price': price,
                    })

        logger.info(f'Extracted {len(self.data) - count_before} new rows.')

    def _save_to_csv(self) -> None:
        """Save self.data to a CSV file."""
        if not self.data:
            logger.warning('No data to save.')
            return

        output_dir = 'cdn'
        if not path.exists(output_dir):
            makedirs(output_dir)

        current_datetime = datetime.datetime.now()
        timestamp = int(current_datetime.timestamp())
        filename = f'{timestamp}_yahoo_finance_crawler_{self.region.replace(" ", "_")}.csv'
        file_path = path.join(output_dir, filename)

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=['symbol', 'name', 'price'],
                quoting=csv.QUOTE_ALL,
            )
            writer.writeheader()
            writer.writerows(self.data)
        logger.info(f'Saved to {file_path}')
