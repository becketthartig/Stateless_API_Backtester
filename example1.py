### example1.py ###
#
# Implements a super basic trading strategy for LLY
# Shows how to run multiple days and write stateless strategies
# This template can be generalized to any stock and stateless strategy module possible
#


from src.interface import DataInterface
from src.results import Grapher
from src.marketsimulator import MarketSimulator, IdealFillSlippageModel, ZeroCostStructure

from example_strategies.reversion import RangeBound


API_KEY = "YOUR_API_KEY"
STOCK = "LLY"
DATES = ["2025-07-14", "2025-07-15", "2025-07-16", "2025-07-17", "2025-07-18"]


if __name__ == "__main__":


    DI = DataInterface(API_KEY, STOCK, DATES, use_NY_hours=False, start_hour=4, end_hour=23.98)
    Results = Grapher()

    # Can write your own slippage model and cost structure based on the structure in marketsimulator.py
    MS = MarketSimulator(slippage_model=IdealFillSlippageModel(), cost_structure=ZeroCostStructure())

    # Stable mean reversion strategy
    Strategy = RangeBound(mean=780, deviation=13, max_allowed_position=100)


    sample = DI.next_sample()

    while sample:

        if sample.NBBO.get("bid", 0) == 0 or sample.NBBO.get("ask", 0) == 0:
            continue

        order_qty, buy_side = Strategy.get_order(sample.NBBO, MS.positions.get(STOCK, 0))
        if order_qty != 0:
            MS.fill_order(STOCK, sample.NBBO, order_qty, sample.temporal, buy_side)

        Results.add_data(sample.temporal, (sample.NBBO.get("bid"), sample.NBBO.get("ask")), MS.positions.get(STOCK, 0), MS.get_equity_curve_sample(STOCK, sample.NBBO))
        
        sample = DI.next_sample()


    print(f"Final Unrealized PnL for {STOCK}: {MS.get_stock_unrealized_PnL(STOCK, DI.last_sample.NBBO)}")
    print(f"Final Realized PnL for {STOCK}: {MS.get_stock_Pnl(STOCK)}")
    Results.show_plot()