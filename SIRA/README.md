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

## Histórico do Desenvolvimento e Estado Atual do Projeto

### 1. Visão geral

O SIRA (Sistema de Alerta e Resposta Ambiental) é um protótipo acadêmico desenvolvido em Python para a disciplina de Ciências do Ambiente. A proposta é reunir funcionalidades relacionadas ao registro e à visualização de alertas ambientais, ao acompanhamento de indicadores e à educação ambiental, além de apoiar atividades de extensão universitária.

A versão atual foi organizada para separar a interface, a lógica de processamento das requisições e o armazenamento dos dados, facilitando a manutenção do código e a revisão colaborativa.

### 2. Arquitetura e tecnologias utilizadas

O projeto está dividido em três componentes principais:

- **Frontend (`frontend.py`):** desenvolvido com Streamlit, responsável pela interface gráfica e pela interação com os usuários.
- **Backend (`backend.py`):** desenvolvido com Flask, responsável por disponibilizar uma API REST para comunicação entre a interface e os serviços de processamento.
- **Banco de dados (`database.py`):** utiliza SQLite para armazenar e consultar informações relacionadas aos alertas ambientais, aos participantes e aos registros de feedback.

O projeto também utiliza dependências Python descritas em `requirements.txt`. A separação dos componentes busca facilitar futuras alterações, testes e possíveis ampliações do sistema.

### 3. Funcionalidades desenvolvidas

A interface está organizada em cinco seções principais:

**3.1. Mapa e visualização de alertas**

Área destinada à visualização dos alertas ambientais registrados e à consulta das informações disponíveis. A proposta é facilitar a identificação e o acompanhamento dos registros de ocorrências ambientais.

**3.2. Emissão de alertas**

Interface para registrar novas ocorrências ambientais, reunindo informações pertinentes ao alerta. Foram incorporadas validações para campos obrigatórios, coordenadas, categorias, datas e demais informações relevantes, com o objetivo de reduzir registros inconsistentes.

**3.3. Indicadores ambientais**

Seção destinada à apresentação de indicadores e informações que auxiliem na compreensão dos registros e do cenário ambiental representado pelo protótipo.

**3.4. Educação ambiental e fundamentação legal**

Área voltada à disponibilização de conteúdos educativos e referências normativas relacionadas à temática ambiental. A fundamentação legal foi atualizada para considerar a Resolução CONAMA nº 506/2024, referente aos padrões nacionais de qualidade do ar.

**3.5. Módulo de extensão**

Seção destinada ao registro de participantes e à coleta de feedbacks sobre a utilização do sistema. Essa funcionalidade busca apoiar atividades acadêmicas e de extensão, permitindo reunir informações sobre a experiência dos usuários.

### 4. Melhorias realizadas na versão atual

Durante a revisão do código, foram identificados pontos que poderiam comprometer a consistência dos registros, a organização do projeto e o tratamento de falhas. A versão corrigida contempla as seguintes melhorias:

- **Validação de entradas:** foram reforçadas as verificações de campos, coordenadas geográficas, categorias, datas, endereços de e-mail e notas de avaliação.
- **Organização do banco de dados:** foram aprimorados o gerenciamento do caminho do arquivo SQLite, o tratamento das conexões e o controle das transações, buscando reduzir inconsistências durante as operações.
- **Tratamento de falhas da API:** o comportamento alternativo da interface foi ajustado para permitir a consulta de informações disponíveis sem recorrer à gravação direta no banco de dados quando a API estiver indisponível.
- **Dependências:** o arquivo `requirements.txt` foi ajustado para contemplar as bibliotecas necessárias, incluindo o Pandas.
- **Configuração do servidor:** o modo de depuração do Flask foi desativado na configuração entregue, evitando deixar essa opção habilitada por padrão.
- **Referências ambientais:** foi atualizada a referência normativa relativa à qualidade do ar.
- **Identificação dos dados:** os registros utilizados para demonstração foram identificados como dados simulados, evitando confundi-los com ocorrências ambientais reais.

Essas alterações buscam tornar o protótipo mais organizado e previsível, mas não representam uma certificação de segurança ou de funcionamento em ambiente de produção.

### 5. Dados e limitações conhecidas

O banco de dados contempla estruturas para alertas ambientais, participantes e feedbacks. A versão de demonstração utiliza seis registros simulados, que devem ser diferenciados de dados obtidos em campo ou de informações fornecidas por órgãos oficiais.

O sistema ainda possui limitações importantes:

- A execução integrada da API e da interface precisa ser verificada em ambiente de uso, incluindo os fluxos de consulta, cadastro e tratamento de erros.
- A emissão de alertas ainda não conta com autenticação de usuários.
- O SQLite é adequado ao escopo inicial do protótipo, mas pode apresentar limitações em cenários com muitos acessos e gravações simultâneas.
- O tratamento de dados pessoais deve ser revisado, considerando privacidade, controle de acesso, armazenamento e os princípios da Lei Geral de Proteção de Dados (LGPD).
- Os alertas apresentados pelo sistema não substituem comunicações, monitoramentos ou alertas oficiais emitidos pelas autoridades competentes.
- As informações ambientais e as referências normativas devem ser revisadas para assegurar sua atualidade, precisão e adequação ao objetivo acadêmico.

### 6. Estado atual e próximos passos

A versão corrigida reúne a interface em Streamlit, o backend em Flask, a camada de persistência em SQLite e os arquivos de dependências e documentação. Entretanto, a integração completa dos componentes ainda precisa ser validada por meio de testes de execução, e não se deve considerar que todos os fluxos estejam comprovadamente funcionais antes dessa verificação.

A próxima etapa consiste na revisão colaborativa do projeto. Recomenda-se que os integrantes:

1. Leiam os arquivos e compreendam a responsabilidade de cada componente.
2. Verifiquem se as funcionalidades implementadas correspondem aos objetivos definidos para o trabalho.
3. Executem o sistema e testem os principais fluxos, incluindo emissão, consulta e tratamento de falhas.
4. Confiram as validações, a consistência dos dados e a comunicação entre frontend e backend.
5. Revisem as referências ambientais, os textos educativos e a fundamentação legal.
6. Identifiquem problemas, limitações e melhorias possíveis, registrando as alterações propostas.
7. Avaliem a necessidade de testes automatizados, melhorias de segurança e ajustes de interface.

Este documento registra o estado de desenvolvimento da versão atual e serve como ponto de partida para a revisão do grupo. As funcionalidades, as correções e as limitações descritas devem ser confrontadas com o código e com os resultados dos testes realizados pelos integrantes antes da apresentação da versão final do trabalho.
