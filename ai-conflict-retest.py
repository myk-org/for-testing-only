def greet():
    return "Hello from MAIN"

def process_data(items):
    return [item.lower() for item in items]

def validate(data):
    return all(isinstance(d, str) for d in data)

def main():
    print(greet())
    data = ["Alpha", "Beta", "Gamma", "Delta"]
    if validate(data):
        print(process_data(data))

if __name__ == "__main__":
    main()
