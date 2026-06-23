def flatten(nested_list):
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result

def chunk(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]

def retry(fn, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception:
            if attempt == max_attempts - 1:
                raise
