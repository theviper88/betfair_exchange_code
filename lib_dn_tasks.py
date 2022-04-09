import sqlite3
import operator as op
from functools import reduce

def log_market_position(datetime, market_id, market_type, expected_value, worst_position, matched_volume):

    connection = sqlite3.connect('exchange.db')
    with connection:
        cur = connection.cursor()
        market_values = [[datetime, market_id, market_type, expected_value, worst_position, matched_volume]]
        cur.executemany("INSERT INTO market_positions values(?, ?, ?, ?, ?, ?)", market_values)


def ncr(n, r):
    r = min(r, n-r)
    numer = reduce(op.mul, range(n, n-r, -1), 1)
    denom = reduce(op.mul, range(1, r+1), 1)
    return numer / denom





