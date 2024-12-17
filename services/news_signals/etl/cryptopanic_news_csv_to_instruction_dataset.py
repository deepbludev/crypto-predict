# 1. download the csv from cryptopanic
# 2. convert to pandas df
# 3. get sentiment for each story using the sentiment analyzer
# 4. load to jsonl file locally


from news_signals.signals import analyzer


def etl():
    print(analyzer.prompt)


if __name__ == "__main__":
    etl()
