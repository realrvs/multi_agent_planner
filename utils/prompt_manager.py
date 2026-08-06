"""
Утилита для управления промптами через базу данных
"""

from config.prompt_db import prompt_db

def show_prompt_info(agent: str = None):
    """Показывает информацию о промптах"""
    agents = ["research", "analysis", "execution"] if not agent else [agent]
    
    print("\n" + "=" * 80)
    print("📝 ИНФОРМАЦИЯ О ПРОМПТАХ")
    print("=" * 80)
    
    for a in agents:
        versions = prompt_db.get_all_versions(a)
        active = prompt_db.get_active_version(a)
        
        print(f"\n🔹 {a.upper()}")
        print(f"   Активная версия: {active}")
        print(f"   Всего версий: {len(versions)}")
        
        for v in versions:
            is_active = "✅" if v['version'] == active else "  "
            print(f"   {is_active} {v['version']}: {v.get('description', 'Нет описания')[:40]}")

def get_current_prompts() -> dict:
    """Возвращает текущие активные промпты"""
    result = {}
    for agent in ["research", "analysis", "execution"]:
        version = prompt_db.get_active_version(agent)
        prompt_data = prompt_db.get_prompt(agent, version)
        result[agent] = {
            "version": version,
            "description": prompt_data.get('description', ''),
            "template": prompt_data.get('template', ''),
            "temperature": prompt_data.get('temperature', 0.3),
            "max_tokens": prompt_data.get('max_tokens', 2000)
        }
    return result