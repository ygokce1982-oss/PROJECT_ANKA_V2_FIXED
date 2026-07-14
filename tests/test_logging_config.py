import logging
import os
import tempfile
import unittest

from core.logging_config import configure_logging, get_log_file


class LoggingConfigTests(unittest.TestCase):
    def test_logging_directory_created_and_file_configured(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "anka.log")
            try:
                os.environ["ANKA_LOG_DIR"] = temp_dir
                configure_logging()

                self.assertTrue(os.path.isdir(temp_dir))
                self.assertTrue(os.path.exists(log_file))
            finally:
                logging.shutdown()
                logging.getLogger().handlers.clear()
                os.environ.pop("ANKA_LOG_DIR", None)
                if os.path.exists(log_file):
                    os.remove(log_file)

    def test_console_and_file_handler_present(self) -> None:
        configure_logging()
        logger = __import__("logging").getLogger()
        handler_types = {type(handler).__name__ for handler in logger.handlers}

        self.assertIn("StreamHandler", handler_types)
        self.assertIn("RotatingFileHandler", handler_types)


if __name__ == "__main__":
    unittest.main()


if __name__ == "__main__":
    unittest.main()
