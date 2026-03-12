def greet():
    return "Hello from DEV"

def process_data(items):
    return [item.upper() for item in items]

def validate(data):
    return all(isinstance(d, str) for d in data)

def main():
    print(greet())
    data = ["alpha", "beta", "gamma"]
    if validate(data):
        print(process_data(data))

if __name__ == "__main__":
    main()
