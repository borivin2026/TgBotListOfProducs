import csv
import io
from typing import List
from models.entities import ListItem

class CSVService:
    """Сервис для генерации CSV-файлов из списков товаров."""

    @staticmethod
    def generate_shopping_list_csv(items: List[ListItem]) -> io.BytesIO:
        """
        Создает CSV файл в памяти.
        
        :param items: Список товаров
        :return: Объект BytesIO с данными CSV
        """
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        # Заголовок
        writer.writerow(['Товар', 'Количество', 'Примечание', 'Статус'])
        
        # Данные
        for item in items:
            status = "Куплено" if item.is_bought else "Нужно купить"
            writer.writerow([item.name, item.quantity, item.note or "", status])
            
        # Превращаем в байты для отправки через Telegram API
        buf = io.BytesIO()
        buf.write(output.getvalue().encode('utf-8'))
        buf.seek(0)
        return buf

    @staticmethod
    def generate_receipt_csv(items: List[dict]) -> io.BytesIO:
        """
        Создает CSV файл для оцифрованного чека.
        
        :param items: Список словарей с данными товаров чека
        :return: Объект BytesIO с данными CSV
        """
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        # Заголовок
        writer.writerow(['Товар', 'Цена', 'Кол-во', 'Сумма'])
        
        # Данные
        for item in items:
            writer.writerow([
                item.get('name', 'Неизвестно'),
                item.get('price', 0.0),
                item.get('quantity', 1.0),
                item.get('total', 0.0)
            ])
            
        buf = io.BytesIO()
        buf.write(output.getvalue().encode('utf-8'))
        buf.seek(0)
        return buf
