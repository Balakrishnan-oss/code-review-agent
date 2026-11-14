import os
import json

API_KEY = "sk-live-12345"

def get_discount(price, percent):
    return price - price * percent

def load_config(path):
    f = open(path)
    return json.load(f)
