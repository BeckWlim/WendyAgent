from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class MemoryNote:
    path: str
    title: str
    content: str
    score: float = 0.0


class MarkdownMemoryVault:
    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "sessions").mkdir(exist_ok=True)
        (self.root / "notes").mkdir(exist_ok=True)

    def write_note(self, title: str, content: str, namespace: str = "notes") -> str:
        folder = self.root / self._clean_segment(namespace)
        folder.mkdir(parents=True, exist_ok=True)
        filename = self._clean_segment(title) or datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        path = folder / f"{filename}.md"
        header = f"# {title}\n\ncreated: {datetime.now(UTC).isoformat()}\n\n"
        path.write_text(header + content.strip() + "\n", encoding="utf-8")
        return str(path)

    def append_session_turn(self, session_id: str, question: str, answer: str) -> str:
        path = self.root / "sessions" / f"{self._clean_segment(session_id)}.md"
        if not path.exists():
            path.write_text(f"# Session {session_id}\n\n", encoding="utf-8")
        block = (
            f"## {datetime.now(UTC).isoformat()}\n\n"
            f"### User\n\n{question.strip()}\n\n"
            f"### Assistant\n\n{answer.strip()}\n\n"
        )
        with path.open("a", encoding="utf-8") as file:
            file.write(block)
        return str(path)

    def search(self, query: str, limit: int = 5) -> list[MemoryNote]:
        terms = self._terms(query)
        if not terms:
            return []

        results: list[MemoryNote] = []
        for path in self.root.rglob("*.md"):
            content = path.read_text(encoding="utf-8", errors="ignore")
            score = self._score(content, terms)
            if score > 0:
                results.append(MemoryNote(str(path), self._title(content, path), content, score))

        results.sort(key=lambda note: note.score, reverse=True)
        return results[:limit]

    def iter_notes(self) -> list[MemoryNote]:
        notes: list[MemoryNote] = []
        for path in self.root.rglob("*.md"):
            content = path.read_text(encoding="utf-8", errors="ignore")
            notes.append(MemoryNote(str(path), self._title(content, path), content, 0.0))
        return notes

    def _score(self, content: str, terms: Iterable[str]) -> float:
        lowered = content.lower()
        return float(sum(lowered.count(term) for term in terms))

    def _terms(self, query: str) -> list[str]:
        return [term.lower() for term in re.findall(r"[\w\u4e00-\u9fff]+", query) if len(term) > 1]

    def _title(self, content: str, path: Path) -> str:
        for line in content.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return path.stem

    def _clean_segment(self, value: str) -> str:
        return re.sub(r"[^a-zA-Z0-9._\-\u4e00-\u9fff]+", "_", value).strip("_")
