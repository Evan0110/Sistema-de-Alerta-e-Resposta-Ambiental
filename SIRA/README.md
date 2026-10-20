# SIRA — Sistema de Alerta e Resposta Ambiental

Protótipo acadêmico com interface Streamlit, API Flask e persistência SQLite. Os registros iniciais são **simulados** e não são alertas oficiais.

## Requisitos

- Python 3.10 ou superior
- Conexão à internet na primeira instalação das dependências

## Execução rápida

### Linux (incluindo Linux Mint)

1. Extraia a pasta do projeto.
2. Abra um terminal dentro dela.
3. Execute `chmod +x iniciar.sh` (uma vez, se necessário).
4. Execute `./iniciar.sh`.
5. O Streamlit abrirá a interface no navegador. Para encerrar, pressione `Ctrl+C`.

O script cria um ambiente virtual `.venv`, instala as dependências, inicializa o banco e inicia a API local. O log da API fica em `backend.log`.

### Windows

1. Instale Python 3.10+ e marque a opção de adicionar Python ao PATH.
2. Extraia a pasta do projeto.
3. Execute `iniciar.bat`.

O script abre a API em uma janela separada e inicia a interface na janela atual.

## Execução manual

Em dois terminais, dentro da pasta do projeto:

```bash
python database.py
python backend.py
```

No segundo terminal, ou em um terceiro:

```bash
python -m streamlit run frontend.py
```

- Interface: `http://localhost:8501`
- API: `http://127.0.0.1:5000/api/health`
- Banco: `sira_dados.db`, criado na pasta do projeto.

## Endpoints

- `GET /api/health`: estado da API
- `GET /api/alerts?risk_type=Todos&severity=Todas`: consulta alertas e filtros
- `POST /api/alerts`: cadastra alerta
- `GET /api/indicators`: indicadores agregados
- `POST /api/extension/register`: registra participante
- `POST /api/extension/feedback`: registra feedback

Os endpoints de escrita esperam JSON. Erros de validação retornam HTTP 400; e-mail já cadastrado retorna HTTP 409.

## Correções e decisões desta versão

- Caminho absoluto e estável para o SQLite, com timeout, transações e fechamento garantido da conexão.
- Validação de campos, categorias, coordenadas, data/hora, e-mail e notas de feedback.
- Consultas SQL parametrizadas e índices/chaves definidos por esquema.
- Fallback da interface somente para **leitura**. Escritas não são repetidas diretamente no banco quando a API falha, reduzindo o risco de duplicidade após timeout.
- Dependências completas, incluindo pandas.
- API vinculada a `127.0.0.1`, sem modo debug.
- Dados de demonstração explicitamente identificados como simulados.

## Limitações importantes

Esta é uma aplicação de demonstração acadêmica, não um sistema oficial de alerta nem uma plataforma pronta para uso público. A emissão de alertas ainda não tem autenticação/autorização; por isso, mantenha a API local. Para publicar ou usar com pessoas externas, implementar autenticação, controle de permissões, HTTPS, proteção contra abuso, política de privacidade e revisão LGPD. O cadastro armazena nome e e-mail; informe a finalidade e retenção dos dados aos participantes.

As orientações exibidas são informativas e não substituem instruções da Defesa Civil, serviços de emergência, órgãos ambientais ou autoridades sanitárias. Antes de entregar o relatório, confira a legislação em fontes oficiais e documente apenas testes realmente realizados.
