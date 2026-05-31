import re

def escape_markdown(text: str) -> str:
    """
    Экранирует специальные символы для Telegram Markdown (V1).
    Символы: *, _, `, [
    """
    if not text:
        return ""
    # В Markdown V1 экранируются только эти символы
    escape_chars = r'\*_`\['
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def validate_file_size(file_size: int | None, max_mb: int = 5) -> bool:
    """
    Проверяет, не превышает ли файл допустимый размер.
    """
    if not file_size:
        return False
    return file_size <= max_mb * 1024 * 1024
