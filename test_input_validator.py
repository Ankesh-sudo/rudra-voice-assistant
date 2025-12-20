# test_input_validator.py

from core.input.input_validator import InputValidator

validator = InputValidator()

tests = [
    "hmm",
    "",
    "ok",
    "open",
    "open browser",
    "Hey please open the browser",
    "open browser",
    "   ...   ",
]

for t in tests:
    result = validator.validate(t)
    print(f"INPUT: {repr(t)}")
    print(f"RESULT: {result}")
    print("-" * 40)
