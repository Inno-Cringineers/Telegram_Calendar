import asyncio
import os
import time

import pytest
from dotenv import load_dotenv
from telethon import TelegramClient


def load_env() -> None:
    """Loads .env from project root."""
    load_dotenv()


@pytest.mark.asyncio
async def test_bot_fast_response_10_times() -> None:
    """
    Test sends /start 10 times and verifies that in 9 out of 10 cases
    the bot responds in less than 5 seconds.
    """
    load_env()

    API_ID = int(os.getenv("API_ID") or "")
    API_HASH = os.getenv("API_HASH") or ""
    PHONE_NUMBER = os.getenv("PHONE_NUMBER") or ""
    BOT_USERNAME = os.getenv("BOT_USERNAME") or ""

    if not API_ID or not API_HASH or not PHONE_NUMBER or not BOT_USERNAME:
        pytest.skip("API_ID, API_HASH or PHONE_NUMBER is not set")

    client = TelegramClient("test_session", API_ID, API_HASH)

    try:
        await client.start(PHONE_NUMBER)
        print("🔗 Connection established")

        bot = await client.get_entity(BOT_USERNAME)
        print("✅ Bot found")

        total_attempts = 10
        fast_responses = 0  # Responses < 5 seconds
        successful_responses = 0  # All successful responses
        response_times = []

        print(f"🚀 Testing {total_attempts} /start requests...")
        print(f"🎯 Goal: {total_attempts - 1}/{total_attempts} responses < 5 sec")

        for attempt in range(total_attempts):
            start_time = time.time()
            response_received = False
            response_time = None

            print(f"\n📨 Attempt {attempt + 1}/{total_attempts}: Sending /start...")

            try:
                # 1. Send /start
                await client.send_message(bot, "/start")

                # 2. Wait for bot response
                for _wait_attempt in range(10):
                    await asyncio.sleep(0.5)

                    # Get latest messages
                    messages = await client.get_messages(bot, limit=1)

                    for message in messages:
                        # Look for message from bot that is NOT a /start command
                        if (
                            message.sender_id == bot.id
                            and message.text
                            and not message.text.strip().startswith("/start")
                        ):
                            response_time = time.time() - start_time
                            response_times.append(response_time)
                            successful_responses += 1
                            response_received = True

                            # Check response speed
                            if response_time <= 5.0:
                                fast_responses += 1
                                print(f"✅ #{attempt + 1}: Response in {response_time:.2f} sec ✅ FAST")
                            else:
                                print(f"⚠️ #{attempt + 1}: Response in {response_time:.2f} sec ⚠️ SLOW")

                            break

                    if response_received:
                        break

                if not response_received:
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    print(f"❌ #{attempt + 1}: NO RESPONSE in {response_time:.2f} sec ❌")

            except Exception as e:
                response_time = time.time() - start_time
                response_times.append(response_time)
                print(f"💥 #{attempt + 1}: ERROR - {e} ❌")

            # Pause between requests (avoid flood protection)
            if attempt < total_attempts - 1:
                await asyncio.sleep(1)

        # 📊 Results analysis
        print("\n" + "=" * 60)
        print("📊 FINAL RESULTS:")
        print(f"✅ Successful responses: {successful_responses}/{total_attempts}")
        print(f"⚡ Fast responses (<5 sec): {fast_responses}/{total_attempts}")

        if response_times:
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)

            print(f"📈 Average response time: {avg_time:.2f} sec")
            print(f"🏎️  Minimum time: {min_time:.2f} sec")
            print(f"🐌 Maximum time: {max_time:.2f} sec")

            # Detailed statistics
            print("\n📋 Attempt details:")
            for i, rt in enumerate(response_times, 1):
                status = "✅" if rt <= 5.0 else "⚠️ " if rt < 10 else "❌"
                speed = "FAST" if rt <= 5.0 else "SLOW" if rt < 10 else "TIMEOUT"
                print(f"  #{i}: {rt:.2f} sec {status} {speed}")

        # 🎯 MAIN ASSERT CHECKS
        print("\n🎯 CRITERIA CHECK:")

        # 1. Check that fast responses >= 9
        assert fast_responses >= 9, f"Required 9/{total_attempts} fast responses (<5 sec), got {fast_responses}"
        print(f"✅ Fast responses: {fast_responses}/{total_attempts} ✓")

        print("\n🎉 TEST PASSED! Bot consistently responds quickly to /start")

    except Exception as e:
        print(f"💥 Critical error: {e}")
        raise
    finally:
        await client.disconnect()
        print("🔒 Connection closed")
