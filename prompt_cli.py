"""
CLI утилита для управления промптами в базе данных
Использование:
    python prompt_cli.py list                    # Показать все промпты
    python prompt_cli.py show <agent>            # Показать промпты для агента
    python prompt_cli.py switch <agent> <version> # Переключить версию
    python prompt_cli.py add <agent> <version>    # Добавить новую версию
    python prompt_cli.py edit <agent> <version>   # Редактировать версию
    python prompt_cli.py delete <agent> <version> # Удалить версию
    python prompt_cli.py history [agent]          # Показать историю
    python prompt_cli.py export <agent> [version] # Экспортировать промпт
"""

import sys
import os
import argparse
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config.prompt_db import prompt_db

def cmd_list(args):
    """Показать все промпты"""
    print("\n" + "=" * 80)
    print("📝 ВСЕ ПРОМПТЫ В БАЗЕ ДАННЫХ")
    print("=" * 80)
    
    agents = ["research", "analysis", "execution"]
    
    for agent in agents:
        versions = prompt_db.get_all_versions(agent)
        active_version = prompt_db.get_active_version(agent)
        
        if not versions:
            print(f"\n⚠️ Нет промптов для агента {agent}")
            continue
        
        print(f"\n🔹 {agent.upper()} (активная: {active_version})")
        print("-" * 40)
        
        for version in versions:
            is_active = "✅" if version['version'] == active_version else "  "
            print(f"{is_active} {version['version']}: {version.get('description', 'Нет описания')[:50]}")
            print(f"   Температура: {version.get('temperature', 0.3)} | Tokens: {version.get('max_tokens', 2000)}")
            print(f"   Хеш: {prompt_db.get_prompt_hash(agent, version['version'])}")

def cmd_show(args):
    """Показать промпты для агента"""
    agent = args.agent
    versions = prompt_db.get_all_versions(agent)
    active_version = prompt_db.get_active_version(agent)
    
    if not versions:
        print(f"❌ Нет промптов для агента {agent}")
        return
    
    print("\n" + "=" * 80)
    print(f"📝 ПРОМПТЫ ДЛЯ {agent.upper()}")
    print("=" * 80)
    print(f"Активная версия: {active_version}\n")
    
    for version in versions:
        is_active = "✅ (АКТИВНАЯ)" if version['version'] == active_version else ""
        print(f"📌 ВЕРСИЯ: {version['version']} {is_active}")
        print(f"   Описание: {version.get('description', 'Нет описания')}")
        print(f"   Температура: {version.get('temperature', 0.3)}")
        print(f"   Max tokens: {version.get('max_tokens', 2000)}")
        print(f"   Хеш: {prompt_db.get_prompt_hash(agent, version['version'])}")
        print(f"   Создан: {version.get('created_at', 'Неизвестно')}")
        
        # Показываем первые 200 символов промпта
        template = version.get('template', '')
        if template:
            preview = template[:200] + "..." if len(template) > 200 else template
            print(f"\n   📄 Промпт (первые 200 символов):")
            print(f"   {preview}")
        print("-" * 40)

def cmd_switch(args):
    """Переключить версию"""
    agent = args.agent
    version = args.version
    
    print(f"\n🔄 Переключение {agent} на версию {version}...")
    
    if prompt_db.set_active_version(agent, version, changed_by='cli'):
        print(f"✅ Промпт для {agent} переключен на версию {version}")
        
        # Показываем новую конфигурацию
        prompt_data = prompt_db.get_prompt(agent, version)
        print(f"\n📋 Новая конфигурация:")
        print(f"   Описание: {prompt_data.get('description', 'Нет описания')}")
        print(f"   Температура: {prompt_data.get('temperature', 0.3)}")
        print(f"   Max tokens: {prompt_data.get('max_tokens', 2000)}")
        print(f"   Хеш: {prompt_db.get_prompt_hash(agent, version)}")
    else:
        print(f"❌ Версия {version} для {agent} не найдена")
        versions = prompt_db.get_all_versions(agent)
        available = [v['version'] for v in versions]
        print(f"   Доступные версии: {', '.join(available)}")

def cmd_add(args):
    """Добавить новую версию"""
    agent = args.agent
    version = args.version
    
    print(f"\n📝 Добавление новой версии {version} для {agent}")
    
    # Проверяем, существует ли уже такая версия
    existing = prompt_db.get_prompt(agent, version)
    if existing:
        print(f"❌ Версия {version} уже существует для {agent}")
        return
    
    # Если передан файл, читаем из него
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                template = f.read()
            print(f"✅ Шаблон загружен из {args.file}")
        except Exception as e:
            print(f"❌ Ошибка чтения файла: {e}")
            return
    else:
        print("Введите текст промпта (закончите ввод Ctrl+D или Ctrl+Z):")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        template = "\n".join(lines)
    
    if not template.strip():
        print("❌ Промпт не может быть пустым")
        return
    
    # Добавляем
    success = prompt_db.add_version(
        agent_name=agent,
        version=version,
        template=template,
        description=args.description or f"Версия {version} добавлена через CLI",
        temperature=args.temperature or 0.3,
        max_tokens=args.max_tokens or 2000,
        changed_by='cli'
    )
    
    if success:
        print(f"✅ Версия {version} добавлена для {agent}")
        if args.active:
            prompt_db.set_active_version(agent, version, changed_by='cli')
            print(f"✅ Версия {version} установлена как активная")
    else:
        print(f"❌ Не удалось добавить версию {version}")

def cmd_edit(args):
    """Редактировать версию"""
    agent = args.agent
    version = args.version
    
    print(f"\n✏️ Редактирование версии {version} для {agent}")
    
    current = prompt_db.get_prompt(agent, version)
    if not current:
        print(f"❌ Версия {version} для {agent} не найдена")
        return
    
    print("\n📄 Текущий промпт:")
    print("-" * 40)
    print(current.get('template', ''))
    print("-" * 40)
    
    # Проверяем, редактируем ли через файл
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                new_template = f.read()
            print(f"✅ Новый шаблон загружен из {args.file}")
        except Exception as e:
            print(f"❌ Ошибка чтения файла: {e}")
            return
    else:
        print("\nВведите новый текст промпта (закончите ввод Ctrl+D или Ctrl+Z):")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        new_template = "\n".join(lines)
    
    if not new_template.strip():
        print("❌ Промпт не может быть пустым")
        return
    
    # Обновляем
    success = prompt_db.update_version(
        agent_name=agent,
        version=version,
        template=new_template,
        description=args.description or current.get('description', ''),
        temperature=args.temperature or current.get('temperature', 0.3),
        max_tokens=args.max_tokens or current.get('max_tokens', 2000),
        changed_by='cli'
    )
    
    if success:
        print(f"✅ Версия {version} для {agent} обновлена")
    else:
        print(f"❌ Не удалось обновить версию {version}")

def cmd_delete(args):
    """Удалить версию"""
    agent = args.agent
    version = args.version
    
    active_version = prompt_db.get_active_version(agent)
    if version == active_version:
        print(f"❌ Нельзя удалить активную версию {version} для {agent}")
        return
    
    # Подтверждение
    if not args.force:
        confirm = input(f"⚠️ Удалить версию {version} для {agent}? (y/N): ")
        if confirm.lower() != 'y':
            print("Отменено")
            return
    
    success = prompt_db.delete_version(agent, version, changed_by='cli')
    
    if success:
        print(f"✅ Версия {version} для {agent} удалена")
    else:
        print(f"❌ Не удалось удалить версию {version}")

def cmd_history(args):
    """Показать историю изменений"""
    print("\n" + "=" * 80)
    print("📜 ИСТОРИЯ ИЗМЕНЕНИЙ ПРОМПТОВ")
    print("=" * 80)
    
    history = prompt_db.get_history(args.agent, limit=args.limit)
    
    if not history:
        print("Нет записей в истории")
        return
    
    for entry in history:
        print(f"\n📌 {entry.get('changed_at', 'Неизвестно')}")
        print(f"   Действие: {entry.get('action', 'unknown').upper()}")
        print(f"   Агент: {entry.get('agent_name', 'unknown')}")
        print(f"   Версия: {entry.get('new_version', 'unknown')}")
        print(f"   Кто: {entry.get('changed_by', 'unknown')}")

def cmd_export(args):
    """Экспортировать промпт в файл"""
    agent = args.agent
    version = args.version or prompt_db.get_active_version(agent)
    
    prompt_data = prompt_db.get_prompt(agent, version)
    if not prompt_data:
        print(f"❌ Промпт для {agent} версии {version} не найден")
        return
    
    filename = args.output or f"prompt_{agent}_{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    output = f"""
{'='*80}
АГЕНТ: {agent.upper()}
ВЕРСИЯ: {version}
ОПИСАНИЕ: {prompt_data.get('description', 'Нет описания')}
ТЕМПЕРАТУРА: {prompt_data.get('temperature', 0.3)}
MAX TOKENS: {prompt_data.get('max_tokens', 2000)}
ХЕШ: {prompt_db.get_prompt_hash(agent, version)}
СОЗДАН: {prompt_data.get('created_at', 'Неизвестно')}
{'='*80}

{prompt_data.get('template', '')}
"""
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"✅ Промпт экспортирован в {filename}")
    except Exception as e:
        print(f"❌ Ошибка сохранения файла: {e}")

def cmd_json(args):
    """Экспортировать все промпты в JSON"""
    import json
    
    data = {}
    agents = ["research", "analysis", "execution"]
    
    for agent in agents:
        versions = prompt_db.get_all_versions(agent)
        data[agent] = {
            "active": prompt_db.get_active_version(agent),
            "versions": versions
        }
    
    filename = args.output or f"prompts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        print(f"✅ Все промпты экспортированы в {filename}")
    except Exception as e:
        print(f"❌ Ошибка сохранения файла: {e}")

def cmd_compare(args):
    """Сравнить две версии промпта"""
    agent = args.agent
    version1 = args.version1
    version2 = args.version2 or prompt_db.get_active_version(agent)
    
    prompt1 = prompt_db.get_prompt(agent, version1)
    prompt2 = prompt_db.get_prompt(agent, version2)
    
    if not prompt1 or not prompt2:
        print("❌ Одна из версий не найдена")
        return
    
    print("\n" + "=" * 80)
    print(f"📊 СРАВНЕНИЕ ВЕРСИЙ {version1} vs {version2} для {agent.upper()}")
    print("=" * 80)
    
    print(f"\n📌 Версия {version1}:")
    print(f"   Описание: {prompt1.get('description', 'Нет описания')}")
    print(f"   Температура: {prompt1.get('temperature', 0.3)}")
    print(f"   Max tokens: {prompt1.get('max_tokens', 2000)}")
    print(f"   Хеш: {prompt_db.get_prompt_hash(agent, version1)}")
    print(f"   Длина: {len(prompt1.get('template', ''))} символов")
    
    print(f"\n📌 Версия {version2}:")
    print(f"   Описание: {prompt2.get('description', 'Нет описания')}")
    print(f"   Температура: {prompt2.get('temperature', 0.3)}")
    print(f"   Max tokens: {prompt2.get('max_tokens', 2000)}")
    print(f"   Хеш: {prompt_db.get_prompt_hash(agent, version2)}")
    print(f"   Длина: {len(prompt2.get('template', ''))} символов")
    
    # Показываем diff
    print("\n📄 Различия в тексте:")
    print("-" * 40)
    
    template1_lines = prompt1.get('template', '').split('\n')
    template2_lines = prompt2.get('template', '').split('\n')
    
    max_lines = max(len(template1_lines), len(template2_lines))
    diff_count = 0
    
    for i in range(max_lines):
        line1 = template1_lines[i] if i < len(template1_lines) else ""
        line2 = template2_lines[i] if i < len(template2_lines) else ""
        
        if line1 != line2:
            diff_count += 1
            if diff_count <= 10:  # Показываем первые 10 различий
                print(f"Строка {i+1}:")
                if line1:
                    print(f"  {version1}: {line1[:80]}...")
                if line2:
                    print(f"  {version2}: {line2[:80]}...")
                print()
    
    if diff_count > 10:
        print(f"... и еще {diff_count - 10} различий")

def main():
    parser = argparse.ArgumentParser(description="Управление промптами в базе данных")
    subparsers = parser.add_subparsers(dest="command", help="Команды")
    
    # Команда list
    parser_list = subparsers.add_parser("list", help="Показать все промпты")
    
    # Команда show
    parser_show = subparsers.add_parser("show", help="Показать промпты для агента")
    parser_show.add_argument("agent", choices=["research", "analysis", "execution"], help="Имя агента")
    
    # Команда switch
    parser_switch = subparsers.add_parser("switch", help="Переключить версию")
    parser_switch.add_argument("agent", choices=["research", "analysis", "execution"], help="Имя агента")
    parser_switch.add_argument("version", help="Версия")
    
    # Команда add
    parser_add = subparsers.add_parser("add", help="Добавить новую версию")
    parser_add.add_argument("agent", choices=["research", "analysis", "execution"], help="Имя агента")
    parser_add.add_argument("version", help="Версия")
    parser_add.add_argument("-f", "--file", help="Файл с промптом")
    parser_add.add_argument("-d", "--description", help="Описание")
    parser_add.add_argument("-t", "--temperature", type=float, help="Температура")
    parser_add.add_argument("-m", "--max-tokens", type=int, help="Max tokens")
    parser_add.add_argument("-a", "--active", action="store_true", help="Сделать активной")
    
    # Команда edit
    parser_edit = subparsers.add_parser("edit", help="Редактировать версию")
    parser_edit.add_argument("agent", choices=["research", "analysis", "execution"], help="Имя агента")
    parser_edit.add_argument("version", help="Версия")
    parser_edit.add_argument("-f", "--file", help="Файл с новым промптом")
    parser_edit.add_argument("-d", "--description", help="Новое описание")
    parser_edit.add_argument("-t", "--temperature", type=float, help="Новая температура")
    parser_edit.add_argument("-m", "--max-tokens", type=int, help="Новый max tokens")
    
    # Команда delete
    parser_delete = subparsers.add_parser("delete", help="Удалить версию")
    parser_delete.add_argument("agent", choices=["research", "analysis", "execution"], help="Имя агента")
    parser_delete.add_argument("version", help="Версия")
    parser_delete.add_argument("-f", "--force", action="store_true", help="Без подтверждения")
    
    # Команда history
    parser_history = subparsers.add_parser("history", help="Показать историю")
    parser_history.add_argument("agent", nargs="?", help="Имя агента")
    parser_history.add_argument("-l", "--limit", type=int, default=50, help="Количество записей")
    
    # Команда export
    parser_export = subparsers.add_parser("export", help="Экспортировать промпт")
    parser_export.add_argument("agent", choices=["research", "analysis", "execution"], help="Имя агента")
    parser_export.add_argument("version", nargs="?", help="Версия (по умолчанию активная)")
    parser_export.add_argument("-o", "--output", help="Имя выходного файла")
    
    # Команда json
    parser_json = subparsers.add_parser("json", help="Экспортировать все промпты в JSON")
    parser_json.add_argument("-o", "--output", help="Имя выходного файла")
    
    # Команда compare
    parser_compare = subparsers.add_parser("compare", help="Сравнить две версии")
    parser_compare.add_argument("agent", choices=["research", "analysis", "execution"], help="Имя агента")
    parser_compare.add_argument("version1", help="Первая версия")
    parser_compare.add_argument("version2", nargs="?", help="Вторая версия (по умолчанию активная)")
    
    args = parser.parse_args()
    
    # Словарь команд
    commands = {
        "list": cmd_list,
        "show": cmd_show,
        "switch": cmd_switch,
        "add": cmd_add,
        "edit": cmd_edit,
        "delete": cmd_delete,
        "history": cmd_history,
        "export": cmd_export,
        "json": cmd_json,
        "compare": cmd_compare
    }
    
    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()