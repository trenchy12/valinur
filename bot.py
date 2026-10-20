import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
import json
import os

TOKEN = "8864156137:AAHhgrC6k0-scdGVFP9Txd6-1Ma1rjjPRyQ"

TASKS_FILE = "tasks.json"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я бот-надзиратель.\n\n"
        "Пиши задачу текстом, например:\n"
        "«25.10 надо сдать отчёт»\n\n"
        "Пока не пришлёшь фото — буду напоминать каждые 2 часа."
    )

@dp.message(F.text & ~F.text.startswith("/"))
async def add_task(message: Message):
    text = message.text.strip()
    user_id = str(message.from_user.id)
    
    tasks = load_tasks()
    if user_id not in tasks:
        tasks[user_id] = []
    
    task = {
        "id": len(tasks[user_id]) + 1,
        "text": text,
        "created": datetime.now().isoformat(),
        "done": False
    }
    tasks[user_id].append(task)
    save_tasks(tasks)
    
    await message.answer(f"Задача добавлена:\n{text}\n\nЖду фото-доказательство.")

@dp.message(F.photo)
async def handle_photo(message: Message):
    user_id = str(message.from_user.id)
    tasks = load_tasks()
    
    if user_id not in tasks or not any(not t["done"] for t in tasks[user_id]):
        await message.answer("Нет активных задач.")
        return
    
    for task in reversed(tasks[user_id]):
        if not task["done"]:
            task["done"] = True
            task["completed_at"] = datetime.now().isoformat()
            save_tasks(tasks)
            await message.answer("Фото принято. Задача закрыта.")
            return

async def reminder_loop():
    while True:
        await asyncio.sleep(7200)  # 2 часа
        tasks = load_tasks()
        for user_id, user_tasks in tasks.items():
            for task in user_tasks:
                if not task["done"]:
                    try:
                        await bot.send_message(
                            int(user_id),
                            f"Напоминание!\n\n{task['text']}\n\nПришли фото, иначе не отстану."
                        )
                    except Exception as e:
                        logging.error(e)

async def main():
    asyncio.create_task(reminder_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
