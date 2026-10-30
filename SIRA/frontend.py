"""Interface Streamlit do SIRA."""
from datetime import datetime
import html
import os
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px
import pandas as pd
import database
import backend

API_URL = os.getenv("SIRA_API_URL", "http://127.0.0.1:5000/api")
RISK_TYPES = ["Enchente", "Deslizamento", "Queimada", "Seca", "Qualidade do Ar", "Contaminação de Água"]
SEVERITIES = ["Atenção", "Alerta", "Emergência"]
ROLES = ["Cidadão / Morador", "Agente de Defesa Civil", "Estudante / Pesquisador", "Gestor Público"]

st.set_page_config(page_title="SIRA - Sistema de Alerta Ambiental", page_icon="🌍", layout="wide")

# No Streamlit Cloud, os segredos são lidos apenas no servidor. Localmente, a
# ausência deles mantém o SQLite e a API Flask usados pelo iniciar.sh.
try:
    supabase_url = st.secrets.get("SUPABASE_URL")
    supabase_key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY")
except Exception:
    supabase_url = supabase_key = None
if supabase_url and supabase_key:
    database.configure_remote_storage(supabase_url, supabase_key)


@st.cache_resource
def initialize_storage():
    database.init_db()
    return True


try:
    initialize_storage()
except Exception as exc:
    st.error(f"Não foi possível iniciar o armazenamento do SIRA: {exc}")
    st.stop()
st.markdown("""
<style>
.main-header {font-size:2rem;color:#1E3A8A;font-weight:700}
.sub-header {font-size:1.05rem;color:#4B5563}
</style>
""", unsafe_allow_html=True)
st.markdown('<div class="main-header">SIRA — Sistema de Alerta e Resposta Ambiental</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Plataforma acadêmica de monitoramento de riscos e extensão universitária</div>', unsafe_allow_html=True)
st.warning("Protótipo acadêmico para avaliação extensionista. Os registros são demonstrativos e não representam alertas oficiais. Em emergências, siga os canais das autoridades competentes.")

with st.sidebar:
    st.header("Perfil de teste")
    persona = st.radio("Como deseja explorar o SIRA?", ["Público geral", "Operador"], key="persona_ativa")
    st.caption("Os perfis são simulações para avaliação do protótipo. Não representam vínculo com órgãos públicos.")
    if persona == "Operador":
        st.info("Explore a consulta pública e a emissão de um alerta demonstrativo.")
    else:
        st.info("Explore o mapa, os alertas, os indicadores e as orientações.")

@st.cache_data(ttl=10)
def fetch_alerts(risk_filter="Todos", severity_filter="Todas"):
    """Consulta a API; se estiver indisponível, permite leitura local apenas."""
    if database.remote_storage_enabled():
        try:
            return database.list_alerts(risk_filter, severity_filter), False
        except Exception:
            return [], "cloud_error"
    try:
        response = requests.get(f"{API_URL}/alerts", params={"risk_type": risk_filter, "severity": severity_filter}, timeout=2)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            raise ValueError("Formato de resposta inesperado")
        return data, False
    except (requests.RequestException, ValueError):
        rows = database.list_alerts(risk_filter, severity_filter)
        return rows, True


def post_json(endpoint, payload):
    """Não faz fallback de escrita: evita registros duplicados após timeout."""
    if database.remote_storage_enabled():
        try:
            if endpoint == "/alerts":
                backend.create_alert_record(payload)
                message = "Alerta demonstrativo salvo com sucesso."
            elif endpoint == "/extension/register":
                backend.create_participant_record(payload)
                message = "Inscrição registrada."
            elif endpoint == "/extension/feedback":
                backend.create_feedback_record(payload)
                message = "Feedback registrado."
            else:
                return False, "Operação desconhecida."
            fetch_alerts.clear()
            return True, message
        except (backend.ValidationError, backend.ConflictError) as exc:
            return False, str(exc)
        except Exception:
            return False, "Não foi possível salvar no banco online. Verifique a configuração e tente novamente."
    try:
        response = requests.post(f"{API_URL}{endpoint}", json=payload, timeout=4)
    except requests.RequestException:
        return False, "API indisponível. Nenhum dado foi gravado; inicie o backend e tente novamente."
    try:
        body = response.json()
    except ValueError:
        body = {}
    if response.status_code in (200, 201):
        fetch_alerts.clear()
        return True, body.get("message", "Registro salvo com sucesso.")
    return False, body.get("error", f"Falha ao salvar (HTTP {response.status_code}).")


tab_labels = ["🗺️ Mapa & Alertas"]
if persona == "Operador":
    tab_labels.append("📢 Emissão de Alerta")
tab_labels += ["📊 Painel de Indicadores", "📚 Educação Ambiental", "🤝 Projeto de Extensão"]
tabs = iter(st.tabs(tab_labels))
tab_mapa = next(tabs)
tab_emissao = next(tabs) if persona == "Operador" else None
tab_indicadores, tab_educacao, tab_extensao = next(tabs), next(tabs), next(tabs)

with tab_mapa:
    f1, f2 = st.columns(2)
    with f1:
        tipo_filtro = st.selectbox("Filtrar por tipo de risco", ["Todos"] + RISK_TYPES)
    with f2:
        severidade_filtro = st.selectbox("Filtrar por severidade", ["Todas"] + SEVERITIES)
    alertas, local_mode = fetch_alerts(tipo_filtro, severidade_filtro)
    if local_mode == "cloud_error":
        st.error("Não foi possível consultar o banco online. Verifique a conexão do app.")
    elif local_mode:
        st.info("API indisponível: exibindo dados locais em modo somente leitura.")
    col_map, col_feed = st.columns([1.8, 1.2])
    with col_map:
        st.subheader("Visualização geográfica dos riscos ambientais")
        mapa = folium.Map(location=[-15.7797, -47.9297], zoom_start=4, tiles="OpenStreetMap")
        cores = {"Emergência": "red", "Alerta": "orange", "Atenção": "beige"}
        valid_points = 0
        for alert in alertas:
            try:
                lat, lng = float(alert["lat"]), float(alert["lng"])
                if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                    continue
                popup_text = "<br>".join([
                    f"<b>{html.escape(str(alert['title']))}</b>",
                    f"<b>Severidade:</b> {html.escape(str(alert['severity']))}",
                    f"<b>Local:</b> {html.escape(str(alert['location']))}",
                    f"<b>Emissor:</b> {html.escape(str(alert['issuer']))}",
                    html.escape(str(alert["description"]))
                ])
                folium.Marker([lat, lng], popup=folium.Popup(popup_text, max_width=300),
                              tooltip=f"{alert['risk_type']} - {alert['location']}",
                              icon=folium.Icon(color=cores.get(alert["severity"], "blue"), icon="info-sign")).add_to(mapa)
                valid_points += 1
            except (KeyError, TypeError, ValueError):
                continue
        if valid_points:
            mapa.fit_bounds(mapa.get_bounds(), padding=(20, 20))
        st_folium(mapa, width=None, height=480, key="mapa_alertas")
    with col_feed:
        st.subheader(f"Feed de alertas ({len(alertas)})")
        if not alertas:
            st.info("Nenhum alerta corresponde aos filtros selecionados.")
        for a in alertas:
            with st.expander(f"📍 {a['title']} — {a['location']}"):
                st.write(f"**Severidade:** {a['severity']}")
                st.write(f"**Órgão emissor:** {a['issuer']}")
                st.write(f"**Data/hora:** {a['date_time']}")
                st.write(f"**Descrição:** {a['description']}")
                st.info(f"**Orientação informativa:** {a['instructions']}")

if tab_emissao is not None:
  with tab_emissao:
    st.subheader("Experiência do operador: emitir alerta demonstrativo")
    st.caption("Nesta versão acadêmica, a emissão não possui autenticação. Use apenas em ambiente local de demonstração.")
    with st.form("form_novo_alerta"):
        c1, c2 = st.columns(2)
        with c1:
            titulo = st.text_input("Título do alerta", max_chars=200)
            tipo_risco = st.selectbox("Tipo de risco ambiental", RISK_TYPES)
            severidade = st.selectbox("Grau de severidade", SEVERITIES, index=1)
            emissor = st.text_input("Órgão ou equipe emissora (simulação)", max_chars=200, placeholder="Ex.: Equipe de teste SIRA")
        with c2:
            local = st.text_input("Local / região", max_chars=200)
            latitude = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=-22.9056, format="%.4f")
            longitude = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=-47.0608, format="%.4f")
            data_hora = st.text_input("Data e hora (AAAA-MM-DD HH:MM)", value=datetime.now().strftime("%Y-%m-%d %H:%M"), max_chars=16)
        descricao = st.text_area("Descrição detalhada do evento", max_chars=2000)
        instrucoes = st.text_area("Orientações informativas à população", max_chars=2000)
        submitted = st.form_submit_button("📢 Emitir alerta ambiental")
    if submitted:
        try:
            datetime.strptime(data_hora.strip(), "%Y-%m-%d %H:%M")
        except ValueError:
            st.error("Data/hora inválida. Use o formato AAAA-MM-DD HH:MM.")
        else:
            payload = {"title": f"[SIMULAÇÃO] {titulo.strip()}", "risk_type": tipo_risco, "severity": severidade,
                       "location": local.strip(), "lat": latitude, "lng": longitude,
                       "issuer": emissor.strip(), "description": descricao.strip(),
                       "instructions": instrucoes.strip(), "date_time": data_hora.strip()}
            ok, message = post_json("/alerts", payload)
            (st.success if ok else st.error)(message)

with tab_indicadores:
    st.subheader("Painel de indicadores e gestão de riscos")
    alertas_all, local_mode = fetch_alerts()
    if local_mode == "cloud_error":
        st.error("Não foi possível consultar os indicadores no banco online.")
    elif local_mode:
        st.info("Indicadores calculados sobre os dados locais disponíveis; a API está indisponível.")
    if alertas_all:
        df = pd.DataFrame(alertas_all)
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de registros", len(df))
        c2.metric("Registros classificados como emergência", int((df["severity"] == "Emergência").sum()))
        c3.metric("Tipos de risco registrados", int(df["risk_type"].nunique()))
        g1, g2 = st.columns(2)
        with g1:
            fig_sev = px.pie(df, names="severity", title="Distribuição por severidade",
                             color="severity", color_discrete_map={"Emergência": "#EF4444", "Alerta": "#F97316", "Atenção": "#EAB308"})
            st.plotly_chart(fig_sev, use_container_width=True)
        with g2:
            by_type = df.groupby("risk_type", as_index=False).size().rename(columns={"size": "total"})
            fig_type = px.bar(by_type, x="risk_type", y="total", title="Registros por tipo de risco", labels={"risk_type": "Tipo de risco", "total": "Total"})
            st.plotly_chart(fig_type, use_container_width=True)
    else:
        st.info("Nenhum registro encontrado para gerar estatísticas.")

with tab_educacao:
    st.subheader("Educação ambiental e legislação")
    st.markdown("Conteúdo introdutório para fins didáticos. A síntese não substitui a leitura da legislação nem orientações de autoridades.")
    left, right = st.columns(2)
    with left:
        st.markdown("### 🌊 Enchentes e inundações\n- **Causas/impactos:** impermeabilização do solo, ocupação de várzeas e chuvas intensas.\n- **Base legal:** Lei nº 12.608/2012 (Política Nacional de Proteção e Defesa Civil).\n- **ODS relacionado:** ODS 11 — Cidades e Comunidades Sustentáveis.")
        st.markdown("### ⛰️ Deslizamentos de encostas\n- **Causas/impactos:** remoção de vegetação, saturação do solo e ocupação de áreas suscetíveis.\n- **Base legal:** Lei nº 6.938/1981 (Política Nacional do Meio Ambiente) e Lei nº 12.651/2012 (Código Florestal), conforme o caso.\n- **ODS relacionado:** ODS 11 e 15.")
        st.markdown("### 💨 Qualidade do ar\n- **Causas/impactos:** emissões veiculares e industriais, queimadas e material particulado.\n- **Base legal:** Resolução CONAMA nº 506/2024, que atualiza os padrões nacionais de qualidade do ar.\n- **ODS relacionado:** ODS 3 — Saúde e Bem-Estar.")
    with right:
        st.markdown("### 🔥 Queimadas e incêndios florestais\n- **Causas/impactos:** uso inadequado do fogo, estiagem e incêndios em vegetação.\n- **Base legal:** Lei nº 9.605/1998 (Lei de Crimes Ambientais); a aplicação de dispositivos depende das circunstâncias do fato.\n- **ODS relacionado:** ODS 13 e 15.")
        st.markdown("### ☀️ Secas e estiagens\n- **Causas/impactos:** baixa precipitação, variabilidade climática e pressão sobre recursos hídricos.\n- **Base legal:** Lei nº 9.433/1997 (Política Nacional de Recursos Hídricos).\n- **ODS relacionado:** ODS 6 — Água Potável e Saneamento.")
        st.markdown("### 🚯 Contaminação da água\n- **Causas/impactos:** lançamento de efluentes e descarte inadequado de resíduos.\n- **Base legal:** Resolução CONAMA nº 357/2005 trata da classificação dos corpos de água e diretrizes ambientais; não é, por si só, a norma de potabilidade da água.\n- **ODS relacionado:** ODS 6.")
    st.caption("Referência constitucional geral: Constituição Federal de 1988, art. 225. Confira a redação consolidada das normas em fontes oficiais antes da entrega acadêmica.")

with tab_extensao:
    st.subheader("Projeto de extensão universitária")
    st.markdown("Área para cadastro voluntário de participantes e coleta de percepções de usabilidade. Colete somente dados necessários e explique sua finalidade aos participantes.")
    sub1, sub2 = st.tabs(["📝 Inscrição de agente externo", "💬 Feedback e usabilidade"])
    with sub1:
        with st.form("form_ext_inscricao"):
            nome_ext = st.text_input("Nome completo", max_chars=120)
            email_ext = st.text_input("E-mail de contato", max_chars=254)
            org_ext = st.text_input("Instituição / comunidade", max_chars=200)
            perfil_ext = st.selectbox("Perfil do agente", ROLES)
            register = st.form_submit_button("Realizar inscrição")
        if register:
            payload = {"name": nome_ext.strip(), "email": email_ext.strip(), "organization": org_ext.strip(), "role": perfil_ext}
            ok, message = post_json("/extension/register", payload)
            (st.success if ok else st.error)(message)
    with sub2:
        with st.form("form_ext_feedback"):
            nome_fb = st.text_input("Seu nome ou código de participante", max_chars=120)
            persona_fb = st.selectbox("Perfil avaliado neste feedback", ["Público geral", "Operador"], index=0 if persona == "Público geral" else 1)
            usab_rating = st.slider("Facilidade de navegação (1 a 5)", 1, 5, 4)
            clarity_rating = st.slider("Clareza das informações (1 a 5)", 1, 5, 5)
            coment_fb = st.text_area("Sugestões e críticas construtivas", max_chars=2000)
            send_feedback = st.form_submit_button("Enviar avaliação")
        if send_feedback:
            payload = {"participant_name": nome_fb.strip(), "persona": persona_fb, "usability_rating": int(usab_rating),
                       "clarity_rating": int(clarity_rating), "comments": coment_fb.strip()}
            ok, message = post_json("/extension/feedback", payload)
            (st.success if ok else st.error)(message)
