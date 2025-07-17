def basic_fractional_slippage_model(NBBO, order_qty, buy_side=True, slippage_rate=0.001):

    if buy_side:
        ask = NBBO.get("ask")
        ask_size = NBBO.get("ask_size", 0)
        if order_qty <= ask_size:
            return ask, order_qty
        else:
            optimal_fill = ask_size
            suboptimal_fill = order_qty - ask_size
            suboptimal_price = ask * (1 + slippage_rate)
            avg_price = (ask * optimal_fill + suboptimal_price * suboptimal_fill) / order_qty
            return avg_price, order_qty
        
    else:
        bid = NBBO.get("bid")
        bid_size = NBBO.get("bid_size", 0)
        if order_qty <= bid_size:
            return bid, order_qty
        else:
            optimal_fill = bid_size
            suboptimal_fill = order_qty - bid_size
            suboptimal_price = bid * (1 - slippage_rate)
            avg_price = (bid * optimal_fill + suboptimal_price * suboptimal_fill) / order_qty
            return avg_price, order_qty


class MarketSimulator:

    def __init__(self):

        self.positions = {}
        self.postion_PnL = {}

    def fill_order(self, stock, NBBO, order_qty, buy_side=True, slippage_rate=0.001):

        avg_price, filled_qty = basic_fractional_slippage_model(NBBO, order_qty, buy_side, slippage_rate)

        if filled_qty <= 0:
            return None

        if stock not in self.positions:
            self.positions[stock] = 0
            self.postion_PnL[stock] = 0.0

        if buy_side:
            self.positions[stock] += filled_qty
            self.postion_PnL[stock] -= avg_price * filled_qty
        else:
            self.positions[stock] -= filled_qty
            self.postion_PnL[stock] += avg_price * filled_qty

    def get_total_PnL(self):

        return sum(self.postion_PnL.values())