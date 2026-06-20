# Cherry-pick conflict test - MAIN version
def get_greeting():
    return "Hello from MAIN branch - this is the main version"

def get_version():
    return "1.0.0"

def get_status():
    return "stable"

if __name__ == "__main__":
    print(get_greeting())
    print(f"Version: {get_version()}")
    print(f"Status: {get_status()}")
