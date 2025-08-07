import re

class Checker:
    def __init__(self):
        pass

    def check(self, text):
        errors = []
        for i, line in enumerate(text.splitlines()):
            if line.count('{') != line.count('}'):
                errors.append(f"Mismatched braces on line {i+1}")
            if line.count('[') != line.count(']'):
                errors.append(f"Mismatched brackets on line {i+1}")
        return errors
