"""Cited, lightweight RAG over the source PDF, with transparent lexical scoring.

One page is the retrieval unit because the manual is only eight short pages and
most rules are tabular. No embedded private PDF is copied to the public demo.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .store import norm

STOP = set(
    (
        "a o as os de do da dos das e em um uma para por com que como meu minha seu sua no na "
        "nos nas tem posso pode qual quais quanto custa loja produto pedido sobre informacao "
        "gostaria saber "
    ).split()
)
SYNONYMS = {
    "arrependi": ("arrependimento", "devolucao", "online"),
    "devolver": ("devolucao", "arrependimento"),
    "devolucoes": ("devolucao", "troca"),
    "trocar": ("troca", "trocas"),
    "defeito": ("troca", "garantia", "fabricacao"),
    "abrir": ("horario", "funcionamento"),
    "abre": ("horario", "funcionamento"),
    "funciona": ("horario", "funcionamento"),
    "horas": ("horario", "funcionamento"),
    "hora": ("horario", "funcionamento"),
    "onde": ("endereco", "rua"),
    "localizacao": ("endereco", "rua"),
    "pagar": ("pagamento", "parcelamento"),
    "parcela": ("parcelamento", "credito"),
    "parcelas": ("parcelamento", "credito"),
    "parcelar": ("parcelamento", "credito"),
    "pix": ("pagamento", "desconto"),
    "frete": ("entrega", "envio"),
    "entregar": ("entrega", "frete"),
    "rastreamento": ("rastreio", "codigo"),
    "rastrear": ("rastreamento", "codigo"),
    "dados": ("privacidade", "lgpd"),
    "excluir": ("exclusao", "privacidade"),
    "promocao": ("desconto", "promocoes"),
}

# Domain-aware page boost reduces mismatched passages from generic vocabulary.
# The source manual can change: pages below apply only to v2.1 (June/2025).
TOPICS: tuple[tuple[set[str], set[int]], ...] = (
    ({"horario", "funcionamento", "abre", "domingo", "sabado"}, {2}),
    ({"endereco", "rua", "localizacao", "onde"}, {1, 2}),
    ({"contato", "telefone", "whatsapp", "email"}, {2, 6}),
    ({"pagamento", "pix", "debito", "credito", "boleto", "parcelamento", "parcela"}, {3, 6}),
    ({"devolucao", "arrependimento", "troca", "defeito", "trocar", "devolver"}, {4, 7}),
    ({"frete", "entrega", "rastreamento", "rastreio", "correios", "sedex"}, {4, 5}),
    ({"promocao", "desconto", "liquidacao", "black"}, {6, 7}),
    ({"garantia", "fabricante", "defeito"}, {4, 7}),
    ({"lgpd", "privacidade", "dados", "exclusao"}, {7, 8}),
    ({"acessorios", "cordas", "palhetas", "amplificadores"}, {2, 6}),
)


def terms(text: str) -> list[str]:
    raw = [t for t in norm(text).split("_") if len(t) > 2 and t not in STOP]
    expanded = []
    for token in raw:
        t = token if token not in {"horarios", "trocas"} else {"horarios": "horario", "trocas": "troca"}[token]
        expanded.append(t)
        expanded.extend(SYNONYMS.get(t, ()))
    return expanded


@dataclass(frozen=True)
class Chunk:
    page: int
    text: str


def load_policies(data_dir: str | Path) -> PolicyIndex:
    """The manual of a data folder (accented or ASCII file name)."""
    data_dir = Path(data_dir)
    index = PolicyIndex(data_dir / "políticas_da_loja.pdf")
    if not index.chunks:
        alternative = data_dir / "politicas_da_loja.pdf"
        if alternative.exists():
            index = PolicyIndex(alternative)
    return index


class PolicyIndex:
    def __init__(self, pdf_path: str | Path):
        self.pdf_path = Path(pdf_path)
        self.chunks: list[Chunk] = []
        self._build()
        if not self.pdf_path.exists():
            return
        from pypdf import PdfReader
        reader = PdfReader(str(self.pdf_path))
        for page_number, page in enumerate(reader.pages, start=1):
            extracted = page.extract_text() or ""
            text = re.sub(r"\s+", " ", extracted).strip()
            if text:
                self.chunks.append(Chunk(page_number, text))
        self._build()

    def _build(self) -> None:
        """Tokenise the manual once. Per question we only need term counts and document frequencies."""
        self._counters = [Counter(terms(chunk.text)) for chunk in self.chunks]
        self._df: Counter[str] = Counter()
        for counter in self._counters:
            self._df.update(counter.keys())

    def search(self, question: str, top_k: int = 3) -> dict:
        if not self.chunks:
            return {"status": "unavailable", "reason": "Store policies PDF missing or unreadable"}
        qterms = terms(question)
        if not qterms:
            return {"status": "no_evidence", "results": []}
        q = set(qterms)
        n = len(self._counters)
        idf = {token: math.log(1 + (n + 1) / (1 + self._df[token])) for token in q}
        scored = []
        for chunk, counter in zip(self.chunks, self._counters, strict=True):
            score = sum((1 + math.log(1 + counter[token])) * idf[token] for token in q if counter[token] > 0)
            for triggers, pages in TOPICS:
                if q.intersection(triggers) and chunk.page in pages:
                    # Boost only if the page contains at least one of the topic triggers.
                    if any(counter[term] > 0 for term in triggers):
                        score += 3
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda row: (-row[0], row[1].page))
        out = [{"source": self.pdf_path.name, "page": chunk.page, "excerpt": chunk.text}
               for _, chunk in scored[:max(1, min(top_k, 4))]]
        return {"status": "ok" if out else "no_evidence", "results": out,
                "note": "Extracted page text from internal manual v2.1; cite page. Escalate ambiguous or conflicting rules."}
