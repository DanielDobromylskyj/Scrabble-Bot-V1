from pathlib import Path


class Dictionary:
    def __init__(self, path: Path):
        self.path = path
        with self.path.open() as f:
            self.words = set(f.read().splitlines())

    def __contains__(self, word: str) -> bool:
        return word.lower() in self.words

    def __len__(self) -> int:
        return len(self.words)

    def __repr__(self) -> str:
        return f"<Dictionary {self.path}>"
