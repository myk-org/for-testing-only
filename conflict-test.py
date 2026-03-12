def hello():
    return "Hello from DEV branch"

def calculate():
    return 42

def greet(name):
    return f"Hi {name}!"

def main():
    print(hello())
    print(calculate())
    print(greet("World"))

if __name__ == "__main__":
    main()
