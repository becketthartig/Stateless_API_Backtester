import pytz
import requests
from datetime import datetime, time

def get_time_range(date_str, start_hour, end_hour, time_zone="US/Eastern"):

    tz = pytz.timezone(time_zone)
    utc = pytz.utc

    date = datetime.strptime(date_str, "%Y-%m-%d")

    start_tz = tz.localize(datetime.combine(date, time(int(start_hour), (start_hour - int(start_hour)) * 60)))
    end_tz = tz.localize(datetime.combine(date, time(int(end_hour), (end_hour - int(end_hour)) * 60)))

    start_utc = start_tz.astimezone(utc)
    end_utc = end_tz.astimezone(utc)

    return int(start_utc.timestamp() * 1_000_000_000), int(end_utc.timestamp() * 1_000_000_000)

def OC(date_str):

    open_utc, close_utc = get_time_range(date_str, 9.5, 16.0)

    return open_utc, close_utc

def increase_sample_rate_most_recent(to_increase, timestamps, timestamps_onto):

    upsampled = [[] for _ in range(len(to_increase))]

    basei = 0
    for ts in timestamps_onto:
        while basei + 1 < len(timestamps) and timestamps[basei + 1] <= ts:
            basei += 1

        for i in range(len(to_increase)):
            if timestamps[basei] <= ts:
                upsampled[i].append(to_increase[i][basei])
            else:
                upsampled[i].append(0)

    return upsampled

def get_polygon_trades_stream(ticker, date, api_key, limit=50000, max_iter=10000, use_NY_hours=True, start_hour=9.5, end_hour=16.0, time_zone="US/Eastern"):

    if use_NY_hours:
        O, C = OC(date)
    else:
        O, C = get_time_range(date, start_hour, end_hour, time_zone)
    next_url =f"https://api.polygon.io/v3/trades/{ticker}?timestamp.gte={O}&timestamp.lte={C}&order=asc&limit={limit}&sort=timestamp"
    api_append = f"&apiKey={api_key}"

    iter = 1
    while next_url:

        if iter > max_iter:
            break

        next_url += api_append

        response = requests.get(next_url)
        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code} - {response.text}")

        data = response.json()
        trades = data.get("results", [])

        for trade in trades:
            yield trade

        next_url = data.get("next_url")
        print(iter * limit)
        iter += 1

def get_polygon_quotes_stream(ticker, date, api_key, limit=50000, max_iter=10000, use_NY_hours=True, start_hour=9.5, end_hour=16.0, time_zone="US/Eastern"):

    if use_NY_hours:
        O, C = OC(date)
    else:
        O, C = get_time_range(date, start_hour, end_hour, time_zone)
    next_url =f"https://api.polygon.io/v3/quotes/{ticker}?timestamp.gte={O}&timestamp.lte={C}&order=asc&limit={limit}&sort=timestamp"
    api_append = f"&apiKey={api_key}"

    iter = 1
    while next_url:

        if iter > max_iter:
            break

        next_url += api_append

        response = requests.get(next_url)
        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code} - {response.text}")

        data = response.json()
        trades = data.get("results", [])

        for trade in trades:
            yield trade

        next_url = data.get("next_url")
        print(iter * limit)
        iter += 1