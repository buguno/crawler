import os
import sys
from unittest.mock import MagicMock, patch

from src.app import main


def test_main_default_args():
    """Testa se o main usa os argumentos padrão quando nenhum é passado."""
    with patch('src.app.YahooFinanceCrawler') as mock_crawler_class:
        mock_instance = MagicMock()
        mock_crawler_class.return_value = mock_instance

        with (
            patch.object(sys, 'argv', ['app.py']),
            patch.dict(
                os.environ, {'BASE_URL': 'http://mock.url'}, clear=True
            ),
        ):
            main()

        # O padrão no app.py é 'Brazil' e headless=True
        mock_crawler_class.assert_called_once_with(
            region='Brazil', base_url='http://mock.url', headless=True
        )
        mock_instance.run.assert_called_once()


def test_main_custom_args():
    """Testa se o main usa os argumentos passados via CLI."""
    with patch('src.app.YahooFinanceCrawler') as mock_crawler_class:
        mock_instance = MagicMock()
        mock_crawler_class.return_value = mock_instance

        # Teste passando região e flag para mostrar navegador
        with (
            patch.object(
                sys,
                'argv',
                ['app.py', '--region', 'United States', '--show-browser'],
            ),
            patch.dict(
                os.environ, {'BASE_URL': 'http://mock.url'}, clear=True
            ),
        ):
            main()

        # Se passou --show-browser, headless deve ser False
        mock_crawler_class.assert_called_once_with(
            region='United States', base_url='http://mock.url', headless=False
        )
        mock_instance.run.assert_called_once()


def test_main_missing_env_var():
    """Testa se o main loga erro e sai se BASE_URL não estiver definida."""
    with patch('src.app.logger') as mock_logger:
        with patch('src.app.YahooFinanceCrawler') as mock_crawler_class:
            with (
                patch.object(sys, 'argv', ['app.py']),
                patch.dict(os.environ, {}, clear=True),
            ):
                main()

            mock_logger.error.assert_called_with(
                'BASE_URL environment variable is not set'
            )
            mock_crawler_class.assert_not_called()
