# Test file for PR review command testing

def calculate_sum(a, b):
    result = a + b
    return result

def unsafe_query(user_input):
    # SQL injection vulnerability for testing
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"
    return query

def missing_error_handling():
    file = open("some_file.txt")
    content = file.read()
    return content

def unused_variable():
    x = 10
    y = 20
    return x
