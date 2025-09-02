# Configuração do Vitally

## Variáveis de Ambiente Necessárias

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```bash
# Google Sheets Configuration
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id_here
GOOGLE_SHEETS_WORKSHEET=Pacientes
GOOGLE_CREDENTIALS_FILE=credentials.json
```

## Passos para Configurar

1. **Crie uma planilha no Google Sheets**

   - Crie uma nova planilha no Google Sheets
   - Adicione uma aba chamada "Pacientes" (ou o nome que preferir)

2. **Configure o Google Service Account**

   - Vá para [Google Cloud Console](https://console.cloud.google.com/)
   - Crie um projeto ou selecione um existente
   - Ative a Google Sheets API
   - Crie uma conta de serviço
   - Baixe o arquivo JSON de credenciais
   - Renomeie para `credentials.json` e coloque na raiz do projeto

3. **Compartilhe a planilha**

   - Compartilhe a planilha com o email da conta de serviço (encontrado no arquivo credentials.json)
   - Dê permissão de "Editor"

4. **Configure as variáveis**
   - Copie o ID da planilha da URL ou use a URL completa
   - Atualize o arquivo `.env` ou `config.py` com os valores reais

## Estrutura da Planilha

A planilha deve ter as seguintes colunas:

- id
- nome
- telefone
- email
- data_entrada
- data_ultimo_pagamento
- data_proxima_cobranca
- ativo

## Testando

Após a configuração, execute:

```bash
cd frontend
streamlit run ui_streamlit.py
```

O sistema deve conectar com o Google Sheets e funcionar corretamente.
