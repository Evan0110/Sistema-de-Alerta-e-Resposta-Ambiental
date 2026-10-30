# SIRA — Sistema de Alerta e Resposta Ambiental

Protótipo acadêmico da disciplina Ciências do Ambiente, no ciclo básico das Engenharias, com atividade de extensão universitária. O projeto explora como uma interface de informação e comunicação pode apoiar a consulta e a comunicação de riscos ambientais.

## Avaliação extensionista por dois perfis

Os participantes da extensão podem alternar entre duas **personas simuladas**:

- **Público geral:** consulta mapa, alertas, indicadores e orientações informativas.
- **Operador:** consulta as mesmas informações e testa o formulário de emissão de alertas demonstrativos.

Após explorar cada perfil, envie um feedback separado na área **Projeto de Extensão**, selecionando o perfil avaliado. Assim, a equipe consegue comparar a experiência de consulta com a experiência de emissão. Os perfis não comprovam vínculo com INMET, Defesa Civil ou qualquer órgão.

Sugestão de roteiro: (1) explore o mapa como público geral e encontre um alerta; (2) troque para Operador e cadastre um alerta claramente simulado; (3) volte ao público geral e localize o registro; (4) envie um feedback para cada perfil sobre facilidade, clareza, pontos positivos e melhorias.

## Execução local

### Com Docker (uma opção sem instalar Python manualmente)

Instale Docker Desktop ou Docker Engine com o plugin Compose, abra um terminal nesta pasta e execute:

```bash
docker compose up --build
```

Abra `http://localhost:8501`. Para encerrar, pressione `Ctrl+C`. Os dados ficam em um volume Docker chamado `sira-data`.

### Linux

Execute `./iniciar.sh`. O script cria um ambiente virtual, instala dependências e inicia a API e a interface. Abra o endereço mostrado pelo Streamlit.

### Windows

Execute `iniciar.bat`. O script prepara o ambiente e abre a API e a interface.

### Execução manual

Em terminais separados:

```bash
python database.py
python backend.py
python -m streamlit run frontend.py
```

## Publicação por link

O SIRA pode ser publicado como site usando Streamlit Community Cloud para a interface e Supabase para o banco de dados. Quando os segredos do Supabase estão configurados, a interface usa o banco remoto; sem eles, continua usando a API Flask e o SQLite locais. Isso preserva o modo local de demonstração.

### Preparação dos serviços

1. Crie um projeto no Supabase e execute `supabase_schema.sql` no SQL Editor para criar as tabelas.
2. Copie a URL do projeto e a chave `service_role` do Supabase. Essa chave é secreta: use-a somente nas configurações de Secrets do app no Streamlit Cloud.
3. Envie o projeto para um repositório GitHub. Não envie `.streamlit/secrets.toml`, banco SQLite, `.venv` ou credenciais.
4. No Streamlit Community Cloud, crie o app a partir do repositório e indique `frontend.py` como arquivo principal.
5. Em App settings > Secrets, cadastre os campos do arquivo `.streamlit/secrets.toml.example`, preenchidos com os valores reais do Supabase.
6. Para um piloto restrito, convide os avaliadores por e-mail nas configurações de compartilhamento. Para permitir entrada livre, torne o app público. Qualquer visitante autorizado poderá testar a persona Operador, que emite alertas demonstrativos.

O plano gratuito do Streamlit pode colocar apps sem visitas em repouso. O Supabase Free pode pausar projetos com pouca atividade. Consulte as condições atuais dos serviços antes de iniciar uma rodada de avaliação.

Antes de convidar pessoas externas, definam quem pode acessar o link, como os dados serão removidos ao fim da avaliação e qual aviso de privacidade será apresentado. Esta versão é para teste acadêmico controlado: não possui autenticação de operador, e qualquer visitante pode alternar para a persona de teste Operador. Alertas são simulações e não devem ser usados para orientar decisões reais.

## Componentes

- `frontend.py`: interface Streamlit com mapa, feed, painel, conteúdo educativo, perfis e feedback.
- `backend.py`: API Flask com validação de alertas, inscrições e feedbacks.
- `database.py`: persistência SQLite, índices/esquema e dados iniciais fictícios.
- `tests/test_backend.py`: testes existentes para endpoints básicos.

Endpoints: `GET /api/health`, `GET/POST /api/alerts`, `GET /api/indicators`, `POST /api/extension/register` e `POST /api/extension/feedback`.

## Dados e cuidados

Os registros iniciais são **simulados**, assim como os emitidos no roteiro de avaliação. A interface apresenta orientações gerais e não substitui instruções de Defesa Civil, serviços de emergência, órgãos ambientais ou autoridades sanitárias.

O formulário de extensão solicita nome, e-mail e instituição/comunidade para inscrição, e nome ou código do participante no feedback. Para uso com pessoas externas, expliquem a finalidade da coleta, limitem o acesso aos registros, estabeleçam prazo de retenção e obtenham consentimento apropriado para a atividade. A aplicação não está pronta para operação pública ou emissão real de alertas.
