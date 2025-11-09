import asyncio
import csv
import os
import math
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

COEFS = {
    1: {'GF/GP': 0.53, 'GA/GP': -0.58, 'PP%': -0.28, 'PK%': -0.37,
        'Shots/GP': 0.09, 'SA/GP': -0.52, 'GF_rate_P1': 1.10, 'GA_rate_P1': -1.30},
    2: {'GF/GP': 0.38, 'GA/GP': -0.16, 'PP%': 0.71, 'PK%': -0.03,
        'Shots/GP': -0.08, 'SA/GP': -0.10, 'GF_rate_P2': 1.13, 'GA_rate_P2': -1.58},
    3: {'GF/GP': 0.32, 'GA/GP': -0.61, 'PP%': -0.25, 'PK%': 0.41,
        'Shots/GP': 0.22, 'SA/GP': -0.61, 'GF_rate_P3': 1.09, 'GA_rate_P3': -1.21}
}

def logistic(z):
    return 1 / (1 + math.exp(-z))

def predict_goal_probability(period, stats):
    coefs = COEFS[period]
    z = sum(coefs[k] * stats.get(k, 0) for k in coefs)
    return logistic(z) * 100

def interpret(prob):
    if prob >= 70:
        return "⚡ Высокая вероятность — рассмотреть ТБ 0.5 или ИТБ команды"
    elif prob >= 50:
        return "🟡 Средняя вероятность — возможен гол в ближайшие 5 минут"
    else:
        return "🔵 Низкая вероятность — игра без явного давления"

def save_to_csv(period, stats, prob, interpretation):
    filename = "nhl_live_predictions.csv"
    file_exists = os.path.isfile(filename)
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Период", "GF/GP", "GA/GP", "PP%", "PK%", "Shots/GP",
                             "SA/GP", "GF_rate", "GA_rate", "Вероятность (%)", "Оценка"])
        writer.writerow([
            period,
            stats.get('GF/GP',''), stats.get('GA/GP',''), stats.get('PP%',''), stats.get('PK%',''),
            stats.get('Shots/GP',''), stats.get('SA/GP',''),
            stats.get(f'GF_rate_P{period}',''), stats.get(f'GA_rate_P{period}',''),
            round(prob,2), interpretation
        ])

class PredictStates(StatesGroup):
    period = State()
    params = State()

@dp.message(Command("start"))
async def start_cmd(message: Message):
    text = (
        "👋 Привет! Я *NHL Live Predictor Bot*.

"
        "Я помогу оценить вероятность гола в ближайшие 5 минут по текущей статистике периода.

"
        "Команда: /predict — начать ввод данных.
"
        "Команда: /last — показать последние прогнозы."
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("predict"))
async def ask_period(message: Message, state: FSMContext):
    await state.set_state(PredictStates.period)
    await message.answer("Введите номер периода (1 / 2 / 3):")

@dp.message(PredictStates.period)
async def ask_params(message: Message, state: FSMContext):
    try:
        period = int(message.text.strip())
        if period not in (1,2,3):
            raise ValueError
    except ValueError:
        await message.answer("❌ Период должен быть числом 1, 2 или 3.")
        return
    await state.update_data(period=period, stats={})
    await state.set_state(PredictStates.params)
    keys = list(COEFS[period].keys())
    await message.answer(f"Отлично. Введите значение для *{keys[0]}*:", parse_mode='Markdown')

@dp.message(PredictStates.params)
async def collect_params(message: Message, state: FSMContext):
    data = await state.get_data()
    period = data['period']
    stats = data['stats']
    keys = list(COEFS[period].keys())
    current_param = keys[len(stats)]
    try:
        stats[current_param] = float(message.text.strip())
    except ValueError:
        await message.answer("Введите число, пожалуйста.")
        return

    if len(stats) < len(keys):
        next_param = keys[len(stats)]
        await state.update_data(stats=stats)
        await message.answer(f"Введите значение для *{next_param}*:", parse_mode='Markdown')
        return

    prob = predict_goal_probability(period, stats)
    interpretation = interpret(prob)
    save_to_csv(period, stats, prob, interpretation)

    result = (f"📊 *Результат:*
"
              f"Период: {period}
"
              f"Вероятность гола в ближайшие 5 минут: *{prob:.2f}%*
"
              f"{interpretation}

"
              f"✅ Сохранено в nhl_live_predictions.csv")
    await message.answer(result, parse_mode='Markdown')
    await state.clear()

@dp.message(Command("last"))
async def show_last(message: Message):
    filename = "nhl_live_predictions.csv"
    if not os.path.isfile(filename):
        await message.answer("Пока нет сохранённых прогнозов.")
        return
    with open(filename, encoding="utf-8") as f:
        lines = f.readlines()[-5:]
    await message.answer("Последние прогнозы:\n" + ''.join(lines))

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
