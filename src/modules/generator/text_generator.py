"""
Модуль генерации текста поздравлений.
Поддерживает fallback шаблоны и готов к интеграции с GigaChat API.
"""
import json
import random
from typing import Dict, Any, Optional, List
from datetime import datetime

from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.models import Client
from .templates.prompt_templates import PromptTemplates


class TextGenerator:
    """Генератор текста поздравлений."""
    
    def __init__(self, use_ai: Optional[bool] = None):
        """
        Инициализация генератора.
        
        Args:
            use_ai: Использовать ли AI (GigaChat). По умолчанию из настроек.
        """
        self.use_ai = use_ai if use_ai is not None else settings.USE_REAL_AI
        
        # Кэш для хранения сгенерированных текстов (для демо)
        self.cache = {}
        
        # Дополнительные пожелания для разнообразия
        self.wishes_pool = [
            "Пусть каждый день приносит радость и новые достижения!",
            "Желаем успехов во всех начинаниях и крепкого здоровья!",
            "Пусть удача сопутствует во всем, а планы реализуются легко!",
            "Желаем процветания бизнесу и гармонии в личной жизни!",
            "Пусть все финансовые вопросы решаются максимально выгодно!",
            "Желаем мудрых решений и уверенности в завтрашнем дне!",
            "Пусть сотрудничество с нашим банком приносит взаимную выгоду!",
        ]
    
    def generate_for_client(
        self,
        db: Session,
        client_id: int,
        event_type: str = "birthday",
        tone: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Сгенерировать поздравление для конкретного клиента.
        
        Args:
            db: Сессия базы данных
            client_id: ID клиента
            event_type: Тип события (birthday, professional, holiday)
            tone: Тон поздравления (официальный, дружеский и т.д.)
            use_cache: Использовать кэш
            
        Returns:
            Словарь с сгенерированным текстом и метаданными
        """
        # Проверяем кэш
        cache_key = f"{client_id}_{event_type}_{tone}"
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]
        
        # Получаем клиента из БД
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise ValueError(f"Клиент с ID {client_id} не найден")
        
        # Определяем сегмент для выбора шаблона
        segment = self._determine_segment(client.segment)
        
        # Создаем контекст для шаблона
        context = self._create_context(client, event_type, tone)
        
        # Генерируем текст
        if self.use_ai and settings.GIGACHAT_API_KEY:
            text = self._generate_with_ai(context, event_type, segment)
        else:
            text = self._generate_with_template(context, event_type, segment)
        
        # Добавляем случайное дополнительное пожелание для разнообразия
        if random.random() > 0.5:  # 50% chance
            extra_wish = random.choice(self.wishes_pool)
            text = text.rstrip() + "\n\n" + extra_wish
        
        result = {
            "text": text,
            "client_id": client_id,
            "client_name": client.full_name,
            "event_type": event_type,
            "segment": segment,
            "generated_at": datetime.now().isoformat(),
            "method": "ai" if self.use_ai else "template",
            "tone": tone or self._determine_tone(segment),
            "length": len(text),
            "context": context
        }
        
        # Сохраняем в кэш
        self.cache[cache_key] = result
        
        return result
    
    def _create_context(self, client: Client, event_type: str, tone: Optional[str]) -> Dict[str, Any]:
        """Создает контекст для генерации текста."""
        from datetime import date
        
        today = date.today()
        
        # Определяем возраст (если ДР)
        age = None
        if event_type == "birthday":
            try:
                age = today.year - client.birthday.year
                # Корректируем, если ДР еще не наступил в этом году
                if today.month < client.birthday.month or (today.month == client.birthday.month and today.day < client.birthday.day):
                    age -= 1
            except:
                age = None
        
        context = {
            "full_name": client.full_name,
            "first_name": client.first_name,
            "last_name": client.last_name,
            "email": client.email,
            "company": client.company_name or "компании",
            "position": client.position or "должности",
            "segment": client.segment or "клиент",
            "phone": client.phone,
            "event_type": event_type,
            "tone": tone or self._determine_tone(client.segment),
            "age": age,
            "is_jubilee": age and age % 10 == 0 and age >= 30,  # юбилей (30, 40, 50...)
        }
        
        # Добавляем прилагательные для возраста
        if age:
            if age < 30:
                context["age_adjective"] = "молодой"
            elif age < 50:
                context["age_adjective"] = "зрелый"
            else:
                context["age_adjective"] = "уважаемый"
        
        return context
    
    def _determine_segment(self, segment: Optional[str]) -> str:
        """Определяет сегмент клиента для выбора шаблона."""
        if not segment:
            return "default"
        
        segment_lower = segment.lower()
        
        if "vip" in segment_lower:
            return "vip"
        elif "loyal" in segment_lower or "лояльн" in segment_lower:
            return "loyal"
        elif "new" in segment_lower or "нов" in segment_lower:
            return "new"
        else:
            return "default"
    
    def _determine_tone(self, segment: str) -> str:
        """Определяет тон поздравления по сегменту."""
        tones = {
            "vip": "официальный",
            "loyal": "дружеский",
            "new": "приветливый",
            "default": "уважительный"
        }
        return tones.get(segment, "уважительный")
    
    def _generate_with_template(
        self,
        context: Dict[str, Any],
        event_type: str,
        segment: str
    ) -> str:
        """
        Генерация текста с использованием шаблонов (fallback метод).
        
        Args:
            context: Контекст с данными клиента
            event_type: Тип события
            segment: Сегмент клиента
            
        Returns:
            Сгенерированный текст
        """
        # Получаем шаблон
        template = PromptTemplates.get_template_by_event_type(event_type, segment)
        
        # Форматируем шаблон
        text = PromptTemplates.format_template(template, context)
        
        # Для юбилеев добавляем специальное упоминание
        if context.get("is_jubilee") and event_type == "birthday":
            age = context.get("age")
            jubilee_text = f"\n\nОтдельно поздравляем с {age}-летним юбилеем! Это значимая веха, и мы гордимся, что можем быть частью вашего пути."
            text += jubilee_text
        
        return text
    
    def _generate_with_ai(
        self,
        context: Dict[str, Any],
        event_type: str,
        segment: str
    ) -> str:
        """
        Генерация текста с использованием GigaChat API.
        Пока заглушка - в реальной реализации здесь будет вызов API.
        
        Args:
            context: Контекст с данными клиента
            event_type: Тип события
            segment: Сегмент клиента
            
        Returns:
            Сгенерированный текст
        """
        # TODO: Реализовать реальный вызов GigaChat API
        
        # Временная заглушка - используем шаблоны
        template = PromptTemplates.get_template_by_event_type(event_type, segment)
        text = PromptTemplates.format_template(template, context)
        
        # Добавляем маркер, что это AI-генерация
        text = text + "\n\n[Текст сгенерирован с использованием AI]"
        
        return text
    
    def batch_generate(
        self,
        db: Session,
        client_ids: List[int],
        event_type: str = "birthday"
    ) -> List[Dict[str, Any]]:
        """
        Массовая генерация поздравлений для нескольких клиентов.
        
        Args:
            db: Сессия базы данных
            client_ids: Список ID клиентов
            event_type: Тип события
            
        Returns:
            Список сгенерированных поздравлений
        """
        results = []
        
        for client_id in client_ids:
            try:
                result = self.generate_for_client(db, client_id, event_type, use_cache=False)
                results.append(result)
            except Exception as e:
                results.append({
                    "client_id": client_id,
                    "error": str(e),
                    "success": False
                })
        
        return results
    
    def clear_cache(self):
        """Очистить кэш генератора."""
        self.cache.clear()


# Синглтон экземпляр для удобного использования
_generator_instance = None

def get_text_generator(use_ai: Optional[bool] = None) -> TextGenerator:
    """
    Получить экземпляр генератора текста (синглтон).
    
    Args:
        use_ai: Использовать ли AI
        
    Returns:
        Экземпляр TextGenerator
    """
    global _generator_instance
    
    if _generator_instance is None:
        _generator_instance = TextGenerator(use_ai=use_ai)
    elif use_ai is not None:
        # Пересоздаем, если изменился флаг use_ai
        _generator_instance = TextGenerator(use_ai=use_ai)
    
    return _generator_instance


if __name__ == "__main__":
    """Тестирование генератора текста."""
    from src.core.database import SessionLocal
    
    print("🧪 Тестирование генератора текста...")
    
    db = SessionLocal()
    try:
        # Получаем тестового клиента
        client = db.query(Client).first()
        
        if not client:
            print("❌ Нет клиентов в базе. Запустите seed_database.py")
        else:
            generator = TextGenerator(use_ai=False)
            
            print(f"\n1. Генерация для клиента: {client.full_name} (сегмент: {client.segment})")
            
            # Генерация с шаблоном
            result = generator.generate_for_client(db, client.id, "birthday")
            
            print(f"\n2. Результат:")
            print(f"   Метод: {result['method']}")
            print(f"   Тон: {result['tone']}")
            print(f"   Длина: {result['length']} символов")
            print(f"\n3. Текст:")
            print("-" * 50)
            print(result["text"])
            print("-" * 50)
            
            # Тест массовой генерации
            print(f"\n4. Массовая генерация (первые 3 клиента):")
            all_clients = db.query(Client).limit(3).all()
            if all_clients:
                client_ids = [c.id for c in all_clients]
                batch_results = generator.batch_generate(db, client_ids[:2], "birthday")
                
                for res in batch_results:
                    status = "✅" if res.get("success", True) else "❌"
                    print(f"   {status} Клиент {res['client_id']}: {res.get('length', 'error')} символов")
    
    finally:
        db.close()