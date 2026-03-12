def get_config():
    return {"env": "production", "debug": False, "workers": 4}

def format_output(data):
    return " | ".join(f"{k}={v}" for k, v in data.items())

def validate_config(config):
    required = ["env", "debug"]
    return all(k in config for k in required)

def main():
    config = get_config()
    if validate_config(config):
        print(format_output(config))

if __name__ == "__main__":
    main()
