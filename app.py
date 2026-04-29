"""
NeveStudio - Gerador de Dashboards interativos com Plotly
Interface Tkinter -> gera dashboard HTML (estático) com filtros globais
que recomputam todos os gráficos via Plotly.js no navegador.

Tema: Saúde / Obesidade no Brasil (dados fictícios).
"""

from __future__ import annotations

import json
import os
import random
import tempfile
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# DADOS FICTÍCIOS
# ---------------------------------------------------------------------------
random.seed(42)

MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
         "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
ANOS = list(range(2018, 2026))
REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
SEXOS = ["Homens", "Mulheres"]
FAIXAS = ["20-29", "30-39", "40-49", "50-60"]

# Séries anuais por sexo (total, por sexo)
SERIES_ANUAIS = {
    "obesidade": {
        "Homens":   [16.9, 17.7, 18.6, 19.8, 21.0, 21.9, 22.7, 23.5],
        "Mulheres": [18.6, 19.4, 20.3, 21.5, 22.7, 23.6, 24.5, 25.6],
    },
    "sobrepeso": {
        "Homens":   [53.0, 53.8, 55.0, 55.9, 56.8, 57.6, 58.2, 58.9],
        "Mulheres": [51.2, 52.1, 53.4, 54.1, 55.0, 55.8, 56.4, 57.2],
    },
    "imc": {
        "Homens":   [26.4, 26.6, 26.8, 26.9, 27.1, 27.2, 27.3, 27.5],
        "Mulheres": [25.9, 26.1, 26.3, 26.5, 26.8, 27.0, 27.1, 27.2],
    },
}

# Atendimentos mensais por região (2025)
ATENDIMENTOS_MENSAIS_REG = {
    "Norte":        [620, 660, 700, 690, 730, 760, 790, 760, 740, 800, 820, 850],
    "Nordeste":     [1820, 1900, 2010, 1960, 2080, 2180, 2270, 2160, 2120, 2310, 2380, 2520],
    "Centro-Oeste": [880, 920, 990, 970, 1030, 1080, 1110, 1080, 1040, 1140, 1170, 1210],
    "Sudeste":      [4180, 4360, 4720, 4570, 4900, 5100, 5290, 5070, 4940, 5410, 5500, 5760],
    "Sul":          [1610, 1690, 1810, 1750, 1860, 1940, 2020, 1940, 1900, 2080, 2120, 2210],
}

# Distribuição IMC por região (proporções, soma ~100)
DIST_CATEGORIAS_REG = {
    "labels": ["Peso normal", "Sobrepeso", "Obesidade I",
               "Obesidade II", "Obesidade III"],
    "cores":  ["#10b981", "#fde68a", "#fb923c", "#ef4444", "#991b1b"],
    "por_regiao": {
        "Norte":        [42.1, 33.8, 14.2, 6.9, 3.0],
        "Nordeste":     [40.0, 33.5, 15.1, 7.5, 3.9],
        "Centro-Oeste": [38.4, 33.4, 16.0, 8.0, 4.2],
        "Sudeste":      [37.5, 34.0, 16.5, 7.8, 4.2],
        "Sul":          [36.2, 34.2, 17.2, 8.0, 4.4],
    },
}

# População por região (em milhares avaliados)
POP_REGIAO = {"Norte": 8420, "Nordeste": 23710, "Centro-Oeste": 11280,
              "Sudeste": 51640, "Sul": 19340}

CORES_REGIAO = {"Norte": "#60a5fa", "Nordeste": "#a78bfa",
                "Centro-Oeste": "#fde68a", "Sudeste": "#fb923c",
                "Sul": "#10b981"}

# Dispersão por sexo (para permitir filtro)
def _disp(n: int, mean_imc: float) -> list[dict]:
    return [{"imc": random.gauss(mean_imc, 4),
             "horas": max(0, random.gauss(3.5, 2.5))} for _ in range(n)]

DISPERSAO_SEXO = {"Homens": _disp(120, 27.4), "Mulheres": _disp(120, 26.9)}

# Histograma por sexo
HIST_SEXO = {
    "Homens":   [random.gauss(27.4, 4.1) for _ in range(1500)],
    "Mulheres": [random.gauss(26.9, 4.3) for _ in range(1500)],
}

# Mapa por estado (com região)
MAPA_ESTADOS = [
    ("AC", "Norte", 22.1), ("AP", "Norte", 21.8), ("AM", "Norte", 22.9),
    ("PA", "Norte", 23.7), ("RO", "Norte", 23.4), ("RR", "Norte", 21.5),
    ("TO", "Norte", 23.6),
    ("AL", "Nordeste", 25.4), ("BA", "Nordeste", 24.6), ("CE", "Nordeste", 23.5),
    ("MA", "Nordeste", 24.9), ("PB", "Nordeste", 24.1), ("PE", "Nordeste", 25.3),
    ("PI", "Nordeste", 23.9), ("RN", "Nordeste", 24.5), ("SE", "Nordeste", 24.7),
    ("DF", "Centro-Oeste", 26.3), ("GO", "Centro-Oeste", 27.1),
    ("MT", "Centro-Oeste", 26.4), ("MS", "Centro-Oeste", 25.2),
    ("ES", "Sudeste", 25.8), ("MG", "Sudeste", 26.8), ("RJ", "Sudeste", 26.9),
    ("SP", "Sudeste", 26.1),
    ("PR", "Sul", 27.5), ("RS", "Sul", 28.2), ("SC", "Sul", 27.8),
]

# Funil por região (proporcional)
FUNIL_BASE = {"Cadastros": 1.00, "Triagem": 0.75, "Avaliação clínica": 0.56,
              "Plano nutricional": 0.38, "Acompanhamento ativo": 0.24}

# Tabela 2 (faixas etárias)
TABELA_FAIXAS_DATA = {
    "20-29": {"pacientes": 24310, "imc": 25.4, "sobrepeso": 48.2, "obesidade": 16.1},
    "30-39": {"pacientes": 31870, "imc": 26.8, "sobrepeso": 55.7, "obesidade": 22.4},
    "40-49": {"pacientes": 35620, "imc": 27.9, "sobrepeso": 60.3, "obesidade": 27.8},
    "50-60": {"pacientes": 36650, "imc": 28.4, "sobrepeso": 63.1, "obesidade": 31.5},
}

# Candlestick (índice diário)
def _gerar_candles(n: int = 30) -> list[dict]:
    base = datetime(2026, 4, 1)
    out = []
    preco = 72.0
    for i in range(n):
        o = preco
        c = o + random.uniform(-1.8, 1.9)
        h = max(o, c) + random.uniform(0.2, 1.2)
        lo = min(o, c) - random.uniform(0.2, 1.2)
        out.append({"data": (base + timedelta(days=i)).strftime("%Y-%m-%d"),
                    "open": round(o, 2), "high": round(h, 2),
                    "low": round(lo, 2), "close": round(c, 2)})
        preco = c
    return out

CANDLES = _gerar_candles()

# Waterfall (composição de custo por região - escala simples)
WATERFALL_BASE = {
    "Atendimentos": 380, "Medicamentos": 210, "Internações": 290,
    "Cirurgias bariátricas": 150, "Programas preventivos": -750,
}
BASE_2024 = 4520

# Polar por sexo
POLAR = {
    "categorias": ["Alimentação", "Atividade física", "Sono",
                   "Hidratação", "Estresse", "Acompanhamento médico"],
    "Homens":   [62, 55, 70, 58, 48, 41],
    "Mulheres": [71, 49, 66, 67, 52, 58],
}


# ---------------------------------------------------------------------------
# Empacotar dados para JS
# ---------------------------------------------------------------------------
def montar_payload() -> dict:
    return {
        "anos": ANOS,
        "meses": MESES,
        "regioes": REGIOES,
        "sexos": SEXOS,
        "faixas": FAIXAS,
        "cores_regiao": CORES_REGIAO,
        "pop_regiao": POP_REGIAO,
        "series_anuais": SERIES_ANUAIS,
        "atend_mensais_reg": ATENDIMENTOS_MENSAIS_REG,
        "dist_categorias": DIST_CATEGORIAS_REG,
        "dispersao_sexo": DISPERSAO_SEXO,
        "hist_sexo": HIST_SEXO,
        "mapa_estados": [{"uf": uf, "regiao": r, "obesidade": v}
                         for uf, r, v in MAPA_ESTADOS],
        "funil_base": FUNIL_BASE,
        "tabela_faixas": TABELA_FAIXAS_DATA,
        "candles": CANDLES,
        "waterfall_base": WATERFALL_BASE,
        "base_2024": BASE_2024,
        "polar": POLAR,
    }


# ---------------------------------------------------------------------------
# Geração do HTML do dashboard
# ---------------------------------------------------------------------------
def gerar_dashboard_html() -> str:
    payload_json = json.dumps(montar_payload(), ensure_ascii=False)
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
  body {{ font-family: 'Inter','Segoe UI',Arial,sans-serif; background:#f1f5f9;
         color:#0f172a; min-height:100vh; }}

  /* NAVBAR */
  .navbar {{ background: linear-gradient(135deg,#0f172a 0%,#1e3a8a 60%,#4338ca 100%);
    color:white; padding:18px 32px; display:flex; align-items:center;
    justify-content:space-between; box-shadow:0 6px 20px rgba(15,23,42,.18);
    position:sticky; top:0; z-index:50;
    border-bottom:1px solid rgba(255,255,255,.08); }}
  .nav-brand {{ display:flex; align-items:center; gap:14px; }}
  .nav-logo {{ width:42px; height:42px;
    background:linear-gradient(135deg,#38bdf8,#6366f1); border-radius:12px;
    display:flex; align-items:center; justify-content:center; color:white;
    box-shadow:0 4px 14px rgba(56,189,248,.45); }}
  .nav-logo svg {{ width:26px; height:26px; display:block; }}
  .nav-name {{ font-size:20px; font-weight:700; letter-spacing:-.3px; }}
  .nav-links {{ display:flex; gap:6px; }}
  .nav-links a {{ color:rgba(255,255,255,.78); text-decoration:none;
    font-size:13px; font-weight:500; padding:8px 14px; border-radius:8px;
    transition:background .15s,color .15s; }}
  .nav-links a:hover {{ background:rgba(255,255,255,.1); color:white; }}
  .nav-meta {{ text-align:right; font-size:12px;
    color:rgba(255,255,255,.78); line-height:1.5; }}
  .nav-meta b {{ color:white; font-weight:600; }}

  .dashboard {{ max-width:1680px; margin:0 auto; padding:24px 28px 40px; }}
  .page-title {{ font-size:22px; font-weight:700; color:#0f172a;
    margin-bottom:4px; letter-spacing:-.4px; }}
  .page-sub {{ font-size:13px; color:#64748b; margin-bottom:18px; }}

  /* FILTROS */
  .filters {{ background:white; border-radius:12px; padding:16px 20px;
    box-shadow:0 1px 3px rgba(15,23,42,.06); margin-bottom:18px;
    display:flex; flex-wrap:wrap; gap:18px; align-items:flex-end; }}
  .filter-group {{ display:flex; flex-direction:column; gap:6px; }}
  .filter-group label {{ font-size:11px; font-weight:700; color:#475569;
    text-transform:uppercase; letter-spacing:.5px; }}
  .filter-group select, .filter-group input[type=range] {{
    background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px;
    padding:8px 10px; font-family:inherit; font-size:13px; color:#0f172a;
    min-width:160px; outline:none; transition:border-color .15s; }}
  .filter-group select:focus {{ border-color:#6366f1; }}
  .filter-group select[multiple] {{ min-height:88px; }}
  .filter-actions {{ display:flex; gap:8px; margin-left:auto; }}
  .btn {{ background:#6366f1; color:white; border:none; border-radius:8px;
    padding:10px 18px; font-family:inherit; font-size:13px; font-weight:600;
    cursor:pointer; transition:background .15s,transform .1s; }}
  .btn:hover {{ background:#4f46e5; }}
  .btn:active {{ transform:scale(.97); }}
  .btn.ghost {{ background:#f1f5f9; color:#475569; }}
  .btn.ghost:hover {{ background:#e2e8f0; }}
  .filter-hint {{ width:100%; font-size:11px; color:#94a3b8;
    margin-top:-4px; }}

  /* GRID */
  .grid {{ display:grid; gap:16px; }}
  .kpi-row {{ grid-template-columns:repeat(5,1fr); margin-bottom:16px; }}
  .kpi-card {{ background:white; border-radius:12px; padding:18px 20px;
    box-shadow:0 1px 3px rgba(15,23,42,.06); transition:transform .15s,box-shadow .15s;
    border-top:4px solid #6366f1; }}
  .kpi-card:hover {{ transform:translateY(-2px);
    box-shadow:0 10px 25px rgba(15,23,42,.1); }}
  .kpi-title {{ font-size:12px; color:#64748b; font-weight:600;
    text-transform:uppercase; letter-spacing:.5px; margin-bottom:8px; }}
  .kpi-value {{ font-size:28px; font-weight:700; line-height:1.2;
    letter-spacing:-.5px; color:#0f172a; }}
  .kpi-delta {{ font-size:12px; color:#10b981; margin-top:6px; font-weight:600; }}
  .kpi-period {{ color:#94a3b8; font-weight:400; margin-left:4px; }}

  .row-2  {{ grid-template-columns:1fr 1fr; margin-bottom:16px; }}
  .row-3  {{ grid-template-columns:1.2fr 1fr 1.2fr; margin-bottom:16px; }}
  .row-3e {{ grid-template-columns:1fr 1fr 1fr; margin-bottom:16px; }}

  .chart-card {{ background:white; border-radius:12px; padding:8px;
    box-shadow:0 1px 3px rgba(15,23,42,.06); min-height:380px; }}
  .chart-card.tall {{ min-height:460px; }}
  .chart-card .js-plotly-plot {{ width:100% !important; }}

  .section-title {{ font-size:13px; font-weight:700; color:#475569;
    text-transform:uppercase; letter-spacing:.8px; margin:22px 0 10px;
    border-left:3px solid #6366f1; padding:4px 0 4px 10px; }}

  .footer {{ text-align:center; color:#94a3b8; font-size:12px;
    margin-top:28px; padding:12px; }}

  @media (max-width:1200px) {{
    .kpi-row {{ grid-template-columns:repeat(3,1fr); }}
    .row-2,.row-3,.row-3e {{ grid-template-columns:1fr; }}
    .navbar {{ flex-direction:column; gap:12px; align-items:flex-start; }}
    .nav-links {{ flex-wrap:wrap; }}
  }}
  @media (max-width:700px) {{ .kpi-row {{ grid-template-columns:1fr 1fr; }} }}
</style>
</head>
<body>

<nav class="navbar">
  <div class="nav-brand">
    <div class="nav-logo">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2v20"/><path d="M2 12h20"/>
        <path d="M4.93 4.93l14.14 14.14"/><path d="M19.07 4.93L4.93 19.07"/>
        <path d="M12 4l-2 2M12 4l2 2"/><path d="M12 20l-2-2M12 20l2-2"/>
        <path d="M4 12l2-2M4 12l2 2"/><path d="M20 12l-2-2M20 12l-2 2"/>
      </svg>
    </div>
    <div><span class="nav-name">NeveStudio</span></div>
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
  <div class="filters">
    <div class="filter-group">
      <label>Ano inicial</label>
      <select id="f-ano-ini"></select>
    </div>
    <div class="filter-group">
      <label>Ano final</label>
      <select id="f-ano-fim"></select>
    </div>
    <div class="filter-group">
      <label>Sexo</label>
      <select id="f-sexo">
        <option value="Todos">Todos</option>
        <option value="Homens">Homens</option>
        <option value="Mulheres">Mulheres</option>
      </select>
    </div>
    <div class="filter-group">
      <label>Região</label>
      <select id="f-regiao">
        <option value="Todas">Todas</option>
      </select>
    </div>
    <div class="filter-group">
      <label>Faixa etária</label>
      <select id="f-faixa">
        <option value="Todas">Todas</option>
        <option value="20-29">20-29</option>
        <option value="30-39">30-39</option>
        <option value="40-49">40-49</option>
        <option value="50-60">50-60</option>
      </select>
    </div>
    <div class="filter-actions">
      <button class="btn ghost" id="btn-reset">Limpar</button>
      <button class="btn" id="btn-apply">Aplicar filtros</button>
    </div>
    <div class="filter-hint">Os filtros são aplicados a todos os gráficos do dashboard simultaneamente.</div>
  </div>

  <div id="kpis" class="section-title">Indicadores principais</div>
  <div class="grid kpi-row" id="kpi-row"></div>

  <div id="timelines" class="section-title">Tendências anuais</div>
  <div class="grid row-2">
    <div class="chart-card"><div id="tl1" style="height:380px;"></div></div>
    <div class="chart-card"><div id="tl2" style="height:380px;"></div></div>
  </div>

  <div id="mensais" class="section-title">Análises mensais</div>
  <div class="grid row-3">
    <div class="chart-card"><div id="m1" style="height:380px;"></div></div>
    <div class="chart-card"><div id="m2" style="height:380px;"></div></div>
    <div class="chart-card"><div id="m3" style="height:380px;"></div></div>
  </div>

  <div id="analise" class="section-title">Análise estatística e geográfica</div>
  <div class="grid row-3e">
    <div class="chart-card"><div id="disp" style="height:380px;"></div></div>
    <div class="chart-card"><div id="hist" style="height:380px;"></div></div>
    <div class="chart-card tall"><div id="mapa" style="height:460px;"></div></div>
  </div>

  <div class="grid row-2">
    <div class="chart-card"><div id="funil" style="height:380px;"></div></div>
    <div class="chart-card"><div id="polar" style="height:380px;"></div></div>
  </div>

  <div id="tabelas" class="section-title">Tabelas dinâmicas</div>
  <div class="grid row-2">
    <div class="chart-card"><div id="tab1" style="height:380px;"></div></div>
    <div class="chart-card"><div id="tab2" style="height:380px;"></div></div>
  </div>

  <div id="avancados" class="section-title">Indicadores avançados</div>
  <div class="grid row-2">
    <div class="chart-card tall"><div id="candle" style="height:460px;"></div></div>
    <div class="chart-card tall"><div id="water" style="height:460px;"></div></div>
  </div>

  <div class="footer">NeveStudio · Gerado com Python + Plotly · Dados meramente ilustrativos</div>
</div>

<script id="payload" type="application/json">{payload_json}</script>
<script>
const DATA = JSON.parse(document.getElementById('payload').textContent);

// ===== Estado dos filtros =====
const state = {{
  anoIni: DATA.anos[0],
  anoFim: DATA.anos[DATA.anos.length - 1],
  sexo: 'Todos',
  regioes: [...DATA.regioes],
  faixa: 'Todas',
}};

// ===== Layout base =====
const baseLayout = (title) => ({{
  title: {{text: title, x: 0.02, xanchor: 'left',
           font: {{size: 15, color: '#1e293b'}}}},
  template: 'plotly_white',
  font: {{family: 'Inter, Segoe UI, Arial', size: 12, color: '#1e293b'}},
  margin: {{l: 50, r: 25, t: 55, b: 50}},
  paper_bgcolor: 'white', plot_bgcolor: 'white',
  legend: {{orientation: 'h', y: -0.18, x: 0.5, xanchor: 'center'}},
  xaxis: {{showgrid: false, linecolor: '#e2e8f0'}},
  yaxis: {{gridcolor: '#f1f5f9', linecolor: '#e2e8f0'}},
}});

const config = {{displaylogo: false, responsive: true,
                modeBarButtonsToRemove: ['lasso2d', 'select2d']}};

// ===== Helpers =====
function anosFiltrados() {{
  return DATA.anos.filter(a => a >= state.anoIni && a <= state.anoFim);
}}
function indicesAnos() {{
  return DATA.anos.map((a, i) => [a, i])
    .filter(([a]) => a >= state.anoIni && a <= state.anoFim)
    .map(([, i]) => i);
}}
function sexosAtivos() {{
  return state.sexo === 'Todos' ? DATA.sexos : [state.sexo];
}}
function regioesAtivas() {{
  return state.regioes.length ? state.regioes : DATA.regioes;
}}
function fmtBR(n) {{
  return n.toLocaleString('pt-BR', {{maximumFractionDigits: 1}});
}}

// ===== KPIs =====
function calcKPIs() {{
  const idx = indicesAnos();
  const sexos = sexosAtivos();
  const regs = regioesAtivas();
  const fator = state.faixa === 'Todas' ? 1
    : DATA.tabela_faixas[state.faixa].pacientes /
      Object.values(DATA.tabela_faixas).reduce((s, v) => s + v.pacientes, 0);

  const popTotal = regs.reduce((s, r) => s + DATA.pop_regiao[r], 0);
  const populacao = Math.round(popTotal * fator);

  // IMC médio (último ano filtrado, média entre sexos)
  const ultimoIdx = idx[idx.length - 1];
  const imcMed = sexos.reduce((s, sx) =>
      s + DATA.series_anuais.imc[sx][ultimoIdx], 0) / sexos.length;

  // Taxa obesidade média do período
  let somaObes = 0, count = 0;
  sexos.forEach(sx => idx.forEach(i => {{
    somaObes += DATA.series_anuais.obesidade[sx][i]; count++;
  }}));
  const taxaObes = somaObes / count;

  const atividade = state.sexo === 'Homens' ? 32.4
                  : state.sexo === 'Mulheres' ? 41.2 : 37.1;

  // Custo SUS proporcional à população filtrada
  const popPctTotal = popTotal / Object.values(DATA.pop_regiao)
    .reduce((s, v) => s + v, 0);
  const custo = (4.8 * popPctTotal * fator);

  return [
    {{titulo: 'População avaliada', valor: fmtBR(populacao),
      delta: '+4,2%', cor: '#3b82f6'}},
    {{titulo: 'IMC médio', valor: imcMed.toFixed(1).replace('.', ','),
      delta: '+0,5', cor: '#f59e0b'}},
    {{titulo: 'Taxa de obesidade', valor: taxaObes.toFixed(1).replace('.', ',') + '%',
      delta: '+1,8 p.p.', cor: '#ef4444'}},
    {{titulo: 'Atividade física regular', valor: atividade.toFixed(1).replace('.', ',') + '%',
      delta: '+2,4 p.p.', cor: '#10b981'}},
    {{titulo: 'Custo SUS estimado', valor: 'R$ ' + custo.toFixed(2).replace('.', ',') + ' bi',
      delta: '+6,1%', cor: '#8b5cf6'}},
  ];
}}

function renderKPIs() {{
  const html = calcKPIs().map(k => `
    <div class="kpi-card" style="border-top:4px solid ${{k.cor}};">
      <div class="kpi-title">${{k.titulo}}</div>
      <div class="kpi-value" style="color:${{k.cor}};">${{k.valor}}</div>
      <div class="kpi-delta">${{k.delta}} <span class="kpi-period">vs ano anterior</span></div>
    </div>`).join('');
  document.getElementById('kpi-row').innerHTML = html;
}}

// ===== Gráficos =====
function plotTimelineObesidade() {{
  const xs = anosFiltrados();
  const idx = indicesAnos();
  const sexos = sexosAtivos();
  const med = (key) => idx.map((i, k) => sexos.reduce((s, sx) =>
      s + DATA.series_anuais[key][sx][i], 0) / sexos.length);
  const traces = [
    {{x: xs, y: med('obesidade'), mode: 'lines+markers', name: 'Obesidade (%)',
      line: {{color: '#ef4444', width: 3}}, marker: {{size: 8}},
      fill: 'tozeroy', fillcolor: 'rgba(239,68,68,0.10)'}},
    {{x: xs, y: med('sobrepeso'), mode: 'lines+markers', name: 'Sobrepeso (%)',
      line: {{color: '#f59e0b', width: 3}}, marker: {{size: 8}}}},
  ];
  Plotly.react('tl1', traces,
    baseLayout('Evolução anual: Sobrepeso e Obesidade'), config);
}}

function plotTimelineIMC() {{
  const xs = anosFiltrados();
  const idx = indicesAnos();
  const cores = {{Homens: '#3b82f6', Mulheres: '#ec4899'}};
  const traces = sexosAtivos().map(sx => ({{
    x: xs, y: idx.map(i => DATA.series_anuais.imc[sx][i]),
    mode: 'lines+markers', name: sx,
    line: {{color: cores[sx], width: 3}}, marker: {{size: 8}},
  }}));
  Plotly.react('tl2', traces,
    baseLayout('IMC médio por sexo (kg/m²)'), config);
}}

function plotMensalAtendimentos() {{
  const regs = regioesAtivas();
  const fator = state.faixa === 'Todas' ? 1
    : DATA.tabela_faixas[state.faixa].pacientes /
      Object.values(DATA.tabela_faixas).reduce((s, v) => s + v.pacientes, 0);
  const totais = DATA.meses.map((_, m) =>
    Math.round(regs.reduce((s, r) =>
      s + DATA.atend_mensais_reg[r][m], 0) * fator));
  const trace = {{
    x: DATA.meses, y: totais, type: 'bar', marker: {{color: '#3b82f6'}},
    text: totais.map(v => (v / 1000).toFixed(1) + 'k'),
    textposition: 'outside',
    hovertemplate: '<b>%{{x}}</b><br>%{{y:,}} atendimentos<extra></extra>',
  }};
  const layout = baseLayout('Atendimentos mensais (2025)');
  layout.showlegend = false;
  Plotly.react('m1', [trace], layout, config);
}}

function plotMensalDistribuicao() {{
  const regs = regioesAtivas();
  const valores = DATA.dist_categorias.labels.map((_, i) => {{
    const soma = regs.reduce((s, r) =>
      s + DATA.dist_categorias.por_regiao[r][i] * DATA.pop_regiao[r], 0);
    const peso = regs.reduce((s, r) => s + DATA.pop_regiao[r], 0);
    return +(soma / peso).toFixed(1);
  }});
  const trace = {{
    type: 'pie', labels: DATA.dist_categorias.labels, values: valores,
    hole: 0.55,
    marker: {{colors: DATA.dist_categorias.cores,
              line: {{color: 'white', width: 2}}}},
    textinfo: 'percent',
    hovertemplate: '<b>%{{label}}</b><br>%{{value}}%<extra></extra>',
  }};
  Plotly.react('m2', [trace],
    baseLayout('Distribuição por categoria de IMC'), config);
}}

function plotMensalRegioes() {{
  const regs = regioesAtivas();
  const fator = state.faixa === 'Todas' ? 1
    : DATA.tabela_faixas[state.faixa].pacientes /
      Object.values(DATA.tabela_faixas).reduce((s, v) => s + v.pacientes, 0);
  // soma do mês mais recente
  const dados = regs.map(r => ({{
    regiao: r,
    valor: Math.round(DATA.atend_mensais_reg[r][11] * fator),
    cor: DATA.cores_regiao[r],
  }})).sort((a, b) => a.valor - b.valor);
  const trace = {{
    type: 'bar', orientation: 'h',
    x: dados.map(d => d.valor),
    y: dados.map(d => d.regiao),
    marker: {{color: dados.map(d => d.cor)}},
    text: dados.map(d => d.valor.toLocaleString('pt-BR')),
    textposition: 'outside',
    hovertemplate: '<b>%{{y}}</b><br>%{{x:,}} atendimentos<extra></extra>',
  }};
  const layout = baseLayout('Atendimentos por região (mês atual)');
  layout.showlegend = false;
  Plotly.react('m3', [trace], layout, config);
}}

function plotDispersao() {{
  const sexos = sexosAtivos();
  const cores = {{Homens: '#3b82f6', Mulheres: '#ec4899'}};
  const traces = sexos.map(sx => ({{
    type: 'scatter', mode: 'markers', name: sx,
    x: DATA.dispersao_sexo[sx].map(p => p.horas),
    y: DATA.dispersao_sexo[sx].map(p => p.imc),
    marker: {{size: 8, color: cores[sx], opacity: 0.7,
              line: {{width: 0.5, color: 'white'}}}},
    hovertemplate: 'Atividade: %{{x:.1f}} h/sem<br>IMC: %{{y:.1f}}<extra></extra>',
  }}));
  const layout = baseLayout('Dispersão: Atividade física x IMC');
  layout.xaxis.title = {{text: 'Horas de atividade física / semana'}};
  layout.yaxis.title = {{text: 'IMC (kg/m²)'}};
  Plotly.react('disp', traces, layout, config);
}}

function plotHistograma() {{
  const sexos = sexosAtivos();
  const cores = {{Homens: '#3b82f6', Mulheres: '#ec4899'}};
  const traces = sexos.map(sx => ({{
    type: 'histogram', x: DATA.hist_sexo[sx], name: sx,
    nbinsx: 40, opacity: 0.65,
    marker: {{color: cores[sx]}},
  }}));
  const layout = baseLayout('Histograma de IMC da amostra');
  layout.barmode = 'overlay';
  layout.xaxis.title = {{text: 'IMC (kg/m²)'}};
  layout.yaxis.title = {{text: 'Frequência'}};
  Plotly.react('hist', traces, layout, config);
}}

function plotMapa() {{
  const regs = regioesAtivas();
  const ativos = DATA.mapa_estados.filter(e => regs.includes(e.regiao));
  const trace = {{
    type: 'choropleth',
    locations: ativos.map(e => e.uf),
    z: ativos.map(e => e.obesidade),
    locationmode: 'geojson-id',
    geojson: 'https://raw.githubusercontent.com/codeforgermany/click_that_hood/main/public/data/brazil-states.geojson',
    featureidkey: 'properties.sigla',
    colorscale: [[0, '#dbeafe'], [0.5, '#f59e0b'], [1, '#991b1b']],
    colorbar: {{title: 'Obesidade %', thickness: 12, len: 0.75}},
    marker: {{line: {{color: 'white', width: 0.6}}}},
    hovertemplate: '<b>%{{location}}</b><br>Obesidade: %{{z}}%<extra></extra>',
  }};
  const layout = baseLayout('Prevalência de obesidade por estado (Brasil)');
  layout.geo = {{fitbounds: 'locations', visible: false, bgcolor: 'white'}};
  Plotly.react('mapa', [trace], layout, config);
}}

function plotFunil() {{
  const regs = regioesAtivas();
  const fator = state.faixa === 'Todas' ? 1
    : DATA.tabela_faixas[state.faixa].pacientes /
      Object.values(DATA.tabela_faixas).reduce((s, v) => s + v.pacientes, 0);
  const popTotal = regs.reduce((s, r) => s + DATA.pop_regiao[r], 0) * fator;
  const etapas = Object.keys(DATA.funil_base);
  const valores = etapas.map(e => Math.round(popTotal * DATA.funil_base[e]));
  const trace = {{
    type: 'funnel', y: etapas, x: valores,
    textinfo: 'value+percent initial',
    marker: {{color: ['#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#ec4899']}},
    connector: {{line: {{color: '#cbd5e1', width: 1}}}},
  }};
  Plotly.react('funil', [trace],
    baseLayout('Funil de jornada do paciente'), config);
}}

function plotPolar() {{
  const sexos = sexosAtivos();
  const coresLine = {{Homens: '#3b82f6', Mulleres: '#ec4899', Mulheres: '#ec4899'}};
  const coresFill = {{Homens: 'rgba(59,130,246,0.25)',
                     Mulheres: 'rgba(236,72,153,0.25)'}};
  const cats = DATA.polar.categorias.concat([DATA.polar.categorias[0]]);
  const traces = sexos.map(sx => ({{
    type: 'scatterpolar', name: sx,
    r: DATA.polar[sx].concat([DATA.polar[sx][0]]),
    theta: cats, fill: 'toself',
    line: {{color: coresLine[sx]}}, fillcolor: coresFill[sx],
  }}));
  const layout = baseLayout('Adesão a hábitos saudáveis (%)');
  layout.polar = {{bgcolor: 'white',
    radialaxis: {{visible: true, range: [0, 100], gridcolor: '#e2e8f0'}},
    angularaxis: {{gridcolor: '#e2e8f0'}}}};
  Plotly.react('polar', traces, layout, config);
}}

function plotTabelaRegioes() {{
  const regs = regioesAtivas();
  const idx = indicesAnos();
  const ultimoIdx = idx[idx.length - 1];
  const imcMed = (DATA.series_anuais.imc.Homens[ultimoIdx] +
                  DATA.series_anuais.imc.Mulheres[ultimoIdx]) / 2;
  const linhas = regs.map(r => {{
    const dist = DATA.dist_categorias.por_regiao[r];
    const obes = (dist[2] + dist[3] + dist[4]).toFixed(1);
    return [r, DATA.pop_regiao[r].toLocaleString('pt-BR'),
            (imcMed + (Math.random() * 0.4 - 0.2)).toFixed(1).replace('.', ','),
            obes.replace('.', ',') + '%', '+1,8 p.p.'];
  }});
  const cols = [0, 1, 2, 3, 4].map(c => linhas.map(l => l[c]));
  const trace = {{
    type: 'table',
    header: {{values: ['<b>Região</b>', '<b>População</b>', '<b>IMC médio</b>',
                       '<b>Obesidade %</b>', '<b>Variação</b>'],
              fill: {{color: '#1e293b'}},
              font: {{color: 'white', size: 12, family: 'Inter, Segoe UI'}},
              align: 'left', height: 34}},
    cells: {{values: cols,
             fill: {{color: [linhas.map((_, i) => i % 2 ? 'white' : '#f8fafc')]}},
             font: {{color: '#1e293b', size: 12}},
             align: 'left', height: 30}},
  }};
  Plotly.react('tab1', [trace], {{
    title: {{text: 'Indicadores por região', x: 0.02, xanchor: 'left',
             font: {{size: 15, color: '#1e293b'}}}},
    margin: {{l: 10, r: 10, t: 55, b: 10}}, paper_bgcolor: 'white',
  }}, config);
}}

function plotTabelaFaixas() {{
  const faixas = state.faixa === 'Todas' ? DATA.faixas : [state.faixa];
  const linhas = faixas.map(f => {{
    const d = DATA.tabela_faixas[f];
    return [f + ' anos', d.pacientes.toLocaleString('pt-BR'),
            d.imc.toFixed(1).replace('.', ','),
            d.sobrepeso.toFixed(1).replace('.', ',') + '%',
            d.obesidade.toFixed(1).replace('.', ',') + '%'];
  }});
  const cols = [0, 1, 2, 3, 4].map(c => linhas.map(l => l[c]));
  const trace = {{
    type: 'table',
    header: {{values: ['<b>Faixa etária</b>', '<b>Pacientes</b>',
                       '<b>IMC médio</b>', '<b>Sobrepeso %</b>', '<b>Obesidade %</b>'],
              fill: {{color: '#1e293b'}},
              font: {{color: 'white', size: 12, family: 'Inter, Segoe UI'}},
              align: 'left', height: 34}},
    cells: {{values: cols,
             fill: {{color: [linhas.map((_, i) => i % 2 ? 'white' : '#f8fafc')]}},
             font: {{color: '#1e293b', size: 12}},
             align: 'left', height: 30}},
  }};
  Plotly.react('tab2', [trace], {{
    title: {{text: 'Indicadores por faixa etária', x: 0.02, xanchor: 'left',
             font: {{size: 15, color: '#1e293b'}}}},
    margin: {{l: 10, r: 10, t: 55, b: 10}}, paper_bgcolor: 'white',
  }}, config);
}}

function plotCandlestick() {{
  const trace = {{
    type: 'candlestick',
    x: DATA.candles.map(c => c.data),
    open: DATA.candles.map(c => c.open),
    high: DATA.candles.map(c => c.high),
    low: DATA.candles.map(c => c.low),
    close: DATA.candles.map(c => c.close),
    increasing: {{line: {{color: '#10b981'}}}},
    decreasing: {{line: {{color: '#ef4444'}}}},
    name: 'Índice',
  }};
  const layout = baseLayout('Índice diário de saúde populacional');
  layout.showlegend = false;
  layout.xaxis.rangeslider = {{visible: false}};
  layout.yaxis.title = {{text: 'Pontos'}};
  Plotly.react('candle', [trace], layout, config);
}}

function plotWaterfall() {{
  const regs = regioesAtivas();
  const popPct = regs.reduce((s, r) => s + DATA.pop_regiao[r], 0) /
    Object.values(DATA.pop_regiao).reduce((s, v) => s + v, 0);
  const labels = ['Base 2024', ...Object.keys(DATA.waterfall_base), 'Total 2025'];
  const measure = ['absolute',
    ...Object.keys(DATA.waterfall_base).map(() => 'relative'), 'total'];
  const valores = [Math.round(DATA.base_2024 * popPct),
    ...Object.values(DATA.waterfall_base).map(v => Math.round(v * popPct)), 0];
  const trace = {{
    type: 'waterfall', x: labels, measure, y: valores,
    text: valores.map((v, i) =>
      i === valores.length - 1 ? '' : ('R$ ' + v + 'M')),
    textposition: 'outside',
    connector: {{line: {{color: '#cbd5e1'}}}},
    increasing: {{marker: {{color: '#ef4444'}}}},
    decreasing: {{marker: {{color: '#10b981'}}}},
    totals: {{marker: {{color: '#3b82f6'}}}},
  }};
  const layout = baseLayout('Composição do custo estimado SUS (R$ mi)');
  layout.yaxis.title = {{text: 'R$ (milhões)'}};
  Plotly.react('water', [trace], layout, config);
}}

// ===== Renderização =====
function renderAll() {{
  renderKPIs();
  plotTimelineObesidade(); plotTimelineIMC();
  plotMensalAtendimentos(); plotMensalDistribuicao(); plotMensalRegioes();
  plotDispersao(); plotHistograma(); plotMapa();
  plotFunil(); plotPolar();
  plotTabelaRegioes(); plotTabelaFaixas();
  plotCandlestick(); plotWaterfall();
}}

// ===== Setup filtros =====
function setupFilters() {{
  const ini = document.getElementById('f-ano-ini');
  const fim = document.getElementById('f-ano-fim');
  DATA.anos.forEach(a => {{
    ini.add(new Option(a, a));
    fim.add(new Option(a, a));
  }});
  ini.value = state.anoIni;
  fim.value = state.anoFim;

  const regSel = document.getElementById('f-regiao');
  DATA.regioes.forEach(r => regSel.add(new Option(r, r)));

  document.getElementById('btn-apply').addEventListener('click', () => {{
    state.anoIni = +ini.value;
    state.anoFim = +fim.value;
    if (state.anoIni > state.anoFim) {{
      [state.anoIni, state.anoFim] = [state.anoFim, state.anoIni];
      ini.value = state.anoIni; fim.value = state.anoFim;
    }}
    state.sexo = document.getElementById('f-sexo').value;
    const r = regSel.value;
    state.regioes = r === 'Todas' ? [...DATA.regioes] : [r];
    state.faixa = document.getElementById('f-faixa').value;
    renderAll();
  }});

  document.getElementById('btn-reset').addEventListener('click', () => {{
    state.anoIni = DATA.anos[0];
    state.anoFim = DATA.anos[DATA.anos.length - 1];
    state.sexo = 'Todos';
    state.regioes = [...DATA.regioes];
    state.faixa = 'Todas';
    ini.value = state.anoIni; fim.value = state.anoFim;
    document.getElementById('f-sexo').value = 'Todos';
    document.getElementById('f-faixa').value = 'Todas';
    regSel.value = 'Todas';
    renderAll();
  }});
}}

setupFilters();
renderAll();
window.addEventListener('resize', () => {{
  ['tl1','tl2','m1','m2','m3','disp','hist','mapa','funil','polar',
   'tab1','tab2','candle','water'].forEach(id => Plotly.Plots.resize(id));
}});
</script>

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
        self.geometry("560x520")
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
                 "  - Filtros globais (ano, sexo, regiões, faixa etária)\n"
                 "  - 5 Big Numbers (KPIs)\n"
                 "  - 2 Gráficos de linha do tempo\n"
                 "  - 3 Gráficos com dados mensais\n"
                 "  - 1 Dispersão, 1 Histograma\n"
                 "  - 1 Mapa coroplético do Brasil\n"
                 "  - 1 Funil, 1 Polar chart\n"
                 "  - 2 Tabelas dinâmicas\n"
                 "  - 1 Candlestick, 1 Waterfall",
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
