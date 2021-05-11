from functools import lru_cache
from ledgerx_api import get_contracts, get_book_state
import arrow

from market import get_vol, get_price

contracts = get_contracts()
option_chain = contracts['option_chain']
futures = contracts['futures_contracts']

def get_btc_price():
    # Pulls nearest dated futures and gets the mid price
    now = arrow.utcnow()
    closest_expiry = None
    closest_future = None
    for future in futures:
        future_expiry = arrow.get(future['date_expires'])

        if not closest_expiry:
            closest_expiry = future_expiry
        if future_expiry > now and (future_expiry - now) < (closest_expiry - now):
            closest_future = future

    low_ask = 1e9
    high_bid = 0
    book_state = get_book_state(closest_future['id'], cache=False)['data']['book_states']
    for state in book_state:
        price = state['price']/100
        if state['is_ask']:
            if price < low_ask:
                low_ask = price
        else:
            if price > high_bid:
                high_bid = price
    mid = (high_bid + low_ask) / 2
    return(mid)


def get_expirys():
    expirys = []
    now = arrow.utcnow()
    # loops over expiration datetime strings and filters for expirations in the future
    for expiry in list(option_chain.keys()):
        expiry_date = arrow.get(expiry)
        if now < expiry_date:
            fmt = 'MM-DD-YY'
            label = expiry_date.format(fmt)
            expirys.append((expiry, label))

    # Reverse our relevant dates to make the nearest expiry [0]
    expirys.reverse()
    return expirys


@lru_cache()
def get_expiry_data(expiry_key, option_type, smoothing_factor):
    now = arrow.utcnow()
    expiry_series = option_chain[expiry_key]
    asks = []
    bids = []
    mids = []
    book_top = []
    max_size = 0
    high_strike = 0
    low_strike = 10e9
    btc_price = get_btc_price()

    # Every contract is different strike
    for contract in expiry_series:

        if option_type == 0 and contract['type'] == 'put':
            continue
        if option_type == 1 and contract['type'] == 'call':
            continue

        strike = contract['strike_price']/100
        if strike > high_strike:
            high_strike = strike
        if strike < low_strike:
            low_strike = strike

        book_state = get_book_state(contract['id'], cache=True)['data']['book_states']

        high_bid = 0
        low_ask = 10e9

        for state in book_state:
            price = state['price']/100
            size = state['size']
            if size > max_size:
                max_size = size

            # find top of orderbook
            if state['is_ask'] and price < low_ask:
                low_ask = price
            elif not state['is_ask'] and price > high_bid:
                high_bid = price

        book_top.append((strike, high_bid, low_ask))
        mid = (high_bid + low_ask) / 2
        mids.append((strike, mid))

        # Loop over again, not sure how to avoid this because
        # we need to find mid before filtering orders to remove outliers
        for state in book_state:
            price = state['price']/100
            if abs(price - mid) < (low_ask - high_bid) * 2:
                if state['is_ask']:
                    asks.append((price, strike, size))
                else:
                    bids.append((price, strike, size))

    # Mid line
    # Sort by strike price (x_axis)
    # https://stackoverflow.com/a/9764364
    mids = sorted(mids)
    strikes, mid_price = zip(*mids)

    # Get top of order book bid/ask to calc IV
    # Calculate IV skew plot from spline mid prices
    # TODO: figure out how to use seconds and division to get partial days
    dte = (arrow.get(expiry_key) - now).days
    if option_type == 1:
        flag = 'p'
    else:
        flag = 'c'

    # Here create series of IV for top bid and ask prices
    bid_iv = []
    ask_iv = []
    for strike, bid, ask in book_top:
        attrs = {
            'price': bid,
            'dte': dte,
            'ul_price': btc_price,
            'strike': strike,
            'flag': flag
        }
        bid_vol = get_vol(attrs)
        if bid_vol == 0:
            continue
        bid_iv.append((strike, bid_vol))
        attrs['price'] = ask
        ask_iv.append((strike, get_vol(attrs)))

    # Finally return a dict of all the different series for the data sources
    return {
        'btc_price': btc_price,
        'bids': bids,
        'asks': asks,
        'mids': mids,
        'ask_iv': ask_iv,
        'bid_iv': bid_iv
    }