"""
NeveStudio - Gerador de Dashboards com Plotly
Interface gráfica (Tkinter) que gera um dashboard analítico completo
sobre saúde / obesidade no Brasil (dados fictícios).
"""

from __future__ import annotations

import os
import random
import tempfile
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

import plotly.graph_objects as go
import plotly.io as pio


# ---------------------------------------------------------------------------
# DADOS FICTÍCIOS
# ---------------------------------------------------------------------------
random.seed(42)

MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
         "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
ANOS = list(range(2018, 2026))

BIG_NUMBERS = [
    {"titulo": "População avaliada", "valor": "128.450",
     "delta": "+4,2%", "cor": "#3b82f6"},
    {"titulo": "IMC médio nacional", "valor": "27,3",
     "delta": "+0,5", "cor": "#f59e0b"},
    {"titulo": "Taxa de obesidade", "valor": "24,6%",
     "delta": "+1,8 p.p.", "cor": "#ef4444"},
    {"titulo": "Atividade física regular", "valor": "37,1%",
     "delta": "+2,4 p.p.", "cor": "#10b981"},
    {"titulo": "Custo SUS estimado", "valor": "R$ 4,8 bi",
     "delta": "+6,1%", "cor": "#8b5cf6"},
]

# Séries anuais
SERIE_OBESIDADE_ANOS = [17.8, 18.6, 19.5, 20.7, 21.9, 22.8, 23.7, 24.6]
SERIE_SOBREPESO_ANOS = [52.1, 53.0, 54.2, 55.0, 55.9, 56.7, 57.3, 58.1]
SERIE_IMC_HOMENS = [26.4, 26.6, 26.8, 26.9, 27.1, 27.2, 27.3, 27.5]
SERIE_IMC_MULHERES = [25.9, 26.1, 26.3, 26.5, 26.8, 27.0, 27.1, 27.2]

# Mensais
ATENDIMENTOS_MENSAIS = [9800, 10250, 11100, 10780, 11540, 12030,
                        12480, 11980, 11620, 12750, 13020, 13540]

DIST_CATEGORIAS = {
    "labels": ["Peso normal", "Sobrepeso", "Obesidade I",
               "Obesidade II", "Obesidade III"],
    "valores": [38.5, 33.7, 15.4, 6.8, 2.4],
    "cores": ["#10b981", "#fde68a", "#fb923c", "#ef4444", "#991b1b"],
}

ATEND_POR_REGIAO = {
    "regioes": ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"],
    "valores": [8420, 23710, 11280, 51640, 19340],
    "cores": ["#60a5fa", "#a78bfa", "#fde68a", "#fb923c", "#10b981"],
}

# Dispersão: relação IMC x horas de atividade física semanal
DISPERSAO = {
    "imc": [random.gauss(27, 4) for _ in range(180)],
    "horas": [max(0, random.gauss(3.5, 2.5)) for _ in range(180)],
}

# Histograma: distribuição de IMC da amostra
HISTOGRAMA_IMC = [random.gauss(27, 4.2) for _ in range(2500)]

# Mapa: prevalência de obesidade por estado (simplificado, alguns estados)
MAPA_ESTADOS = {
    "uf": ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
           "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
           "RS", "RO", "RR", "SC", "SP", "SE", "TO"],
    "obesidade": [22.1, 25.4, 21.8, 22.9, 24.6, 23.5, 26.3, 25.8, 27.1,
                  24.9, 26.4, 25.2, 26.8, 23.7, 24.1, 27.5, 25.3, 23.9,
                  26.9, 24.5, 28.2, 23.4, 21.5, 27.8, 26.1, 24.7, 23.6],
}

# Funil: jornada do paciente
FUNIL = {
    "etapas": ["Cadastros", "Triagem", "Avaliação clínica",
               "Plano nutricional", "Acompanhamento ativo"],
    "valores": [128450, 96340, 72180, 48720, 31250],
}

# Tabela 1: indicadores por região
TABELA_REGIOES = {
    "headers": ["Região", "População", "IMC médio", "Obesidade %", "Variação"],
    "linhas": [
        ["Norte",        "8.420",  "26,2", "22,8%", "+1,2 p.p."],
        ["Nordeste",     "23.710", "26,9", "24,1%", "+1,5 p.p."],
        ["Centro-Oeste", "11.280", "27,4", "25,3%", "+1,9 p.p."],
        ["Sudeste",      "51.640", "27,5", "25,8%", "+2,1 p.p."],
        ["Sul",          "19.340", "27,8", "26,4%", "+2,4 p.p."],
    ],
}

# Tabela 2: top faixas etárias
TABELA_FAIXAS = {
    "headers": ["Faixa etária", "Pacientes", "IMC médio",
                "Sobrepeso %", "Obesidade %"],
    "linhas": [
        ["20–29 anos", "24.310", "25,4", "48,2%", "16,1%"],
        ["30–39 anos", "31.870", "26,8", "55,7%", "22,4%"],
        ["40–49 anos", "35.620", "27,9", "60,3%", "27,8%"],
        ["50–60 anos", "36.650", "28,4", "63,1%", "31,5%"],
    ],
}

# Candlestick: indicador "índice de saúde populacional" diário (30 dias)
def _gerar_candles(n: int = 30) -> dict:
    base = datetime(2026, 4, 1)
    datas, op, hi, lo, cl = [], [], [], [], []
    preco = 72.0
    for i in range(n):
        datas.append((base + timedelta(days=i)).strftime("%Y-%m-%d"))
        o = preco
        c = o + random.uniform(-1.8, 1.9)
        h = max(o, c) + random.uniform(0.2, 1.2)
        l = min(o, c) - random.uniform(0.2, 1.2)
        op.append(round(o, 2)); hi.append(round(h, 2))
        lo.append(round(l, 2)); cl.append(round(c, 2))
        preco = c
    return {"datas": datas, "open": op, "high": hi, "low": lo, "close": cl}

CANDLES = _gerar_candles()

# Waterfall: composição do custo SUS estimado
WATERFALL = {
    "labels": ["Base 2024", "Atendimentos", "Medicamentos",
               "Internações", "Cirurgias bariátricas",
               "Programas preventivos", "Total 2025"],
    "measure": ["absolute", "relative", "relative", "relative",
                "relative", "relative", "total"],
    "valores": [4520, 380, 210, 290, 150, -750, 0],
}

# Polar: distribuição de hábitos por categoria
POLAR = {
    "categorias": ["Alimentação", "Atividade física", "Sono",
                   "Hidratação", "Estresse", "Acompanhamento médico"],
    "homens": [62, 55, 70, 58, 48, 41],
    "mulheres": [71, 49, 66, 67, 52, 58],
}


# ---------------------------------------------------------------------------
# Helpers de figura
# ---------------------------------------------------------------------------
def _layout_base(fig: go.Figure, titulo: str) -> go.Figure:
    fig.update_layout(
        title=dict(text=titulo, x=0.02, xanchor="left",
                   font=dict(size=15, color="#1e293b")),
        template="plotly_white",
        font=dict(family="Inter, Segoe UI, Arial", size=12, color="#1e293b"),
        margin=dict(l=50, r=25, t=55, b=50),
        paper_bgcolor="white",
        plot_bgcolor="white",
        legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
    )
    fig.update_xaxes(showgrid=False, linecolor="#e2e8f0")
    fig.update_yaxes(gridcolor="#f1f5f9", linecolor="#e2e8f0")
    return fig


# Time-series
def fig_timeline_obesidade() -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ANOS, y=SERIE_OBESIDADE_ANOS, mode="lines+markers",
        name="Obesidade (%)", line=dict(color="#ef4444", width=3),
        marker=dict(size=8), fill="tozeroy",
        fillcolor="rgba(239,68,68,0.10)"))
    fig.add_trace(go.Scatter(
        x=ANOS, y=SERIE_SOBREPESO_ANOS, mode="lines+markers",
        name="Sobrepeso (%)", line=dict(color="#f59e0b", width=3),
        marker=dict(size=8)))
    return _layout_base(fig, "Evolução anual: Sobrepeso e Obesidade")


def fig_timeline_imc() -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ANOS, y=SERIE_IMC_HOMENS, mode="lines+markers",
        name="Homens", line=dict(color="#3b82f6", width=3),
        marker=dict(size=8)))
    fig.add_trace(go.Scatter(
        x=ANOS, y=SERIE_IMC_MULHERES, mode="lines+markers",
        name="Mulheres", line=dict(color="#ec4899", width=3),
        marker=dict(size=8)))
    return _layout_base(fig, "IMC médio por sexo (kg/m²)")


# Mensais
def fig_mensal_atendimentos() -> go.Figure:
    fig = go.Figure(go.Bar(
        x=MESES, y=ATENDIMENTOS_MENSAIS,
        marker_color="#3b82f6",
        text=[f"{v/1000:.1f}k" for v in ATENDIMENTOS_MENSAIS],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y:,} atendimentos<extra></extra>"))
    fig.update_layout(showlegend=False)
    return _layout_base(fig, "Atendimentos mensais (2025)")


def fig_mensal_distribuicao() -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=DIST_CATEGORIAS["labels"],
        values=DIST_CATEGORIAS["valores"],
        hole=0.55,
        marker=dict(colors=DIST_CATEGORIAS["cores"],
                    line=dict(color="white", width=2)),
        textinfo="percent",
        hovertemplate="<b>%{label}</b><br>%{value}%<extra></extra>"))
    return _layout_base(fig, "Distribuição por categoria de IMC")


def fig_mensal_regioes() -> go.Figure:
    dados = sorted(zip(ATEND_POR_REGIAO["valores"],
                       ATEND_POR_REGIAO["regioes"],
                       ATEND_POR_REGIAO["cores"]))
    valores = [d[0] for d in dados]
    regioes = [d[1] for d in dados]
    cores = [d[2] for d in dados]
    fig = go.Figure(go.Bar(
        x=valores, y=regioes, orientation="h",
        marker_color=cores,
        text=[f"{v:,}".replace(",", ".") for v in valores],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x:,} atendimentos<extra></extra>"))
    fig.update_layout(showlegend=False)
    return _layout_base(fig, "Atendimentos por região (mês atual)")


# Novos
def fig_dispersao() -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=DISPERSAO["horas"], y=DISPERSAO["imc"], mode="markers",
        marker=dict(
            size=9,
            color=DISPERSAO["imc"],
            colorscale=[[0, "#10b981"], [0.5, "#f59e0b"], [1, "#ef4444"]],
            showscale=True,
            colorbar=dict(title="IMC", thickness=12, len=0.75),
            line=dict(width=0.5, color="white"),
            opacity=0.78,
        ),
        hovertemplate="Atividade: %{x:.1f} h/sem<br>IMC: %{y:.1f}<extra></extra>",
    ))
    fig.update_layout(showlegend=False)
    fig.update_xaxes(title_text="Horas de atividade física / semana")
    fig.update_yaxes(title_text="IMC (kg/m²)")
    return _layout_base(fig, "Dispersão: Atividade física x IMC")


def fig_histograma() -> go.Figure:
    fig = go.Figure(go.Histogram(
        x=HISTOGRAMA_IMC, nbinsx=40,
        marker=dict(color="#6366f1", line=dict(color="white", width=1)),
        hovertemplate="IMC: %{x}<br>Pacientes: %{y}<extra></extra>",
    ))
    fig.update_layout(showlegend=False, bargap=0.04)
    fig.update_xaxes(title_text="IMC (kg/m²)")
    fig.update_yaxes(title_text="Frequência")
    return _layout_base(fig, "Histograma de IMC da amostra")


def fig_mapa() -> go.Figure:
    fig = go.Figure(go.Choropleth(
        locations=MAPA_ESTADOS["uf"],
        z=MAPA_ESTADOS["obesidade"],
        locationmode="geojson-id",
        geojson="https://raw.githubusercontent.com/codeforgermany/click_that_hood/main/public/data/brazil-states.geojson",
        featureidkey="properties.sigla",
        colorscale=[[0, "#dbeafe"], [0.5, "#f59e0b"], [1, "#991b1b"]],
        colorbar=dict(title="Obesidade %", thickness=12, len=0.75),
        marker_line_color="white",
        marker_line_width=0.6,
        hovertemplate="<b>%{location}</b><br>Obesidade: %{z}%<extra></extra>",
    ))
    fig.update_geos(fitbounds="locations", visible=False, bgcolor="white")
    return _layout_base(fig, "Prevalência de obesidade por estado (Brasil)")


def fig_funil() -> go.Figure:
    fig = go.Figure(go.Funnel(
        y=FUNIL["etapas"], x=FUNIL["valores"],
        textinfo="value+percent initial",
        marker=dict(color=["#3b82f6", "#6366f1", "#8b5cf6",
                           "#a855f7", "#ec4899"]),
        connector=dict(line=dict(color="#cbd5e1", width=1)),
    ))
    return _layout_base(fig, "Funil de jornada do paciente")


def _fig_tabela(headers: list, linhas: list, titulo: str) -> go.Figure:
    cols = list(zip(*linhas))
    fig = go.Figure(go.Table(
        header=dict(
            values=[f"<b>{h}</b>" for h in headers],
            fill_color="#1e293b",
            font=dict(color="white", size=12, family="Inter, Segoe UI"),
            align="left", height=34,
        ),
        cells=dict(
            values=cols,
            fill_color=[["#f8fafc", "white"] * len(linhas)],
            font=dict(color="#1e293b", size=12),
            align="left", height=30,
        ),
    ))
    fig.update_layout(
        title=dict(text=titulo, x=0.02, xanchor="left",
                   font=dict(size=15, color="#1e293b")),
        margin=dict(l=10, r=10, t=55, b=10),
        paper_bgcolor="white",
    )
    return fig


def fig_tabela_regioes() -> go.Figure:
    return _fig_tabela(TABELA_REGIOES["headers"],
                       TABELA_REGIOES["linhas"],
                       "Indicadores por região")


def fig_tabela_faixas() -> go.Figure:
    return _fig_tabela(TABELA_FAIXAS["headers"],
                       TABELA_FAIXAS["linhas"],
                       "Indicadores por faixa etária")


def fig_candlestick() -> go.Figure:
    fig = go.Figure(go.Candlestick(
        x=CANDLES["datas"],
        open=CANDLES["open"], high=CANDLES["high"],
        low=CANDLES["low"], close=CANDLES["close"],
        increasing_line_color="#10b981",
        decreasing_line_color="#ef4444",
        name="Índice",
    ))
    fig.update_layout(showlegend=False, xaxis_rangeslider_visible=False)
    fig.update_yaxes(title_text="Pontos")
    return _layout_base(fig, "Índice diário de saúde populacional")


def fig_waterfall() -> go.Figure:
    fig = go.Figure(go.Waterfall(
        x=WATERFALL["labels"],
        measure=WATERFALL["measure"],
        y=WATERFALL["valores"],
        text=[f"R$ {v}M" if v else "" for v in WATERFALL["valores"]],
        textposition="outside",
        connector=dict(line=dict(color="#cbd5e1")),
        increasing=dict(marker=dict(color="#ef4444")),
        decreasing=dict(marker=dict(color="#10b981")),
        totals=dict(marker=dict(color="#3b82f6")),
    ))
    fig.update_yaxes(title_text="R$ (milhões)")
    return _layout_base(fig, "Composição do custo estimado SUS (R$ mi)")


def fig_polar() -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=POLAR["homens"] + [POLAR["homens"][0]],
        theta=POLAR["categorias"] + [POLAR["categorias"][0]],
        fill="toself", name="Homens",
        line=dict(color="#3b82f6"),
        fillcolor="rgba(59,130,246,0.25)"))
    fig.add_trace(go.Scatterpolar(
        r=POLAR["mulheres"] + [POLAR["mulheres"][0]],
        theta=POLAR["categorias"] + [POLAR["categorias"][0]],
        fill="toself", name="Mulheres",
        line=dict(color="#ec4899"),
        fillcolor="rgba(236,72,153,0.25)"))
    fig.update_layout(
        polar=dict(
            bgcolor="white",
            radialaxis=dict(visible=True, range=[0, 100],
                            gridcolor="#e2e8f0"),
            angularaxis=dict(gridcolor="#e2e8f0"),
        ),
    )
    return _layout_base(fig, "Adesão a hábitos saudáveis (%)")


# ---------------------------------------------------------------------------
# HTML do dashboard
# ---------------------------------------------------------------------------
def _fig_to_div(fig: go.Figure, div_id: str) -> str:
    return pio.to_html(
        fig, include_plotlyjs=False, full_html=False, div_id=div_id,
        config={"displaylogo": False, "responsive": True,
                "modeBarButtonsToRemove": ["lasso2d", "select2d"]})


def _kpi_card(kpi: dict) -> str:
    return f"""
    <div class="kpi-card" style="border-top:4px solid {kpi['cor']};">
      <div class="kpi-title">{kpi['titulo']}</div>
      <div class="kpi-value" style="color:{kpi['cor']};">{kpi['valor']}</div>
      <div class="kpi-delta">{kpi['delta']} <span class="kpi-period">vs ano anterior</span></div>
    </div>"""


def gerar_dashboard_html() -> str:
    figs = {
        "tl1": _fig_to_div(fig_timeline_obesidade(), "tl1"),
        "tl2": _fig_to_div(fig_timeline_imc(), "tl2"),
        "m1": _fig_to_div(fig_mensal_atendimentos(), "m1"),
        "m2": _fig_to_div(fig_mensal_distribuicao(), "m2"),
        "m3": _fig_to_div(fig_mensal_regioes(), "m3"),
        "disp": _fig_to_div(fig_dispersao(), "disp"),
        "hist": _fig_to_div(fig_histograma(), "hist"),
        "mapa": _fig_to_div(fig_mapa(), "mapa"),
        "funil": _fig_to_div(fig_funil(), "funil"),
        "tab1": _fig_to_div(fig_tabela_regioes(), "tab1"),
        "tab2": _fig_to_div(fig_tabela_faixas(), "tab2"),
        "candle": _fig_to_div(fig_candlestick(), "candle"),
        "water": _fig_to_div(fig_waterfall(), "water"),
        "polar": _fig_to_div(fig_polar(), "polar"),
    }
    kpis_html = "\n".join(_kpi_card(k) for k in BIG_NUMBERS)
    data_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    return f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<title>NeveStudio - Dashboard Saúde Brasil</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
    background: #f1f5f9;
    color: #0f172a;
    min-height: 100vh;
  }}

  /* ===== NAVBAR ===== */
  .navbar {{
    background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 60%, #4338ca 100%);
    color: white;
    padding: 18px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 6px 20px rgba(15, 23, 42, 0.18);
    position: sticky;
    top: 0;
    z-index: 50;
    border-bottom: 1px solid rgba(255,255,255,0.08);
  }}
  .nav-brand {{ display: flex; align-items: center; gap: 14px; }}
  .nav-logo {{
    width: 42px; height: 42px;
    background: linear-gradient(135deg, #38bdf8, #6366f1);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    color: white;
    box-shadow: 0 4px 14px rgba(56, 189, 248, 0.45);
  }}
  .nav-logo svg {{ width: 26px; height: 26px; display: block; }}
  .nav-name {{ font-size: 20px; font-weight: 700; letter-spacing: -0.3px; }}
  .nav-links {{ display: flex; gap: 6px; }}
  .nav-links a {{
    color: rgba(255,255,255,0.78);
    text-decoration: none;
    font-size: 13px; font-weight: 500;
    padding: 8px 14px; border-radius: 8px;
    transition: background .15s, color .15s;
  }}
  .nav-links a:hover {{
    background: rgba(255,255,255,0.10);
    color: white;
  }}
  .nav-meta {{
    text-align: right; font-size: 12px;
    color: rgba(255,255,255,0.78);
    line-height: 1.5;
  }}
  .nav-meta b {{ color: white; font-weight: 600; }}

  /* ===== CONTEÚDO ===== */
  .dashboard {{ max-width: 1680px; margin: 0 auto; padding: 24px 28px 40px; }}

  .page-title {{
    font-size: 22px; font-weight: 700; color: #0f172a;
    margin-bottom: 4px; letter-spacing: -0.4px;
  }}
  .page-sub {{ font-size: 13px; color: #64748b; margin-bottom: 22px; }}

  .grid {{ display: grid; gap: 16px; }}
  .kpi-row {{ grid-template-columns: repeat(5, 1fr); margin-bottom: 16px; }}
  .kpi-card {{
    background: white; border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 1px 3px rgba(15,23,42,0.06), 0 1px 2px rgba(15,23,42,0.04);
    transition: transform .15s, box-shadow .15s;
  }}
  .kpi-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(15,23,42,0.10);
  }}
  .kpi-title {{ font-size: 12px; color: #64748b; font-weight: 600;
                text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }}
  .kpi-value {{ font-size: 28px; font-weight: 700; line-height: 1.2; letter-spacing: -0.5px; }}
  .kpi-delta {{ font-size: 12px; color: #10b981; margin-top: 6px; font-weight: 600; }}
  .kpi-period {{ color: #94a3b8; font-weight: 400; margin-left: 4px; }}

  .row-2  {{ grid-template-columns: 1fr 1fr; margin-bottom: 16px; }}
  .row-3  {{ grid-template-columns: 1.2fr 1fr 1.2fr; margin-bottom: 16px; }}
  .row-3e {{ grid-template-columns: 1fr 1fr 1fr; margin-bottom: 16px; }}

  .chart-card {{
    background: white; border-radius: 12px;
    padding: 8px;
    box-shadow: 0 1px 3px rgba(15,23,42,0.06), 0 1px 2px rgba(15,23,42,0.04);
    min-height: 380px;
  }}
  .chart-card.tall {{ min-height: 460px; }}
  .chart-card .js-plotly-plot {{ width: 100% !important; }}

  .section-title {{
    font-size: 13px; font-weight: 700; color: #475569;
    text-transform: uppercase; letter-spacing: 0.8px;
    margin: 22px 0 10px; padding-left: 4px;
    border-left: 3px solid #6366f1;
    padding: 4px 0 4px 10px;
  }}

  .footer {{
    text-align: center; color: #94a3b8;
    font-size: 12px; margin-top: 28px; padding: 12px;
  }}

  @media (max-width: 1200px) {{
    .kpi-row {{ grid-template-columns: repeat(3, 1fr); }}
    .row-2, .row-3, .row-3e {{ grid-template-columns: 1fr; }}
    .navbar {{ flex-direction: column; gap: 12px; align-items: flex-start; }}
    .nav-links {{ flex-wrap: wrap; }}
  }}
  @media (max-width: 700px) {{
    .kpi-row {{ grid-template-columns: 1fr 1fr; }}
  }}
</style>
</head>
<body>

  <nav class="navbar">
    <div class="nav-brand">
      <div class="nav-logo">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2v20"/>
          <path d="M2 12h20"/>
          <path d="M4.93 4.93l14.14 14.14"/>
          <path d="M19.07 4.93L4.93 19.07"/>
          <path d="M12 4l-2 2M12 4l2 2"/>
          <path d="M12 20l-2-2M12 20l2-2"/>
          <path d="M4 12l2-2M4 12l2 2"/>
          <path d="M20 12l-2-2M20 12l-2 2"/>
        </svg>
      </div>
      <div>
        <span class="nav-name">NeveStudio</span>
      </div>
    </div>
    <div class="nav-links">
      <a href="#kpis">Visão geral</a>
      <a href="#timelines">Tendências</a>
      <a href="#mensais">Mensais</a>
      <a href="#analise">Análise</a>
      <a href="#tabelas">Tabelas</a>
      <a href="#avancados">Avançados</a>
    </div>
    <div class="nav-meta">
      <div><b>Dashboard Saúde Brasil</b></div>
      <div>Atualizado em {data_str}</div>
    </div>
  </nav>

  <div class="dashboard">
    <div class="page-title">Dashboard Saúde Brasil — Sobrepeso e Obesidade</div>
    <div class="page-sub">Indicadores de saúde populacional · Faixa etária 20–60 anos · Dados fictícios</div>

    <div id="kpis" class="section-title">Indicadores principais</div>
    <div class="grid kpi-row">{kpis_html}</div>

    <div id="timelines" class="section-title">Tendências anuais</div>
    <div class="grid row-2">
      <div class="chart-card">{figs['tl1']}</div>
      <div class="chart-card">{figs['tl2']}</div>
    </div>

    <div id="mensais" class="section-title">Análises mensais</div>
    <div class="grid row-3">
      <div class="chart-card">{figs['m1']}</div>
      <div class="chart-card">{figs['m2']}</div>
      <div class="chart-card">{figs['m3']}</div>
    </div>

    <div id="analise" class="section-title">Análise estatística e geográfica</div>
    <div class="grid row-3e">
      <div class="chart-card">{figs['disp']}</div>
      <div class="chart-card">{figs['hist']}</div>
      <div class="chart-card tall">{figs['mapa']}</div>
    </div>

    <div class="grid row-2">
      <div class="chart-card">{figs['funil']}</div>
      <div class="chart-card">{figs['polar']}</div>
    </div>

    <div id="tabelas" class="section-title">Tabelas dinâmicas</div>
    <div class="grid row-2">
      <div class="chart-card">{figs['tab1']}</div>
      <div class="chart-card">{figs['tab2']}</div>
    </div>

    <div id="avancados" class="section-title">Indicadores avançados</div>
    <div class="grid row-2">
      <div class="chart-card tall">{figs['candle']}</div>
      <div class="chart-card tall">{figs['water']}</div>
    </div>

    <div class="footer">
      NeveStudio Analytics · Gerado com Python + Plotly · Dados meramente ilustrativos
    </div>
  </div>
</body>
</html>
"""


def abrir_dashboard() -> str:
    html = gerar_dashboard_html()
    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix=".html", prefix="nevestudio_dashboard_",
        mode="w", encoding="utf-8")
    tmp.write(html)
    tmp.close()
    webbrowser.open("file://" + os.path.abspath(tmp.name))
    return tmp.name


# ---------------------------------------------------------------------------
# Interface gráfica
# ---------------------------------------------------------------------------
class NeveStudioApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("NeveStudio")
        self.geometry("560x500")
        self.configure(bg="#f1f5f9")
        self.resizable(False, False)
        self._build_ui()

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TLabel", background="#f1f5f9", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"),
                        background="#f1f5f9", foreground="#1e3a8a")
        style.configure("Sub.TLabel", font=("Segoe UI", 10),
                        background="#f1f5f9", foreground="#64748b")
        style.configure("Big.TButton", font=("Segoe UI", 11, "bold"), padding=12)
        style.configure("TLabelframe", background="#f1f5f9")
        style.configure("TLabelframe.Label", background="#f1f5f9",
                        font=("Segoe UI", 10, "bold"))

        ttk.Label(self, text="NeveStudio",
                  style="Title.TLabel").pack(pady=(24, 0))
        ttk.Label(self, text="Gerador de dashboards interativos com Plotly",
                  style="Sub.TLabel").pack(pady=(0, 18))

        frame = ttk.Labelframe(self, text="Dashboard disponível", padding=18)
        frame.pack(fill="x", padx=25, pady=8)

        ttk.Label(
            frame,
            text="Saúde Brasil — Sobrepeso e Obesidade\n\n"
                 "Componentes:\n"
                 "  - 5 Big Numbers (KPIs)\n"
                 "  - 2 Gráficos de linha do tempo\n"
                 "  - 3 Gráficos com dados mensais\n"
                 "  - 1 Gráfico de dispersão\n"
                 "  - 1 Histograma\n"
                 "  - 1 Mapa coroplético do Brasil\n"
                 "  - 1 Gráfico de funil\n"
                 "  - 2 Tabelas dinâmicas\n"
                 "  - 1 Gráfico de candlestick\n"
                 "  - 1 Waterfall chart\n"
                 "  - 1 Polar chart",
            justify="left",
        ).pack(anchor="w", pady=(0, 14))

        ttk.Button(
            frame, text="Gerar Dashboard",
            style="Big.TButton", command=self._on_gerar,
        ).pack(fill="x")

        self.status = ttk.Label(
            self, text="Pronto. O dashboard será aberto no navegador.",
            style="Sub.TLabel")
        self.status.pack(side="bottom", pady=14)

    def _on_gerar(self) -> None:
        try:
            self.status.config(text="Gerando dashboard...")
            self.update_idletasks()
            caminho = abrir_dashboard()
            self.status.config(
                text=f"Dashboard aberto: {os.path.basename(caminho)}")
        except Exception as exc:  # noqa: BLE001
            self.status.config(text="Erro ao gerar dashboard.")
            messagebox.showerror("Erro ao gerar dashboard", str(exc))


if __name__ == "__main__":
    NeveStudioApp().mainloop()
