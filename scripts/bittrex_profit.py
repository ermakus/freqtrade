import sys
from io import BytesIO
from pandas import DataFrame, read_csv
from datetime import timedelta
import argparse


def orders_total_sell(df):
    return (df['Price']  - df['CommissionPaid']).sum()


def orders_total_buy(df):
    return (df['Price']  + df['CommissionPaid']).sum()


def print_stat(df, idx):
    buy  = df.loc[df['Type'] == 'LIMIT_BUY']
    sell = df.loc[df['Type'] == 'LIMIT_SELL']
    profit = orders_total_sell(sell) - orders_total_buy(buy)
    print("{0} {1: .8f} {2: 4d} {3: 4d} {4: 4d}".format( idx, profit, df.shape[0], buy.shape[0], sell.shape[0]))


def full_stats(filename, days):
    fh = open(filename, 'rb')
    buf = BytesIO(fh.read().decode('UTF-16').encode('UTF-8'))
    df = read_csv( buf,
                   parse_dates=["Opened","Closed"],
                   index_col="Closed")
    df.sort_index(inplace=True)
    if days:
        last = df.index[-1].to_pydatetime().replace(hour=0, minute=0, second=0) - timedelta(days=days-1)
        df = df.loc[df.index >= last]

    print("--------------------------------------")
    print("Date      Profit       Trades Buy Sell")
    print("--------------------------------------")
    for idx, day in df.groupby(df.index.date):
        idx = str(day.index[0])[:10]
        print_stat(day, idx)
    print("--------------------------------------")
    print_stat(df,'Total     ')

def main():
    parser = argparse.ArgumentParser(description='Parse bittrex orders csv and calulate daily profits')
    parser.add_argument('path', metavar='PATH', type=str,
                    help='Path to fullOrders.csv file (UTF16 encoding)')
    parser.add_argument('--days', default=0, type=int,
                    help='process last N days (default: all)')

    args = parser.parse_args()
    full_stats( args.path, args.days )

if __name__ == "__main__":
    main()
