# Notas de implantação e entrega — Artefact

## Material disponível e lacunas

- O PDF recebido descreve a prova, mas não contém as tabelas `data/*.csv` nem o PDF `data/políticas_da_loja.pdf`.
- O projeto nesta pasta é uma **base funcional e testável**, não uma solução final validada com os dados reais da Empório da Música.
- Substitua as fixtures ilustrativas do diretório `tests/fixtures` pelos arquivos originais em `data/` **sem publicar dados pessoais ou segredos**.
- Se a estrutura das colunas reais diferir dos nomes genéricos, ajustar mapeamento no arquivo `src/emporio_agent/store.py` e registrar a suposição no README.

## Prioridade de validação

1. Adicionar dados reais e inspecionar o esquema: `python -m emporio_agent inspect --data-dir data`.
2. Ajustar nomes de colunas e relacionamento entre pedidos e clientes; não permitir consultar pedido com apenas um ID.
3. Verificar extração e recuperação de todos os itens das políticas: horários, endereço, pagamento, troca, devolução.
4. Configurar API key em `.env` local (a CLI usa variáveis de ambiente; carregue com o seu terminal/gerenciador de segredos).
5. Executar conversas reais e avaliar possíveis alucinações e dados incorretos.
6. Gravar 3–5 exemplos reais, revisar README, executar testes, gerar commits progressivos verdadeiros.
7. Publicar repositório no GitHub e enviar o link no e-mail original.
8. O e-mail de recrutamento também menciona um Google Forms (e entrega em PDF), embora o PDF exija resposta por e-mail com o repositório. Para reduzir risco, seguir ambos e pedir confirmação do recrutamento se necessário.

## Prazo

E-mail recebido em 31/10/2026: até o final do segundo dia útil. Como 02/11/2026 (segunda-feira) é Finados, feriado nacional no Brasil, se a contagem considerar esse feriado, o segundo dia útil é quarta-feira 04/11/2026. Se a recrutadora considerar a segunda-feira útil, o segundo dia útil é terça-feira 03/11/2026. O fuso de corte também não foi explicitado. Adote 03/11 como meta interna conservadora, sem afirmar que é a data oficial.

## Proteção de dados

Nunca publicar no repositório os CSVs originais com e-mails, telefones, documentos ou endereços de clientes. O arquivo `.gitignore` cobre os dados do diretório `data/`, mas revise se outros nomes de arquivos contêm dados sensíveis antes do `git push`.

## Assistência de IA

O projeto base foi elaborado com auxílio de ChatGPT/GPT-6. Isso deve ser declarado no README final. O candidato deve revisar código, compreender as decisões e testar o comportamento com o conjunto de dados recebido, sem declarar validações que ainda não ocorreram.
