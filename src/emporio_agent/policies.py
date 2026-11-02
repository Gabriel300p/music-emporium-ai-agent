"""Lightweight, explainable, citation-bearing PDF retrieval without vector infra."""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from .store import norm

STOP = set("a o as os de do da dos das e em um uma para por com que como meu minha seu sua no na nos nas tem posso pode qual quais quanto custa".split())
EXPAND = {
    "devolver": ("devolucao", "arrependimento"),
    "devolucao": ("devolver", "arrependimento"),
    "arrependi": ("arrependimento", "devolucao"),
    "trocar": ("troca",),
    "abre": ("horario", "funcionamento"),
    "funciona": ("horario", "funcionamento"),
    "horas": ("horario", "funcionamento"),
    "pagar": ("pagamento", "parcelamento"),
    "parcela": ("parcelamento", "pagamento"),
    "endereco": ("localizacao", "rua"),
}


def tokens(text: str) -> list[str]:
    words = norm(text).split("_")
    result = []
    for w in words:
        if len(w) < 3 or w in STOP:
            continue
        result.append(w)
        result.extend(EXPAND.get(w, ()))
    return result


@dataclass(frozen=True)
class Chunk:
    page: int
    text: str


class PolicyIndex:
    def __init__(self, pdf_path: str | Path):
        self.pdf_path = Path(pdf_path)
        self.chunks: list[Chunk] = []
        if not self.pdf_path.exists():
            return
        from pypdf import PdfReader
        reader = PdfReader(str(self.pdf_path))
        for page_no, page in enumerate(reader.pages, start=1):
            content = re.sub(r"[ \t]+", " ", page.extract_text(extraction_mode="plain") or "").strip()
            if not content:
                continue
            # Keep paragraph-like regions and page attribution. Never merge pages.
            while len(content) > 650:
                split = content.rfind("\n", 300, 650)
                if split < 300:
                    split = content.rfind(". ", 300, 650)
                if split < 300:
                    split = 600
                self.chunks.append(Chunk(page_no, content[:split].strip()))
                content = content[max(0, split - 60):].strip()
            if content:
                self.chunks.append(Chunk(page_no, content))

    def search(self, question: str, top_k: int = 3) -> dict:
        if not self.chunks:
            return {"status": "unavailable", "reason": "Store policy PDF is missing or contains no extractable text."}
        terms = tokens(question)
        if not terms:
            return {"status": "no_evidence", "results": []}
        docs = [Counter(tokens(chunk.text)) for chunk in self.chunks]
        n = len(docs)
        scored = []
        for i, counter in enumerate(docs):
            score = sum((1 + math.log(counter[t])) * math.log(1 + (n + 1) / (1 + sum(t in c for c in docs)))
                        for t in set(terms) if counter[t] > 0)
            if score > 0:
                scored.append((score, self.chunks[i]))
        scored.sort(key=lambda x: x[0], reverse=True)
        return {"status": "ok" if scored else "no_evidence", "results": [
            {"source": self.pdf_path.name, "page": chunk.page, "excerpt": chunk.text[:650]}
            for _, chunk in scored[:max(1, min(top_k, 5))]
        ], "note": "Extracted excerpts only. No policy conclusions should be invented beyond cited text."}
