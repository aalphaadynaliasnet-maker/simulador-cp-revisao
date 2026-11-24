import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta
import os

# ==============================================================================
# 1. TABELA INDICIÁRIA E VALORES PECUNIÁRIOS (SFRCI 09/2026 + AE CP)
# ==============================================================================
TABELA_INDICES = {
    128: 1116.50, 131: 1133.26, 134: 1150.03, 137: 1166.78, 140: 1183.54,
    144: 1205.88, 148: 1228.24, 152: 1250.59, 156: 1272.93, 161: 1300.88,
    166: 1328.83, 171: 1356.76, 176: 1384.70, 182: 1418.22, 189: 1457.34,
    196: 1495.37, 203: 1534.56, 210: 1574.22, 217: 1613.87, 224: 1653.00,
    231: 1693.46, 238: 1733.92, 245: 1774.39, 252: 1814.86, 259: 1855.31,
    266: 1895.78, 273: 1936.24, 280: 1976.70, 288: 2025.30, 296: 2073.88
}

VALORES_PECUNIARIOS = {
    "diuturnidade_unit": 25.00,
    "subsidio_escala_pct": 0.185,
    "pp_revisao": 6.20,
    "irev": 0.80,
    "pp_geral": 6.50,
    "itinerancia": 8.30,
    "subsidio_refeicao": 10.45,
    "limite_isencao_sr": 10.20,
    "abono_transporte": 4.91,
    "repouso_inf_18h": 30.00,
    "repouso_sup_18h": 32.00,
    "taxa_ss": 0.11
}

FICHEIRO_ESCALA = "escala_cobr20.csv"

def gerar_escala_base():
    descansos = {1, 7, 8, 15, 16, 23, 24, 31, 32, 39, 40, 47, 48, 55, 56, 63, 64, 71, 72, 79, 80, 87, 88, 95, 96, 103, 104, 111, 112, 119, 120}
    os_especificas = {
        2:  {"Tipo": "Bordo", "Inicio": "13:15", "Fim": "21:12", "PNT": "07:57", "Min_Rev": 320, "Rep_Fora": "Sim (<18h)", "Obs": "5405 GUA"},
        3:  {"Tipo": "Bordo", "Inicio": "06:50", "Fim": "14:50", "PNT": "08:00", "Min_Rev": 300, "Rep_Fora": "Não", "Obs": "5402 COB"},
        4:  {"Tipo": "Bordo", "Inicio": "05:03", "Fim": "11:59", "PNT": "06:56", "Min_Rev": 290, "Rep_Fora": "Não", "Obs": "4500/16804"},
        5:  {"Tipo": "Bordo", "Inicio": "05:25", "Fim": "12:46", "PNT": "07:21", "Min_Rev": 310, "Rep_Fora": "Não", "Obs": "4601/4609"},
        6:  {"Tipo": "Bordo", "Inicio": "05:18", "Fim": "12:37", "PNT": "07:19", "Min_Rev": 305, "Rep_Fora": "Não", "Obs": "4500/4513"},
        9:  {"Tipo": "Bordo", "Inicio": "11:22", "Fim": "19:22", "PNT": "08:00", "Min_Rev": 330, "Rep_Fora": "Sim (<18h)", "Obs": "16812/5403 GUA"},
        10: {"Tipo": "Bordo", "Inicio": "04:50", "Fim": "12:50", "PNT": "08:00", "Min_Rev": 310, "Rep_Fora": "Não", "Obs": "5400 COB"},
        11: {"Tipo": "SUPRA", "Inicio": "08:00", "Fim": "16:00", "PNT": "08:00", "Min_Rev": 0,   "Rep_Fora": "Não", "Obs": "SUPRA"},
        12: {"Tipo": "Bordo", "Inicio": "05:57", "Fim": "13:27", "PNT": "07:30", "Min_Rev": 325, "Rep_Fora": "Sim (<18h)", "Obs": "4502/16812 FFO"},
        13: {"Tipo": "Bordo", "Inicio": "06:16", "Fim": "11:19", "PNT": "06:00", "Min_Rev": 260, "Rep_Fora": "Não", "Obs": "16803/16811"},
        14: {"Tipo": "Bordo", "Inicio": "05:57", "Fim": "11:57", "PNT": "06:00", "Min_Rev": 250, "Rep_Fora": "Não", "Obs": "4502/4511"},
        17: {"Tipo": "Bordo", "Inicio": "11:49", "Fim": "19:49", "PNT": "08:00", "Min_Rev": 340, "Rep_Fora": "Não", "Obs": "524/4425/731"},
        18: {"Tipo": "Bordo", "Inicio": "12:45", "Fim": "19:18", "PNT": "06:33", "Min_Rev": 280, "Rep_Fora": "Não", "Obs": "5401/5404"},
        19: {"Tipo": "Bordo", "Inicio": "14:41", "Fim": "21:00", "PNT": "06:19", "Min_Rev": 270, "Rep_Fora": "Não", "Obs": "4619/4680"},
        20: {"Tipo": "Bordo", "Inicio": "11:35", "Fim": "19:42", "PNT": "08:07", "Min_Rev": 350, "Rep_Fora": "Sim (<18h)", "Obs": "5208/5213 ESV"},
        21: {"Tipo": "Bordo", "Inicio": "06:28", "Fim": "13:54", "PNT": "07:26", "Min_Rev": 315, "Rep_Fora": "Não", "Obs": "5200/5204"},
        22: {"Tipo": "Bordo", "Inicio": "11:41", "Fim": "18:55", "PNT": "07:14", "Min_Rev": 300, "Rep_Fora": "Não", "Obs": "720/821"},
        33: {"Tipo": "Bordo", "Inicio": "16:12", "Fim": "23:59", "PNT": "07:49", "Min_Rev": 330, "Rep_Fora": "Sim (<18h)", "Obs": "4512/16830 FFO"},
        34: {"Tipo": "Bordo", "Inicio": "12:43", "Fim": "18:50", "PNT": "06:07", "Min_Rev": 265, "Rep_Fora": "Não", "Obs": "16817/4676"},
        60: {"Tipo": "Bordo", "Inicio": "01:59", "Fim": "08:34", "PNT": "06:35", "Min_Rev": 270, "Rep_Fora": "Não", "Obs": "3400/4505"},
        89: {"Tipo": "SUPRA", "Inicio": "08:00", "Fim": "16:00", "PNT": "08:00", "Min_Rev": 0,   "Rep_Fora": "Não", "Obs": "SUPRA"},
        90: {"Tipo": "SUPRA", "Inicio": "08:00", "Fim": "16:00", "PNT": "08:00", "Min_Rev": 0,   "Rep_Fora": "Não", "Obs": "SUPRA"},
        114:{"Tipo": "SUPRA", "Inicio": "08:00", "Fim": "16:00", "PNT": "08:00", "Min_Rev": 0,   "Rep_Fora": "Não", "Obs": "SUPRA"},
        115:{"Tipo": "SUPRA", "Inicio": "08:00", "Fim": "16:00", "PNT": "08:00", "Min_Rev": 0,   "Rep_Fora": "Não", "Obs": "SUPRA"},
        116:{"Tipo": "Bordo", "Inicio": "18:00", "Fim": "23:59", "PNT": "06:02", "Min_Rev": 250, "Rep_Fora": "Sim (<18h)", "Obs": "16830 FFO"},
        117:{"Tipo": "Bordo", "Inicio": "12:50", "Fim": "20:41", "PNT": "07:51", "Min_Rev": 335, "Rep_Fora": "Não", "Obs": "4670/4521"},
        118:{"Tipo": "Bordo", "Inicio": "13:58", "Fim": "21:29", "PNT": "07:31", "Min_Rev": 310, "Rep_Fora": "Não", "Obs": "802/6455"},
    }

    registos = []
    for num_os in range(1, 121):
        if num_os in descansos:
            registos.append({"OS": num_os, "Tipo": "Descanso", "Inicio": "", "Fim": "", "PNT": "00:00", "Min_Rev": 0, "Rep_Fora": "Não", "Obs": "Descanso Semanal"})
        elif num_os in os_especificas:
            item = os_especificas[num_os].copy()
            item["OS"] = num_os
            registos.append(item)
        else:
            registos.append({"OS": num_os, "Tipo": "Bordo", "Inicio": "08:00", "Fim": "16:00", "PNT": "08:00", "Min_Rev": 300, "Rep_Fora": "Não", "Obs": "Serviço Escala"})
    
    return pd.DataFrame(registos)

def carregar_escala():
    if os.path.exists(FICHEIRO_ESCALA):
        return pd.read_csv(FICHEIRO_ESCALA).fillna("")
    return gerar_escala_base()

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

st.set_page_config(page_title="Simulador Vencimento CP - Revisão", page_icon="🚆", layout="wide")

st.title("🚆 Simulador de Abonos e Vencimento — Revisão Comercial (CP)")
st.markdown("Baseado no **AE da CP (BTE 39/2024)**, **Tabela SFRCI (09/2026)** e **Escala COBR20**.")

df_escala = carregar_escala()
mapa_escala = df_escala.set_index("OS").to_dict(orient="index")

with st.sidebar:
    st.header("👤 Dados do Trabalhador")
    indice = st.selectbox("Índice Salarial (ORV: 137 a 171)", list(TABELA_INDICES.keys()), index=3)
    num_diut = st.slider("N.º de Diuturnidades (25,00 €/cada)", 0, 5, 2)
    tem_escala = st.checkbox("Subsídio de Escala (18,50%)", value=True)
    tem_transporte = st.checkbox("Disponibilidade 00h-06h30 (Abono Transp.)", value=True)
    
    st.divider()
    st.header("💶 Vendas a Bordo no Mês")
    receita_bordo = st.number_input("Valor Total da Receita (€)", min_value=0.0, value=0.0, step=10.0, format="%.2f")
    qtd_bilhetes = st.number_input("Quantidade de Bilhetes Vendidos", min_value=0, value=0, step=1)
    valor_por_bilhete = st.number_input("Comissão/Valor por Bilhete (€)", min_value=0.0, value=0.0, step=0.05, format="%.2f")

    st.divider()
    st.header("🏛️ Descontos e Retenções")
    taxa_irs = st.number_input("Taxa de Retenção IRS (%)", min_value=0.0, max_value=50.0, value=14.5, step=0.5)
    quota_sindical_pct = st.number_input("Quota Sindical (% sobre Base)", min_value=0.0, max_value=5.0, value=1.0, step=0.1)
    outros_descontos = st.number_input("Outros Descontos Fixos (€)", min_value=0.0, value=0.0, step=1.0)

retrib_base = TABELA_INDICES[indice]
valor_diut = num_diut * VALORES_PECUNIARIOS["diuturnidade_unit"]
valor_sub_escala = round(retrib_base * VALORES_PECUNIARIOS["subsidio_escala_pct"], 2) if tem_escala else 0.0
rm = round(retrib_base + valor_diut + valor_sub_escala, 2)
rd = round(rm / 30.0, 2)
rh = round((rm * 12.0) / (52.0 * 40.0), 2)

# Menu de Navegação Infalível
pagina = st.radio(
    "Escolhe a secção:",
    ["📅 1. Escala Mensal", "🧾 2. Simulador de Recibo", "⚙️ 3. Gerir Escala (OS)"],
    horizontal=True
)
st.divider()

# Preparação dos dados do mês (partilhada entre Escala Mensal e Recibo)
meses_pt = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}
col1, col2, col3 = st.columns(3)
with col1:
    mes = st.selectbox("Mês", list(meses_pt.keys()), index=10, format_func=lambda x: meses_pt[x])
with col2:
    ano = st.number_input("Ano", min_value=2024, max_value=2030, value=2026)
with col3:
    os_dia_1 = st.number_input("Qual a tua OS no Dia 1 do mês?", min_value=1, max_value=120, value=1)

_, num_dias = calendar.monthrange(ano, mes)
dias_semana_pt = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

dados_mes = []
for dia in range(1, num_dias + 1):
    data_atual = datetime(ano, mes, dia)
    dia_sem = dias_semana_pt[data_atual.weekday()]
    os_atual = ((os_dia_1 - 1 + (dia - 1)) % 120) + 1
    
