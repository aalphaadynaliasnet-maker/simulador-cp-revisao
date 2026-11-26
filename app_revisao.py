import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta
import os
import re
import pdfplumber

TABELA_INDICES = {
    128: 1116.50, 131: 1133.26, 134: 1150.03, 137: 1166.78, 140: 1183.54,
    144: 1205.88, 148: 1228.24, 152: 1250.59, 156: 1272.93, 161: 1300.88,
    166: 1328.83, 171: 1356.76, 176: 1384.70, 182: 1418.22, 189: 1457.34,
    196: 1495.37, 203: 1534.56, 210: 1574.22, 217: 1613.87, 224: 1653.00,
    231: 1693.46, 238: 1733.92, 245: 1774.39, 252: 1814.86, 259: 1855.31,
    266: 1895.78, 273: 1936.24, 280: 1976.70, 288: 2025.30, 296: 2073.88
}

INDICES_LISTA = (
    128, 131, 134, 137, 140, 144, 148, 152, 156, 161,
    166, 171, 176, 182, 189, 196, 203, 210, 217, 224,
    231, 238, 245, 252, 259, 266, 273, 280, 288, 296
)

def gerar_escala_base():
    descansos = {1, 7, 8, 15, 16, 23, 24, 31, 32, 39, 40, 47, 48, 55, 56, 63, 64, 71, 72, 79, 80, 87, 88, 95, 96, 103, 104, 111, 112, 119, 120}
    registos = list()
    for num_os in range(1, 121):
        if num_os in descansos:
            registos.append({"OS": num_os, "Tipo": "Descanso", "Inicio": "", "Fim": "", "Min_Rev": 0, "Rep_Fora": "Não", "Obs": "Descanso Semanal"})
        else:
            registos.append({"OS": num_os, "Tipo": "Bordo", "Inicio": "08:00", "Fim": "16:00", "Min_Rev": 300, "Rep_Fora": "Não", "Obs": f"Serviço OS {num_os}"})
    return pd.DataFrame(registos)

def ler_pdf_escala_cp(ficheiro_pdf):
    registos_por_os = dict()
    with pdfplumber.open(ficheiro_pdf) as pdf:
        os_atual = None
        for page in pdf.pages:
            tabelas = page.extract_tables()
            for tabela in tabelas:
                for linha in tabela:
                    if not linha or len(linha) < 5:
                        continue
                    celulas = tuple(str(c).replace("\n", " ").strip() if c else "" for c in linha)
                    if "Dias da" in celulas or "EM VIGOR" in celulas:
                        continue
                    primeira = next(iter(celulas), "")
                    if primeira.isdigit():
                        os_atual = int(primeira)
                    if os_atual is None:
                        continue
                    texto_linha = " ".join(celulas)
                    if os_atual not in registos_por_os:
                        if "Descanso" in texto_linha:
                            registos_por_os.update({os_atual: {"OS": os_atual, "Tipo": "Descanso", "Inicio": "", "Fim": "", "Min_Rev": 0, "Rep_Fora": "Não", "Obs": "Descanso"}})
                        elif "SUPRA" in texto_linha:
                            registos_por_os.update({os_atual: {"OS": os_atual, "Tipo": "SUPRA", "Inicio": "08:00", "Fim": "16:00", "Min_Rev": 0, "Rep_Fora": "Não", "Obs": "SUPRA"}})
                        else:
                            horas = re.findall(r"\b\d{1,2}:\d{2}\b", texto_linha)
                            it_h = iter(horas)
                            inicio = next(it_h, "08:00")
                            fim = next(it_h, "16:00")
                            rep_fora = "Sim (<18h)" if texto_linha.lower().endswith(" x") or " x " in texto_linha.lower() else "Não"
                            registos_por_os.update({os_atual: {"OS": os_atual, "Tipo": "Bordo", "Inicio": inicio, "Fim": fim, "Min_Rev": 300, "Rep_Fora": rep_fora, "Obs": texto_linha[:40]}})
    if not registos_por_os:
        return gerar_escala_base()
    lista_ordenada = tuple(registos_por_os.get(k) for k in sorted(registos_por_os.keys()))
    return pd.DataFrame(lista_ordenada)

def calcular_horas_noturnas(inicio_str, fim_str):
    if not inicio_str or not fim_str or ":" not in str(inicio_str) or ":" not in str(fim_str):
        return 0.0
    try:
        h1, m1 = map(int, str(inicio_str).split(":"))
        h2, m2 = map(int, str(fim_str).split(":"))
        dt_inicio = datetime(2026, 1, 1, h1, m1)
        dt_fim = datetime(2026, 1, 1, h2, m2)
        if dt_fim <= dt_inicio:
            dt_fim += timedelta(days=1)
        minutos_noturnos = 0
        atual = dt_inicio
        while atual < dt_fim:
            if atual.hour >= 20 or atual.hour < 7:
                minutos_noturnos += 1
            atual += timedelta(minutes=1)
        return round(minutos_noturnos / 60.0, 2)
    except Exception:
        return 0.0

def calcular_abono_falhas(receita_total):
    if receita_total <= 0:
        return 0.0
    if receita_total <= 250.0:
        valor = receita_total * 0.055
    else:
        valor = (receita_total * 0.045) + 2.55
    return round(max(15.00, valor), 2)

st.set_page_config(page_title="Simulador CP Revisão", page_icon="🚆", layout="wide")
st.title("🚆 Simulador de Abonos — Revisão Comercial (CP)")

# --- BOTÃO DE CARREGAR ESCALA SEMPRE VISÍVEL NO TOPO ---
with st.expander("📂 CARREGAR ESCALA DO PC (PDF da CP / Excel / CSV) — Clica aqui para abrir", expanded=True):
    ficheiro_carregado = st.file_uploader("Seleciona o ficheiro da escala no teu computador", type=("pdf", "csv", "xlsx"))
    if ficheiro_carregado is not None:
        try:
            nome_fich = ficheiro_carregado.name.lower()
            if nome_fich.endswith(".pdf"):
                df_novo = ler_pdf_escala_cp(ficheiro_carregado)
            elif nome_fich.endswith(".csv"):
                df_novo = pd.read_csv(ficheiro_carregado).fillna("")
            else:
                df_novo = pd.read_excel(ficheiro_carregado).fillna("")
            st.session_state.update({"df_escala_custom": df_novo, "nome_escala_atual": ficheiro_carregado.name})
            st.success(f"✅ Escala '{ficheiro_carregado.name}' carregada com {len(df_novo)} OS!")
        except Exception as e:
            st.error(f"Erro ao ler ficheiro: {e}")

df_escala = st.session_state.get("df_escala_custom", gerar_escala_base())
mapa_escala = df_escala.set_index("OS").to_dict(orient="index")
max_os = int(df_escala.get("OS").max()) if len(df_escala) > 0 else 120

# --- MENU LATERAL ---
st.sidebar.header("👤 Dados do Trabalhador")
indice = st.sidebar.selectbox("Índice Salarial", INDICES_LISTA, index=3)
num_diut = st.sidebar.slider("Diuturnidades (25 €)", 0, 5, 2)
tem_escala = st.sidebar.checkbox("Subsídio de Escala (18,5%)", value=True)
tem_transporte = st.sidebar.checkbox("Abono Transporte (4,91 €/dia)", value=True)

st.sidebar.divider()
st.sidebar.header("💶 Vendas a Bordo")
receita_bordo = st.sidebar.number_input("Receita Total (€)", min_value=0.0, value=0.0, step=10.0)
qtd_bilhetes = st.sidebar.number_input("Qtd. Bilhetes Vendidos", min_value=0, value=0, step=1)
valor_por_bilhete = st.sidebar.number_input("Comissão por Bilhete (€)", min_value=0.0, value=0.0, step=0.05)

st.sidebar.divider()
st.sidebar.header("🏛️ Descontos")
taxa_irs = st.sidebar.number_input("Taxa IRS (%)", min_value=0.0, max_value=50.0, value=14.5, step=0.5)
quota_sindical_pct = st.sidebar.number_input("Quota Sindical (%)", min_value=0.0, max_value=5.0, value=1.0, step=0.1)
outros_descontos = st.sidebar.number_input("Outros Descontos (€)", min_value=0.0, value=0.0, step=1.0)

# --- CÁLCULOS BASE ---
retrib_base = TABELA_INDICES.get(indice, 1166.78)
valor_diut = num_diut * 25.00
valor_sub_escala = round(retrib_base * 0.185, 2) if tem_escala else 0.0
rm = round(retrib_base + valor_diut + valor_sub_escala, 2)
rh = round((rm * 12.0) / (52.0 * 40.0), 2)

st.divider()
st.subheader("📅 1. Escolher o Serviço e Mês")
mes = st.selectbox("Mês", (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), index=10)
ano = st.number_input("Ano", min_value=2024, max_value=2030, value=2026)
os_dia_1 = st.number_input(f"Qual é a tua OS no Dia 1 do mês? (1 a {max_os})", min_value=1, max_value=max_os, value=1)

_, num_dias = calendar.monthrange(ano, mes)
dias_semana_pt = ("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")
nome_escala = st.session_state.get("nome_escala_atual", "Base")
chave_atual = f"{nome_escala}-{ano}-{mes}-{os_dia_1}"

if st.button("🔄 Gerar / Reiniciar Mês") or st.session_state.get("chave_mes") != chave_atual or "df_mes" not in st.session_state:
    dados_mes = list()
    for dia in range(1, num_dias + 1):
        data_atual = datetime(ano, mes, dia)
        dia_sem = dias_semana_pt.index(dias_semana_pt) if False else tuple(dias_semana_pt).__getitem__(data_atual.weekday())
        os_atual = ((os_dia_1 - 1 + (dia - 1)) % max_os) + 1
        linha_os = mapa_escala.get(os_atual, {"Tipo": "Descanso", "Inicio": "", "Fim": "", "Min_Rev": 0, "Rep_Fora": "Não", "Obs": ""})
        tipo = linha_os.get("Tipo", "Descanso")
        inicio = linha_os.get("Inicio", "")
        fim = linha_os.get("Fim", "")
        min_rev = int(float(linha_os.get("Min_Rev", 0))) if str(linha_os.get("Min_Rev", "")).strip() != "" else 0
        rep_fora = linha_os.get("Rep_Fora", "Não")
        obs = linha_os.get("Obs", "")
        h_noturnas = calcular_horas_noturnas(inicio, fim) if tipo in ("Bordo", "SUPRA") else 0.0
        dados_mes.append({
            "Dia": dia, "Semana": dia_sem, "OS": os_atual, "Serviço": obs,
            "Situação": tipo, "Início": inicio, "Fim": fim,
            "H. Noturnas": h_noturnas, "Min. Revisão (mr)": min_rev,
            "H. Extras": 0.0, "Dia Desc. Trab.": "Não", "Repouso Fora": rep_fora, "RENFE": False
        })
    st.session_state.update({"df_mes": pd.DataFrame(dados_mes), "chave_mes": chave_atual})

df_mes_editado = st.data_editor(
    st.session_state.get("df_mes"),
    column_config={
        "Situação": st.column_config.SelectboxColumn("Situação", options=("Bordo", "SUPRA", "Descanso", "Feriado", "Férias", "Formação", "Falta")),
        "Dia Desc. Trab.": st.column_config.SelectboxColumn("Dia Desc./Fer. Trab.", options=("Não", "Com Compensação (+50%)", "Sem Compensação (+75%)")),
        "Repouso Fora": st.column_config.SelectboxColumn("Repouso Fora Sede", options=("Não", "Sim (<18h)", "Sim (>18h)")),
    },
    use_container_width=True,
    hide_index=True
)

st.divider()
st.subheader("🧾 2. Resumo do Recibo Calculado")

dias_bordo = len(df_mes_editado.query("Situação == 'Bordo'"))
