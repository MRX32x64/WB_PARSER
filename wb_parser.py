from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import csv
import random
from datetime import datetime

class FullWildberriesParser:
    def __init__(self):
        self.setup_driver()
        self.wait = WebDriverWait(self.driver, 15)
    
    def setup_driver(self):
        """Настраиваем Chrome driver в headless-режиме"""
        chrome_options = Options()
        
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def human_like_delay(self):
        """Случайная задержка как у человека"""
        time.sleep(random.uniform(1, 2))
    
    def search_products(self, query):
        """Поиск товаров с полной информацией"""
        print(f"🔍 Начинаем поиск: '{query}'")
        
        try:
            encoded_query = query.replace(' ', '%20')
            url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={encoded_query}"
            
            print(f"🌐 Открываем страницу...")
            self.driver.get(url)
            
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            print("✅ Страница загружена")
            
            self.human_like_delay()
            
            total_products = self.scroll_page()
            
            products = self.parse_product_cards(total_products)
            
            return products
            
        except Exception as e:
            print(f"❌ Ошибка при поиске: {e}")
            return []
    
    def scroll_page(self):
        """Прокручиваем страницу для загрузки всех товаров и подсчитываем их"""
        print("📜 Прокручиваем страницу для загрузки всех товаров...")
        
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_attempts = 10
        last_product_count = 0
        same_count_attempts = 0
        
        while scroll_attempts < max_attempts:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            current_products = self.count_visible_products()
            print(f"📦 Загружено товаров: {current_products}")
            
            if current_products == last_product_count:
                same_count_attempts += 1
                if same_count_attempts >= 2:
                    print("✅ Все товары загружены")
                    break
            else:
                same_count_attempts = 0
            
            last_product_count = current_products
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                scroll_attempts += 1
            else:
                scroll_attempts = 0
            
            last_height = new_height
            scroll_attempts += 1
        
        print(f"🎯 Всего загружено товаров: {last_product_count}")
        return last_product_count
    
    def count_visible_products(self):
        """Подсчитываем количество видимых товаров"""
        selectors = [
            "div.product-card",
            "[data-card]",
            ".card",
            ".j-card-item"
        ]
        
        for selector in selectors:
            try:
                cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if cards:
                    return len(cards)
            except:
                continue
        return 0
    
    def parse_product_cards(self, expected_count):
        """Парсим ВСЕ карточки товаров с полной информацией"""
        products = []
        
        try:
            selectors = [
                "div.product-card",
                "[data-card]",
                ".card",
                ".j-card-item"
            ]
            
            product_cards = []
            for selector in selectors:
                try:
                    cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if cards:
                        print(f"✅ Найдено карточек: {len(cards)}")
                        product_cards = cards
                        break
                except:
                    continue
            
            if not product_cards:
                print("❌ Не найдено карточек товаров")
                return []
            
            print(f"📦 Начинаем обработку ВСЕХ {len(product_cards)} товаров...")
            print("⏳ Это может занять несколько минут...")
            
            successful_parses = 0
            for i, card in enumerate(product_cards, 1):
                try:
                    if i % 10 == 0 or i == len(product_cards):
                        print(f"🔄 Обработано {i}/{len(product_cards)} товаров...")
                    
                    product_data = self.parse_single_product(card)
                    if product_data:
                        products.append(product_data)
                        successful_parses += 1
                    
                except Exception as e:
                    print(f"⚠️ Ошибка обработки товара {i}: {e}")
                    continue
            
            print(f"✅ Успешно обработано товаров: {successful_parses}/{len(product_cards)}")
            return products
            
        except Exception as e:
            print(f"❌ Ошибка парсинга карточек: {e}")
            return []
    
    def parse_single_product(self, card):
        """Парсим одну карточку товара с максимальной информацией"""
        try:
            product_data = {}
            
            product_data['name'] = self.get_product_name(card)
            
            product_data['brand'] = self.get_product_brand(card)
            
            product_data['price'] = self.get_product_price(card)
            
            product_data['link'] = self.get_product_link(card)
            
            product_data['rating'] = self.get_product_rating(card)
            
            product_data['reviews'] = self.get_product_reviews(card)
            
            product_data['parse_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if (product_data['name'] and product_data['price'] and 
                product_data['name'] != "Название не найдено" and
                product_data['price'] != "0"):
                return product_data
            else:
                return None
                
        except Exception as e:
            return None
    
    def get_product_name(self, card):
        """Получаем полное название товара"""
        name_selectors = [
            ".product-card__name",
            ".goods-name",
            "[class*='name']",
            ".j-card-name",
            "span:first-child"
        ]
        
        for selector in name_selectors:
            try:
                name_elem = card.find_element(By.CSS_SELECTOR, selector)
                name = name_elem.text.strip()
                if name and len(name) > 3:
                    return name
            except:
                continue
        
        return "Название не найдено"
    
    def get_product_brand(self, card):
        """Получаем бренд товара"""
        brand_selectors = [
            ".product-card__brand",
            ".brand-name",
            "[class*='brand']",
            ".j-card-brand"
        ]
        
        for selector in brand_selectors:
            try:
                brand_elem = card.find_element(By.CSS_SELECTOR, selector)
                brand = brand_elem.text.strip()
                if brand:
                    return brand
            except:
                continue
        
        return "Бренд не указан"
    
    def get_product_price(self, card):
        """Получаем цену товара"""
        price_selectors = [
            ".price__lower-price",
            ".final-cost",
            "[class*='price']",
            ".j-card-price",
            "ins"
        ]
        
        for selector in price_selectors:
            try:
                price_elem = card.find_element(By.CSS_SELECTOR, selector)
                price_text = price_elem.text.strip()
                price = ''.join(filter(lambda x: x.isdigit(), price_text))
                if price:
                    return price
            except:
                continue
        
        return "0"
    
    def get_product_link(self, card):
        """Получаем ссылку на товар"""
        try:
            link_elem = card.find_element(By.TAG_NAME, "a")
            link = link_elem.get_attribute("href")
            
            if link and "wildberries.ru" in link:
                return link
            else:
                if link and link.startswith("/"):
                    return "https://www.wildberries.ru" + link
                
        except:
            pass
        
        return "Ссылка не найдена"
    
    def get_product_rating(self, card):
        """Получаем рейтинг товара"""
        rating_selectors = [
            ".product-card__rating",
            ".address-rate-mini",
            "[class*='rating']",
            ".j-card-rating"
        ]
        
        for selector in rating_selectors:
            try:
                rating_elem = card.find_element(By.CSS_SELECTOR, selector)
                rating = rating_elem.text.strip()
                if rating:
                    return rating
            except:
                continue
        
        return "Нет рейтинга"
    
    def get_product_reviews(self, card):
        """Получаем количество отзывов"""
        review_selectors = [
            ".product-card__count",
            ".goods-comments",
            "[class*='review']",
            "[class*='feedback']",
            ".j-card-feedback"
        ]
        
        for selector in review_selectors:
            try:
                review_elem = card.find_element(By.CSS_SELECTOR, selector)
                reviews = review_elem.text.strip()
                if reviews:
                    return reviews
            except:
                continue
        
        return "0"
    
    def save_to_csv(self, products, query):
        """Сохраняем результаты в CSV файл"""
        if not products:
            print("😞 Нет данных для сохранения")
            return False
        
        filename = f"wildberries_all_products_{query}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
                fieldnames = ['brand', 'name', 'price', 'rating', 'reviews', 'link', 'parse_date']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                
                for product in products:
                    writer.writerow(product)
            
            print(f"💾 Файл сохранен: {filename}")
            print(f"📊 Сохранено товаров: {len(products)}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            return False
    
    def display_results(self, products, query):
        """Выводим ВСЕ результаты в консоль"""
        if not products:
            print("😞 Товары не найдены")
            return
        
        print(f"\n🎯 РЕЗУЛЬТАТЫ ПО ЗАПРОСУ: '{query}'")
        print(f"📊 ВСЕГО НАЙДЕНО ТОВАРОВ: {len(products)}")
        print("=" * 100)
        
        for i, product in enumerate(products, 1):
            print(f"\n📦 ТОВАР {i}:")
            print(f"   🏷️  БРЕНД: {product['brand']}")
            print(f"   📋 НАЗВАНИЕ: {product['name']}")
            print(f"   💰 ЦЕНА: {product['price']} руб.")
            print(f"   ⭐ РЕЙТИНГ: {product['rating']}")
            print(f"   💬 ОТЗЫВЫ: {product['reviews']}")
            print(f"   🔗 ССЫЛКА: {product['link']}")
            print("-" * 100)
    
    def close(self):
        """Закрываем браузер"""
        if self.driver:
            self.driver.quit()
            print("🔚 Браузер закрыт")

def main():
    print("🚀 SELENIUM ПАРСЕР WILDBERRIES (ВСЕ ТОВАРЫ)")
    print("=" * 60)
    
    parser = FullWildberriesParser()
    
    try:
        query = input("🔍 Введите поисковый запрос: ").strip()
        if not query:
            query = "чехол для iphone"
        
        print(f"\n🎯 Поиск: '{query}'")
        print("⏳ Это может занять несколько минут в зависимости от количества товаров...")


        start_time = time.time()
        products = parser.search_products(query)
        end_time = time.time()
        
        if products:
            print(f"\n✅ УСПЕХ! Найдено товаров: {len(products)}")
            print(f"⏱️  Время выполнения: {end_time - start_time:.2f} секунд")
            
            parser.display_results(products, query)
            
            save_csv = input("\n💾 Сохранить ВСЕ товары в CSV файл? (y/n): ").strip().lower()
            if save_csv == 'y' or save_csv == 'д':
                parser.save_to_csv(products, query)
                print("✅ Все данные сохранены в CSV файл!")
            else:
                print("ℹ️ Данные не сохранены")
        else:
            print("\n😞 Товары не найдены. Возможные причины:")
            print("   • Неправильный запрос")
            print("   • Изменилась структура сайта")
            print("   • Нет товаров по вашему запросу")
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    
    finally:
        parser.close()

if __name__ == "__main__":
    main()