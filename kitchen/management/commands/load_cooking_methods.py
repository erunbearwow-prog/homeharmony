# management/commands/load_cooking_methods.py

from django.core.management.base import BaseCommand
from kitchen.models import CookingMethod


class Command(BaseCommand):
    help = 'Загрузка способов кулинарной обработки'

    def handle(self, *args, **options):
        methods = [
            # Основные термические способы
            {'code': 'boil', 'name': 'Варка', 'is_heat_treatment': True},
            {'code': 'boil_peeled', 'name': 'Варка очищенного', 'is_heat_treatment': True},
            {'code': 'boil_in_skin', 'name': 'Варка в кожуре', 'is_heat_treatment': True},
            {'code': 'steam', 'name': 'Варка на пару', 'is_heat_treatment': True},
            {'code': 'stew', 'name': 'Припускание', 'is_heat_treatment': True},
            {'code': 'braise', 'name': 'Тушение', 'is_heat_treatment': True},
            {'code': 'fry', 'name': 'Жарка', 'is_heat_treatment': True},
            {'code': 'fry_deep', 'name': 'Жарка во фритюре', 'is_heat_treatment': True},
            {'code': 'saute', 'name': 'Пассерование', 'is_heat_treatment': True},
            {'code': 'bake', 'name': 'Запекание', 'is_heat_treatment': True},
            {'code': 'roast', 'name': 'Жарка целиком', 'is_heat_treatment': True},

            # Механические способы
            {'code': 'peel', 'name': 'Очистка', 'is_heat_treatment': False},
            {'code': 'cut', 'name': 'Нарезка', 'is_heat_treatment': False},
            {'code': 'mince', 'name': 'Измельчение', 'is_heat_treatment': False},
            {'code': 'bread', 'name': 'Панирование', 'is_heat_treatment': False},

            # Специальные способы
            {'code': 'roast_whole', 'name': 'Запекание целиком', 'is_heat_treatment': True},
            {'code': 'fry_pieces', 'name': 'Жарка кусочками', 'is_heat_treatment': True},
        ]

        for method in methods:
            obj, created = CookingMethod.objects.update_or_create(
                code=method['code'],
                defaults={
                    'name': method['name'],
                    'is_heat_treatment': method['is_heat_treatment']
                }
            )
            status = '✓' if created else '○'
            self.stdout.write(f'{status} {obj.name} ({obj.code})')

        self.stdout.write(self.style.SUCCESS(f'Загружено {len(methods)} способов обработки'))