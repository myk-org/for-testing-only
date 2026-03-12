def get_config():
    return {"env": "development", "debug": True}

def format_output(data):
    lines = []
    for key, val in data.items():
        lines.append(f"{key}: {val}")
    return "\n".join(lines)

def main():
    config = get_config()
    print(format_output(config))

if __name__ == "__main__":
    main()
