# management/commands/load_loss_norms.py

from django.core.management.base import BaseCommand
from kitchen.models import CookingMethod, ProductLossNorm


class Command(BaseCommand):
    help = 'Загрузка норм потерь при обработке продуктов'

    def handle(self, *args, **options):
        # Получаем методы обработки
        methods = {m.code: m for m in CookingMethod.objects.all()}

        # Данные для загрузки
        losses_data = [
            # ===== ОВОЩИ =====
            # Картофель
            {'product': 'Картофель молодой', 'category': 'vegetable', 'method': 'boil_peeled',
             'cold_loss': 20, 'heat_loss': 6, 'season': 'до 1 сентября', 'source': 'Сборник рецептур'},
            {'product': 'Картофель', 'category': 'vegetable', 'method': 'boil_peeled',
             'cold_loss': 25, 'heat_loss': 4, 'season': '1.09-31.10', 'source': 'Сборник рецептур'},
            {'product': 'Картофель', 'category': 'vegetable', 'method': 'boil_peeled',
             'cold_loss': 40, 'heat_loss': 3, 'season': 'с 1 марта', 'source': 'Сборник рецептур'},
            {'product': 'Картофель', 'category': 'vegetable', 'method': 'fry',
             'cold_loss': 25, 'heat_loss': 36, 'source': 'Сборник рецептур'},
            {'product': 'Картофель', 'category': 'vegetable', 'method': 'fry_deep',
             'cold_loss': 25, 'heat_loss': 54, 'source': 'Сборник рецептур'},
            {'product': 'Картофель', 'category': 'vegetable', 'method': 'boil_in_skin',
             'cold_loss': 25, 'heat_loss': 3, 'source': 'Сборник рецептур'},

            # Морковь
            {'product': 'Морковь', 'category': 'vegetable', 'method': 'boil_peeled',
             'cold_loss': 20, 'heat_loss': 0.5, 'season': 'до 1 января', 'source': 'Сборник рецептур'},
            {'product': 'Морковь', 'category': 'vegetable', 'method': 'boil_peeled',
             'cold_loss': 25, 'heat_loss': 0.5, 'season': 'с 1 января', 'source': 'Сборник рецептур'},
            {'product': 'Морковь', 'category': 'vegetable', 'method': 'saute',
             'cold_loss': 20, 'heat_loss': 32, 'source': 'Сборник рецептур'},

            # Свекла
            {'product': 'Свекла', 'category': 'vegetable', 'method': 'boil_in_skin',
             'cold_loss': 20, 'heat_loss': 2, 'season': 'до 1 января', 'source': 'Сборник рецептур'},
            {'product': 'Свекла', 'category': 'vegetable', 'method': 'boil_in_skin',
             'cold_loss': 25, 'heat_loss': 2, 'season': 'с 1 января', 'source': 'Сборник рецептур'},

            # Лук
            {'product': 'Лук репчатый', 'category': 'vegetable', 'method': 'saute',
             'cold_loss': 16, 'heat_loss': 50, 'source': 'Сборник рецептур'},
            {'product': 'Лук репчатый', 'category': 'vegetable', 'method': 'fry',
             'cold_loss': 16, 'heat_loss': 26, 'source': 'Сборник рецептур'},

            # Капуста
            {'product': 'Капуста белокочанная', 'category': 'vegetable', 'method': 'boil',
             'cold_loss': 20, 'heat_loss': 8, 'source': 'Сборник рецептур'},
            {'product': 'Капуста белокочанная', 'category': 'vegetable', 'method': 'braise',
             'cold_loss': 20, 'heat_loss': 21, 'source': 'Сборник рецептур'},
            {'product': 'Капуста белокочанная', 'category': 'vegetable', 'method': 'fry',
             'cold_loss': 20, 'heat_loss': 28, 'source': 'Сборник рецептур'},
            {'product': 'Цветная капуста', 'category': 'vegetable', 'method': 'boil',
             'cold_loss': 40, 'heat_loss': 10, 'source': 'Сборник рецептур'},

            # Баклажаны, кабачки
            {'product': 'Баклажаны', 'category': 'vegetable', 'method': 'fry',
             'cold_loss': 15, 'heat_loss': 35, 'source': 'Сборник рецептур'},
            {'product': 'Кабачки', 'category': 'vegetable', 'method': 'fry',
             'cold_loss': 20, 'heat_loss': 37, 'source': 'Сборник рецептур'},

            # ===== ГРИБЫ =====
            {'product': 'Шампиньоны', 'category': 'mushroom', 'method': 'boil',
             'cold_loss': 24, 'heat_loss': 30, 'source': 'Сборник рецептур'},
            {'product': 'Шампиньоны', 'category': 'mushroom', 'method': 'fry',
             'cold_loss': 24, 'heat_loss': 60, 'source': 'Сборник рецептур'},
            {'product': 'Белые грибы', 'category': 'mushroom', 'method': 'boil',
             'cold_loss': 24, 'heat_loss': 25, 'source': 'Сборник рецептур'},

            # ===== МЯСО =====
            {'product': 'Говядина', 'category': 'meat', 'method': 'boil',
             'cold_loss': 15, 'heat_loss': 38, 'source': 'Сборник рецептур'},
            {'product': 'Говядина', 'category': 'meat', 'method': 'fry',
             'cold_loss': 15, 'heat_loss': 37, 'source': 'Сборник рецептур'},
            {'product': 'Говядина', 'category': 'meat', 'method': 'braise',
             'cold_loss': 15, 'heat_loss': 20, 'source': 'Сборник рецептур'},
            {'product': 'Свинина', 'category': 'meat', 'method': 'boil',
             'cold_loss': 12, 'heat_loss': 40, 'source': 'Сборник рецептур'},
            {'product': 'Свинина', 'category': 'meat', 'method': 'fry',
             'cold_loss': 12, 'heat_loss': 35, 'source': 'Сборник рецептур'},
            {'product': 'Баранина', 'category': 'meat', 'method': 'boil',
             'cold_loss': 15, 'heat_loss': 40, 'source': 'Сборник рецептур'},

            # ===== ПТИЦА =====
            {'product': 'Курица', 'category': 'poultry', 'method': 'boil',
             'cold_loss': 31, 'heat_loss': 28, 'source': 'Сборник рецептур'},
            {'product': 'Курица', 'category': 'poultry', 'method': 'fry',
             'cold_loss': 31, 'heat_loss': 25, 'source': 'Сборник рецептур'},
            {'product': 'Цыпленок-бройлер', 'category': 'poultry', 'method': 'boil',
             'cold_loss': 26, 'heat_loss': 28, 'source': 'Сборник рецептур'},

            # ===== РЫБА =====
            {'product': 'Минтай', 'category': 'fish', 'method': 'boil',
             'cold_loss': 40, 'heat_loss': 18, 'source': 'Сборник рецептур'},
            {'product': 'Треска', 'category': 'fish', 'method': 'boil',
             'cold_loss': 33, 'heat_loss': 18, 'source': 'Сборник рецептур'},
            {'product': 'Семга', 'category': 'fish', 'method': 'boil',
             'cold_loss': 35, 'heat_loss': 18, 'source': 'Сборник рецептур'},
        ]

        for data in losses_data:
            method = methods.get(data['method'])
            if not method:
                self.stdout.write(self.style.WARNING(f'Метод {data["method"]} не найден'))
                continue

            obj, created = ProductLossNorm.objects.update_or_create(
                product_name=data['product'],
                processing_method=method,
                season_note=data.get('season', 'круглогодично'),
                defaults={
                    'product_category': data['category'],
                    'cold_loss_percent': data['cold_loss'],
                    'heat_loss_percent': data['heat_loss'],
                    'source': data['source'],
                }
            )

            # management/commands/load_loss_norms.py - добавить

            grain_data = [
                # Крупы
                {'product': 'Рис круглый', 'category': 'grain', 'method': 'boil',
                 'behavior': 'gain', 'gain_factor': 3.0, 'source': 'Сборник рецептур'},
                {'product': 'Рис длинный', 'category': 'grain', 'method': 'boil',
                 'behavior': 'gain', 'gain_factor': 2.5, 'source': 'Сборник рецептур'},
                {'product': 'Гречка', 'category': 'grain', 'method': 'boil',
                 'behavior': 'gain', 'gain_factor': 2.2, 'source': 'Сборник рецептур'},
                {'product': 'Овсянка', 'category': 'grain', 'method': 'boil',
                 'behavior': 'gain', 'gain_factor': 2.0, 'source': 'Сборник рецептур'},
                {'product': 'Манка', 'category': 'grain', 'method': 'boil',
                 'behavior': 'gain', 'gain_factor': 4.0, 'source': 'Сборник рецептур'},
                {'product': 'Пшено', 'category': 'grain', 'method': 'boil',
                 'behavior': 'gain', 'gain_factor': 2.5, 'source': 'Сборник рецептур'},

                # Макароны
                {'product': 'Макароны', 'category': 'grain', 'method': 'boil',
                 'behavior': 'gain', 'gain_factor': 2.0, 'source': 'Сборник рецептур'},
                {'product': 'Спагетти', 'category': 'grain', 'method': 'boil',
                 'behavior': 'gain', 'gain_factor': 2.0, 'source': 'Сборник рецептур'},
                {'product': 'Вермишель', 'category': 'grain', 'method': 'boil',
                 'behavior': 'gain', 'gain_factor': 2.5, 'source': 'Сборник рецептур'},

                # Изделия из теста
                {'product': 'Пельмени', 'category': 'grain', 'method': 'boil',
                 'behavior': 'gain', 'gain_factor': 1.5, 'source': 'Сборник рецептур'},
                {'product': 'Вареники', 'category': 'grain', 'method': 'boil',
                 'behavior': 'gain', 'gain_factor': 1.4, 'source': 'Сборник рецептур'},
                {'product': 'Манты', 'category': 'grain', 'method': 'steam',
                 'behavior': 'gain', 'gain_factor': 1.3, 'source': 'Сборник рецептур'},

                # Бобовые
                {'product': 'Фасоль', 'category': 'grain', 'method': 'boil',
                 'behavior': 'gain', 'gain_factor': 2.5, 'source': 'Сборник рецептур'},
                {'product': 'Чечевица', 'category': 'grain', 'method': 'boil',
                 'behavior': 'gain', 'gain_factor': 2.2, 'source': 'Сборник рецептур'},
            ]

            for data in grain_data:
                method = methods.get(data['method'])
                if method:
                    obj, created = ProductLossNorm.objects.update_or_create(
                        product_name=data['product'],
                        processing_method=method,
                        defaults={
                            'product_category': data['category'],
                            'processing_behavior': data['behavior'],
                            'gain_factor': data['gain_factor'],
                            'source': data['source'],
                        }
                    )

            status = '✓' if created else '○'
            self.stdout.write(f'{status} {obj.product_name} → {obj.processing_method.name}')

        self.stdout.write(self.style.SUCCESS(f'Загружено {len(losses_data)} норм потерь'))