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


def calculate_ibkr_proFIXED_fee(shares, avg_price):

    PER_SHARE_FEE = 0.005
    MIN_ORDER_FEE = 1.00 

    return min(max(shares * PER_SHARE_FEE, MIN_ORDER_FEE), shares * avg_price * 0.01)


class MarketSimulator:

    def __init__(self):
        self.positions = {}
        self.position_PnL = {}
        self.short_lots = {}  

    def fill_order(self, stock, NBBO, order_qty, buy_side=True, slippage_rate=0.001, cost_to_borrow=0.0, timestamp=None):
        """
        timestamp: Unix nanosecond timestamp for simulation time
        """
        avg_price, filled_qty = basic_fractional_slippage_model(NBBO, order_qty, buy_side, slippage_rate)
        if filled_qty <= 0:
            return None

        if stock not in self.positions:
            self.positions[stock] = 0
            self.position_PnL[stock] = 0.0
            self.short_lots[stock] = []

        if buy_side:
            if self.positions[stock] < 0:
                qty_to_cover = min(filled_qty, abs(self.positions[stock]))
                self._cover_short(stock, qty_to_cover, avg_price, timestamp)
                filled_qty -= qty_to_cover
            self.positions[stock] += filled_qty
            self.position_PnL[stock] -= avg_price * filled_qty + calculate_ibkr_proFIXED_fee(filled_qty, avg_price)
        else:
            self.positions[stock] -= filled_qty
            self.short_lots[stock].append({
                "qty": filled_qty,
                "entry_time": timestamp,
                "entry_price": avg_price,
                "borrow_rate": cost_to_borrow
            })
            self.position_PnL[stock] += avg_price * filled_qty - calculate_ibkr_proFIXED_fee(filled_qty, avg_price)

    def _cover_short(self, stock, qty_to_cover, cover_price, timestamp):
        lots = self.short_lots[stock]
        qty_left = qty_to_cover
        while qty_left > 0 and lots:
            lot = lots[0]
            lot_qty = lot["qty"]
            used_qty = min(qty_left, lot_qty)
            holding_seconds = (timestamp - lot["entry_time"]) / 1e9
            holding_days = holding_seconds / 86400
            borrow_cost = used_qty * lot["entry_price"] * lot["borrow_rate"] * holding_days / 365
            pnl = (lot["entry_price"] - cover_price) * used_qty - borrow_cost
            self.position_PnL[stock] += pnl
            lot["qty"] -= used_qty
            qty_left -= used_qty
            if lot["qty"] == 0:
                lots.pop(0)

    def get_total_PnL(self):
        return sum(self.position_PnL.values())