"""
Тест для проверки работы с промптами из базы данных
Проверяет:
1. Создание базы данных
2. Загрузку начальных промптов
3. Получение промптов
4. Переключение версий
5. Добавление новых версий
6. Обновление промптов
7. Удаление версий
"""

import os
import sys
import time
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.prompt_db import prompt_db

def print_header(title: str):
    """Печатает заголовок теста"""
    print("\n" + "=" * 80)
    print(f"🧪 {title}")
    print("=" * 80)

def print_success(message: str):
    """Печатает сообщение об успехе"""
    print(f"✅ {message}")

def print_error(message: str):
    """Печатает сообщение об ошибке"""
    print(f"❌ {message}")

def print_info(message: str):
    """Печатает информационное сообщение"""
    print(f"📌 {message}")

def test_db_initialization():
    """Тест 1: Проверка инициализации базы данных"""
    print_header("ТЕСТ 1: ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ")
    
    try:
        # Проверяем, что база данных создана
        db_exists = os.path.exists("prompts.db")
        if db_exists:
            print_success("База данных создана (файл prompts.db существует)")
        else:
            print_error("База данных не создана")
            return False
        
        # Проверяем, что есть данные
        from config.prompt_db import prompt_db
        
        # Проверяем количество промптов в базе
        with sqlite3.connect("prompts.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM prompts")
            count = cursor.fetchone()[0]
            
            if count > 0:
                print_success(f"Загружено {count} промптов")
            else:
                print_error("Нет данных в таблице prompts")
                return False
            
            # Проверяем активные версии
            cursor.execute("SELECT COUNT(*) FROM active_versions")
            active_count = cursor.fetchone()[0]
            
            if active_count > 0:
                print_success(f"Найдено {active_count} активных версий")
            else:
                print_error("Нет активных версий")
                return False
        
        return True
        
    except Exception as e:
        print_error(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_prompts():
    """Тест 2: Получение промптов"""
    print_header("ТЕСТ 2: ПОЛУЧЕНИЕ ПРОМПТОВ")
    
    agents = ["research", "analysis", "execution"]
    all_success = True
    
    for agent in agents:
        print(f"\n📌 Агент: {agent.upper()}")
        
        # Получаем активную версию
        active_version = prompt_db.get_active_version(agent)
        print_info(f"Активная версия: {active_version}")
        
        # Получаем промпт
        prompt_data = prompt_db.get_prompt(agent, active_version)
        
        if prompt_data:
            print_success(f"Промпт получен для {agent}")
            print(f"   Версия: {prompt_data.get('version', 'unknown')}")
            print(f"   Описание: {prompt_data.get('description', 'Нет описания')}")
            print(f"   Температура: {prompt_data.get('temperature', 0.3)}")
            print(f"   Длина промпта: {len(prompt_data.get('template', ''))} символов")
            print(f"   Хеш: {prompt_db.get_prompt_hash(agent, active_version)}")
        else:
            print_error(f"Не удалось получить промпт для {agent}")
            all_success = False
    
    return all_success

def test_version_switching():
    """Тест 3: Переключение версий"""
    print_header("ТЕСТ 3: ПЕРЕКЛЮЧЕНИЕ ВЕРСИЙ")
    
    agent = "research"
    
    # Получаем все версии
    versions = prompt_db.get_all_versions(agent)
    
    if len(versions) < 2:
        print_info("Недостаточно версий для теста, пропускаем...")
        return True
    
    # Запоминаем текущую активную версию
    current_active = prompt_db.get_active_version(agent)
    print_info(f"Текущая активная версия: {current_active}")
    
    # Находим другую версию
    other_version = None
    for v in versions:
        if v['version'] != current_active:
            other_version = v['version']
            break
    
    if other_version:
        print_info(f"Переключаем на версию: {other_version}")
        
        # Переключаем
        success = prompt_db.set_active_version(agent, other_version, changed_by='test')
        
        if success:
            print_success(f"Версия переключена на {other_version}")
            
            # Проверяем, что версия действительно изменилась
            new_active = prompt_db.get_active_version(agent)
            if new_active == other_version:
                print_success("Подтверждено: активная версия изменилась")
            else:
                print_error(f"Ошибка: активная версия не изменилась (ожидалось {other_version}, получено {new_active})")
                return False
            
            # Возвращаем обратно
            print_info(f"Возвращаем на версию: {current_active}")
            prompt_db.set_active_version(agent, current_active, changed_by='test')
            print_success(f"Версия возвращена на {current_active}")
        else:
            print_error(f"Не удалось переключить на версию {other_version}")
            return False
    
    return True

def test_add_version():
    """Тест 4: Добавление новой версии"""
    print_header("ТЕСТ 4: ДОБАВЛЕНИЕ НОВОЙ ВЕРСИИ")
    
    agent = "research"
    test_version = "test_v1"
    
    # Проверяем, что версии нет
    existing = prompt_db.get_prompt(agent, test_version)
    if existing:
        print_info(f"Версия {test_version} уже существует, удаляем...")
        prompt_db.delete_version(agent, test_version)
    
    # Создаем тестовый промпт
    test_template = """
Тестовый промпт для агента {agent}
Создан: {timestamp}

Запрос: {query}

Это тестовый промпт для проверки работы с базой данных.
"""
    
    # Добавляем версию
    success = prompt_db.add_version(
        agent_name=agent,
        version=test_version,
        template=test_template,
        description="Тестовая версия для проверки",
        temperature=0.5,
        max_tokens=1000,
        changed_by='test'
    )
    
    if success:
        print_success(f"Версия {test_version} добавлена для {agent}")
        
        # Проверяем, что версия действительно добавлена
        new_prompt = prompt_db.get_prompt(agent, test_version)
        if new_prompt:
            print_success("Версия найдена в базе данных")
            print(f"   Описание: {new_prompt.get('description', '')}")
            print(f"   Температура: {new_prompt.get('temperature', 0.3)}")
            print(f"   Max tokens: {new_prompt.get('max_tokens', 2000)}")
        else:
            print_error("Версия не найдена после добавления")
            return False
    else:
        print_error(f"Не удалось добавить версию {test_version}")
        return False
    
    # Удаляем тестовую версию
    print_info(f"Удаляем тестовую версию {test_version}...")
    prompt_db.delete_version(agent, test_version, changed_by='test')
    print_success("Тестовая версия удалена")
    
    return True

def test_update_version():
    """Тест 5: Обновление существующей версии"""
    print_header("ТЕСТ 5: ОБНОВЛЕНИЕ ВЕРСИИ")
    
    agent = "research"
    version = "v1"
    
    # Получаем текущий промпт
    current = prompt_db.get_prompt(agent, version)
    if not current:
        print_error(f"Версия {version} не найдена")
        return False
    
    original_template = current.get('template', '')
    original_description = current.get('description', '')
    
    print_info(f"Текущая длина промпта: {len(original_template)} символов")
    
    # Обновляем описание
    new_description = f"{original_description} (обновлено тестом {datetime.now().strftime('%Y-%m-%d %H:%M')})"
    new_template = original_template + "\n\n[Добавлено тестом]"
    
    success = prompt_db.update_version(
        agent_name=agent,
        version=version,
        template=new_template,
        description=new_description,
        temperature=0.4,
        max_tokens=2500,
        changed_by='test'
    )
    
    if success:
        print_success(f"Версия {version} обновлена")
        
        # Проверяем изменения
        updated = prompt_db.get_prompt(agent, version)
        
        if updated:
            print(f"   Новое описание: {updated.get('description', '')}")
            print(f"   Новая температура: {updated.get('temperature', 0.3)}")
            print(f"   Новый max tokens: {updated.get('max_tokens', 2000)}")
            
            # Возвращаем обратно
            print_info("Восстанавливаем оригинальный промпт...")
            prompt_db.update_version(
                agent_name=agent,
                version=version,
                template=original_template,
                description=original_description,
                temperature=current.get('temperature', 0.3),
                max_tokens=current.get('max_tokens', 2000),
                changed_by='test_restore'
            )
            print_success("Оригинальный промпт восстановлен")
        else:
            print_error("Не удалось получить обновленную версию")
            return False
    else:
        print_error(f"Не удалось обновить версию {version}")
        return False
    
    return True

def test_prompt_formatting():
    """Тест 6: Форматирование промпта"""
    print_header("ТЕСТ 6: ФОРМАТИРОВАНИЕ ПРОМПТА")
    
    agent = "research"
    version = prompt_db.get_active_version(agent)
    
    prompt_data = prompt_db.get_prompt(agent, version)
    template = prompt_data.get('template', '')
    
    # Тестовые данные для форматирования
    test_data = {
        "query": "Тестовый запрос для проверки форматирования",
        "test_param": "Это тестовый параметр"
    }
    
    try:
        # Пробуем отформатировать
        formatted = template.format(**test_data)
        print_success("Промпт успешно отформатирован")
        print(f"   Длина отформатированного промпта: {len(formatted)} символов")
        print("\n📄 Первые 200 символов:")
        print("-" * 40)
        print(formatted[:200] + "...")
        print("-" * 40)
        return True
    except KeyError as e:
        print_error(f"Ошибка форматирования: отсутствует параметр {e}")
        return False
    except Exception as e:
        print_error(f"Ошибка: {e}")
        return False

def test_history():
    """Тест 7: Проверка истории изменений"""
    print_header("ТЕСТ 7: ИСТОРИЯ ИЗМЕНЕНИЙ")
    
    try:
        history = prompt_db.get_history(limit=5)
        
        if history:
            print_success(f"Найдено {len(history)} записей в истории")
            for i, entry in enumerate(history, 1):
                print(f"\n{i}. Действие: {entry.get('action', 'unknown')}")
                print(f"   Агент: {entry.get('agent_name', 'unknown')}")
                print(f"   Версия: {entry.get('new_version', 'unknown')}")
                print(f"   Кто: {entry.get('changed_by', 'unknown')}")
                print(f"   Время: {entry.get('changed_at', 'unknown')}")
        else:
            print_info("История пуста (это нормально для первого запуска)")
        
        return True
    except Exception as e:
        print_error(f"Ошибка: {e}")
        return False

def test_performance():
    """Тест 8: Проверка производительности"""
    print_header("ТЕСТ 8: ПРОВЕРКА ПРОИЗВОДИТЕЛЬНОСТИ")
    
    agent = "research"
    iterations = 10
    
    print_info(f"Выполняем {iterations} запросов к БД...")
    
    start_time = time.time()
    
    for _ in range(iterations):
        prompt_db.get_prompt(agent)
        prompt_db.get_active_version(agent)
        prompt_db.get_prompt_hash(agent, "v1")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print_success(f"Выполнено {iterations * 3} запросов за {total_time:.3f} секунд")
    print(f"   Среднее время на запрос: {total_time / (iterations * 3) * 1000:.2f} мс")
    
    return True

def test_delete_version():
    """Тест 9: Удаление версии"""
    print_header("ТЕСТ 9: УДАЛЕНИЕ ВЕРСИИ")
    
    agent = "research"
    test_version = "delete_test"
    
    # Создаем тестовую версию
    template = "Тестовая версия для удаления"
    prompt_db.add_version(
        agent_name=agent,
        version=test_version,
        template=template,
        description="Версия для теста удаления",
        changed_by='test'
    )
    
    # Проверяем, что версия создана
    prompt_data = prompt_db.get_prompt(agent, test_version)
    if not prompt_data:
        print_error("Не удалось создать тестовую версию")
        return False
    
    # Удаляем версию
    success = prompt_db.delete_version(agent, test_version, changed_by='test')
    
    if success:
        print_success(f"Версия {test_version} удалена")
        
        # Проверяем, что версия удалена
        prompt_data = prompt_db.get_prompt(agent, test_version)
        if not prompt_data:
            print_success("Подтверждено: версия удалена из БД")
        else:
            print_error("Версия все еще существует в БД")
            return False
    else:
        print_error(f"Не удалось удалить версию {test_version}")
        return False
    
    return True

def run_all_tests():
    """Запускает все тесты"""
    print("\n" + "=" * 80)
    print("🚀 ЗАПУСК ТЕСТОВ ДЛЯ ПРОМПТОВ ИЗ БАЗЫ ДАННЫХ")
    print("=" * 80)
    
    tests = [
        ("Инициализация БД", test_db_initialization),
        ("Получение промптов", test_get_prompts),
        ("Переключение версий", test_version_switching),
        ("Добавление версии", test_add_version),
        ("Обновление версии", test_update_version),
        ("Форматирование промпта", test_prompt_formatting),
        ("История изменений", test_history),
        ("Производительность", test_performance),
        ("Удаление версии", test_delete_version)
    ]
    
    results = []
    total = len(tests)
    passed = 0
    
    for name, test_func in tests:
        try:
            print_info(f"\n▶️ Запуск: {name}")
            result = test_func()
            if result:
                print_success(f"✅ Тест '{name}' пройден")
                passed += 1
                results.append((name, True))
            else:
                print_error(f"❌ Тест '{name}' не пройден")
                results.append((name, False))
        except Exception as e:
            print_error(f"❌ Тест '{name}' упал с ошибкой: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Итоги
    print("\n" + "=" * 80)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 80)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    print(f"\n📈 Пройдено: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print(f"\n⚠️ {total - passed} тестов не пройдены")
    
    return passed == total

if __name__ == "__main__":
    import sqlite3
    success = run_all_tests()
    sys.exit(0 if success else 1)