# 🩺 Vitally

Vitally é uma aplicação web para **gestão de pacientes em clínicas e consultórios**, com foco em fisioterapia.  
O sistema permite cadastro, edição e acompanhamento de pacientes, controle de pagamentos e vencimentos, além de envio automático de lembretes.

O deploy da aplicação está disponível em: [vitally.streamlit.app](https://vitally.streamlit.app)

---

## 🚀 Funcionalidades

- 👥 **Gerenciamento de pacientes** (cadastro, edição, listagem e status de ativo/inativo).  
- 📚 **Controle de aulas** (definição de dias da semana que o paciente participa).  
- 💳 **Pagamentos** (registro de pagamentos e cálculo automático da próxima cobrança).  
- 📬 **Lembretes automáticos** de pagamento via e-mail (próximos vencimentos em até 7 dias).  
- 🔐 **Autenticação de usuários** com hash seguro de senhas (bcrypt).  
- 📊 **Visualização em tabelas** e exportação de dados.  
- 🛡️ **Validações automáticas** (e-mail, telefone e dados obrigatórios).  

---

## 🛠️ Tecnologias Utilizadas

- [Python 3.11+](https://www.python.org/)  
- [Streamlit](https://streamlit.io/) – interface web interativa  
- [SQLAlchemy](https://www.sqlalchemy.org/) – ORM para banco de dados  
- [SQLite/PostgreSQL] – banco de dados (dependendo da configuração `DATABASE_URL`)  
- [bcrypt](https://pypi.org/project/bcrypt/) – autenticação e hashing de senhas  
- [dotenv](https://pypi.org/project/python-dotenv/) – gerenciamento de variáveis de ambiente  
- [pandas](https://pandas.pydata.org/) – exibição e manipulação de tabelas  

---

## 📂 Estrutura do Projeto

```bash
vitally/
│── src/
│   ├── db/
│   │   ├── db.py
│   │   └── tables.py
│   ├── models/
│   │   └── paciente_model.py
│   ├── repositories/
│   │   └── paciente_repository_sql.py
│   ├── services/
│   │   └── clinica_service.py
│   ├── security/
│   │   └── auth.py
│   ├── utils/
│   │   ├── create_user.py
│   │   └── send_reminders.py
├── streamlit_app.py
├── .env.example
├── requirements.txt
└── README.md
```

---

## ⚙️ Variáveis de Ambiente

O projeto utiliza um arquivo `.env`. Exemplo:

```bash
DATABASE_URL=sqlite:///./db.sqlite3
SMTP_HOST=smtp.seuprovedor.com
SMTP_PORT=587
SMTP_USER=usuario
SMTP_PASS=senha
SMTP_FROM=nao-responder@vitally.com
SMTP_USE_TLS=true
```

---

## ▶️ Como Rodar Localmente

1. Clone o repositório:

```bash
git clone https://github.com/seuusuario/vitally.git
cd vitally
```

2. Crie e ative o ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate
.venv\Scripts\activate
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Configure o arquivo `.env` com suas credenciais.

5. Execute o app:

```bash
streamlit run src/streamlit_app.py
```

---

## 🔐 Autenticação

- Usuários são armazenados na tabela `users`.  
- Senhas são salvas com hash seguro (`bcrypt`).  
- Login realizado diretamente no app com formulário de autenticação.  
- Para criar um novo usuário administrador:

```bash
python src/utils/create_user.py
```

---

## 📬 Lembretes Automáticos

Um script envia lembretes de cobrança via e-mail para pacientes com vencimento em até 7 dias:

```bash
python src/utils/send_reminders.py
```

Certifique-se de que o `.env` contenha as variáveis SMTP configuradas.

---

## 🌐 Deploy

O projeto já está disponível em produção no Streamlit Cloud:  
🔗 [vitally.streamlit.app](https://vitally.streamlit.app)

---

## 📌 Roadmap Futuro

- 📱 Integração com WhatsApp para lembretes automáticos.  
- 📊 Relatórios financeiros e de presença em aulas.  
- 🔔 Notificações push.  
- 🧩 Multiusuário com diferentes permissões (admin, gestor, professor).  

---

## 👨‍💻 Autor

Desenvolvido por **Guilherme Henrique Braga e Silva**  
📧 [Contato](mailto:gui100920@gmail.com)  
🌐 [GitHub](https://github.com/guilhermehbs) | [LinkedIn](https://www.linkedin.com/in/guilhermehbs)
