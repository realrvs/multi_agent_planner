import json
from datetime import datetime
from typing import Dict, Any
from config.observability import observability
from config.prompts import prompt_versioning

class MetricsMonitor:
    """Мониторинг метрик агентов"""
    
    def __init__(self):
        self.metrics_history = []
    
    def collect_metrics(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Собирает метрики из состояния"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "user_query": state.get("user_query", ""),
            "current_agent": state.get("current_agent", ""),
            "agent_metrics": {}
        }
        
        # Собираем метрики каждого агента
        for agent_name in ["ResearchAgent", "AnalysisAgent", "ExecutionAgent"]:
            if agent_name in state:
                agent_state = state[agent_name]
                if isinstance(agent_state, dict) and "metrics" in agent_state:
                    metrics["agent_metrics"][agent_name] = agent_state["metrics"]
        
        # Добавляем информацию о версиях промптов
        metrics["prompt_versions"] = {}
        for agent in ["research", "analysis", "execution"]:
            version_info = prompt_versioning.get_version_info(agent)
            metrics["prompt_versions"][agent] = {
                "version": version_info.get("version"),
                "hash": version_info.get("hash")
            }
        
        self.metrics_history.append(metrics)
        return metrics
    
    def get_summary(self) -> Dict[str, Any]:
        """Возвращает сводку по метрикам"""
        if not self.metrics_history:
            return {"message": "Нет собранных метрик"}
        
        total_calls = sum(
            sum(agent.get("metrics", {}).get("calls", 0) 
                for agent in m.get("agent_metrics", {}).values())
            for m in self.metrics_history
        )
        
        total_errors = sum(
            sum(agent.get("metrics", {}).get("errors", 0) 
                for agent in m.get("agent_metrics", {}).values())
            for m in self.metrics_history
        )
        
        total_tokens = sum(
            sum(agent.get("metrics", {}).get("total_tokens", 0) 
                for agent in m.get("agent_metrics", {}).values())
            for m in self.metrics_history
        )
        
        return {
            "total_executions": len(self.metrics_history),
            "total_calls": total_calls,
            "total_errors": total_errors,
            "total_tokens": total_tokens,
            "success_rate": (total_calls - total_errors) / total_calls if total_calls > 0 else 0,
            "metrics_history": self.metrics_history[-5:]  # Последние 5
        }
    
    def export_metrics(self, filename: str = "metrics_export.json"):
        """Экспортирует метрики в JSON файл"""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.metrics_history, f, ensure_ascii=False, indent=2)
        print(f"✅ Метрики экспортированы в {filename}")

metrics_monitor = MetricsMonitor()