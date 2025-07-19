class RangeBound:

    def __init__(self, mean, deviation, max_allowed_position=100):

        self.mean = mean
        self.deviation = deviation
        self.max_allowed_position = max_allowed_position

    def get_order(self, NBBO, current_position):

        order_qty = 0
        buy_side = True
        
        midpoint = (NBBO.get("bid") + NBBO.get("ask")) / 2

        if midpoint > self.mean + self.deviation:
            order_qty = current_position + self.max_allowed_position
            buy_side = False
        elif midpoint < self.mean - self.deviation:
            order_qty = abs(current_position - self.max_allowed_position)

        return order_qty, buy_side