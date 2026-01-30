from unittest.mock import MagicMock, patch

import pytest
from selenium.webdriver.common.by import By

from src.crawler.core import YahooFinanceCrawler


@pytest.fixture
def mock_driver():
    with patch('src.crawler.core.webdriver.Chrome') as mock_chrome:
        driver = MagicMock()
        mock_chrome.return_value = driver
        yield driver


@pytest.fixture
def crawler(mock_driver):
    return YahooFinanceCrawler(region='Brazil', base_url='http://test.url')


def test_initialization(crawler):
    assert crawler.region == 'Brazil'
    assert crawler.base_url == 'http://test.url'
    assert crawler.data == []
    assert crawler.driver is not None


def test_setup_driver_options():
    with patch('src.crawler.core.webdriver.Chrome') as mock_chrome:
        with patch('src.crawler.core.Options') as mock_options:
            YahooFinanceCrawler(region='US', base_url='http://test.url')
            mock_options.return_value.add_argument.assert_any_call(
                '--no-sandbox'
            )
            assert mock_options.return_value.page_load_strategy == 'eager'


def test_run_flow(crawler):
    with (
        patch.object(crawler, '_apply_region_filter') as mock_apply,
        patch.object(crawler, '_set_rows_per_page_to_100') as mock_rows,
        patch.object(crawler, '_scrape_all_pages') as mock_scrape,
        patch.object(crawler, '_save_to_csv') as mock_save,
    ):
        crawler.run()

        crawler.driver.get.assert_called_with('http://test.url')
        mock_apply.assert_called_once()
        mock_rows.assert_called_once()
        mock_scrape.assert_called_once()
        mock_save.assert_called_once()
        crawler.driver.quit.assert_called_once()


def test_run_failure(crawler):
    crawler.driver.get.side_effect = Exception('Simulated connection error')

    with patch('src.crawler.core.logger') as mock_logger:
        with pytest.raises(Exception) as excinfo:
            crawler.run()

        assert 'Simulated connection error' in str(excinfo.value)
        mock_logger.error.assert_called_once()
        crawler.driver.quit.assert_called_once()


def test_save_to_csv(crawler):
    crawler.data = [{'symbol': 'A', 'name': 'B', 'price': '10'}]

    with patch('builtins.open', new_callable=MagicMock) as mock_open:
        with patch('src.crawler.core.makedirs') as mock_makedirs:
            with patch('src.crawler.core.path.exists', return_value=False):
                with patch('src.crawler.core.csv.DictWriter') as mock_writer:
                    crawler._save_to_csv()

                    mock_makedirs.assert_called_with('cdn')
                    assert mock_open.called
                    mock_writer.return_value.writeheader.assert_called_once()
                    mock_writer.return_value.writerows.assert_called_with(
                        crawler.data
                    )


def test_close(crawler):
    crawler.close()
    crawler.driver.quit.assert_called_once()


def test_apply_region_filter(crawler):
    EXPECTED_CLICKS = 2
    EXPECTED_CALLS = 1

    with patch('src.crawler.core.WebDriverWait') as mock_wait:
        mock_element = MagicMock()
        mock_wait.return_value.until.return_value = mock_element

        mock_search_input = MagicMock()
        crawler.driver.find_element.return_value = mock_search_input
        crawler.driver.find_elements.return_value = []

        crawler._apply_region_filter()

        assert mock_wait.call_count >= EXPECTED_CALLS
        crawler.driver.find_element.assert_called_with(
            By.CSS_SELECTOR, 'input[placeholder="Search..."]'
        )
        mock_search_input.clear.assert_called_once()
        mock_search_input.send_keys.assert_called_with('Brazil')
        assert crawler.driver.execute_script.call_count >= EXPECTED_CLICKS


def test_apply_region_filter_clears_selection(crawler):
    with patch('src.crawler.core.WebDriverWait') as mock_wait:
        mock_checkbox = MagicMock()
        mock_checkbox.is_selected.return_value = True

        crawler.driver.find_elements.side_effect = [[mock_checkbox], []]

        crawler.driver.find_element.return_value = MagicMock()

        crawler._apply_region_filter()

        crawler.driver.execute_script.assert_any_call(
            'arguments[0].click();', mock_checkbox
        )


def test_apply_region_filter_clearing_exception(crawler):
    with patch('src.crawler.core.WebDriverWait') as mock_wait:
        mock_wait.side_effect = [
            MagicMock(),
            MagicMock(),
            Exception('Simulated error while clearing selection'),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
        ]

        crawler.driver.find_element.return_value = MagicMock()

        with patch('src.crawler.core.logger') as mock_logger:
            crawler._apply_region_filter()

            mock_logger.warning.assert_called_with(
                'Error while clearing selection: Simulated error while clearing selection'
            )


def test_set_rows_per_page_to_100(crawler):
    EXPECTED_JS_CLICKS = 2
    EXPECTED_CALLS = 3

    with patch('src.crawler.core.WebDriverWait') as mock_wait:
        mock_dropdown = MagicMock()
        mock_option_100 = MagicMock()
        mock_updated_table = MagicMock()

        mock_wait.return_value.until.side_effect = [
            mock_dropdown,
            mock_option_100,
            mock_updated_table,
        ]

        with patch('src.crawler.core.logger') as mock_logger:
            crawler._set_rows_per_page_to_100()

            assert mock_wait.return_value.until.call_count == EXPECTED_CALLS
            assert (
                crawler.driver.execute_script.call_count == EXPECTED_JS_CLICKS
            )
            mock_logger.info.assert_any_call(
                'Selected 100 rows per page via JS.'
            )
            mock_logger.info.assert_any_call('Table updated to 100 rows.')


def test_scrape_all_pages(crawler):
    EXPECTED_CALLS = 2
    mock_next_btn = MagicMock()
    mock_next_btn.is_enabled.return_value = True
    mock_next_btn.get_attribute.side_effect = [None, 'true']

    crawler.driver.find_elements.return_value = [mock_next_btn]

    with patch.object(crawler, '_extract_current_page') as mock_extract:
        crawler._scrape_all_pages()

        assert mock_extract.call_count == EXPECTED_CALLS
        crawler.driver.execute_script.assert_called_once_with(
            'arguments[0].click();', mock_next_btn
        )
