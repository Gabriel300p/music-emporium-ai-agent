"""The rule-based offline agent should read like a store assistant: complete answers, no technical leftovers."""
import re
from pathlib import Path

from emporio_agent.offline import OfflineAgent, best_sentences

DEMO = Path(__file__).resolve().parents[1] / "demo_data"
PUBLIC = Path(__file__).resolve().parents[1] / "data_public"


def ask(question, data=DEMO, agent=None):
    agent = agent or OfflineAgent(data)
    return agent.reply(question)


def test_greeting_introduces_the_assistant_and_offers_topics_without_calling_tools():
    reply, trace = ask("Oi, bom dia!")
    assert trace == []
    assert "Empório da Música" in reply and "?" in reply
    assert all(topic in reply.lower() for topic in ("preço", "pedido", "troca"))


def test_thanks_gets_a_polite_closing():
    reply, trace = ask("Obrigado!")
    assert trace == [] and "por nada" in reply.lower()


def test_address_and_hours_are_answered_with_the_content_not_a_page_pointer():
    reply, trace = ask("Qual o endereço da loja e o horário de funcionamento?")
    assert trace[0] == {"tool": "search_policies", "status": "ok"}
    assert "Rua Exemplo, 10" in reply and "9h as 18h" in reply
    assert "Confira o trecho" not in reply and "Modo offline limitado" not in reply
    assert "(Manual, p. 1)" in reply or "página 1" in reply


def test_payment_question_is_answered_from_the_manual():
    reply, trace = ask("Posso pagar no PIX? Tem desconto?")
    assert trace[0]["tool"] == "search_policies"
    assert "5%" in reply and "PIX" in reply


def test_return_policy_quotes_the_rule_and_hands_the_case_to_the_team():
    reply, trace = ask("Me arrependi da compra, posso devolver?")
    assert trace[0]["tool"] == "search_policies"
    assert "7 (sete) dias" in reply and "equipe" in reply.lower()
    assert "(Manual, p. 1)" in reply or "página 1" in reply


def test_product_list_is_a_friendly_intro_a_short_list_and_a_follow_up_question():
    reply, trace = ask("Quais violões disponíveis custando até R$ 1.000?")
    assert trace == [{"tool": "search_products", "status": "ok"}]
    assert "R$ 599,90" in reply and "R$ 879,20" in reply and "1.099,00" in reply
    assert "Exibindo" not in reply and "registros" not in reply
    assert reply.rstrip().endswith("?"), "closes with a follow-up question"
    assert re.search(r"^- \*\*", reply, re.M), "items are bold-named list entries the page can render"


def test_a_long_result_shows_at_most_five_items_and_says_there_are_more():
    reply, _ = ask("Quais violões disponíveis?", data=PUBLIC)
    items = [line for line in reply.splitlines() if line.startswith("- ")]
    assert 1 <= len(items) <= 5
    assert re.search(r"mais \d+", reply) and "Exibindo" not in reply


def test_single_product_answer_gives_price_pix_and_availability():
    reply, _ = ask("Quanto custa o Takamine GD20?", data=PUBLIC)
    assert "Takamine GD20" in reply and "R$ 2.199,00" in reply
    assert "PIX" in reply and "R$ 2.089,05" in reply
    assert "estoque" in reply.lower()


def test_promotions_show_old_and_new_price_and_the_pix_rule():
    reply, trace = ask("Quais promoções estão ativas?")
    assert [t["tool"] for t in trace] == ["search_promotions", "search_policies"]
    assert "R$ 1.099,00" in reply and "R$ 879,20" in reply and "-20%" in reply
    assert "PIX" in reply and "Manual, p. 1" in reply


def test_verified_order_is_summarised_in_portuguese_without_leaking_the_email():
    agent = OfflineAgent(DEMO)
    agent.reply("Qual o status do pedido 1001?")
    reply, trace = agent.reply("Meu email é ana@example.test")
    assert trace[0]["status"] == "verified"
    assert "enviado" in reply and "shipped" not in reply
    assert "DEMO0001" in reply and "ana@example.test" not in reply


def test_denied_order_explains_what_to_check_and_reveals_nothing():
    agent = OfflineAgent(DEMO)
    agent.reply("Qual o status do pedido 1001?")
    reply, trace = agent.reply("Meu email é errado@example.test")
    assert trace[0]["status"] == "not_verified"
    assert "não posso apresentar" in reply and "e-mail" in reply
    assert "DEMO0001" not in reply and "enviado" not in reply


def test_order_without_email_asks_only_for_the_email():
    reply, trace = ask("Quero saber do pedido 1001")
    assert trace == [] and "e-mail" in reply and "1001" in reply


def test_out_of_scope_redirects_with_examples_of_what_it_can_do():
    reply, trace = ask("Quem ganhou a Copa de 2014?")
    assert trace == []
    assert "instrumentos musicais" in reply and "pedido" in reply.lower()


def test_best_sentences_picks_the_matching_sentences_in_order_and_skips_the_rest():
    text = "Horario: segunda a sexta, 9h as 18h. Endereco: Rua Exemplo, 10. Pagamento: PIX com 5% de desconto. Devolucao em 7 dias."
    assert best_sentences(text, "qual o horario?", 2) == ["Horario: segunda a sexta, 9h as 18h."]
    both = best_sentences(text, "endereco e horario da loja", 3)
    assert both == ["Horario: segunda a sexta, 9h as 18h.", "Endereco: Rua Exemplo, 10."]
    assert best_sentences(text, "xyz qwerty", 2) == []


def test_accessories_are_not_sold_and_no_catalogue_search_is_made():
    for question in ("Vocês vendem cabo de guitarra?", "Tem palheta?", "Preciso de um amplificador"):
        reply, trace = ask(question, data=PUBLIC)
        assert trace == [], question
        assert "acessórios" in reply and "instrumentos" in reply, question
