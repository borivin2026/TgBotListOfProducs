import logging
import sys
from pathlib import Path

def setup_logger(name: str = "bot") -> logging.Logger:
    """
    Настройка логгера для записи в файл и вывода в консоль.
    
    :param name: Имя логгера
    :return: Объект Logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Формат логирования
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Путь к логам
    from config import LOG_FILE
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(exist_ok=True)
    
    # Обработчик для записи в файл (с кодировкой utf-8)
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# Инициализируем основной логгер
logger = setup_logger()
