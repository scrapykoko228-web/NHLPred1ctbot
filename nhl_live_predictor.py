import math, csv, os

# --- Коэффициенты моделей по периодам ---
COEFS = {
    1: {
        'GF/GP': 0.53, 'GA/GP': -0.58, 'PP%': -0.28, 'PK%': -0.37,
        'Shots/GP': 0.09, 'SA/GP': -0.52, 'GF_rate_P1': 1.10, 'GA_rate_P1': -1.30
    },
    2: {
        'GF/GP': 0.38, 'GA/GP': -0.16, 'PP%': 0.71, 'PK%': -0.03,
        'Shots/GP': -0.08, 'SA/GP': -0.10, 'GF_rate_P2': 1.13, 'GA_rate_P2': -1.58
    },
    3: {
        'GF/GP': 0.32, 'GA/GP': -0.61, 'PP%': -0.25, 'PK%': 0.41,
        'Shots/GP': 0.22, 'SA/GP': -0.61, 'GF_rate_P3': 1.09, 'GA_rate_P3': -1.21
    }
}

def logistic(z):
    return 1 / (1 + math.exp(-z))

def predict_goal_probability(period, stats):
    if period not in COEFS:
        raise ValueError("Период должен быть 1, 2 или 3.")

    coefs = COEFS[period]
    z = 0
    for k, w in coefs.items():
        if k in stats:
            z += w * stats[k]

    p = logistic(z)
    return p * 100

def interpret(prob):
    if prob >= 70:
        return "⚡ Высокая вероятность — рассмотреть ТБ 0.5 или ИТБ команды"
    elif prob >= 50:
        return "🟡 Средняя вероятность — возможен гол в ближайшие 5 минут"
    else:
        return "🔵 Низкая вероятность — игра без явного давления"

def save_to_csv(period, stats, prob):
    filename = "nhl_live_predictions.csv"
    file_exists = os.path.isfile(filename)

    with open(filename, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Период", "GF/GP", "GA/GP", "PP%", "PK%", "Shots/GP", "SA/GP", "GF_rate", "GA_rate", "Вероятность (%)"])
        writer.writerow([
            period,
            stats.get('GF/GP', ''), stats.get('GA/GP', ''), stats.get('PP%', ''), stats.get('PK%', ''),
            stats.get('Shots/GP', ''), stats.get('SA/GP', ''),
            stats.get(f'GF_rate_P{period}', ''), stats.get(f'GA_rate_P{period}', ''),
            round(prob, 2)
        ])

if __name__ == "__main__":
    print("\n=== NHL Live Predictor (по периодам) ===")
    period = int(input("Введите период (1/2/3): "))

    stats = {}
    for k in COEFS[period].keys():
        val = float(input(f"Введите значение {k}: "))
        stats[k] = val

    prob = predict_goal_probability(period, stats)

    print(f"\nПериод: {period}")
    print(f"Вероятность гола в ближайшие 5 минут: {prob:.2f}%")
    print(interpret(prob))

    save_to_csv(period, stats, prob)
    print("\n✅ Результат сохранён в nhl_live_predictions.csv")
