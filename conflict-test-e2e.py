# Cherry-pick conflict test - DEV version
def get_greeting():
    return "Hello from DEV branch - this is the dev version"

def get_version():
    return "2.0.0-dev"

def get_status():
    return "stable"

if __name__ == "__main__":
    print(get_greeting())
    print(f"Version: {get_version()}")
    print(f"Status: {get_status()}")
