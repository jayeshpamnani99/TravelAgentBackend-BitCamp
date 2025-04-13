import os

def get_prompt(filename: str) -> str:
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path, "r", encoding="utf-8") as file:
        return file.read()
