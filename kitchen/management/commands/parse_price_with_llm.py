"""
Скрипт для парсинга цен с использованием локальной LLM (Ollama)
Запуск: python parse_price_with_llm.py

Требования:
    - Установленный Ollama (https://ollama.com)
    - Загруженная модель: ollama pull qwen2.5:7b
    - Установленные Python пакеты: pip install playwright ollama beautifulsoup4 lxml requests
    - Установленный браузер: playwright install chromium
"""

import json
import re
import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from ollama import Client
from playwright.sync_api import sync_playwright

# ==================== НАСТРОЙКИ ====================
OLLAMA_HOST = 'http://localhost:11434'
MODEL_NAME = 'qwen2.5:7b'
TIMEOUT = 30
MAX_HTML_LENGTH = 15000
CACHE_FILE = 'price_cache.json'
LOG_FILE = 'parser.log'

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ProductInfo:
    """Класс для хранения информации о товаре."""
    name: str = 'Неизвестно'
    price: Optional[float] = None
    weight: Optional[str] = None
    store: str = 'Неизвестный магазин'
    url: str = ''
    source: str = 'LLM'
    timestamp: float = time.time()
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует объект в словарь."""
        data = asdict(self)
        if self.error is None:
            data.pop('error', None)
        return data


class PriceCache:
    """Кеш для результатов парсинга."""

    def __init__(self, cache_file: str = CACHE_FILE):
        self.cache_file = Path(cache_file)
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Загружает кеш из файла."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                logger.warning("Не удалось загрузить кеш, создаю новый")
        return {}

    def save(self):
        """Сохраняет кеш в файл."""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def get(self, url: str) -> Optional[Dict[str, Any]]:
        """Получает данные из кеша."""
        if url in self.cache:
            timestamp = self.cache[url].get('timestamp', 0)
            if time.time() - timestamp < 86400:  # 24 часа
                logger.info(f"📦 Берём из кеша: {url}")
                return self.cache[url]
            else:
                logger.info(f"⏰ Кеш устарел для {url}, обновляем")
                del self.cache[url]
        return None

    def set(self, url: str, data: Dict[str, Any]):
        """Сохраняет данные в кеш."""
        self.cache[url] = data
        self.save()


class PriceParser:
    """Парсер цен с использованием LLM."""

    def __init__(self, model: str = MODEL_NAME, host: str = OLLAMA_HOST):
        self.ollama = Client(host=host)
        self.model = model
        self.cache = PriceCache()
        self.stats = {
            'total': 0,
            'from_cache': 0,
            'from_llm': 0,
            'errors': 0,
            'success': 0
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })

    def parse_page(self, url: str, use_browser: bool = True, use_cache: bool = True) -> ProductInfo:
        """Парсит страницу товара и возвращает структурированные данные."""
        self.stats['total'] += 1

        if use_cache:
            cached_data = self.cache.get(url)
            if cached_data:
                self.stats['from_cache'] += 1
                return ProductInfo(**cached_data)

        logger.info(f"🌐 Загружаем страницу: {url}")

        try:
            html = self._fetch_html(url, use_browser)
            if not html:
                raise ValueError("Не удалось загрузить HTML страницы")

            result = self._extract_with_llm(html, url)
            self.stats['success'] += 1
            self.stats['from_llm'] += 1

            if use_cache and result.price is not None:
                self.cache.set(url, result.to_dict())

            return result

        except Exception as e:
            logger.error(f"❌ Ошибка при парсинге {url}: {e}")
            self.stats['errors'] += 1
            return ProductInfo(
                url=url,
                error=str(e),
                source='Error'
            )

    def _fetch_html(self, url: str, use_browser: bool = True) -> Optional[str]:
        """Загружает HTML страницы."""
        # Сначала пробуем через браузер (он лучше обходит блокировки)
        if use_browser:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        headless=True,
                        args=['--disable-blink-features=AutomationControlled']
                    )
                    context = browser.new_context(
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        viewport={'width': 1920, 'height': 1080},
                        locale='ru-RU',
                        timezone_id='Europe/Moscow',
                    )
                    page = context.new_page()

                    # Добавляем скрипт для обхода детекции
                    page.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });
                    """)

                    page.goto(url, wait_until='networkidle', timeout=TIMEOUT * 1000)

                    # Ждём появления цены
                    try:
                        page.wait_for_selector('.price, .product-price, [data-price], .cost, .price-current', timeout=5000)
                    except:
                        pass

                    html = page.content()
                    browser.close()
                    return html
            except Exception as e:
                logger.warning(f"Браузерный рендеринг не удался, пробуем обычный запрос: {e}")
                return self._fetch_html(url, use_browser=False)
        else:
            # Обычный HTTP запрос с сессией
            try:
                response = self.session.get(url, timeout=TIMEOUT)

                # Если 403, пробуем с другими заголовками
                if response.status_code == 403:
                    logger.warning(f"Получен 403, пробуем с альтернативными заголовками...")
                    self.session.headers.update({
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    })
                    response = self.session.get(url, timeout=TIMEOUT)

                response.raise_for_status()
                return response.text
            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка загрузки {url}: {e}")
                return None

    def _extract_with_llm(self, html: str, url: str) -> ProductInfo:
        """Извлекает данные с помощью LLM."""
        soup = BeautifulSoup(html, 'html.parser')
        for script in soup(['script', 'style', 'noscript']):
            script.decompose()

        clean_html = re.sub(r'\s+', ' ', soup.prettify())

        if len(clean_html) > MAX_HTML_LENGTH:
            clean_html = clean_html[:MAX_HTML_LENGTH] + "... [обрезано]"

        prompt = self._build_prompt(clean_html)

        logger.info(f"🧠 Отправляем запрос к LLM (модель: {self.model})...")

        try:
            response = self.ollama.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'Ты — точный и внимательный парсер данных. Отвечай только JSON.'
                    },
                    {'role': 'user', 'content': prompt}
                ],
                stream=False,
                options={
                    'temperature': 0.1,
                    'top_p': 0.9,
                    'num_predict': 512,
                }
            )

            content = self._extract_json(response)

            if content:
                data = json.loads(content)

                price = data.get('price')
                if isinstance(price, str):
                    price = self._clean_price(price)
                elif price is not None:
                    price = float(price)

                return ProductInfo(
                    name=data.get('name', 'Неизвестно'),
                    price=price,
                    weight=data.get('weight'),
                    store=self._detect_store(url),
                    url=url,
                    source='LLM',
                    timestamp=time.time()
                )
            else:
                raise ValueError("Не удалось извлечь JSON из ответа LLM")

        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга JSON: {e}")
            return ProductInfo(
                url=url,
                error=f'JSONDecodeError: {e}',
                source='Error'
            )
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга LLM: {e}")
            return ProductInfo(
                url=url,
                error=str(e),
                source='Error'
            )

    def _build_prompt(self, html: str) -> str:
        """Строит промпт для LLM."""
        prompt = f'''Ты — умный парсер цен. Проанализируй HTML-код страницы магазина и извлеки следующую информацию:

1. Название товара (product_name) — полное название продукта
2. Цена (price) — текущая цена в рублях (только число, без валюты)
3. Вес/объем (weight) — вес или объем упаковки (например, "500г", "1л", "200 мл")

Верни ответ ТОЛЬКО в формате JSON с полями:
- name: строка
- price: число (float) или null
- weight: строка или null

Вот HTML-код страницы:

{html}

Важно:
- Игнорируй старые/перечеркнутые цены, бери только актуальную
- Если цена в другой валюте — конвертируй в рубли
- Если вес не указан — верни null
- Если цена не найдена — верни price: null
- Ответь только JSON-объектом, без дополнительного текста'''

        return prompt

    def _extract_json(self, response: Dict[str, Any]) -> Optional[str]:
        """Извлекает JSON из ответа LLM."""
        content = response.get('message', {}).get('content', '')

        # Ищем JSON в разных форматах
        patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'\{[\s\S]*\}',
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                content = match.group(1) if '```' in pattern else match.group()
                break

        content = content.strip()
        if content.startswith('{') and content.endswith('}'):
            return content

        return None

    def _clean_price(self, price_str: str) -> Optional[float]:
        """Очищает строку цены и конвертирует в число."""
        if not price_str:
            return None

        cleaned = re.sub(r'[^\d.,]', '', price_str)
        cleaned = cleaned.replace(',', '.')

        try:
            return float(cleaned)
        except ValueError:
            return None

    def _detect_store(self, url: str) -> str:
        """Определяет магазин по URL."""
        url_lower = url.lower()

        stores = {
            '5ka.ru': 'Пятерочка',
            'perekrestok.ru': 'Перекресток',
            'lenta.com': 'Лента',
            'ashen.ru': 'Ашан',
            'magnit.ru': 'Магнит',
            'ozon.ru': 'Ozon',
            'wildberries.ru': 'Wildberries',
            'dns-shop.ru': 'DNS',
            'mvideo.ru': 'М.Видео',
            'eldorado.ru': 'Эльдорадо',
            'citilink.ru': 'Ситилинк',
        }

        for domain, store_name in stores.items():
            if domain in url_lower:
                return store_name

        return 'Неизвестный магазин'

    def get_stats(self) -> Dict[str, int]:
        """Возвращает статистику парсинга."""
        return self.stats


def batch_parse(
    urls: List[str],
    model: str = MODEL_NAME,
    use_browser: bool = True,
    use_cache: bool = True
) -> List[ProductInfo]:
    """Парсит список URL и возвращает результаты."""
    parser = PriceParser(model=model)
    results = []

    for i, url in enumerate(urls, 1):
        logger.info(f"📄 [{i}/{len(urls)}] Парсим: {url}")
        result = parser.parse_page(url, use_browser, use_cache)
        results.append(result)

        if i < len(urls):
            time.sleep(2)  # Увеличил задержку между запросами

    stats = parser.get_stats()
    logger.info(f"""
📊 СТАТИСТИКА:
   Всего: {stats['total']}
   Из кеша: {stats['from_cache']}
   С помощью LLM: {stats['from_llm']}
   Успешно: {stats['success']}
   Ошибок: {stats['errors']}
    """)

    return results


def fetch_product_price(
    url: str,
    model: str = MODEL_NAME,
    use_browser: bool = True,
    use_cache: bool = True
) -> Optional[Dict[str, Any]]:
    """Основная функция для получения цены товара."""
    parser = PriceParser(model=model)
    result = parser.parse_page(url, use_browser, use_cache)
    return result.to_dict()


def export_to_csv(results: List[ProductInfo], filename: str = 'prices.csv'):
    """Экспортирует результаты в CSV."""
    import csv

    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['Название', 'Цена', 'Вес', 'Магазин', 'URL', 'Дата'])

        for result in results:
            writer.writerow([
                result.name,
                result.price,
                result.weight,
                result.store,
                result.url,
                datetime.fromtimestamp(result.timestamp).strftime('%Y-%m-%d %H:%M:%S')
            ])

    logger.info(f"📊 Результаты экспортированы в {filename}")


def check_url_availability(url: str) -> bool:
    """Проверяет доступность URL."""
    try:
        # Пробуем через браузер для обхода блокировок
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            response = page.goto(url, wait_until='domcontentloaded', timeout=10000)
            status = response.status if response else 0
            browser.close()
            return status == 200
    except:
        # Если браузер не работает, пробуем обычный запрос
        try:
            response = requests.get(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                timeout=10
            )
            return response.status_code == 200
        except:
            return False


def demo_with_local_html():
    """Демонстрация работы с локальным HTML."""
    print("\n🧪 Демонстрация работы с локальным HTML...")

    test_html = """
    <html>
        <head><title>Тестовый товар</title></head>
        <body>
            <h1 class="product-name">Молоко "Домик в деревне" 3.2% 1л</h1>
            <div class="price">89.99 ₽</div>
            <span class="weight">1 л</span>
        </body>
    </html>
    """

    parser = PriceParser()
    result = parser._extract_with_llm(test_html, 'test://local')

    print(f"\n📊 РЕЗУЛЬТАТ ДЕМОНСТРАЦИИ:")
    print(f"   Название: {result.name}")
    print(f"   Цена: {result.price} руб.")
    print(f"   Вес: {result.weight}")
    print(f"   Магазин: {result.store}")
    print(f"   Источник: {result.source}")

    # Сохраняем результат демонстрации
    with open('demo_result.json', 'w', encoding='utf-8') as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
    print("\n✅ Демонстрационный результат сохранен в demo_result.json")

    return result


if __name__ == '__main__':
    print("=" * 60)
    print("🧠 ПАРСЕР ЦЕН С ИСПОЛЬЗОВАНИЕМ ЛОКАЛЬНОЙ LLM")
    print("=" * 60)

    # Проверяем Ollama
    try:
        client = Client(host=OLLAMA_HOST)
        models = client.list()
        available_models = [m.get('name', 'unknown') for m in models.get('models', [])]
        print(f"✅ Ollama запущена. Доступные модели: {available_models}")
    except Exception as e:
        print("❌ Ollama не запущена! Запустите: ollama serve")
        print(f"   Ошибка: {e}")
        exit(1)

    # РЕАЛЬНЫЕ URL ДЛЯ ТЕСТИРОВАНИЯйцук
    test_urls = [
        # URL для тестирования
        # 'https://5ka.ru/product/laym-v-upakovke-3-sht--3358910/',
        # Добавьте другие URL для тестирования:
        # 'https://www.perekrestok.ru/catalog/product/1300020117',
        # 'https://lenta.com/product/1092021-moloko-3-2-1l/',
        'https://www.wildberries.ru/catalog/135433601/detail.aspx',
    ]

    if test_urls:
        print("\n🔍 Проверяем доступность URL...")
        available_urls = []
        for url in test_urls:
            print(f"   Проверяем: {url}")
            if check_url_availability(url):
                available_urls.append(url)
                print(f"   ✅ {url} - доступен")
            else:
                print(f"   ❌ {url} - недоступен (возможно, требуется авторизация)")

        if available_urls:
            print(f"\n📋 Парсим {len(available_urls)} URL...")
            results = batch_parse(available_urls, use_browser=True)

            print("\n📊 РЕЗУЛЬТАТЫ:")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result.url}")
                print(f"   Название: {result.name}")
                print(f"   Цена: {result.price} руб." if result.price else "   Цена: не найдена")
                print(f"   Вес: {result.weight or 'не указан'}")
                print(f"   Магазин: {result.store}")
                if result.error:
                    print(f"   ❌ Ошибка: {result.error}")

            if results:
                with open('parsed_prices.json', 'w', encoding='utf-8') as f:
                    json.dump(
                        [r.to_dict() for r in results],
                        f,
                        ensure_ascii=False,
                        indent=2
                    )

                export_to_csv(results)
        else:
            print("\n❌ Нет доступных URL для парсинга")
            demo_with_local_html()
    else:
        print("\n⚠️ Нет URL для тестирования. Запускаем демонстрацию с локальным HTML...")
        demo_with_local_html()

    print("\n" + "=" * 60)
    print("✅ Готово!")
    print("=" * 60)