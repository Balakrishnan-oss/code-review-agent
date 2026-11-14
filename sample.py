import os

password = "admin123"

def average(numbers):
    total = 0
    for n in numbers:
        total += n
    return total / len(numbers)

def read_file(path):
    f = open(path)
    data = f.read()
    return data

def get_item(items, index):
    return items[index + 1]
