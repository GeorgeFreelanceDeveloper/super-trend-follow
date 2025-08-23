# region imports
from AlgorithmImports import *
import datetime
# endregion

"""
    The Supertrend Strategy is a trend trading strategy 
    developed by Oliver Seban that uses the Supertrend indicator to identify 
    and trends in the financial markets. This strategy focuses on entering the market 
    in line with the main trend and exiting the market when the trend begins to reverse.
"""
class SupertrendV2(QCAlgorithm):

    INDEXES = {
        "SP500": {
            "stocks": ["NVDA", "MSFT", "AAPL", "AMZN", "META", "AVGO", "GOOGL", "BRK.B", "TSLA", "GOOG"],
            "benchmark_symbol": "SPY"
            # https://finance.yahoo.com/quote/SPY/holdings/
        },
        "NASDAQ100": {
            "stocks": ["NVDA", "MSFT", "AAPL", "AMZN", "AVGO", "META", "NFLX", "TSLA", "COST", "GOOGL"],
            "benchmark_symbol": "QQQ"
            # https://finance.yahoo.com/quote/QQQ/holdings/
        },
        "SP500 MOMENTUM": {
            "stocks": ["NVDA", "META", "AMZN", "AVGO", "JPM", "TSLA", "WMT", "NFLX", "PLTR", "COST"],
            "benchmark_symbol": "SPMO"
            # https://finance.yahoo.com/quote/SPMO/holdings/
        },
        "SP MEDIUM CAP MOMENTUM": {
            "stocks": ["IBKR", "EME", "SFM", "FIX", "GWRE", "USFD", "CRS", "EQH", "CW", "CASY"],
            "benchmark_symbol": "XMMO"
            # https://finance.yahoo.com/quote/XMMO/holdings/
        },
        "SP SMALL CAP MOMENTUM": {
            "stocks": ["EAT", "CORT", "COOP", "AWI", "IDCC", "SKYW", "JXN", "CALM", "DY", "SMTC"],
            "benchmark_symbol": "XSMO"
            # https://finance.yahoo.com/quote/XSMO/holdings/
        },
        "IPOX 100 US": {
            "stocks": ["GEV", "PLTR", "APP", "CEG", "RBLX", "DASH", "IBM", "HOOD", "TT", "IOT"],
            "benchmark_symbol": "FPX"
            # https://finance.yahoo.com/quote/FPX/
        }
    }

    BENCHMARK_OLD = "SPY"  # fallback benchmark

    BREAK_OUTS = {
        "LONG_TERM": {"atr_period": 10, "factor": 30},
        "MEDIUM_TERM": {"atr_period": 10, "factor": 10},
        "SHORT_TERM": {"atr_period": 10, "factor": 3}
    }

    def initialize(self):

        # ********************************
        # User defined inputs
        # ********************************
        self.index = self.get_parameter("index", "SP500 MOMENTUM")
        self.breakout = self.get_parameter("breakout", "LONG_TERM")
        self.leverage = self.get_parameter("leverage", 0)


        # Filter settings
        self.enable_filter = True if (self.get_parameter("enable_filter", "True") == "True") else False

        # ********************************
        # Algorithm settings
        # ********************************
        self.set_start_date(datetime.date.today().year - 20, 1, 1)
        self.set_cash(10000)
        self.enable_automatic_indicator_warm_up = True

        self.benchmark_symbol = self.INDEXES[self.index]["benchmark_symbol"]
        self.benchmark_old_symbol = self.BENCHMARK_OLD
        self.symbols = self.INDEXES[self.index]["stocks"]
        self.markets = {symbol: self.add_equity(symbol, Resolution.DAILY) for symbol in self.symbols}
        self.add_equity(self.benchmark_symbol, Resolution.DAILY)
        self.add_equity(self.benchmark_old_symbol, Resolution.DAILY)
        self.enable_trading = True

        # Init indicators
        self.strs = {symbol: self.str(symbol, self.BREAK_OUTS[self.breakout]["atr_period"], self.BREAK_OUTS[self.breakout]["factor"]) for symbol in
                            self.symbols}
        self.benchmark_sma200 = self.sma(self.benchmark_symbol, 200)
        self.benchmark_old_sma200 = self.sma(self.benchmark_old_symbol, 200)

    def on_data(self, data: Slice):
        # **********************************
        # Zkontroluj trend benchmarku
        # **********************************
        if self.enable_filter:
            if self.benchmark_symbol in data.Bars:
                bar_benchmark = data.Bars[self.benchmark_symbol]
                self.enable_trading = bar_benchmark.close >= self.benchmark_sma200[1].value
            elif self.benchmark_old_symbol in data.Bars:  # fallback
                bar_benchmark = data.Bars[self.benchmark_old_symbol]
                self.enable_trading = bar_benchmark.close >= self.benchmark_old_sma200[1].value

        # **********************************
        # Aplikuj strategii na každou akcii
        # **********************************
        for symbol in self.symbols:
            _str = self.strs[symbol]
            self.strategy(data, symbol, _str)

    def strategy(self, data, symbol, _str):
        # **********************************
        # Perform calculations and analysis
        # **********************************

        # Basic
        # Basic
        if symbol not in data.Bars or self.benchmark_symbol not in data.Bars:
            return

        bar = data.Bars[symbol]

        is_uptrend = bar.close > _str[1].value
        buy_condition = is_uptrend and self.enable_trading and not self.portfolio[symbol].is_long
        sell_condition = not is_uptrend and self.portfolio[symbol].is_long if filter else True

        # ********************************
        # Manage trade
        # ********************************
        if buy_condition:
            self.set_holdings(symbol, (1 / len(self.symbols)) + (1 / len(self.symbols) * self.leverage))

        if sell_condition:
            self.liquidate(symbol)