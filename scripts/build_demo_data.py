"""Generates 100% synthetic public demo CSV files and a one-page PDF.

No source customer records, original catalog, or internal store policy are copied.
This script is deterministic and is run only when authoring demo fixtures.
"""
from __future__ import annotations

import csv
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

OUT = Path(__file__).resolve().parents[1] / "demo_data"
OUT.mkdir(exist_ok=True)


def write_csv(name: str, fields: list[str], rows: list[dict]):
    with (OUT / f"{name}.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


write_csv("categories", ["category_id", "name", "description"], [
    {"category_id": "1", "name": "Violões", "description": "Instrumentos de corda"},
    {"category_id": "2", "name": "Guitarras", "description": "Instrumentos elétricos"},
])
write_csv("products", ["product_id", "price_brl", "name", "category_id", "description", "stock_quantity", "status", "specs", "created_at"], [
    {"product_id": "1", "price_brl": "599.90", "name": "Violão Escola C30 Demo", "category_id": "1", "description": "Violão de estudo (fictício)", "stock_quantity": "10", "status": "active", "specs": "{}", "created_at": "2026-10-01"},
    {"product_id": "2", "price_brl": "2199.00", "name": "Takamine GD20 Demo", "category_id": "1", "description": "Violão folk (preço fictício)", "stock_quantity": "5", "status": "active", "specs": "{}", "created_at": "2026-10-01"},
    {"product_id": "3", "price_brl": "1099.00", "name": "Violão Folk Promo Demo", "category_id": "1", "description": "Violão fictício em oferta", "stock_quantity": "4", "status": "active", "specs": "{}", "created_at": "2026-10-01"},
    {"product_id": "4", "price_brl": "999.00", "name": "Guitarra Estudo GX Demo", "category_id": "2", "description": "Guitarra fictícia", "stock_quantity": "0", "status": "active", "specs": "{}", "created_at": "2026-10-01"},
])
write_csv("promotions", ["promotion_id", "product_id", "discount_percent", "description", "is_active"], [
    {"promotion_id": "1", "product_id": "3", "discount_percent": "20", "description": "Oferta fictícia", "is_active": "1"},
])
write_csv("customers", ["customer_id", "name", "phone", "email", "city"], [
    {"customer_id": "1", "name": "Ana Exemplo", "phone": "0000", "email": "ana@example.test", "city": "Cidade Demo"},
    {"customer_id": "2", "name": "Bruno Exemplo", "phone": "0000", "email": "bruno@example.test", "city": "Cidade Demo"},
])
write_csv("orders", ["order_id", "customer_id", "order_date", "status", "total_brl", "payment_method", "tracking_code", "estimated_delivery", "notes"], [
    {"order_id": "1001", "customer_id": "1", "order_date": "2026-10-01", "status": "shipped", "total_brl": "599.90", "payment_method": "pix", "tracking_code": "DEMO0001", "estimated_delivery": "2026-10-10", "notes": ""},
])
write_csv("order_items", ["order_id", "quantity", "product_id"], [
    {"order_id": "1001", "quantity": "1", "product_id": "1"},
])

pdf = canvas.Canvas(str(OUT / "políticas_da_loja.pdf"), pagesize=A4)
pdf.setTitle("Manual ficticio para demonstracao")
pdf.setFont("Helvetica-Bold", 13)
pdf.drawString(55, 770, "EMPORIO DA MUSICA - POLITICAS DEMO (100% FICTICIAS)")
pdf.setFont("Helvetica", 10)
lines = [
    "Documento para testes: NAO representa o manual interno fornecido no desafio.",
    "Horario ficticio: segunda a sexta, 9h as 18h; sabado, 9h as 13h.",
    "Endereco ficticio: Rua Exemplo, 10, Cidade Demo.",
    "Pagamento: PIX com 5% de desconto sobre preco nao promocional.",
    "Promocoes nao acumulam com o desconto PIX.",
    "Devolucao de compras online: 7 (sete) dias corridos apos o recebimento.",
    "Devolucao sujeita a verificacao da embalagem e da conservacao do produto.",
    "A equipe de atendimento deve confirmar casos concretos de troca ou devolucao.",
]
for i, line in enumerate(lines):
    pdf.drawString(55, 740 - i * 24, line)
pdf.save()
print(f"Demo files in {OUT}")
