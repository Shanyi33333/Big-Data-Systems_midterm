class Strategy():
    # option setting needed
    def __setitem__(self, key, value):
        self.options[key] = value

    # option setting needed
    def __getitem__(self, key):
        return self.options.get(key, '')

    def __init__(self):
        # strategy property
        self.subscribedBooks = {
            'Binance': {
                'pairs': ['BTC-USDT'],
            },
        }
        self.period = 360 * 60
        self.options = {}

        # user defined class attribute
        self.last_type = 'sell'
        # self.last_cross_status = None
        self.cross_state_list = np.array([])
        self.close_price_trace = np.array([])
        self.ma_long = 30
        self.ma_short = 5
        self.UP = 1
        self.DOWN = 2
        self.day = -1

    def on_order_state_change(self, order):
        Log("on order state change message: " + str(order) + " order price: " + str(order["price"]))

    def get_current_ma_cross(self):
        s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1]
        l_ma = talib.SMA(self.close_price_trace, self.ma_long)[-1]
        if self.day >= 0:
            self.day += 1
        if np.isnan(s_ma) or np.isnan(l_ma):
            return None
        if s_ma > l_ma:
            return self.UP
        return self.DOWN

    def trade(self, information):
        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        target_currency = pair.split('-')[0]  # BTC
        base_currency = pair.split('-')[1]  # USDT
        base_currency_amount = self['assets'][exchange][base_currency]
        target_currency_amount = self['assets'][exchange][target_currency]
        # add latest price into trace
        close_price = information['candles'][exchange][pair][0]['close']
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        # only keep max length of ma_long count elements
        self.close_price_trace = self.close_price_trace[-self.ma_long:]
        # calculate current ma cross status
        cur_cross = self.get_current_ma_cross()
        self.cross_state_list = np.append(self.cross_state_list, [float(cur_cross)])
        # if cur_cross is None:
        #    return []
        # if self.last_cross_status is None:
        #    self.last_cross_status = cur_cross
        #    return []
        # cross up
        cross_state_len = len(self.cross_state_list)
        if self.last_type == 'sell' and cross_state_len >= 3:
            if self.cross_state_list[cross_state_len - 3] == self.UP and \
                    self.cross_state_list[cross_state_len - 2] == self.DOWN and \
                    self.cross_state_list[cross_state_len - 1] == self.DOWN:
                Log('buying 1 unit of ' + str(target_currency))
                self.last_type = 'buy'
                self.day = 0
                # self.last_cross_status = cur_cross
                return [
                    {
                        'exchange': exchange,
                        'amount': 1,
                        'price': -1,
                        'type': 'MARKET',
                        'pair': pair,
                    }
                ]
        # cross down
        elif self.last_type == 'buy' and cross_state_len >= 3:
            if (self.cross_state_list[cross_state_len - 3] == self.DOWN and \
                self.cross_state_list[cross_state_len - 2] == self.UP and \
                self.cross_state_list[cross_state_len - 1] == self.UP) or self.day == 3:
                Log('assets before selling: ' + str(self['assets'][exchange][base_currency]))
                self.last_type = 'sell'
                self.cross_state_list = np.array([])
                self.day = -1
                # self.last_cross_status = cur_cross
                return [
                    {
                        'exchange': exchange,
                        'amount': -target_currency_amount,
                        'price': -1,
                        'type': 'MARKET',
                        'pair': pair,
                    }
                ]
        # self.last_cross_status = cur_cross
        return []
