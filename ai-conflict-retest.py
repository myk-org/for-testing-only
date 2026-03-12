def greet():
    return "Hello from DEV"

def process_data(items):
    result = []
    for item in items:
        result.append(item.upper())
    return result

def main():
    print(greet())
    data = ["alpha", "beta", "gamma"]
    print(process_data(data))

if __name__ == "__main__":
    main()
