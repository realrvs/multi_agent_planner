import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.identity import IdentityManager, AgentIdentity

def test_identity():
    print("🧪 Тестирование WIMSE-идентичности\n" + "="*60)
    
    # 1. Создаем менеджер идентичности
    manager = IdentityManager()
    print("✅ Менеджер идентичности создан")
    
    # 2. Создаем идентичность для агента
    agent_id = AgentIdentity("ResearchAgent", "researcher")
    print(f"✅ Создана идентичность: {agent_id}")
    print(f"   - Agent ID: {agent_id.agent_id}")
    print(f"   - WIT Hash: {agent_id.wit_hash[:16]}...")
    
    # 3. Проверяем аттестацию
    attestation = agent_id.attestation
    print(f"✅ Создана аттестация:")
    print(f"   - Подпись: {attestation.get('signature', 'N/A')[:16]}...")
    print(f"   - Временная метка: {attestation.get('timestamp')}")
    
    # 4. Проверяем, что аттестация валидна
    is_valid = manager.verify_attestation(attestation)
    print(f"✅ Аттестация валидна: {is_valid}")
    
    # 5. Тестируем верификацию токена
    token = agent_id.wit_token
    try:
        payload = manager.verify_token(token)
        print(f"✅ Токен верифицирован:")
        print(f"   - Agent ID: {payload.get('agent_id')}")
        print(f"   - Роль: {payload.get('role')}")
        print(f"   - Issuer: {payload.get('iss')}")
        print(f"   - Срок действия: {payload.get('exp') - payload.get('iat')} сек")
    except Exception as e:
        print(f"❌ Ошибка верификации токена: {e}")
    
    # 6. Тестируем проверку идентичности другого агента
    agent2 = AgentIdentity("AnalysisAgent", "analyst")
    print(f"\n✅ Создана идентичность для AnalysisAgent: {agent2}")
    
    # Проверяем, может ли ResearchAgent проверить AnalysisAgent
    can_verify = agent_id.verify_peer_identity(agent2.get_identity_context())
    print(f"✅ ResearchAgent может проверить AnalysisAgent: {can_verify}")
    
    # Проверяем, может ли ResearchAgent проверить самого себя
    can_verify_self = agent_id.verify_peer_identity(agent_id.get_identity_context())
    print(f"✅ ResearchAgent может проверить самого себя: {can_verify_self}")
    
    print("\n" + "="*60)
    print("🎉 Тестирование WIMSE-идентичности завершено!")

if __name__ == "__main__":
    test_identity()
