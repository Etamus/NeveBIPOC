# NeveStudio

> Protótipo experimental para validar a futura integração de geração de dashboards interativos no projeto principal **NeveAI**.

NeveStudio é uma aplicação desktop (Python + Tkinter) que gera, com um clique, um **dashboard analítico completo** renderizado em HTML usando a biblioteca [Plotly](https://plotly.com/python/). O dashboard é aberto automaticamente no navegador padrão e funciona de forma totalmente offline depois de carregado (exceto o mapa coroplético, que busca o GeoJSON via CDN).

---
<img width="1895" height="860" alt="image" src="https://github.com/user-attachments/assets/fc941a25-a57e-4b52-a1bc-7504e86eb555" />

---

## Objetivo

Este repositório serve como **prova de conceito (PoC)** para o módulo de visualização de dados que será incorporado ao NeveAI. As metas do protótipo são:

- Validar o pipeline `dados fictícios → figuras Plotly → HTML standalone`.
- Definir um padrão visual (navbar, KPIs, grid responsivo) reutilizável pelo NeveAI.
- Testar a cobertura de tipos de gráfico que o módulo precisará suportar.
- Servir de referência para o futuro endpoint de geração de relatórios do NeveAI.

> Todos os dados exibidos são **fictícios** e gerados apenas para fins de demonstração visual.

---

## Funcionalidades

- Interface gráfica simples em Tkinter com botão único para gerar o dashboard.
- Dashboard estático HTML autossuficiente (Plotly carregado via CDN).
- Layout responsivo com grid CSS, navbar fixa e seções âncora.
- Tema visual baseado em paleta moderna (slate / indigo / cyan) e tipografia Inter.
- 14 visualizações distintas em uma única página.

### Componentes do dashboard

| Categoria              | Componente                                                    |
| ---------------------- | ------------------------------------------------------------- |
| Indicadores principais | 5 Big Numbers (KPIs)                                          |
| Tendências anuais      | 2 gráficos de linha do tempo                                  |
| Análises mensais       | 3 gráficos (barras verticais, rosquinha, barras horizontais)  |
| Análise estatística    | 1 dispersão, 1 histograma                                     |
| Análise geográfica     | 1 mapa coroplético do Brasil                                  |
| Jornada                | 1 funil                                                       |
| Comportamento          | 1 polar chart (radar)                                         |
| Tabelas                | 2 tabelas dinâmicas                                           |
| Indicadores avançados  | 1 candlestick, 1 waterfall                                    |

---

## Stack

- **Python 3.11+**
- **Tkinter** — interface desktop (já incluso no Python no Windows)
- **Plotly** — geração das figuras e do HTML interativo
- **HTML/CSS** — layout do dashboard (sem frameworks, apenas CSS Grid)

---

## Estrutura do projeto

```
NeveStudio/
├── app.py              # App Tkinter + montagem dos gráficos e do HTML
├── requirements.txt    # Dependências Python
└── README.md
```

> Toda a lógica está concentrada em [app.py](app.py) para manter o protótipo simples. Quando portado para o NeveAI, será dividido em módulos (`data/`, `charts/`, `templates/`, etc.).

---

## Instalação

```powershell
# (opcional) criar ambiente virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# instalar dependências
pip install -r requirements.txt
```

---

## Uso

```powershell
python app.py
```

1. A janela do **NeveStudio** será aberta.
2. Clique em **Gerar Dashboard**.
3. O dashboard HTML será salvo em uma pasta temporária e aberto automaticamente no navegador padrão.

---

## Roadmap (rumo à integração no NeveAI)

- [ ] Substituir dados fictícios por fontes reais consumidas pelo NeveAI.
- [ ] Extrair construção de figuras para um pacote `nevestudio.charts` reutilizável.
- [ ] Disponibilizar geração via API (FastAPI) para o frontend do NeveAI consumir.
- [ ] Suporte a temas (claro / escuro) configuráveis pelo usuário.
- [ ] Exportação para PDF / PNG dos dashboards gerados.
- [ ] Sistema de filtros interativos (período, região, faixa etária) sincronizando todos os gráficos.
- [ ] Internacionalização (PT-BR / EN-US).

---

## Status

**Protótipo / PoC** — não destinado a produção.  
A integração definitiva ocorrerá no repositório principal do **NeveAI**.

---

## Licença

Uso interno / experimental no contexto do projeto NeveAI.
