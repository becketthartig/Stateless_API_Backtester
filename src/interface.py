from src.datastream import get_polygon_trades_stream, get_polygon_quotes_stream, increase_sample_rate_most_recent

def get_all_dates_on_range(start_date, end_date):
    from datetime import timedelta
    current_date = start_date
    dates = []
    while current_date <= end_date:
        dates.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)
    return dates

class MarketSample:

    """
    Basic structure that is returned by the DataInterface
    Can be extended to include more information/complex operations on data
    """

    def __init__(self, NBBO, last_trade, temporal):

        self.NBBO = NBBO 
        self.last_trade = last_trade  
        self.temporal = temporal 

class DataInterface:

    """
    Simple class that can be initialized to stream data from Polygon.io
    Limited exposed functions to simplify stateless usage
    """

    def __init__(self, api_key, ticker, dates, use_NY_hours=True, start_hour=9.5, end_hour=16.0, time_zone="US/Eastern"):

        self.api_key = api_key
        self.ticker = ticker
        self.dates = dates
        self.use_NY_hours = use_NY_hours
        self.start_hour = start_hour
        self.end_hour = end_hour
        self.time_zone = time_zone

        self.timestamps = []
        self.current_date_index = 0
        self.current_data_index = 0
        self.need_new_data = True

    def next_sample(self, limit=50000, max_iter=10000):

        """
        Works on a day by day basis to return the next market data sample
        Only returns one consecutive sample at once
        Auto advances next market sample to return
        limit: Maximum number of trades/quotes to fetch at once (helps with data processing)
        max_iter: Maximum number of iterations to fetch data (to prevent super long backtests)
        """

        if self.need_new_data:
            if self.current_date_index >= len(self.dates):
                return None

            date = self.dates[self.current_date_index]
            self._info_for_day(date, limit, max_iter)

            self.current_date_index += 1
            self.current_data_index = 0
            self.need_new_data = False

        sample = MarketSample(
            {
                "bid": self.bids[self.current_data_index],
                "ask": self.asks[self.current_data_index],
                "bid_size": self.bid_sizes[self.current_data_index],
                "ask_size": self.ask_sizes[self.current_data_index]
            },
            {
                "price": self.prices[self.current_data_index],
                "size": self.sizes[self.current_data_index]
            },
            self.timestamps[self.current_data_index]
        )

        self.current_data_index += 1

        if self.current_data_index >= len(self.timestamps):
            self.need_new_data = True

        return sample

    def _info_for_day(self, date, limit=50000, max_iter=10000):

        trades_raw = list(get_polygon_trades_stream(self.ticker, date, self.api_key, limit, max_iter, self.use_NY_hours, self.start_hour, self.end_hour, self.time_zone))
        trades = {trade.get("participant_timestamp", trade["sip_timestamp"]): (trade["price"], trade["size"]) for trade in trades_raw}
        trade_timestamps = sorted(trades.keys())

        quotes_raw = list(get_polygon_quotes_stream(self.ticker, date, self.api_key, limit, max_iter, self.use_NY_hours, self.start_hour, self.end_hour, self.time_zone))
        quotes = {quote.get("participant_timestamp", quote["sip_timestamp"]): (quote.get("bid_price", 0), quote.get("ask_price", 0), quote.get("bid_size", 0), quote.get("ask_size", 0)) for quote in quotes_raw}
        quote_timestamps = sorted(quotes.keys())

        self.prices = increase_sample_rate_most_recent([[trades[t][0] for t in trade_timestamps]], trade_timestamps, quote_timestamps)[0]
        self.sizes = increase_sample_rate_most_recent([[trades[t][1] for t in trade_timestamps]], trade_timestamps, quote_timestamps)[0]
        self.bids = [quotes[t][0] for t in quote_timestamps]
        self.asks = [quotes[t][1] for t in quote_timestamps]
        self.bid_sizes = [quotes[t][2] for t in quote_timestamps]
        self.ask_sizes = [quotes[t][3] for t in quote_timestamps]
        self.timestamps = quote_timestamps