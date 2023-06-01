from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager

api = "key"
secret = "secret"

client = Client(api, secret)

def time_delta(days: int):   
    from datetime import datetime, timedelta
    gmt_time_delta = (datetime.utcnow() - timedelta(days=days)).strftime("%d %b %Y %H:%M:%S")
    gmt_time_now = datetime.utcnow().strftime("%d %b %Y %H:%M:%S")
    print("Delta:", gmt_time_delta, "Now:", gmt_time_now)
    return gmt_time_delta, gmt_time_now

def time_delta_hours(hours: int):   
    from datetime import datetime, timedelta
    gmt_time_delta = (datetime.utcnow() - timedelta(hours=hours)).strftime("%d %b %Y %H:%M:%S")
    gmt_time_now = datetime.utcnow().strftime("%d %b %Y %H:%M:%S")
    print("Delta:", gmt_time_delta, "Now:", gmt_time_now)
    return gmt_time_delta, gmt_time_now

print(time_delta_hours(5))


def delete_outliers(numbers):
    import numpy as np
    mean = np.mean(numbers)
    sd = np.std(numbers)
    lower_bound = mean - 1.5 * sd
    upper_bound = mean + 1.5 * sd
    outliers = []
    for i, x in enumerate(numbers):
        if x < lower_bound or x > upper_bound:
            outliers.append(i)
    print("Выбросы: ", outliers)
    numbers = [x for i, x in enumerate(numbers) if i not in outliers]
    print("Список без выбросов: ", numbers)
    return numbers

def trend_detect(symbol: str):
    delta_7d = time_delta(7)
    delta_1d = time_delta(1)
    klines_7d = client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_12HOUR, delta_7d[0], delta_7d[1])
    klines_1d = client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1HOUR, delta_1d[0], delta_1d[1])
    prices_7d = [round(float(kline[4]), 4) for kline in klines_7d]
    prices_1d = [round(float(kline[4]), 4) for kline in klines_1d]
    prices_7d_cleared = delete_outliers(prices_7d)
    prices_1d_cleared = delete_outliers(prices_1d)
    deltas_7d = [prices_7d_cleared[i] - prices_7d_cleared[i+1] for i in range(len(prices_7d_cleared) - 1)]
    deltas_1d = [prices_1d_cleared[i] - prices_1d_cleared[i+1] for i in range(len(prices_1d_cleared) - 1)]
    print('7d deltas', deltas_7d)
    print('1d deltas', deltas_1d)

    count_7d = 0
    count_1d = 0
    for d in deltas_7d:
        if d > 0:
            count_7d+=1
        if d < 0:
            count_7d-=1
    for d in deltas_1d:
        if d > 0:
            count_1d+=1
        if d < 0:
            count_1d-=1
    print('7d count', count_7d)
    print('1d count', count_1d)

    import numpy as np
    deltas_7d_sum = np.sum(deltas_7d)
    deltas_1d_sum = np.sum(deltas_1d)
    print('7d count', deltas_7d_sum)
    print('1d count', deltas_1d_sum)

    trend_7d = ""
    trend_1d = ""
    if count_7d > 1.5:
        trend_7d = "Down"
    if count_7d < -1.5:
        trend_7d = "Up"
    else:
        trend_7d = "Rigth"

    if count_1d > 1.5:
        trend_1d = "Down"
    if count_1d < -1.5:
        trend_1d = "Up"
    else:
        trend_1d = "Rigth"

    print("7 days:", trend_7d, "1 day:", trend_1d)
    return trend_7d, trend_1d