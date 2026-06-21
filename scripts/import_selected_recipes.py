def parse_ingredient_line(line):
    """Улучшенный парсинг строки с ингредиентом"""
    # Удаляем лишние пробелы
    line = line.strip()

    # Пропускаем строки с "Брутто" и "Нетто"
    if 'Брутто' in line or 'Нетто' in line:
        return None

    # Паттерн: Название (может быть с пробелами) число пробел число
    # Пример: "Лук репчатый 75 63"
    pattern = r'^([А-Яа-я\s\-\(\)]+?)\s+(\d+[\d,.]*)\s+(\d+[\d,.]*)$'
    match = re.match(pattern, line)

    if match:
        name = match.group(1).strip()
        gross = float(match.group(2).replace(',', '.'))
        net = float(match.group(3).replace(',', '.'))
        return {'name': name, 'gross': gross, 'net': net}

    # Альтернативный паттерн: с единицами измерения
    # Пример: "Яйцо 6 шт. 240"
    pattern2 = r'^([А-Яа-я\s\-\(\)]+?)\s+(\d+[\d,.]*)\s+[а-яА-Я.]+\s+(\d+[\d,.]*)$'
    match2 = re.match(pattern2, line)

    if match2:
        name = match2.group(1).strip()
        gross = float(match2.group(2).replace(',', '.'))
        net = float(match2.group(3).replace(',', '.'))
        return {'name': name, 'gross': gross, 'net': net}

    return None