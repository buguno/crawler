import argparse
import logging
from os import getenv

from dotenv import load_dotenv

from src.crawler.core import YahooFinanceCrawler

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Yahoo Finance Crawler')
    parser.add_argument(
        '--region',
        type=str,
        default='Brazil',
        help='Region to filter (e.g., "United States", "Argentina")',
    )
    parser.add_argument(
        '--show-browser',
        action='store_true',
        help='Open the browser window visually (disable headless mode)',
    )
    args = parser.parse_args()

    base_url = getenv('BASE_URL')
    if not base_url:
        logger.error('BASE_URL environment variable is not set')
        return

    is_headless = not args.show_browser

    crawler = YahooFinanceCrawler(
        region=args.region, base_url=base_url, headless=is_headless
    )
    crawler.run()


if __name__ == '__main__':
    main()
