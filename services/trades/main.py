from trades.core.settings import trades_settings


def main():
    print("Hello from trades!")
    settings = trades_settings()
    print(settings)


if __name__ == "__main__":
    main()
