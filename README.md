# 📌 Vitally

Vitally é a plataforma digital que está transformando a forma como clínicas e fisioterapeutas cuidam de seus pacientes.
Com uma agenda inteligente, notificações automáticas, teleconsultas integradas e prescrição digital personalizada, o Vitally elimina a burocracia e coloca o foco onde realmente importa: a saúde e a evolução do paciente.

Mais do que um software de gestão, o Vitally é um parceiro para profissionais da saúde que buscam eficiência, organização e uma experiência moderna para seus pacientes.

## 🚀 O que o Vitally oferece

- 📅 Agendamento online inteligente – sem sobreposições, com lista de espera.

- 🔔 Lembretes automáticos – WhatsApp e e-mail para reduzir faltas.

- 🏋️ Prescrição digital de exercícios – vídeos, PDFs e histórico por paciente.

- 💳 Pagamentos online – consultas avulsas e planos recorrentes.

- 💬 Chat integrado – comunicação entre paciente e fisioterapeuta.

- 📊 Dashboards e relatórios – desempenho clínico e financeiro em tempo real.

- 🎥 Teleconsulta em vídeo – amplie o alcance dos atendimentos.

## 🧩 Público-Alvo

- Fisioterapeutas autônomos que querem profissionalizar seu atendimento.

- Clínicas de pequeno e médio porte que precisam de organização e escalabilidade.

- Pacientes que buscam autonomia e praticidade na relação com o profissional.

- Instituições de ensino que acompanham estudantes em clínicas-escola.

## 🛠️ Stack

- Backend: Django + Django REST Framework (DRF)

- Frontend Web: React (Next.js) + TailwindCSS

- Mobile: React Native (Expo)

- Banco de Dados: PostgreSQL

- Notificações: WhatsApp Cloud API + SendGrid

- Pagamentos: Mercado Pago

- Teleconsulta: LiveKit Cloud

- Infraestrutura: Docker + Redis + Celery + AWS S3

- Observabilidade: Sentry

## 📂 Estrutura do Projeto

```bash
vitally/
│── backend/
│   ├── vitally/
│   ├── apps/
│   ├── requirements.txt
│   └── manage.py
│
│── web/
│   ├── src/
│   │   ├── app/(marketing)
│   │   ├── app/(dashboard) 
│   │   └── components/
│   ├── middleware.ts
│   └── package.json
│
│── mobile/ 
│   ├── app/ 
│   ├── src/lib/ 
│   └── package.json
│
│── docker-compose.yml
│── .env.example
│── README.md
│── docs/
│   └── vitally-contexto.md 
```

## 📖 Documentação

- 📄 [Contexto do Projeto](docs/vitally-contexto.md)
- Swagger/OpenAPI gerado pelo DRF disponível em /api/docs.
  
## ⚙️ Variáveis de Ambiente

> Veja o arquivo .env.example

## 📦 Setup

1. Subir banco e Redis
```bash
docker-compose up -d db redis
```

2. Backend (Django + DRF)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

3. Celery (em outro terminal)
```bash
celery -A vitally.celery_app worker -l info
celery -A vitally.celery_app beat -l info

```

4. Web (Next.js)
```bash
cd ../web
npm install
npm run dev
```

5. Mobile (React Native + Expo)
```bash
cd ../mobile
npm install
npx expo start
```

## 🔐 Autenticação

- JWT Access/Refresh (SimpleJWT).

- Perfis de usuário: admin, physio, patient.

- Middleware no Next.js protege rotas do dashboard (/app), mantendo / público para marketing/landing.

## 📡 Fluxos Principais

- Agenda Inteligente → evita sobreposição, gera lista de espera.

- Notificações → WhatsApp Cloud API e e-mail (SendGrid) para lembretes automáticos.

- Pagamentos → Mercado Pago para consultas avulsas e planos recorrentes.

- Prescrições → exercícios personalizados, anexos em S3.

- Teleconsultas → LiveKit Cloud (web + mobile).

- Relatórios/Dashboards → consultas, finanças, adesão de pacientes.

## 🛤️ Roadmap

- MVP (v1.0)

- - Cadastro de pacientes/fisioterapeutas

- - Agenda inteligente

- - Notificações por e-mail

- - Pagamentos online

- - Prescrição de exercícios

- v2.0

- - Área do paciente e fisioterapeuta

- - Relatórios e dashboards

- - Chat integrado

- - Integração WhatsApp Cloud API

- v3.0 (Premium)

- - Teleconsultas (LiveKit)

- - Planos para clínicas (multi-fisio)

- - Automação de lembretes e reativação de pacientes