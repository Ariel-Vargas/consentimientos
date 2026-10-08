"""
generate_dashboard.py
---------------------
Procesa consent.csv y genera un dashboard HTML estatico listo para GitHub Pages.

Uso:
    python generate_dashboard.py

Salida:
    index.html  -- dashboard completo con los datos embebidos
    style.css   -- estilos del dashboard
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

# ── Configuracion ──────────────────────────────────────────────────────────────
CSV_FILE    = Path(__file__).with_name("consent.csv")
OUTPUT_HTML = Path(__file__).with_name("index.html")
OUTPUT_CSS  = Path(__file__).with_name("style.css")

ESTADOS_ORDEN = ["ACEPTADO", "RECHAZADO", "PENDIENTE"]
CANAL_VACIO   = "SIN CANAL"

# ── Procesamiento ──────────────────────────────────────────────────────────────
def procesar_csv(csv_path: Path) -> dict:
    print(f"Leyendo {csv_path} ...")

    # Detectar encoding
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with open(csv_path, encoding=enc, newline="") as f:
                f.read(1024)
            encoding = enc
            break
        except Exception:
            continue

    print(f"  Encoding detectado: {encoding}")

    fcte = defaultdict(int)
    fce = defaultdict(set)
    fc = defaultdict(set)
    canales_set = set()
    tipos_map   = {}   # tipo_id -> nombre_visible
    fechas_set  = set()
    estados_set = set()
    todos_usuarios = set()
    total_filas = 0

    with open(csv_path, encoding=encoding, newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            canal   = (row.get("canal_origen") or CANAL_VACIO).strip()
            tipo_id = row.get("tipo_consentimiento", "").strip()
            nombre  = row.get("nombre_visible", "").strip()
            estado  = row.get("estado_actual", "").strip()
            usuario = row.get("usuario", "").strip()
            fecha   = row.get("fecha", "")[:10].strip()

            if not nombre or not estado or not usuario:
                continue

            tipos_map[tipo_id] = nombre
            canales_set.add(canal)
            fechas_set.add(fecha)
            estados_set.add(estado)
            todos_usuarios.add(usuario)

            fcte[(fecha, canal, nombre, estado)] += 1
            fce[(fecha, canal, estado)].add(usuario)
            fc[(fecha, canal)].add(usuario)
            total_filas += 1

    print(f"  Filas procesadas: {total_filas:,}")
    return {
        "fcte": fcte,
        "fce": fce,
        "fc": fc,
        "canales": sorted(canales_set),
        "tipos_map": tipos_map,
        "fechas": sorted(fechas_set),
        "estados_set": estados_set,
        "todos_usuarios": todos_usuarios,
        "total_filas": total_filas,
    }


def construir_datos(raw: dict) -> dict:
    fcte = raw["fcte"]
    fce = raw["fce"]
    fc = raw["fc"]
    canales = raw["canales"]
    tipos_map = raw["tipos_map"]
    fechas = raw["fechas"]
    estados_set = raw["estados_set"]
    todos_usuarios = raw["todos_usuarios"]
    total_filas = raw["total_filas"]

    consentimientos = sorted(set(tipos_map.values()))

    estados = [e for e in ESTADOS_ORDEN if e in estados_set]
    estados += sorted(estados_set - set(ESTADOS_ORDEN))

    records = [{"f": k[0], "c": k[1], "t": k[2], "e": k[3], "n": v} for k, v in fcte.items()]
    users_fce = [{"f": k[0], "c": k[1], "e": k[2], "n": len(v)} for k, v in fce.items()]
    users_fc = [{"f": k[0], "c": k[1], "n": len(v)} for k, v in fc.items()]

    kpis = {
        "total_usuarios": len(todos_usuarios),
        "total_registros": total_filas,
        "canales": len(canales),
        "consentimientos": len(consentimientos),
        "fecha_inicio": fechas[0] if fechas else "",
        "fecha_fin":    fechas[-1] if fechas else "",
    }

    return {
        "canales": canales,
        "consentimientos": consentimientos,
        "estados": estados,
        "fechas": fechas,
        "records": records,
        "users_fce": users_fce,
        "users_fc": users_fc,
        "kpis": kpis,
    }


# ── CSS ────────────────────────────────────────────────────────────────────────
CSS = r"""
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:         #0d1117;
  --bg2:        #161b22;
  --bg3:        #21262d;
  --border:     #30363d;
  --text:       #e6edf3;
  --muted:      #8b949e;
  --blue:       #388bfd;
  --blue-bg:    #1f3464;
  --purple:     #bc8cff;
  --purple-bg:  #3a1f6e;
  --teal:       #39d353;
  --teal-bg:    #0d3320;
  --orange:     #f78166;
  --orange-bg:  #5c2018;
  --green:      #3fb950;
  --red:        #f85149;
  --yellow:     #e3b341;
  --radius:     10px;
  --shadow:     0 4px 24px rgba(0,0,0,.45);
  --trans:      .18s ease;
}

html { scroll-behavior: smooth; }
body {
  font-family: "Inter", system-ui, sans-serif;
  background: var(--bg); color: var(--text);
  min-height: 100vh; font-size: 14px; line-height: 1.5;
}

/* HEADER */
.header {
  background: linear-gradient(135deg,#0d1b2a,#162032,#0d1b2a);
  border-bottom: 1px solid var(--border);
  padding: 20px 32px;
  position: sticky; top: 0; z-index: 200;
  backdrop-filter: blur(12px);
}
.header-inner { max-width:1600px; margin:0 auto; display:flex; align-items:center; gap:14px; }
.header-logo {
  width:44px; height:44px; flex-shrink:0;
  background: linear-gradient(135deg,var(--blue),var(--purple));
  border-radius:10px; display:grid; place-items:center; color:#fff;
  box-shadow:0 0 18px rgba(56,139,253,.35);
}
.header-logo svg { width:22px; height:22px; }
.header-title {
  font-size:1.35rem; font-weight:700;
  background: linear-gradient(90deg,#e6edf3,var(--blue));
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}
.header-sub { color:var(--muted); font-size:.82rem; margin-top:2px; }

/* KPIs */
.kpis {
  display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr));
  gap:14px; max-width:1600px; margin:22px auto; padding:0 22px;
}
.kpi-card {
  border-radius:var(--radius); padding:18px 20px;
  display:flex; align-items:center; gap:14px;
  border:1px solid var(--border);
  transition:transform var(--trans),box-shadow var(--trans);
}
.kpi-card:hover { transform:translateY(-3px); box-shadow:var(--shadow); }
.kpi-blue   { background:var(--blue-bg);   border-color:#1d3b6e; }
.kpi-purple { background:var(--purple-bg); border-color:#4a2888; }
.kpi-teal   { background:var(--teal-bg);   border-color:#1a4d2e; }
.kpi-orange { background:var(--orange-bg); border-color:#7a2e1a; }
.kpi-icon  { font-size:1.9rem; line-height:1; }
.kpi-body  { display:flex; flex-direction:column; }
.kpi-value { font-size:1.5rem; font-weight:700; }
.kpi-label { font-size:.72rem; color:var(--muted); margin-top:2px; }

/* FILTROS */
.filters-bar {
  background:var(--bg2); border-top:1px solid var(--border);
  border-bottom:1px solid var(--border);
  padding:12px 22px; position:sticky; top:85px; z-index:100;
}
.filters-inner {
  max-width:1600px; margin:0 auto;
  display:flex; flex-wrap:wrap; gap:10px; align-items:flex-end;
}
.filter-group { display:flex; flex-direction:column; gap:3px; }
.filter-group label { font-size:.7rem; color:var(--muted); text-transform:uppercase; letter-spacing:.05em; font-weight:600; }
.filter-group select, .filter-group input[type="date"] {
  background:var(--bg3); border:1px solid var(--border); color:var(--text);
  padding:7px 10px; border-radius:6px; font-size:.84rem; cursor:pointer;
  transition:border-color var(--trans); min-width:160px; font-family:inherit;
}
.filter-group select { appearance:none; padding-right:28px;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%238b949e' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat:no-repeat; background-position:right 8px center; }
.filter-group select:focus, .filter-group input:focus { outline:none; border-color:var(--blue); }
.btn-reset {
  background:transparent; border:1px solid var(--border); color:var(--muted);
  padding:7px 14px; border-radius:6px; cursor:pointer; font-size:.84rem;
  transition:all var(--trans); align-self:flex-end;
}
.btn-reset:hover { background:var(--bg3); color:var(--text); border-color:var(--blue); }

/* MAIN */
.main { max-width:1600px; margin:0 auto; padding:22px; display:flex; flex-direction:column; gap:22px; }

/* SECCIONES */
.section {
  background:var(--bg2); border:1px solid var(--border);
  border-radius:var(--radius); overflow:hidden; box-shadow:var(--shadow);
}
.section-title {
  padding:14px 18px; font-size:.9rem; font-weight:600;
  border-bottom:1px solid var(--border);
  display:flex; align-items:center; gap:8px;
}
.section-title span { color:var(--muted); font-size:.8rem; font-weight:400; }
.charts-grid { display:grid; grid-template-columns:1fr 1fr; gap:0; }
.chart-panel { padding:16px; position:relative; }
.chart-panel + .chart-panel { border-left:1px solid var(--border); }
.chart-canvas-wrap { position:relative; height:300px; }

/* TABLA */
.table-wrapper { overflow:auto; }
table { border-collapse:collapse; width:100%; white-space:nowrap; }
th {
  background:var(--bg3); padding:10px 14px; font-weight:600;
  font-size:.75rem; text-transform:uppercase; letter-spacing:.04em;
  color:var(--muted); border-bottom:1px solid var(--border);
  border-right:1px solid var(--border); position:sticky; top:0; z-index:5;
}
th:last-child { border-right:none; }
.th-estado { text-align:center; }
.th-sub { font-size:.7rem; font-weight:500; padding:5px 14px; background:var(--bg2); }
.est-aceptado  { color:var(--green);  border-top:3px solid var(--green); }
.est-rechazado { color:var(--red);    border-top:3px solid var(--red); }
.est-pendiente { color:var(--yellow); border-top:3px solid var(--yellow); }
.estado-badge { display:inline-flex; align-items:center; gap:4px; font-size:.78rem; font-weight:700; }
td {
  padding:8px 14px; border-bottom:1px solid var(--border);
  border-right:1px solid var(--border); vertical-align:middle;
}
td:last-child { border-right:none; }
.tr-even { background:var(--bg2); } .tr-odd { background:var(--bg); }
tr:hover td { background:rgba(56,139,253,.07); }
.td-canal { text-align:center; }
.canal-badge {
  display:inline-block; background:var(--bg3); border:1px solid var(--border);
  border-radius:20px; padding:2px 10px; font-size:.73rem; font-weight:600;
  letter-spacing:.04em; color:var(--blue);
}
.td-consent { max-width:260px; white-space:normal; word-break:break-word; }
.td-count   { text-align:right; font-variant-numeric:tabular-nums; font-weight:500; }
.td-total   { text-align:right; font-weight:700; }
.td-pct     { min-width:110px; }
.pct-bar-wrap { display:flex; align-items:center; gap:6px; }
.pct-bar { height:6px; border-radius:3px; min-width:1px; transition:width .3s; }
.pct-bar.est-aceptado  { background:var(--green); }
.pct-bar.est-rechazado { background:var(--red); }
.pct-bar.est-pendiente { background:var(--yellow); }
.pct-bar.est-default   { background:var(--blue); }
.pct-label { font-size:.76rem; color:var(--muted); }
.empty-msg { text-align:center; padding:48px; color:var(--muted); }

/* FOOTER */
.footer { text-align:center; padding:18px; color:var(--muted); font-size:.76rem; border-top:1px solid var(--border); margin-top:10px; }
.footer code { background:var(--bg3); padding:2px 6px; border-radius:4px; }

/* RESPONSIVE */
@media(max-width:900px) {
  .charts-grid { grid-template-columns:1fr; }
  .chart-panel + .chart-panel { border-left:none; border-top:1px solid var(--border); }
}
@media(max-width:640px) {
  .kpis { grid-template-columns:1fr 1fr; }
  .filters-inner { flex-direction:column; }
  .filter-group select, .filter-group input { min-width:100%; }
  .main { padding:12px; }
}
"""


# ── HTML ────────────────────────────────────────────────────────────────────────
def generar_html(datos: dict) -> str:
    json_str = json.dumps(datos, ensure_ascii=False, separators=(",", ":"))
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <meta name="description" content="Dashboard de consentimientos: usuarios unicos por canal, tipo y estado con graficos interactivos."/>
  <title>Dashboard de Consentimientos</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>
  <link rel="stylesheet" href="style.css"/>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
</head>
<body>

<!-- HEADER -->
<header class="header">
  <div class="header-inner">
    <div class="header-logo">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
    </div>
    <div>
      <h1 class="header-title">Dashboard de Consentimientos</h1>
      <p class="header-sub">Usuarios unicos &middot; Canal &middot; Tipo de consentimiento &middot; Estado</p>
    </div>
  </div>
</header>

<!-- KPIs -->
<section class="kpis" id="kpis" aria-label="Indicadores clave"></section>

<!-- FILTROS -->
<section class="filters-bar" aria-label="Filtros">
  <div class="filters-inner">
    <div class="filter-group">
      <label for="f-fecha-ini">Fecha desde</label>
      <input type="date" id="f-fecha-ini"/>
    </div>
    <div class="filter-group">
      <label for="f-fecha-fin">Fecha hasta</label>
      <input type="date" id="f-fecha-fin"/>
    </div>
    <div class="filter-group">
      <label for="f-canal">Canal</label>
      <select id="f-canal"><option value="">Todos los canales</option></select>
    </div>
    <div class="filter-group">
      <label for="f-consent">Consentimiento</label>
      <select id="f-consent"><option value="">Todos</option></select>
    </div>
    <button id="btn-reset" class="btn-reset">&#8635; Limpiar</button>
  </div>
</section>

<!-- GRAFICOS -->
<main class="main">

  <!-- Linea + Barras -->
  <div class="section">
    <div class="section-title">
      📈 Evolucion de Usuarios por Estado
      <span>— usuarios unicos por dia</span>
    </div>
    <div class="charts-grid">
      <div class="chart-panel">
        <div class="section-title" style="border:none;padding:0 0 10px 0;font-size:.8rem;">Grafico de Linea</div>
        <div class="chart-canvas-wrap"><canvas id="chart-line"></canvas></div>
      </div>
      <div class="chart-panel">
        <div class="section-title" style="border:none;padding:0 0 10px 0;font-size:.8rem;">Grafico de Barras</div>
        <div class="chart-canvas-wrap"><canvas id="chart-bar"></canvas></div>
      </div>
    </div>
  </div>

  <!-- Barras por tipo de consentimiento -->
  <div class="section">
    <div class="section-title">
      📊 Distribucion por Tipo de Consentimiento y Estado
      <span>— usuarios unicos totales en rango filtrado</span>
    </div>
    <div class="chart-panel">
      <div class="chart-canvas-wrap" style="height:320px;"><canvas id="chart-tipo"></canvas></div>
    </div>
  </div>

  <!-- Tabla matriz -->
  <div class="section">
    <div class="section-title">
      📋 Matriz Canal x Consentimiento
      <span>— usuarios unicos y porcentaje por estado</span>
    </div>
    <div class="table-wrapper">
      <table id="tabla" aria-live="polite">
        <thead id="tabla-head"></thead>
        <tbody id="tabla-body"></tbody>
      </table>
    </div>
  </div>

</main>

<footer class="footer">
  <p>Generado desde <code>consent.csv</code></p>
</footer>

<script>
// ── Datos embebidos ────────────────────────────────────────────────────────────
const DATA = {json_str};

// ── Helpers ───────────────────────────────────────────────────────────────────
const esc  = s => String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
const fmt  = n => Number(n).toLocaleString("es");
const ECLS = {{ ACEPTADO:"est-aceptado", RECHAZADO:"est-rechazado", PENDIENTE:"est-pendiente" }};
const EICO = {{ ACEPTADO:"✔", RECHAZADO:"✖", PENDIENTE:"⏳" }};
const ECOLOR = {{ ACEPTADO:"#3fb950", RECHAZADO:"#f85149", PENDIENTE:"#e3b341" }};
const ECOLORF= {{ ACEPTADO:"rgba(63,185,80,.15)", RECHAZADO:"rgba(248,81,73,.15)", PENDIENTE:"rgba(227,179,65,.15)" }};

// ── KPIs ──────────────────────────────────────────────────────────────────────
const KPI_DEFS = [
  {{label:"Usuarios Unicos",          key:"total_usuarios",  icon:"👥", cls:"kpi-blue"}},
  {{label:"Registros Totales",         key:"total_registros", icon:"📋", cls:"kpi-purple"}},
  {{label:"Canales",                   key:"canales",         icon:"📡", cls:"kpi-teal"}},
  {{label:"Tipos de Consentimiento",   key:"consentimientos", icon:"📄", cls:"kpi-orange"}},
];
function renderKPIs(kpis) {{
  const kpisEl = document.getElementById("kpis");
  kpisEl.innerHTML = KPI_DEFS.map(d => `
    <div class="kpi-card ${{d.cls}}">
      <span class="kpi-icon">${{d.icon}}</span>
      <div class="kpi-body">
        <span class="kpi-value">${{fmt(kpis[d.key] ?? 0)}}</span>
        <span class="kpi-label">${{d.label}}</span>
      </div>
    </div>`).join("");
}}

// ── Filtros ───────────────────────────────────────────────────────────────────
const fFechaIni = document.getElementById("f-fecha-ini");
const fFechaFin = document.getElementById("f-fecha-fin");
const fCanal    = document.getElementById("f-canal");
const fConsent  = document.getElementById("f-consent");

// Rangos de fecha por defecto
if (DATA.fechas.length) {{
  fFechaIni.min = fFechaIni.value = DATA.fechas[0];
  fFechaFin.max = fFechaFin.value = DATA.fechas[DATA.fechas.length-1];
  fFechaIni.max = DATA.fechas[DATA.fechas.length-1];
  fFechaFin.min = DATA.fechas[0];
}}

DATA.canales.forEach(c => fCanal.insertAdjacentHTML("beforeend",`<option value="${{esc(c)}}">${{esc(c)}}</option>`));
DATA.consentimientos.forEach(c => fConsent.insertAdjacentHTML("beforeend",`<option value="${{esc(c)}}">${{esc(c)}}</option>`));

[fFechaIni, fFechaFin, fCanal, fConsent].forEach(el => el.addEventListener("change", render));
document.getElementById("btn-reset").addEventListener("click", () => {{
  fFechaIni.value = DATA.fechas[0] || "";
  fFechaFin.value = DATA.fechas[DATA.fechas.length-1] || "";
  fCanal.value = ""; fConsent.value = "";
  render();
}});

// ── Charts ────────────────────────────────────────────────────────────────────
const CHART_DEFAULTS = {{
  responsive:true, maintainAspectRatio:false,
  plugins:{{ legend:{{ labels:{{ color:"#8b949e", font:{{family:"Inter",size:11}} }} }},
             tooltip:{{ backgroundColor:"#21262d", borderColor:"#30363d", borderWidth:1,
                        titleColor:"#e6edf3", bodyColor:"#8b949e" }} }},
  scales:{{
    x:{{ ticks:{{ color:"#8b949e", font:{{size:10}} }}, grid:{{ color:"rgba(48,54,61,.6)" }} }},
    y:{{ ticks:{{ color:"#8b949e", font:{{size:10}} }}, grid:{{ color:"rgba(48,54,61,.6)" }}, beginAtZero:true }}
  }}
}};

let chartLine, chartBar, chartTipo;

function destroyCharts() {{
  [chartLine, chartBar, chartTipo].forEach(c => c && c.destroy());
}}

function buildLineBar(fechasFilt, seriesFilt) {{
  // LINE
  const ctxL = document.getElementById("chart-line").getContext("2d");
  chartLine = new Chart(ctxL, {{
    type:"line",
    data:{{ labels: fechasFilt, datasets: DATA.estados.map(e => ({{
      label: e,
      data: fechasFilt.map(f => seriesFilt[f]?.[e] ?? 0),
      borderColor: ECOLOR[e] || "#388bfd",
      backgroundColor: ECOLORF[e] || "rgba(56,139,253,.1)",
      fill:true, tension:.3, pointRadius:3, pointHoverRadius:6,
      borderWidth:2,
    }})) }},
    options:{{
      ...CHART_DEFAULTS,
      scales:{{
        x:{{ ...CHART_DEFAULTS.scales.x,
             type:"category",
             ticks:{{ ...CHART_DEFAULTS.scales.x.ticks, maxRotation:45, maxTicksLimit:15 }} }},
        y:{{ ...CHART_DEFAULTS.scales.y }}
      }},
      interaction:{{ mode:"index", intersect:false }},
      plugins:{{ ...CHART_DEFAULTS.plugins }}
    }}
  }});

  // BAR
  const ctxB = document.getElementById("chart-bar").getContext("2d");
  chartBar = new Chart(ctxB, {{
    type:"bar",
    data:{{ labels: fechasFilt, datasets: DATA.estados.map(e => ({{
      label: e,
      data: fechasFilt.map(f => seriesFilt[f]?.[e] ?? 0),
      backgroundColor: ECOLORF[e] || "rgba(56,139,253,.5)",
      borderColor: ECOLOR[e] || "#388bfd",
      borderWidth:1, borderRadius:3,
    }})) }},
    options:{{
      ...CHART_DEFAULTS,
      scales:{{
        x:{{ ...CHART_DEFAULTS.scales.x, stacked:true,
             ticks:{{ ...CHART_DEFAULTS.scales.x.ticks, maxRotation:45, maxTicksLimit:15 }} }},
        y:{{ ...CHART_DEFAULTS.scales.y, stacked:true }}
      }},
      interaction:{{ mode:"index", intersect:false }},
      plugins:{{ ...CHART_DEFAULTS.plugins }}
    }}
  }});
}}

function buildTipo(tipoDataFilt, filtConsent) {{
  const tipos = filtConsent ? [filtConsent] : DATA.consentimientos;
  const ctxT  = document.getElementById("chart-tipo").getContext("2d");

  // Etiquetas cortas para el eje
  const labelShort = t => t.length > 30 ? t.substring(0,28)+"…" : t;

  chartTipo = new Chart(ctxT, {{
    type:"bar",
    data:{{
      labels: tipos.map(labelShort),
      datasets: DATA.estados.map(e => ({{
        label: e,
        data: tipos.map(t => tipoDataFilt[t]?.[e] ?? 0),
        backgroundColor: ECOLORF[e] || "rgba(56,139,253,.5)",
        borderColor: ECOLOR[e] || "#388bfd",
        borderWidth:1, borderRadius:4,
      }}))
    }},
    options:{{
      ...CHART_DEFAULTS,
      indexAxis:"y",
      scales:{{
        x:{{ ...CHART_DEFAULTS.scales.x, stacked:true }},
        y:{{ ...CHART_DEFAULTS.scales.y, stacked:true,
             ticks:{{ color:"#8b949e", font:{{size:10}}, autoSkip:false }} }}
      }},
      interaction:{{ mode:"index", intersect:false }},
      plugins:{{ ...CHART_DEFAULTS.plugins }}
    }}
  }});
}}

// ── Tabla ────────────────────────────────────────────────────────────────────
function renderTabla(rowsFilt, estados) {{
  const thead = document.getElementById("tabla-head");
  const tbody = document.getElementById("tabla-body");
  thead.innerHTML = "";

  const trh = document.createElement("tr");
  trh.innerHTML =
    `<th class="th-canal" rowspan="2">Canal</th>` +
    `<th class="th-consent" rowspan="2">Consentimiento</th>`;
  estados.forEach(e => {{
    trh.innerHTML += `<th colspan="2" class="th-estado ${{ECLS[e]||''}}">
      <span class="estado-badge">${{EICO[e]||''}} ${{esc(e)}}</span></th>`;
  }});
  trh.innerHTML += `<th class="th-total" rowspan="2">Total</th>`;
  thead.appendChild(trh);

  const trh2 = document.createElement("tr");
  estados.forEach(() => {{
    trh2.innerHTML += `<th class="th-sub">Usuarios</th><th class="th-sub">%</th>`;
  }});
  thead.appendChild(trh2);

  tbody.innerHTML = "";
  if (!rowsFilt.length) {{
    tbody.innerHTML=`<tr><td colspan="999" class="empty-msg">Sin resultados.</td></tr>`;
    return;
  }}
  rowsFilt.forEach((row,i) => {{
    const tr = document.createElement("tr");
    tr.className = i%2===0?"tr-even":"tr-odd";
    let h =
      `<td class="td-canal"><span class="canal-badge">${{esc(row.canal)}}</span></td>` +
      `<td class="td-consent">${{esc(row.consentimiento)}}</td>`;
    estados.forEach(e => {{
      const d = row[e]||{{count:0,pct:0}};
      const pcls = ECLS[e]||"est-default";
      h +=
        `<td class="td-count">${{fmt(d.count)}}</td>` +
        `<td class="td-pct"><div class="pct-bar-wrap">
           <div class="pct-bar ${{pcls}}" style="width:${{Math.min(d.pct,100)}}%"></div>
           <span class="pct-label">${{d.pct.toFixed(1)}}%</span>
         </div></td>`;
    }});
    h += `<td class="td-total">${{fmt(row.total)}}</td>`;
    tr.innerHTML = h;
    tbody.appendChild(tr);
  }});
}}

// ── Render principal ──────────────────────────────────────────────────────────
function render() {{
  const vFechaIni = fFechaIni.value;
  const vFechaFin = fFechaFin.value;
  const vCanal    = fCanal.value;
  const vConsent  = fConsent.value;

  // 1. Filtrar fechas para los graficos
  const fechasFilt = DATA.fechas.filter(f =>
    (!vFechaIni || f >= vFechaIni) && (!vFechaFin || f <= vFechaFin)
  );

  // 2. Filtrar registros atomicos segun todos los filtros activos
  const recordsFilt = DATA.records.filter(r => {{
    if (vFechaIni && r.f < vFechaIni) return false;
    if (vFechaFin && r.f > vFechaFin) return false;
    if (vCanal && r.c !== vCanal) return false;
    if (vConsent && r.t !== vConsent) return false;
    return true;
  }});

  // 3. Actualizar KPIs dinamicamente segun los filtros activos
  const totalRegistros = recordsFilt.reduce((acc, r) => acc + r.n, 0);
  let totalUsuarios = 0;
  if (vConsent) {{
    totalUsuarios = totalRegistros;
  }} else {{
    totalUsuarios = DATA.users_fc
      .filter(u => (!vFechaIni || u.f >= vFechaIni) && (!vFechaFin || u.f <= vFechaFin) && (!vCanal || u.c === vCanal))
      .reduce((acc, u) => acc + u.n, 0);
  }}
  const canalesUnicos = new Set(recordsFilt.map(r => r.c)).size;
  const consentUnicos = new Set(recordsFilt.map(r => r.t)).size;

  renderKPIs({{
    total_usuarios: totalUsuarios,
    total_registros: totalRegistros,
    canales: canalesUnicos,
    consentimientos: consentUnicos
  }});

  // 4. Series de tiempo por fecha y estado (Line y Bar charts)
  const seriesPorFecha = {{}};
  fechasFilt.forEach(f => {{
    seriesPorFecha[f] = {{}};
    DATA.estados.forEach(e => {{ seriesPorFecha[f][e] = 0; }});
  }});

  if (vConsent) {{
    recordsFilt.forEach(r => {{
      if (seriesPorFecha[r.f] && seriesPorFecha[r.f][r.e] !== undefined) {{
        seriesPorFecha[r.f][r.e] += r.n;
      }}
    }});
  }} else {{
    DATA.users_fce
      .filter(u => (!vFechaIni || u.f >= vFechaIni) && (!vFechaFin || u.f <= vFechaFin) && (!vCanal || u.c === vCanal))
      .forEach(u => {{
        if (seriesPorFecha[u.f] && seriesPorFecha[u.f][u.e] !== undefined) {{
          seriesPorFecha[u.f][u.e] += u.n;
        }}
      }});
  }}

  // 5. Totales por consentimiento (Horizontal Bar chart)
  const tiposAMostrar = vConsent ? [vConsent] : DATA.consentimientos;
  const tipoData = {{}};
  tiposAMostrar.forEach(t => {{
    tipoData[t] = {{}};
    DATA.estados.forEach(e => {{ tipoData[t][e] = 0; }});
  }});
  recordsFilt.forEach(r => {{
    if (tipoData[r.t] && tipoData[r.t][r.e] !== undefined) {{
      tipoData[r.t][r.e] += r.n;
    }}
  }});

  // 6. Matriz Canal x Consentimiento (Tabla filtrada por fecha, canal y consentimiento)
  const canalesTabla = vCanal ? [vCanal] : DATA.canales;
  const consentTabla = vConsent ? [vConsent] : DATA.consentimientos;

  const rowsFilt = [];
  canalesTabla.forEach(canal => {{
    consentTabla.forEach(t => {{
      const pairRecs = recordsFilt.filter(r => r.c === canal && r.t === t);
      const total = pairRecs.reduce((acc, r) => acc + r.n, 0);
      if (total === 0) return;

      const fila = {{ canal, consentimiento: t, total }};
      DATA.estados.forEach(e => {{
        const count = pairRecs.filter(r => r.e === e).reduce((acc, r) => acc + r.n, 0);
        const pct   = total > 0 ? Number(((count / total) * 100).toFixed(2)) : 0;
        fila[e] = {{ count, pct }};
      }});
      rowsFilt.push(fila);
    }});
  }});

  destroyCharts();
  buildLineBar(fechasFilt, seriesPorFecha);
  buildTipo(tipoData, vConsent);
  renderTabla(rowsFilt, DATA.estados);
}}

render();
</script>
</body>
</html>
"""


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    raw   = procesar_csv(CSV_FILE)
    datos = construir_datos(raw)

    print(f"Estados     : {datos['estados']}")
    print(f"Canales     : {datos['canales']}")
    print(f"Consents    : {len(datos['consentimientos'])}")
    print(f"Combinaciones: {len(datos['records'])}")
    print(f"Fechas      : {datos['fechas'][0]} -> {datos['fechas'][-1]}")
    print(f"KPIs        : {datos['kpis']}")

    OUTPUT_CSS.write_text(CSS, encoding="utf-8")
    print(f"\n[OK] CSS  -> {OUTPUT_CSS.resolve()}")

    html = generar_html(datos)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"[OK] HTML -> {OUTPUT_HTML.resolve()}")
    print("\nSube index.html + style.css a GitHub Pages.")
