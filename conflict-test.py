def hello():
    return "Hello from MAIN branch"

def calculate():
    return 100

def greet(name):
    return f"Hi {name}\!"

def main():
    print(hello())
    print(calculate())
    print(greet("World"))

if __name__ == "__main__":
    main()
