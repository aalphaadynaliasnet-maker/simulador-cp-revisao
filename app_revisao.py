import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta
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
    supras = {11, 89, 90, 114, 115}
    registos = list()
    for num_os in range(1, 121):
        if num_os in descansos:
            registos.append({"Codigo": f"OS {num_os:03d} | Descanso", "OS": num_os, "Regime": "1..7", "Tipo": "Descanso", "Local_Ini": "", "Inicio": "", "Local_Fim": "", "Fim": "", "PNT": "00:00", "Min_Rev": 0, "Rep_Fora": "Não", "Obs": "Descanso Semanal"})
        elif num_os in supras:
            registos.append({"Codigo": f"OS {num_os:03d} | SUPRA (08:00)", "OS": num_os, "Regime": "1..7", "Tipo": "SUPRA", "Local_Ini": "COB", "Inicio": "08:00", "Local_Fim": "COB", "Fim": "16:00", "PNT": "08:00", "Min_Rev": 0, "Rep_Fora": "Não", "Obs": "SUPRA"})
        else:
            registos.append({"Codigo": f"OS {num_os:03d} | Serviço Base (08:00-16:00)", "OS": num_os, "Regime": "1..7", "Tipo": "Bordo", "Local_Ini": "COB", "Inicio": "08:00", "Local_Fim": "COB", "Fim": "16:00", "PNT": "08:00", "Min_Rev": 300, "Rep_Fora": "Não", "Obs": f"Serviço OS {num_os}"})
    return pd.DataFrame(registos)

def ler_pdf_escala_cp(ficheiro_pdf):
    """Lê TODAS as 120 OS e todas as suas variantes (N, S, F, V) de todas as páginas do PDF da CP."""
    registos = list()
    with pdfplumber.open(ficheiro_pdf) as pdf:
        os_atual = None
        for page in pdf.pages:
            tabelas = page.extract_tables()
            for tabela in tabelas:
                for linha in tabela:
                    if not linha:
                        continue
                    celulas = tuple(str(c).replace("\n", " ").strip() if c else "" for c in linha)
                    texto_completo = " ".join(celulas).strip()
                    if not texto_completo or "EM VIGOR DESDE" in texto_completo or "Dias da Semana" in texto_completo or "F.500.02.002" in texto_completo:
                        continue

                    # Detetar número da OS na 1.ª coluna (1 a 120)
                    c0 = next(iter(celulas), "")
                    if c0.isdigit() and 1 <= int(c0) <= 150:
                        os_atual = int(c0)
                    if os_atual is None:
                        continue

                    # Extrair colunas por posição segura
                    it_c = iter(celulas)
                    _ = next(it_c, "")
                    regime = next(it_c, "")
                    loc_ini = next(it_c, "")
                    hora_ini = next(it_c, "")
                    designacao = next(it_c, "")
                    loc_fim = next(it_c, "")
                    hora_fim = next(it_c, "")
                    pnt = next(it_c, "")
                    rep_s = next(it_c, "")
                    rep_f = next(it_c, "")

                    # Ignorar linhas de continuação sem regime nem designação
                    if not regime and not designacao and not hora_ini and not hora_fim:
                        continue

                    # Identificar Tipo de Serviço
                    if "Descanso" in texto_completo:
                        tipo = "Descanso"
                        min_rev = 0
                        rep_fora = "Não"
                        desc_curta = "Descanso"
                    elif "SUPRA" in texto_completo:
                        tipo = "SUPRA"
                        min_rev = 0
                        rep_fora = "Não"
                        desc_curta = "SUPRA"
                    else:
                        # Verificar se é só Reserva ou se tem comboios comerciais
                        tem_comboios = bool(re.search(r"\b\d{3,5}\b", designacao))
                        tipo = "Bordo" if tem_comboios else "Reserva"
                        
                        # Calcular PNT em minutos e estimar minutos de revisão (descontando TR 45m e s/s)
                        horas_pnt = re.findall(r"\b\d{1,2}:\d{2}\b", pnt)
                        if horas_pnt:
                            hp, mp = map(int, next(iter(horas_pnt)).split(":"))
                            total_pnt_min = hp * 60 + mp
                        else:
                            total_pnt_min = 420
                        
                        desconto_tr = 45 if "(TR)" in designacao else 0
                        qtd_ss = len(re.findall(r"s/s", designacao))
                        min_rev = max(0, total_pnt_min - desconto_tr - (qtd_ss * 35)) if tipo == "Bordo" else 0

                        # Verificar se termina fora da sede (REP F marcado com x ou local fim != local ini/sede)
                        if rep_f.lower() == "x" or (loc_fim and loc_fim not in ("COB", "")):
                            rep_fora = "Sim (<18h)"
                        else:
                            rep_fora = "Não"
                        desc_curta = designacao[:42] if designacao else f"Serviço OS {os_atual}"

                    horario_txt = f"{hora_ini}-{hora_fim}" if hora_ini or hora_fim else pnt
                    reg_txt = regime if regime else "Geral"
                    codigo_label = f"OS {os_atual:03d} | {reg_txt} | {horario_txt} | {desc_curta}"

                    registos.append({
                        "Codigo": codigo_label,
                        "OS": os_atual,
                        "Regime": reg_txt,
                        "Tipo": tipo,
                        "Local_Ini": loc_ini,
                        "Inicio": hora_ini,
                        "Local_Fim": loc_fim,
                        "Fim": hora_fim,
                        "PNT": pnt,
                        "Min_Rev": min_rev,
                        "Rep_Fora": rep_fora,
                        "Obs": desc_curta
                    })

    if not registos:
        return gerar_escala_base()
    return pd.DataFrame(registos)

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

# --- 1. CARREGAR ESCALA DO PC ---
with st.expander("📂 1. CARREGAR ESCALA DO PC (PDF da CP / Excel / CSV)", expanded=True):
    ficheiro_carregado = st.file_uploader("Seleciona o ficheiro da escala no teu computador", type=("pdf", "csv", "xlsx"))
    if ficheiro_carregado is not None:
        if st.session_state.get("ultimo_ficheiro") != ficheiro_carregado.name:
            try:
                nome_fich = ficheiro_carregado.name.lower()
                if nome_fich.endswith(".pdf"):
                    df_novo = ler_pdf_escala_cp(ficheiro_carregado)
                elif nome_fich.endswith(".csv"):
                    df_novo = pd.read_csv(ficheiro_carregado).fillna("")
                else:
                    df_novo = pd.read_excel(ficheiro_carregado).fillna("")
                st.session_state.update({
                    "df_escala_custom": df_novo,
                    "ultimo_ficheiro": ficheiro_carregado.name
                })
                if "df_mes" in st.session_state:
                    del st.session_state["df_mes"]
                st.success(f"✅ Escala '{ficheiro_carregado.name}' carregada com {len(df_novo)} linhas de serviço (OS 1 a {df_novo.get('OS').max()})!")
            except Exception as e:
                st.error(f"Erro ao ler ficheiro: {e}")

df_escala = st.session_state.get("df_escala_custom", gerar_escala_base()).drop_duplicates(subset="Codigo")
lista_codigos_os = tuple(df_escala.get("Codigo").tolist())
mapa_por_codigo = df_escala.set_index("Codigo").to_dict(orient="index")

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
