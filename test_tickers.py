from src.utils.data_fetcher import DataFetcher

df = DataFetcher()

tickers = [
    ('VOLV-B.ST', 'Volvo B'),
    ('HM-B.ST', 'H&M B'),
    ('INVE-B.ST', 'Investor B'),
    ('SEB-A.ST', 'SEB A'),
    ('ESSITY-B.ST', 'Essity B')
]

print("Testing Swedish stock tickers:")
print("-" * 50)

for ticker, name in tickers:
    data = df.fetch_stock_data(ticker, period='5y')
    if data:
        print(f"{name:20} ({ticker:15}): {len(data):4} datapunkter")
    else:
        print(f"{name:20} ({ticker:15}): FAILED")
