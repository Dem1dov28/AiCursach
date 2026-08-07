"""Simple line diff for document revisions."""

from __future__ import annotations

import difflib
from dataclasses import dataclass


@dataclass(frozen=True)
class DiffLine:
    kind: str  # add | remove | same
    text: str

    def to_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "text": self.text}


def diff_plain_text(before: str, after: str) -> list[DiffLine]:
    before_lines = before.splitlines()
    after_lines = after.splitlines()
    result: list[DiffLine] = []

    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, before_lines, after_lines).get_opcodes():
        if tag == "equal":
            for line in before_lines[i1:i2]:
                result.append(DiffLine("same", line))
        elif tag == "delete":
            for line in before_lines[i1:i2]:
                result.append(DiffLine("remove", line))
        elif tag == "insert":
            for line in after_lines[j1:j2]:
                result.append(DiffLine("add", line))
        elif tag == "replace":
            for line in before_lines[i1:i2]:
                result.append(DiffLine("remove", line))
            for line in after_lines[j1:j2]:
                result.append(DiffLine("add", line))

    return result
