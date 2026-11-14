from utils import get_discount, load_config

def checkout(price):
    final = get_discount(price, 20)
    print("Final price:", final)
    return final

def main():
    try:
        config = load_config("config.json")
    except:
        pass
    checkout(100)

if __name__ == "__main__":
    main()
