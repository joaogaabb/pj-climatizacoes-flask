"""
PJ Climatizações — site feito com Python + Flask.

Como rodar:
    pip install -r requirements.txt
    python app.py
Depois abra http://127.0.0.1:5000 no navegador.
"""
import os
import re
import sqlite3
from datetime import datetime

from flask import Flask, Response, g, jsonify, render_template, request

app = Flask(__name__)

# Banco de dados SQLite (um arquivo simples dentro da pasta "instance")
os.makedirs(app.instance_path, exist_ok=True)
DATABASE = os.path.join(app.instance_path, "pj.db")

# Senha da área administrativa (troque definindo a variável de ambiente)
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")


# ---------------------------------------------------------------------------
# DADOS DO SITE
# Para mudar um texto, serviço ou depoimento, basta editar as listas abaixo.
# ---------------------------------------------------------------------------
EMPRESA = {
    "nome": "PJ Climatizações",
    "telefone": "(81) 99999-9999",
    "whatsapp": "5581999999999",
    "email": "contato@pjclimatizacoes.com.br",
    "endereco": "Rua das Turbinas, 245 — Recife, PE",
    "horario": "Seg. a sáb., 8h às 18h",
}

SERVICOS = [
    {
        "titulo": "Instalação",
        "descricao": "Split, multi-split, cassete e janela — instalação completa com teste de carga e vedação.",
        "icone": '<rect x="3" y="6" width="18" height="8" rx="2"/><path d="M7 18v2M12 18v2M17 18v2"/>',
    },
    {
        "titulo": "Limpeza e higienização",
        "descricao": "Remoção de fungos, bactérias e mofo das serpentinas e filtros — ar mais saudável em casa.",
        "icone": '<path d="M4 4l16 16M9 4h11v11"/>',
    },
    {
        "titulo": "Manutenção preventiva",
        "descricao": "Revisões periódicas que evitam pane em pleno verão e prolongam a vida útil do aparelho.",
        "icone": '<path d="M12 2v4M12 18v4M4.9 4.9l2.8 2.8M16.3 16.3l2.8 2.8M2 12h4M18 12h4M4.9 19.1l2.8-2.8M16.3 7.7l2.8-2.8"/>',
    },
    {
        "titulo": "Recarga de gás",
        "descricao": "Diagnóstico de vazamento e recarga com o gás correto para cada modelo de aparelho.",
        "icone": '<path d="M12 3v10M8 9l4-4 4 4M5 15h14v6H5z"/>',
    },
    {
        "titulo": "Dedetização de equipamentos",
        "descricao": "Tratamento contra ácaros e insetos dentro do aparelho, sem uso de produtos agressivos.",
        "icone": '<path d="M9 3h6l1 4H8l1-4Z"/><path d="M6 7h12l-1 14H7L6 7Z"/>',
    },
    {
        "titulo": "Avaliação técnica",
        "descricao": "Visita para diagnosticar o problema e indicar a melhor solução, sem custo e sem compromisso.",
        "icone": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
    },
]

DIFERENCIAIS = [
    {"titulo": "Técnicos certificados", "texto": "Equipe treinada nas principais marcas do mercado, seguindo as normas técnicas do setor."},
    {"titulo": "Atendimento rápido", "texto": "Agendamos visitas em até 24h e priorizamos urgências em dias de calor extremo."},
    {"titulo": "Garantia de serviço", "texto": "90 dias de garantia em toda mão de obra executada, com suporte pós-serviço."},
    {"titulo": "Orçamento sem compromisso", "texto": "Você recebe o valor fechado antes de qualquer serviço — sem surpresas na conta."},
]

PASSOS = [
    {"titulo": "Contato", "texto": "Você nos chama pelo formulário ou WhatsApp e conta o que precisa."},
    {"titulo": "Visita técnica", "texto": "Um técnico avalia o ambiente ou o equipamento e fecha o orçamento com você."},
    {"titulo": "Execução", "texto": "O serviço é feito com equipamento próprio, no dia e horário combinados."},
    {"titulo": "Garantia", "texto": "Acompanhamos o resultado e cobrimos qualquer ajuste dentro do prazo de garantia."},
]

DEPOIMENTOS = [
    {"texto": "Chegaram no horário marcado, limpeza rápida e o ar ficou muito mais gelado. Recomendo.", "autor": "Marina S. — Boa Viagem"},
    {"texto": "Instalaram dois splits no mesmo dia, sem sujeira e explicando cada etapa. Ótimo atendimento.", "autor": "Carlos E. — Casa Forte"},
    {"texto": "Meu ar tinha um cheiro ruim, fizeram a higienização e resolveu na hora. Voltei a usar todo dia.", "autor": "Renata A. — Piedade"},
    {"texto": "Preço justo e nada de custo escondido. O orçamento que combinaram foi exatamente o que paguei.", "autor": "João P. — Graças"},
]

CIDADES = [
    "Recife", "Boa Viagem", "Casa Forte", "Graças", "Piedade", "Olinda",
    "Jaboatão dos Guararapes", "Paulista", "Camaragibe", "São Lourenço da Mata",
]

FAQ = [
    {"pergunta": "Quanto tempo leva uma instalação de ar-condicionado split?",
     "resposta": "Em média de 3 a 5 horas, dependendo da distância entre a unidade externa e a interna e das condições do local de instalação."},
    {"pergunta": "Com que frequência devo limpar o ar-condicionado?",
     "resposta": "Recomendamos limpeza a cada 3 a 4 meses em uso residencial e mensal em ambientes comerciais com uso intenso."},
    {"pergunta": "Vocês fornecem o material de instalação?",
     "resposta": "Sim. Tubulação, suportes, cabos e gás são inclusos no orçamento fechado, sem cobrança extra depois."},
    {"pergunta": "O orçamento tem algum custo?",
     "resposta": "Não. A visita técnica de avaliação é gratuita e sem compromisso de fechar o serviço."},
    {"pergunta": "Qual a garantia do serviço prestado?",
     "resposta": "90 dias de garantia sobre a mão de obra em qualquer serviço executado pela PJ Climatizações."},
]

# Opções do campo "Tipo de serviço" do formulário (vêm da lista de serviços)
OPCOES_SERVICO = [s["titulo"] for s in SERVICOS] + ["Outro"]


# ---------------------------------------------------------------------------
# BANCO DE DADOS
# ---------------------------------------------------------------------------
def get_db():
    """Abre a conexão com o banco (uma por requisição)."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_erro):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Cria a tabela de orçamentos, se ainda não existir."""
    with sqlite3.connect(DATABASE) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orcamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                telefone TEXT NOT NULL,
                cidade TEXT NOT NULL,
                servico TEXT NOT NULL,
                mensagem TEXT,
                criado_em TEXT NOT NULL
            )
            """
        )


# ---------------------------------------------------------------------------
# ROTAS
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """Página inicial: manda os dados das listas para o template."""
    return render_template(
        "index.html",
        empresa=EMPRESA,
        servicos=SERVICOS,
        diferenciais=DIFERENCIAIS,
        passos=PASSOS,
        depoimentos=DEPOIMENTOS,
        cidades=CIDADES,
        faq=FAQ,
        opcoes_servico=OPCOES_SERVICO,
    )


@app.route("/orcamento", methods=["POST"])
def orcamento():
    """Recebe o formulário, valida no servidor e salva no banco."""
    dados = request.get_json(silent=True) or request.form

    nome = (dados.get("nome") or "").strip()
    telefone = (dados.get("telefone") or "").strip()
    cidade = (dados.get("cidade") or "").strip()
    servico = (dados.get("servico") or "").strip()
    mensagem = (dados.get("mensagem") or "").strip()

    erros = []
    if len(nome) < 3:
        erros.append("Informe seu nome completo.")
    if not 10 <= len(re.sub(r"\D", "", telefone)) <= 11:
        erros.append("Informe um telefone válido com DDD.")
    if not cidade:
        erros.append("Informe sua cidade ou bairro.")
    if servico not in OPCOES_SERVICO:
        erros.append("Escolha um tipo de serviço.")

    if erros:
        return jsonify(ok=False, erros=erros), 400

    db = get_db()
    db.execute(
        "INSERT INTO orcamentos (nome, telefone, cidade, servico, mensagem, criado_em) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (nome, telefone, cidade, servico, mensagem, datetime.now().strftime("%d/%m/%Y %H:%M")),
    )
    db.commit()

    primeiro_nome = nome.split()[0]
    return jsonify(
        ok=True,
        mensagem=f"Obrigado, {primeiro_nome}! Recebemos seu pedido e entraremos em contato em breve.",
    )


@app.route("/admin")
def admin():
    """Lista os pedidos de orçamento recebidos (protegida por senha)."""
    auth = request.authorization
    if not auth or auth.username != ADMIN_USER or auth.password != ADMIN_PASSWORD:
        return Response(
            "Acesso restrito.", 401,
            {"WWW-Authenticate": 'Basic realm="Area administrativa"'},
        )

    pedidos = get_db().execute("SELECT * FROM orcamentos ORDER BY id DESC").fetchall()
    return render_template("admin.html", pedidos=pedidos, empresa=EMPRESA)


# Cria o banco ao iniciar
init_db()

if __name__ == "__main__":
    app.run(debug=True)
