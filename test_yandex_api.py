import os
import requests
import json
from dotenv import load_dotenv

def test_yandex_api_connection():
    """
    Тестирует подключение к YandexGPT API.
    Проверяет наличие переменных, корректность ключей и выполняет тестовый запрос.
    """
    print("=" * 60)
    print("🧪 ТЕСТ ПОДКЛЮЧЕНИЯ К YANDEX GPT API")
    print("=" * 60)
    
    # 1. Загружаем переменные из .env
    load_dotenv()
    
    api_key = os.getenv("YANDEX_API_KEY")
    folder_id = os.getenv("YANDEX_FOLDER_ID")
    model_uri = os.getenv("YANDEX_MODEL_URI")
    
    # 2. Проверяем наличие переменных
    print("\n📋 Шаг 1: Проверка переменных окружения")
    print("-" * 40)
    
    errors = []
    
    if not api_key:
        errors.append("❌ YANDEX_API_KEY не найден в .env файле")
    else:
        # Показываем только первые 10 символов для безопасности
        print(f"✅ YANDEX_API_KEY: {api_key[:10]}... (скрыто)")
    
    if not folder_id:
        errors.append("❌ YANDEX_FOLDER_ID не найден в .env файле")
    else:
        print(f"✅ YANDEX_FOLDER_ID: {folder_id}")
    
    if model_uri:
        print(f"✅ YANDEX_MODEL_URI: {model_uri}")
    else:
        # Если URI не указан, формируем стандартный
        if folder_id:
            model_uri = f"gpt://{folder_id}/yandexgpt/latest"
            print(f"ℹ️  YANDEX_MODEL_URI не указан, используем: {model_uri}")
        else:
            errors.append("❌ Не удалось определить YANDEX_MODEL_URI")
    
    if errors:
        print("\n❌ ОШИБКИ:")
        for error in errors:
            print(f"   {error}")
        print("\n💡 Решение: Проверьте файл .env и добавьте недостающие переменные.")
        print("   Пример содержимого .env:")
        print("   YANDEX_API_KEY=AQVNваш_ключ")
        print("   YANDEX_FOLDER_ID=b1gваш_folder_id")
        print("   YANDEX_MODEL_URI=gpt://b1gваш_folder_id/yandexgpt/latest")
        return False
    
    print("\n✅ Все переменные найдены!")
    
    # 3. Проверяем API-запрос
    print("\n📡 Шаг 2: Тестовый запрос к YandexGPT API")
    print("-" * 40)
    
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Api-Key {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "modelUri": model_uri,
        "completionOptions": {
            "stream": False,
            "temperature": 0.1,
            "maxTokens": 50  # Короткий ответ для теста
        },
        "messages": [
            {
                "role": "user",
                "text": "Ответь одним словом: работает ли подключение?"
            }
        ]
    }
    
    try:
        print("⏳ Отправка запроса...")
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📊 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data and "alternatives" in data["result"]:
                answer = data["result"]["alternatives"][0]["message"]["text"]
                print(f"✅ УСПЕХ! Ответ от YandexGPT: '{answer}'")
                print("\n🎉 Подключение работает отлично!")
                return True
            else:
                print("❌ Неожиданный формат ответа:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                return False
        else:
            print(f"❌ Ошибка HTTP {response.status_code}")
            print(f"Текст ошибки: {response.text}")
            
            # Расшифровка частых ошибок
            if response.status_code == 401:
                print("\n💡 Ошибка аутентификации (401):")
                print("   - Проверьте правильность YANDEX_API_KEY")
                print("   - Убедитесь, что ключ активен (не удален)")
                print("   - Проверьте, что у сервисного аккаунта есть роль ai.languageModels.user")
            elif response.status_code == 403:
                print("\n💡 Ошибка доступа (403):")
                print("   - Проверьте YANDEX_FOLDER_ID")
                print("   - Убедитесь, что сервисный аккаунт создан в этом каталоге")
                print("   - Проверьте права доступа к каталогу")
            elif response.status_code == 429:
                print("\n💡 Превышен лимит запросов (429):")
                print("   - Подождите немного и попробуйте снова")
                print("   - Проверьте баланс в Yandex Cloud")
            elif response.status_code == 404:
                print("\n💡 Модель не найдена (404):")
                print("   - Проверьте правильность YANDEX_MODEL_URI")
                print("   - Попробуйте использовать: gpt://{folder_id}/yandexgpt/latest")
            
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Таймаут подключения")
        print("💡 Проверьте интернет-соединение")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка подключения к серверу")
        print("💡 Возможно, требуется VPN для доступа к Yandex API")
        return False
    except Exception as e:
        print(f"❌ Неизвестная ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_alternative_ollama():
    """
    Проверяет, доступна ли локальная модель Ollama.
    """
    print("\n" + "=" * 60)
    print("🔍 ДОПОЛНИТЕЛЬНО: Проверка Ollama (локальная модель)")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            if models:
                print(f"✅ Ollama доступен! Найдены модели: {', '.join(models)}")
                return True
            else:
                print("ℹ️  Ollama запущен, но нет загруженных моделей")
                return False
        else:
            print(f"ℹ️  Ollama не отвечает (статус {response.status_code})")
            return False
    except Exception:
        print("ℹ️  Ollama не обнаружен (не установлен или не запущен)")
        print("   Для установки: https://ollama.ai/")
        return False

if __name__ == "__main__":
    print("\n🚀 Запуск тестов подключения к API\n")
    
    # Основной тест Yandex API
    yandex_ok = test_yandex_api_connection()
    
    # Дополнительный тест Ollama (если нужен)
    test_alternative_ollama()
    
    print("\n" + "=" * 60)
    if yandex_ok:
        print("✅ ИТОГ: YandexGPT подключен и работает!")
        print("   Теперь вы можете запустить основную программу: python main.py")
    else:
        print("❌ ИТОГ: Подключение не удалось")
        print("   Исправьте ошибки и попробуйте снова.")
    print("=" * 60 + "\n")