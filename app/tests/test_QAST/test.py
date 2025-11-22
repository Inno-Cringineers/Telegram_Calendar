import pytest
import asyncio
import time
import os
from telethon import TelegramClient
from dotenv import load_dotenv
from pathlib import Path 

def load_env():
    """Загружает .env из корня проекта"""
    load_dotenv()

@pytest.mark.asyncio
async def test_bot_fast_response_10_times():
    """
    Тест отправляет /start 10 раз и проверяет, что в 9 из 10 случаев
    бот отвечает менее чем за 5 секунд
    """
    load_env()
    
    API_ID = int(os.getenv('API_ID'))
    API_HASH = os.getenv('API_HASH')
    PHONE_NUMBER = os.getenv('PHONE_NUMBER')

    client = TelegramClient('test_session', API_ID, API_HASH)
    
    try:
        await client.start(PHONE_NUMBER)
        print("🔗 Подключение установлено")
        
        bot = await client.get_entity("MyTestCalendarBot")
        print("✅ Бот найден")
        
        total_attempts = 10
        fast_responses = 0  # Ответы < 5 секунд
        successful_responses = 0  # Все успешные ответы
        response_times = []
        
        print(f"🚀 Тестируем {total_attempts} запросов /start...")
        print(f"🎯 Цель: {total_attempts - 1}/{total_attempts} ответов < 5 сек")
        
        for attempt in range(total_attempts):
            start_time = time.time()
            response_received = False
            response_time = None
            
            print(f"\n📨 Попытка {attempt + 1}/{total_attempts}: Отправляем /start...")
            
            try:
                # 1. Отправляем /start
                await client.send_message(bot, "/start")
                
                # 2. Ждем ответ от бота
                for wait_attempt in range(10):  
                    await asyncio.sleep(0.5)
                    
                    # Получаем последние сообщения
                    messages = await client.get_messages(bot, limit=1)
                    
                    for message in messages:
                        # Ищем сообщение от бота, которое НЕ является командой /start
                        if (message.sender_id == bot.id and 
                            message.text and 
                            not message.text.strip().startswith('/start')):
                            
                            response_time = time.time() - start_time
                            response_times.append(response_time)
                            successful_responses += 1
                            response_received = True
                            
                            # Проверяем скорость ответа
                            if response_time <= 5.0:
                                fast_responses += 1
                                print(f"✅ #{attempt + 1}: Ответ за {response_time:.2f} сек ✅ БЫСТРО")
                            else:
                                print(f"⚠️ #{attempt + 1}: Ответ за {response_time:.2f} сек ⚠️ МЕДЛЕННО")
                            
                            break
                    
                    if response_received:
                        break
                
                if not response_received:
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    print(f"❌ #{attempt + 1}: НЕТ ОТВЕТА за {response_time:.2f} сек ❌")
                    
            except Exception as e:
                response_time = time.time() - start_time
                response_times.append(response_time)
                print(f"💥 #{attempt + 1}: ОШИБКА - {e} ❌")
            
            # Пауза между запросами (избегаем flood protection)
            if attempt < total_attempts - 1:
                await asyncio.sleep(1)
        
        # 📊 Анализ результатов
        print(f"\n" + "="*60)
        print("📊 ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        print(f"✅ Успешных ответов: {successful_responses}/{total_attempts}")
        print(f"⚡ Быстрых ответов (<5 сек): {fast_responses}/{total_attempts}")
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            print(f"📈 Среднее время ответа: {avg_time:.2f} сек")
            print(f"🏎️  Минимальное время: {min_time:.2f} сек")
            print(f"🐌 Максимальное время: {max_time:.2f} сек")
            
            # Детальная статистика
            print(f"\n📋 Детали по попыткам:")
            for i, rt in enumerate(response_times, 1):
                status = "✅" if rt <= 5.0 else "⚠️ " if rt < 10 else "❌"
                speed = "БЫСТРО" if rt <= 5.0 else "МЕДЛЕННО" if rt < 10 else "ТАЙМАУТ"
                print(f"  #{i}: {rt:.2f} сек {status} {speed}")
        
        # 🎯 ГЛАВНЫЕ ASSERT-ПРОВЕРКИ
        print(f"\n🎯 ПРОВЕРКА КРИТЕРИЕВ:")
        
        # 1. Проверяем что быстрых ответов >= 9
        assert fast_responses >= 9, (
            f"Требуется 9/{total_attempts} быстрых ответов (<5 сек), "
            f"получено {fast_responses}"
        )
        print(f"✅ Быстрых ответов: {fast_responses}/{total_attempts} ✓")      
        
        print(f"\n🎉 ТЕСТ ПРОЙДЕН! Бот стабильно быстро отвечает на /start")
        
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        raise
    finally:
        await client.disconnect()
        print("🔒 Подключение закрыто")
