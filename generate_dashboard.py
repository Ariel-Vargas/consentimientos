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
  --bg:          #0a0f1d;
  --bg-gradient: radial-gradient(circle at 10% 12%, rgba(56, 189, 248, 0.08) 0%, transparent 40%),
                 radial-gradient(circle at 85% 18%, rgba(139, 92, 246, 0.08) 0%, transparent 40%),
                 radial-gradient(circle at 50% 80%, rgba(16, 185, 129, 0.05) 0%, transparent 50%),
                 #0a0f1d;
  --card-bg:     rgba(17, 28, 51, 0.85);
  --card-bg-sub: rgba(22, 36, 65, 0.75);
  --card-hover:  rgba(24, 40, 72, 0.95);
  --input-bg:    #101b33;
  --border:      rgba(148, 163, 184, 0.16);
  --border-focus:#38bdf8;
  --text:        #f8fafc;
  --text-sec:    #cbd5e1;
  --muted:       #94a3b8;
  --header-bg:   rgba(10, 16, 32, 0.88);

  /* Status Colors */
  --green:       #10b981;
  --green-glow:  rgba(16, 185, 129, 0.22);
  --green-border:rgba(16, 185, 129, 0.4);
  --green-bg:    rgba(16, 185, 129, 0.12);

  --red:         #f43f5e;
  --red-glow:    rgba(244, 63, 94, 0.22);
  --red-border:  rgba(244, 63, 94, 0.4);
  --red-bg:      rgba(244, 63, 94, 0.12);

  --yellow:      #f59e0b;
  --yellow-glow: rgba(245, 158, 11, 0.22);
  --yellow-border:rgba(245, 158, 11, 0.4);
  --yellow-bg:   rgba(245, 158, 11, 0.12);

  /* Accents */
  --cyan:        #38bdf8;
  --purple:      #a855f7;
  --indigo:      #6366f1;

  --radius:      12px;
  --shadow:      0 10px 25px -4px rgba(0, 0, 0, 0.45), 0 4px 10px -2px rgba(0, 0, 0, 0.3);
  --inner-glow:  inset 0 1px 0 rgba(255, 255, 255, 0.08);
  --trans:       0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

html { scroll-behavior: smooth; }
body {
  font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--bg-gradient);
  background-attachment: fixed;
  color: var(--text);
  min-height: 100vh;
  font-size: 14px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

/* HEADER */
.header {
  background: var(--header-bg);
  border-bottom: 1px solid var(--border);
  padding: 16px 32px;
  position: sticky; top: 0; z-index: 200;
  backdrop-filter: blur(16px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.header-inner {
  max-width: 1600px; margin: 0 auto;
  display: flex; align-items: center; justify-content: space-between;
}
.header-brand {
  display: flex; align-items: center; gap: 14px;
}
.header-logo {
  width: 44px; height: 44px; flex-shrink: 0;
  background: linear-gradient(135deg, #0ea5e9, #6366f1, #a855f7);
  border-radius: 12px; display: grid; place-items: center; color: #fff;
  box-shadow: 0 0 20px rgba(14, 165, 233, 0.45);
}
.header-logo svg { width: 24px; height: 24px; }
.header-title {
  font-size: 1.4rem; font-weight: 700; letter-spacing: -0.02em;
  background: linear-gradient(135deg, #ffffff 10%, #93c5fd 60%, #c084fc 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.header-sub { color: var(--muted); font-size: 0.8rem; margin-top: 1px; }
.header-badge {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.25);
  color: var(--cyan); padding: 5px 12px; border-radius: 20px; font-size: 0.78rem; font-weight: 600;
}
.header-badge::before {
  content: ""; width: 7px; height: 7px; border-radius: 50%;
  background: var(--cyan); box-shadow: 0 0 8px var(--cyan);
}

/* KPIs */
.kpis {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px; max-width: 1600px; margin: 24px auto 16px auto; padding: 0 24px;
}
.kpi-card {
  border-radius: var(--radius); padding: 18px 22px;
  display: flex; align-items: center; gap: 16px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  box-shadow: var(--shadow), var(--inner-glow);
  backdrop-filter: blur(12px);
  position: relative; overflow: hidden;
  transition: transform var(--trans), box-shadow var(--trans), border-color var(--trans);
}
.kpi-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 14px 30px -4px rgba(0, 0, 0, 0.55), var(--inner-glow);
}
.kpi-card::after {
  content: ""; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  opacity: 0.9;
}
.kpi-cyan::after   { background: linear-gradient(90deg, #38bdf8, transparent); }
.kpi-purple::after { background: linear-gradient(90deg, #c084fc, transparent); }
.kpi-green::after  { background: linear-gradient(90deg, #34d399, transparent); }
.kpi-amber::after  { background: linear-gradient(90deg, #fbbf24, transparent); }

.kpi-icon-wrap {
  width: 48px; height: 48px; border-radius: 12px;
  display: grid; place-items: center; flex-shrink: 0;
  transition: transform var(--trans);
}
.kpi-card:hover .kpi-icon-wrap { transform: scale(1.08); }
.kpi-cyan .kpi-icon-wrap   { background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }
.kpi-purple .kpi-icon-wrap { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }
.kpi-green .kpi-icon-wrap  { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
.kpi-amber .kpi-icon-wrap  { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }

.kpi-icon-wrap svg { width: 24px; height: 24px; }
.kpi-body { display: flex; flex-direction: column; }
.kpi-value {
  font-size: 1.65rem; font-weight: 700; letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums; line-height: 1.2;
}
.kpi-cyan .kpi-value   { color: #e0f2fe; }
.kpi-purple .kpi-value { color: #f3e8ff; }
.kpi-green .kpi-value  { color: #ecfdf5; }
.kpi-amber .kpi-value  { color: #fffbeb; }
.kpi-label { font-size: 0.74rem; color: var(--muted); margin-top: 3px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }

/* FILTROS BAR */
.filters-bar {
  background: rgba(14, 23, 44, 0.85);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  padding: 14px 24px; position: sticky; top: 77px; z-index: 100;
  backdrop-filter: blur(14px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}
.filters-inner {
  max-width: 1600px; margin: 0 auto;
  display: flex; flex-wrap: wrap; gap: 16px; align-items: flex-end;
}

.filter-group { display: flex; flex-direction: column; gap: 5px; }
.filter-group label {
  font-size: 0.69rem; color: var(--muted); text-transform: uppercase;
  letter-spacing: 0.06em; font-weight: 700;
}
.filter-group select {
  background-color: var(--input-bg);
  border: 1px solid #334e68;
  color: var(--text);
  padding: 7px 32px 7px 12px;
  border-radius: 6px;
  font-size: 0.84rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--trans);
  min-width: 140px;
  font-family: inherit;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
}
.filter-group select:hover {
  border-color: #4a6fa5;
  background-color: #14223d;
}
.filter-group select:focus {
  outline: none;
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2);
}

/* DATE SLICER (Power BI / Image 2 style) */
.date-slicer-group {
  display: flex; flex-direction: column; gap: 5px; min-width: 240px;
}
.date-slicer-boxes {
  display: flex; align-items: center; gap: 8px;
}
.date-box-wrap {
  position: relative; flex: 1;
}
.date-box-input {
  background: #0d172c;
  border: 1px solid #486581;
  color: #ffffff;
  font-family: inherit;
  font-size: 0.88rem;
  font-weight: 500;
  padding: 5px 8px;
  width: 110px;
  text-align: center;
  border-radius: 3px;
  letter-spacing: 0.03em;
  cursor: pointer;
  transition: all var(--trans);
  display: block;
}
.date-box-input:hover {
  border-color: #7097c2;
  box-shadow: 0 0 8px rgba(112, 151, 194, 0.3);
}
.date-box-input:focus {
  outline: none;
  border-color: var(--border-focus);
  box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.3);
}
.date-hidden-picker {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  opacity: 0; pointer-events: none; z-index: -1;
}

/* Range Slider */
.date-slider-wrap {
  position: relative;
  width: 100%;
  height: 20px;
  margin-top: 4px;
  display: flex;
  align-items: center;
  user-select: none;
  touch-action: none;
}
.date-slider-track {
  position: absolute;
  left: 0; right: 0;
  height: 3px;
  background: rgba(255, 255, 255, 0.35);
  border-radius: 2px;
}
.date-slider-fill {
  position: absolute;
  height: 3px;
  background: #ffffff;
  border-radius: 2px;
}
.date-slider-thumb {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #ffffff;
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.7);
  cursor: grab;
  z-index: 3;
  transition: transform 0.1s, box-shadow 0.1s;
}
.date-slider-thumb:active, .date-slider-thumb.active {
  cursor: grabbing;
  transform: translate(-50%, -50%) scale(1.18);
  box-shadow: 0 0 14px rgba(255, 255, 255, 0.95);
}
.date-slider-thumb:focus-visible {
  outline: 2px solid var(--cyan);
  outline-offset: 2px;
}

/* BOTON LIMPIAR */
.btn-reset {
  background: rgba(30, 48, 80, 0.7);
  border: 1px solid #334e68;
  color: var(--text-sec);
  padding: 7px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.84rem;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all var(--trans);
  align-self: flex-end;
}
.btn-reset:hover {
  background: rgba(45, 72, 115, 0.9);
  color: #ffffff;
  border-color: var(--border-focus);
  box-shadow: 0 0 12px rgba(56, 189, 248, 0.25);
}

/* MAIN */
.main {
  max-width: 1600px; margin: 0 auto; padding: 24px;
  display: flex; flex-direction: column; gap: 24px;
}

/* SECCIONES Y TARJETAS */
.section {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow), var(--inner-glow);
  backdrop-filter: blur(12px);
  transition: border-color var(--trans);
}
.section:hover {
  border-color: rgba(148, 163, 184, 0.25);
}
.section-title {
  padding: 16px 22px;
  font-size: 0.95rem; font-weight: 600; letter-spacing: -0.01em;
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
  background: rgba(18, 30, 56, 0.4);
}
.section-title-left {
  display: flex; align-items: center; gap: 10px;
}
.section-title-icon {
  width: 28px; height: 28px; border-radius: 7px;
  background: rgba(56, 189, 248, 0.12); color: var(--cyan);
  display: grid; place-items: center;
}
.section-title-icon svg { width: 16px; height: 16px; }
.section-title span.sub { color: var(--muted); font-size: 0.8rem; font-weight: 400; }

.charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0; min-width: 0; }
.chart-panel { padding: 20px; position: relative; min-width: 0; }
.chart-panel + .chart-panel { border-left: 1px solid var(--border); }
.chart-panel-header {
  font-size: 0.82rem; font-weight: 600; color: var(--text-sec);
  margin-bottom: 12px; display: flex; align-items: center; gap: 6px;
}
.chart-canvas-wrap { position: relative; height: 320px; width: 100%; min-width: 0; }

/* TABLA MATRIZ */
.table-wrapper { overflow: auto; }
table { border-collapse: collapse; width: 100%; white-space: nowrap; }
th {
  background: #111d35; padding: 12px 16px; font-weight: 600;
  font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.05em;
  color: var(--muted); border-bottom: 1px solid var(--border);
  border-right: 1px solid var(--border); position: sticky; top: 0; z-index: 5;
}
th:last-child { border-right: none; }
.th-estado { text-align: center; }
.th-sub { font-size: 0.7rem; font-weight: 600; padding: 6px 14px; background: #0f192e; color: #94a3b8; }

.est-aceptado  { color: #34d399; border-top: 3px solid var(--green); }
.est-rechazado { color: #f43f5e; border-top: 3px solid var(--red); }
.est-pendiente { color: #fbbf24; border-top: 3px solid var(--yellow); }
.estado-badge { display: inline-flex; align-items: center; gap: 5px; font-size: 0.8rem; font-weight: 700; }

td {
  padding: 10px 16px; border-bottom: 1px solid var(--border);
  border-right: 1px solid var(--border); vertical-align: middle;
  font-size: 0.84rem;
}
td:last-child { border-right: none; }
.tr-even { background: rgba(18, 29, 53, 0.6); }
.tr-odd  { background: rgba(13, 21, 40, 0.6); }
tr:hover td { background: rgba(56, 189, 248, 0.08) !important; }

.td-canal { text-align: center; }
.canal-badge {
  display: inline-block;
  background: rgba(56, 189, 248, 0.12);
  border: 1px solid rgba(56, 189, 248, 0.3);
  border-radius: 20px; padding: 3px 12px;
  font-size: 0.75rem; font-weight: 700;
  letter-spacing: 0.04em; color: #38bdf8;
}
.td-consent { max-width: 280px; white-space: normal; word-break: break-word; font-weight: 500; color: #f1f5f9; }
.td-count   { text-align: right; font-variant-numeric: tabular-nums; font-weight: 500; }
.td-total   { text-align: right; font-weight: 700; color: #f8fafc; }
.td-pct     { min-width: 120px; }
.pct-bar-wrap { display: flex; align-items: center; gap: 8px; }
.pct-bar-track { flex: 1; height: 6px; background: rgba(255, 255, 255, 0.08); border-radius: 3px; overflow: hidden; }
.pct-bar { height: 100%; border-radius: 3px; min-width: 1px; transition: width 0.3s ease; }
.pct-bar.est-aceptado  { background: linear-gradient(90deg, #059669, #10b981); }
.pct-bar.est-rechazado { background: linear-gradient(90deg, #e11d48, #f43f5e); }
.pct-bar.est-pendiente { background: linear-gradient(90deg, #d97706, #f59e0b); }
.pct-bar.est-default   { background: linear-gradient(90deg, #2563eb, #38bdf8); }
.pct-label { font-size: 0.75rem; color: var(--muted); font-variant-numeric: tabular-nums; width: 42px; text-align: right; }
.empty-msg { text-align: center; padding: 48px; color: var(--muted); font-size: 0.95rem; }

/* FOOTER */
.footer {
  text-align: center; padding: 22px; color: var(--muted);
  font-size: 0.78rem; border-top: 1px solid var(--border); margin-top: 16px;
}
.footer code {
  background: #111d35; padding: 2px 7px; border-radius: 4px;
  border: 1px solid var(--border); color: #cbd5e1;
}

/* RESPONSIVE */
@media (max-width: 1024px) {
  .charts-grid { grid-template-columns: 1fr; }
  .chart-panel + .chart-panel { border-left: none; border-top: 1px solid var(--border); }
}
@media (max-width: 768px) {
  .kpis { grid-template-columns: 1fr 1fr; padding: 0 16px; }
  .filters-inner { flex-direction: column; align-items: stretch; }
  .filter-group select, .date-slicer-group { width: 100%; }
  .date-slider-wrap { width: 100%; }
  .date-slicer-boxes { justify-content: space-between; }
  .date-box-input { width: 100%; }
  .main { padding: 16px; }
  .header { padding: 14px 16px; }
}
"""


# ── HTML ────────────────────────────────────────────────────────────────────────
def generar_html(datos: dict) -> str:
    json_str = json.dumps(datos, ensure_ascii=False, separators=(",", ":"))
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <meta name="description" content="Dashboard de consentimientos: usuarios unicos por canal, tipo y estado con graficos interactivos y filtros temporales."/>
  <title>Dashboard de Consentimientos</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet"/>
  <link rel="stylesheet" href="style.css"/>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
</head>
<body>

<!-- HEADER -->
<header class="header">
  <div class="header-inner">
    <div class="header-brand">
      
        <h1 class="header-title">Dashboard de Consentimientos</h1>
      </div>
    </div>
  </div>
</header>

<!-- KPIs -->
<section class="kpis" id="kpis" aria-label="Indicadores clave"></section>

<!-- FILTROS -->
<section class="filters-bar" aria-label="Filtros">
  <div class="filters-inner">
    
    <!-- Rango de Fecha estilo Slicer Power BI (como en foto 2) -->
    <div class="date-slicer-group">
      <label>Rango de Fecha</label>
      <div class="date-slicer-boxes">
        <div class="date-box-wrap">
          <input type="text" id="f-fecha-ini-display" class="date-box-input" readonly title="Click para seleccionar fecha de inicio"/>
          <input type="date" id="f-fecha-ini-native" class="date-hidden-picker" tabindex="-1"/>
        </div>
        <div class="date-box-wrap">
          <input type="text" id="f-fecha-fin-display" class="date-box-input" readonly title="Click para seleccionar fecha de fin"/>
          <input type="date" id="f-fecha-fin-native" class="date-hidden-picker" tabindex="-1"/>
        </div>
      </div>
      <div class="date-slider-wrap" id="slider-wrap" title="Arrastra los controles para ajustar el rango de fechas">
        <div class="date-slider-track"></div>
        <div class="date-slider-fill" id="slider-fill"></div>
        <div class="date-slider-thumb" id="slider-thumb-min" tabindex="0" role="slider" aria-label="Fecha inicio"></div>
        <div class="date-slider-thumb" id="slider-thumb-max" tabindex="0" role="slider" aria-label="Fecha fin"></div>
      </div>
    </div>

    <!-- Filtro Año -->
    <div class="filter-group">
      <label for="f-anio">Año</label>
      <select id="f-anio">
        <option value="">Todos los años</option>
      </select>
    </div>

    <!-- Filtro Mes -->
    <div class="filter-group">
      <label for="f-mes">Mes</label>
      <select id="f-mes">
        <option value="">Todos los meses</option>
        <option value="01">Enero</option>
        <option value="02">Febrero</option>
        <option value="03">Marzo</option>
        <option value="04">Abril</option>
        <option value="05">Mayo</option>
        <option value="06">Junio</option>
        <option value="07">Julio</option>
        <option value="08">Agosto</option>
        <option value="09">Septiembre</option>
        <option value="10">Octubre</option>
        <option value="11">Noviembre</option>
        <option value="12">Diciembre</option>
      </select>
    </div>

    <!-- Filtro Canal -->
    <div class="filter-group">
      <label for="f-canal">Canal</label>
      <select id="f-canal">
        <option value="">Todos los canales</option>
      </select>
    </div>

    <!-- Filtro Consentimiento -->
    <div class="filter-group">
      <label for="f-consent">Consentimiento</label>
      <select id="f-consent">
        <option value="">Todos</option>
      </select>
    </div>

    <!-- Botón Limpiar -->
    <button id="btn-reset" class="btn-reset" title="Restablecer todos los filtros">&#8635; Limpiar</button>

  </div>
</section>

<!-- GRAFICOS Y MATRIZ -->
<main class="main">

  <!-- Linea + Barras por Canal -->
  <div class="section">
    <div class="section-title">
      <div class="section-title-left">
        <div class="section-title-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
        </div>
        <div>Evolución de Consentimientos</div>
      </div>
    </div>
    <div class="charts-grid">
      <div class="chart-panel">
        <div class="chart-panel-header">Evolución Temporal de Estados</div>
        <div class="chart-canvas-wrap"><canvas id="chart-line"></canvas></div>
      </div>
      <div class="chart-panel">
        <div class="chart-panel-header">Aceptación y Rechazo por Canal (Usuarios Únicos)</div>
        <div class="chart-canvas-wrap"><canvas id="chart-bar"></canvas></div>
      </div>
    </div>
  </div>

  <!-- Barras por tipo de consentimiento -->
  <div class="section">
    <div class="section-title">
      <div class="section-title-left">
        <div class="section-title-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/></svg>
        </div>
        <div>Distribución por Tipo de Consentimiento y Estado</div>
      </div>
    </div>
    <div class="chart-panel">
      <div class="chart-canvas-wrap" style="height:340px;"><canvas id="chart-tipo"></canvas></div>
    </div>
  </div>

  <!-- Tabla matriz -->
  <div class="section">
    <div class="section-title">
      <div class="section-title-left">
        <div class="section-title-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M3 15h18"/><path d="M9 3v18"/></svg>
        </div>
        <div>Detalle de los Tipos de Consentimiento</div>
      </div>
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
  Generado automáticamente con <code>generate_dashboard.py</code> &bull; Dashboard optimizado para GitHub Pages
</footer>

<script>
// ── Datos embebidos ────────────────────────────────────────────────────────────
const DATA = {json_str};

// ── Helpers ───────────────────────────────────────────────────────────────────
const esc = s => String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
const fmt = n => Number(n).toLocaleString("es");

function toDisplayDate(isoStr) {{
  if (!isoStr || isoStr.length < 10) return "";
  const parts = isoStr.substring(0, 10).split("-");
  return `${{parts[2]}}/${{parts[1]}}/${{parts[0]}}`;
}}

function toISODate(ddmmyyyy) {{
  if (!ddmmyyyy) return "";
  const parts = ddmmyyyy.split("/");
  if (parts.length === 3) {{
    return `${{parts[2]}}-${{parts[1]}}-${{parts[0]}}`;
  }}
  return ddmmyyyy;
}}

// ── Colores Modernos para Estados y Graficos ──────────────────────────────────
const ECLS = {{ ACEPTADO:"est-aceptado", RECHAZADO:"est-rechazado", PENDIENTE:"est-pendiente" }};
const EICO = {{ ACEPTADO:"&#10004;", RECHAZADO:"&#10006;", PENDIENTE:"&#9203;" }};

// Paleta visual moderna y armoniosa
const ECOLOR = {{
  ACEPTADO:  "#10b981", // Emerald vibrante
  RECHAZADO: "#f43f5e", // Rose Crimson moderno
  PENDIENTE: "#f59e0b"  // Amber dorado
}};

const ECOLOR_BORDER = {{
  ACEPTADO:  "#059669",
  RECHAZADO: "#e11d48",
  PENDIENTE: "#d97706"
}};

const ECOLOR_BG = {{
  ACEPTADO:  "rgba(16, 185, 129, 0.2)",
  RECHAZADO: "rgba(244, 63, 94, 0.2)",
  PENDIENTE: "rgba(245, 158, 11, 0.2)"
}};

// ── KPIs ──────────────────────────────────────────────────────────────────────
const KPI_ICONS = {{
  users: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
  records: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`,
  channels: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/></svg>`,
  consents: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`
}};

const KPI_DEFS = [
  {{label:"Usuarios Únicos",         key:"total_usuarios",  iconKey:"users",    cls:"kpi-cyan"}},
  {{label:"Registros Totales",        key:"total_registros", iconKey:"records",  cls:"kpi-purple"}},
  {{label:"Canales Activos",          key:"canales",         iconKey:"channels", cls:"kpi-green"}},
  {{label:"Tipos Consentimiento",     key:"consentimientos", iconKey:"consents", cls:"kpi-amber"}},
];

function renderKPIs(kpis) {{
  const kpisEl = document.getElementById("kpis");
  kpisEl.innerHTML = KPI_DEFS.map(d => `
    <div class="kpi-card ${{d.cls}}">
      <div class="kpi-icon-wrap">${{KPI_ICONS[d.iconKey]}}</div>
      <div class="kpi-body">
        <span class="kpi-value">${{fmt(kpis[d.key] ?? 0)}}</span>
        <span class="kpi-label">${{d.label}}</span>
      </div>
    </div>`).join("");
}}

// ── Elementos de Filtros ───────────────────────────────────────────────────────
const fAnio        = document.getElementById("f-anio");
const fMes         = document.getElementById("f-mes");
const fCanal       = document.getElementById("f-canal");
const fConsent     = document.getElementById("f-consent");
const boxFechaIni  = document.getElementById("f-fecha-ini-display");
const boxFechaFin  = document.getElementById("f-fecha-fin-display");
const natFechaIni  = document.getElementById("f-fecha-ini-native");
const natFechaFin  = document.getElementById("f-fecha-fin-native");
const sliderWrap   = document.getElementById("slider-wrap");
const sliderFill   = document.getElementById("slider-fill");
const thumbMin     = document.getElementById("slider-thumb-min");
const thumbMax     = document.getElementById("slider-thumb-max");

// Poblar dropdown de Años dinamicamente
const aniosUnicos = Array.from(new Set(DATA.fechas.map(f => f.substring(0, 4)))).sort();
aniosUnicos.forEach(a => {{
  fAnio.insertAdjacentHTML("beforeend", `<option value="${{a}}">${{a}}</option>`);
}});

// Poblar Canales y Consentimientos
DATA.canales.forEach(c => fCanal.insertAdjacentHTML("beforeend", `<option value="${{esc(c)}}">${{esc(c)}}</option>`));
DATA.consentimientos.forEach(c => fConsent.insertAdjacentHTML("beforeend", `<option value="${{esc(c)}}">${{esc(c)}}</option>`));

// ── Manejo del Slider de Fechas (Power BI Style) ──────────────────────────────
const globalMinDate = DATA.fechas.length ? DATA.fechas[0] : "";
const globalMaxDate = DATA.fechas.length ? DATA.fechas[DATA.fechas.length - 1] : "";

let minTime = globalMinDate ? new Date(globalMinDate + "T00:00:00").getTime() : 0;
let maxTime = globalMaxDate ? new Date(globalMaxDate + "T00:00:00").getTime() : 0;
const DAY_MS = 86400000;
let totalDays = Math.max(1, Math.round((maxTime - minTime) / DAY_MS));

let currentStartIdx = 0;
let currentEndIdx   = totalDays;

function getIsoFromIdx(idx) {{
  const t = minTime + idx * DAY_MS;
  const d = new Date(t);
  const yy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${{yy}}-${{mm}}-${{dd}}`;
}}

function getIdxFromIso(isoStr) {{
  if (!isoStr) return 0;
  const t = new Date(isoStr + "T00:00:00").getTime();
  const idx = Math.round((t - minTime) / DAY_MS);
  return Math.max(0, Math.min(totalDays, idx));
}}

function updateSliderUI() {{
  const pMin = totalDays > 0 ? (currentStartIdx / totalDays) * 100 : 0;
  const pMax = totalDays > 0 ? (currentEndIdx / totalDays) * 100 : 100;

  thumbMin.style.left = `${{pMin}}%`;
  thumbMax.style.left = `${{pMax}}%`;
  sliderFill.style.left = `${{pMin}}%`;
  sliderFill.style.width = `${{Math.max(0, pMax - pMin)}}%`;

  const dStart = getIsoFromIdx(currentStartIdx);
  const dEnd   = getIsoFromIdx(currentEndIdx);

  boxFechaIni.value = toDisplayDate(dStart);
  boxFechaFin.value = toDisplayDate(dEnd);
  natFechaIni.value = dStart;
  natFechaFin.value = dEnd;
}}

// Inicializar fechas
if (DATA.fechas.length) {{
  updateSliderUI();
}}

// Interacción con Dragging en Thumbs
let draggingThumb = null;

function handleSliderPointer(e) {{
  if (!draggingThumb) return;
  const rect = sliderWrap.getBoundingClientRect();
  const clientX = e.clientX ?? (e.touches && e.touches[0] ? e.touches[0].clientX : 0);
  let pct = (clientX - rect.left) / rect.width;
  pct = Math.max(0, Math.min(1, pct));
  const targetIdx = Math.round(pct * totalDays);

  if (draggingThumb === "min") {{
    currentStartIdx = Math.min(targetIdx, currentEndIdx);
  }} else if (draggingThumb === "max") {{
    currentEndIdx = Math.max(targetIdx, currentStartIdx);
  }}
  updateSliderUI();
  render();
}}

[thumbMin, thumbMax].forEach(thumb => {{
  thumb.addEventListener("pointerdown", e => {{
    e.preventDefault();
    draggingThumb = (thumb === thumbMin) ? "min" : "max";
    thumb.setPointerCapture(e.pointerId);
    thumb.classList.add("active");
  }});
  thumb.addEventListener("pointermove", handleSliderPointer);
  const stopDrag = e => {{
    if (draggingThumb) {{
      thumb.releasePointerCapture(e.pointerId);
      thumb.classList.remove("active");
      draggingThumb = null;
    }}
  }};
  thumb.addEventListener("pointerup", stopDrag);
  thumb.addEventListener("pointercancel", stopDrag);
}});

// Click sobre el track para mover el thumb mas cercano
sliderWrap.addEventListener("pointerdown", e => {{
  if (e.target === thumbMin || e.target === thumbMax) return;
  const rect = sliderWrap.getBoundingClientRect();
  let pct = (e.clientX - rect.left) / rect.width;
  pct = Math.max(0, Math.min(1, pct));
  const clickIdx = Math.round(pct * totalDays);

  const distMin = Math.abs(clickIdx - currentStartIdx);
  const distMax = Math.abs(clickIdx - currentEndIdx);

  if (distMin <= distMax) {{
    currentStartIdx = Math.min(clickIdx, currentEndIdx);
  }} else {{
    currentEndIdx = Math.max(clickIdx, currentStartIdx);
  }}
  updateSliderUI();
  render();
}});

// Click en las cajitas de fecha: abre selector nativo
boxFechaIni.addEventListener("click", () => {{
  try {{ natFechaIni.showPicker(); }} catch(err) {{ natFechaIni.focus(); }}
}});
boxFechaFin.addEventListener("click", () => {{
  try {{ natFechaFin.showPicker(); }} catch(err) {{ natFechaFin.focus(); }}
}});

natFechaIni.addEventListener("change", () => {{
  if (natFechaIni.value) {{
    currentStartIdx = Math.min(getIdxFromIso(natFechaIni.value), currentEndIdx);
    updateSliderUI();
    render();
  }}
}});
natFechaFin.addEventListener("change", () => {{
  if (natFechaFin.value) {{
    currentEndIdx = Math.max(getIdxFromIso(natFechaFin.value), currentStartIdx);
    updateSliderUI();
    render();
  }}
}});

// Cambios de Año y Mes
function onAnioMesChange() {{
  const vAnio = fAnio.value;
  const vMes  = fMes.value;

  if (vAnio && vMes) {{
    const dStart = `${{vAnio}}-${{vMes}}-01`;
    const lastDay = new Date(Number(vAnio), Number(vMes), 0).getDate();
    const dEnd = `${{vAnio}}-${{vMes}}-${{String(lastDay).padStart(2, '0')}}`;
    currentStartIdx = getIdxFromIso(dStart);
    currentEndIdx   = getIdxFromIso(dEnd);
  }} else if (vAnio) {{
    const dStart = `${{vAnio}}-01-01`;
    const dEnd   = `${{vAnio}}-12-31`;
    currentStartIdx = getIdxFromIso(dStart);
    currentEndIdx   = getIdxFromIso(dEnd);
  }} else if (vMes) {{
    // Buscar el año por defecto (primer año de datos)
    const yRef = aniosUnicos[0] || "2026";
    const dStart = `${{yRef}}-${{vMes}}-01`;
    const lastDay = new Date(Number(yRef), Number(vMes), 0).getDate();
    const dEnd = `${{yRef}}-${{vMes}}-${{String(lastDay).padStart(2, '0')}}`;
    currentStartIdx = getIdxFromIso(dStart);
    currentEndIdx   = getIdxFromIso(dEnd);
  }}
  updateSliderUI();
  render();
}}

fAnio.addEventListener("change", onAnioMesChange);
fMes.addEventListener("change", onAnioMesChange);
fCanal.addEventListener("change", render);
fConsent.addEventListener("change", render);

// Boton Limpiar / Reset
document.getElementById("btn-reset").addEventListener("click", () => {{
  fAnio.value = "";
  fMes.value = "";
  fCanal.value = "";
  fConsent.value = "";
  currentStartIdx = 0;
  currentEndIdx = totalDays;
  updateSliderUI();
  render();
}});

// ── Charts Setup ──────────────────────────────────────────────────────────────
const FONT_FAMILY = 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

const CHART_DEFAULTS = {{
  responsive: true,
  maintainAspectRatio: false,
  plugins: {{
    legend: {{
      position: 'top',
      align: 'end',
      labels: {{
        color: "#cbd5e1",
        usePointStyle: true,
        pointStyle: "circle",
        boxWidth: 8,
        padding: 16,
        font: {{ family: FONT_FAMILY, size: 12, weight: 500 }}
      }}
    }},
    tooltip: {{
      backgroundColor: "rgba(10, 16, 32, 0.95)",
      borderColor: "rgba(148, 163, 184, 0.25)",
      borderWidth: 1,
      cornerRadius: 8,
      padding: 12,
      titleColor: "#f8fafc",
      titleFont: {{ family: FONT_FAMILY, size: 13, weight: 600 }},
      bodyColor: "#cbd5e1",
      bodyFont: {{ family: FONT_FAMILY, size: 12 }},
      boxPadding: 6,
      usePointStyle: true
    }}
  }},
  scales: {{
    x: {{
      ticks: {{ color: "#94a3b8", font: {{ family: FONT_FAMILY, size: 11 }} }},
      grid: {{ color: "rgba(148, 163, 184, 0.08)" }}
    }},
    y: {{
      ticks: {{ color: "#94a3b8", font: {{ family: FONT_FAMILY, size: 11 }} }},
      grid: {{ color: "rgba(148, 163, 184, 0.08)" }},
      beginAtZero: true
    }}
  }}
}};

let chartLine, chartBar, chartTipo;

function destroyCharts() {{
  [chartLine, chartBar, chartTipo].forEach(c => c && c.destroy());
}}

function buildLine(fechasFilt, seriesFilt) {{
  const labelsDisplay = fechasFilt.map(toDisplayDate);

  // LINE CHART
  const ctxL = document.getElementById("chart-line").getContext("2d");
  chartLine = new Chart(ctxL, {{
    type: "line",
    data: {{
      labels: labelsDisplay,
      datasets: DATA.estados.map(e => {{
        const color = ECOLOR[e] || "#38bdf8";
        const grad = ctxL.createLinearGradient(0, 0, 0, 300);
        grad.addColorStop(0, ECOLOR_BG[e] || "rgba(56, 189, 248, 0.3)");
        grad.addColorStop(1, "rgba(10, 16, 32, 0.0)");

        return {{
          label: e,
          data: fechasFilt.map(f => seriesFilt[f]?.[e] ?? 0),
          borderColor: color,
          backgroundColor: grad,
          fill: true,
          tension: 0.35,
          pointRadius: 4,
          pointHoverRadius: 7,
          pointBackgroundColor: color,
          pointBorderColor: "#ffffff",
          pointBorderWidth: 1.5,
          borderWidth: 2.5
        }};
      }})
    }},
    options: {{
      ...CHART_DEFAULTS,
      scales: {{
        x: {{
          ...CHART_DEFAULTS.scales.x,
          type: "category",
          ticks: {{ ...CHART_DEFAULTS.scales.x.ticks, maxRotation: 45, maxTicksLimit: 14 }}
        }},
        y: {{ ...CHART_DEFAULTS.scales.y }}
      }},
      interaction: {{ mode: "index", intersect: false }}
    }}
  }});
}}

function buildBarCanal(canalesAMostrar, canalData) {{
  // BAR CHART: Aceptacion y Rechazo por Canal
  const ctxB = document.getElementById("chart-bar").getContext("2d");
  chartBar = new Chart(ctxB, {{
    type: "bar",
    data: {{
      labels: canalesAMostrar,
      datasets: DATA.estados.map(e => ({{
        label: e,
        data: canalesAMostrar.map(c => canalData[c]?.[e] ?? 0),
        backgroundColor: ECOLOR_BG[e] || "rgba(56, 189, 248, 0.35)",
        borderColor: ECOLOR[e] || "#38bdf8",
        borderWidth: 1.5,
        borderRadius: 4,
        minBarLength: 4
      }}))
    }},
    options: {{
      ...CHART_DEFAULTS,
      scales: {{
        x: {{
          ...CHART_DEFAULTS.scales.x,
          stacked: false,
          ticks: {{ color: "#cbd5e1", font: {{ family: "Inter", size: 12, weight: 600 }} }}
        }},
        y: {{
          ...CHART_DEFAULTS.scales.y,
          stacked: false
        }}
      }},
      plugins: {{
        ...CHART_DEFAULTS.plugins,
        tooltip: {{
          ...CHART_DEFAULTS.plugins.tooltip,
          callbacks: {{
            title: function(items) {{
              if (!items || !items.length) return "";
              return `Canal: ${{items[0].label}}`;
            }},
            label: function(context) {{
              const canal = context.label;
              const estado = context.dataset.label;
              const val = context.raw || 0;
              const totalCanal = DATA.estados.reduce((acc, est) => acc + (canalData[canal]?.[est] || 0), 0);
              const pct = totalCanal > 0 ? ((val / totalCanal) * 100).toFixed(1) : "0.0";
              return ` ${{estado}}: ${{fmt(val)}} (${{pct}}%)`;
            }},
            footer: function(items) {{
              if (!items || !items.length) return "";
              const canal = items[0].label;
              const totalCanal = DATA.estados.reduce((acc, est) => acc + (canalData[canal]?.[est] || 0), 0);
              return `Total canal: ${{fmt(totalCanal)}} usuarios`;
            }}
          }}
        }}
      }},
      interaction: {{ mode: "index", intersect: false }}
    }}
  }});
}}

function buildTipo(tipoDataFilt, filtConsent) {{
  const tipos = filtConsent ? [filtConsent] : DATA.consentimientos;
  const ctxT  = document.getElementById("chart-tipo").getContext("2d");

  const labelShort = t => t.length > 34 ? t.substring(0, 32) + "…" : t;

  chartTipo = new Chart(ctxT, {{
    type: "bar",
    data: {{
      labels: tipos.map(labelShort),
      datasets: DATA.estados.map(e => ({{
        label: e,
        data: tipos.map(t => tipoDataFilt[t]?.[e] ?? 0),
        backgroundColor: ECOLOR_BG[e] || "rgba(56, 189, 248, 0.35)",
        borderColor: ECOLOR[e] || "#38bdf8",
        borderWidth: 1.5,
        borderRadius: 4
      }}))
    }},
    options: {{
      ...CHART_DEFAULTS,
      indexAxis: "y",
      scales: {{
        x: {{ ...CHART_DEFAULTS.scales.x, stacked: true }},
        y: {{
          ...CHART_DEFAULTS.scales.y,
          stacked: true,
          ticks: {{ color: "#cbd5e1", font: {{ family: "Inter", size: 11, weight: 500 }}, autoSkip: false }}
        }}
      }},
      plugins: {{
        ...CHART_DEFAULTS.plugins,
        tooltip: {{
          ...CHART_DEFAULTS.plugins.tooltip,
          callbacks: {{
            title: function(items) {{
              if (!items || !items.length) return "";
              const idx = items[0].dataIndex;
              return tipos[idx] || items[0].label;
            }}
          }}
        }}
      }},
      interaction: {{ mode: "index", axis: "y", intersect: false }}
    }}
  }});
}}

// ── Tabla Matriz ─────────────────────────────────────────────────────────────
function renderTabla(rowsFilt, estados) {{
  const thead = document.getElementById("tabla-head");
  const tbody = document.getElementById("tabla-body");
  thead.innerHTML = "";

  const trh = document.createElement("tr");
  trh.innerHTML =
    `<th class="th-canal" rowspan="2">Canal</th>` +
    `<th class="th-consent" rowspan="2">Consentimiento</th>`;
  estados.forEach(e => {{
    trh.innerHTML += `<th colspan="2" class="th-estado ${{ECLS[e] || ''}}">
      <span class="estado-badge">${{EICO[e] || ''}} ${{esc(e)}}</span></th>`;
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
    tbody.innerHTML = `<tr><td colspan="999" class="empty-msg">No se encontraron registros con los filtros seleccionados.</td></tr>`;
    return;
  }}

  rowsFilt.forEach((row, i) => {{
    const tr = document.createElement("tr");
    tr.className = i % 2 === 0 ? "tr-even" : "tr-odd";
    let h =
      `<td class="td-canal"><span class="canal-badge">${{esc(row.canal)}}</span></td>` +
      `<td class="td-consent">${{esc(row.consentimiento)}}</td>`;
    estados.forEach(e => {{
      const d = row[e] || {{ count: 0, pct: 0 }};
      const pcls = ECLS[e] || "est-default";
      h +=
        `<td class="td-count">${{fmt(d.count)}}</td>` +
        `<td class="td-pct">
           <div class="pct-bar-wrap">
             <div class="pct-bar-track">
               <div class="pct-bar ${{pcls}}" style="width:${{Math.min(d.pct, 100)}}%"></div>
             </div>
             <span class="pct-label">${{d.pct.toFixed(1)}}%</span>
           </div>
         </td>`;
    }});
    h += `<td class="td-total">${{fmt(row.total)}}</td>`;
    tr.innerHTML = h;
    tbody.appendChild(tr);
  }});
}}

// ── Render Principal ──────────────────────────────────────────────────────────
function render() {{
  const vFechaIni = natFechaIni.value;
  const vFechaFin = natFechaFin.value;
  const vAnio     = fAnio.value;
  const vMes      = fMes.value;
  const vCanal    = fCanal.value;
  const vConsent  = fConsent.value;

  // 1. Filtrar fechas para los graficos
  const fechasFilt = DATA.fechas.filter(f => {{
    if (vFechaIni && f < vFechaIni) return false;
    if (vFechaFin && f > vFechaFin) return false;
    if (vAnio && !f.startsWith(vAnio)) return false;
    if (vMes && f.substring(5, 7) !== vMes) return false;
    return true;
  }});

  // 2. Filtrar registros atomicos
  const recordsFilt = DATA.records.filter(r => {{
    if (vFechaIni && r.f < vFechaIni) return false;
    if (vFechaFin && r.f > vFechaFin) return false;
    if (vAnio && !r.f.startsWith(vAnio)) return false;
    if (vMes && r.f.substring(5, 7) !== vMes) return false;
    if (vCanal && r.c !== vCanal) return false;
    if (vConsent && r.t !== vConsent) return false;
    return true;
  }});

  // 3. KPIs dinamicos
  const totalRegistros = recordsFilt.reduce((acc, r) => acc + r.n, 0);
  let totalUsuarios = 0;
  if (vConsent) {{
    totalUsuarios = totalRegistros;
  }} else {{
    totalUsuarios = DATA.users_fc
      .filter(u => {{
        if (vFechaIni && u.f < vFechaIni) return false;
        if (vFechaFin && u.f > vFechaFin) return false;
        if (vAnio && !u.f.startsWith(vAnio)) return false;
        if (vMes && u.f.substring(5, 7) !== vMes) return false;
        if (vCanal && u.c !== vCanal) return false;
        return true;
      }})
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

  // 4. Series temporales por fecha y estado
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
      .filter(u => {{
        if (vFechaIni && u.f < vFechaIni) return false;
        if (vFechaFin && u.f > vFechaFin) return false;
        if (vAnio && !u.f.startsWith(vAnio)) return false;
        if (vMes && u.f.substring(5, 7) !== vMes) return false;
        if (vCanal && u.c !== vCanal) return false;
        return true;
      }})
      .forEach(u => {{
        if (seriesPorFecha[u.f] && seriesPorFecha[u.f][u.e] !== undefined) {{
          seriesPorFecha[u.f][u.e] += u.n;
        }}
      }});
  }}

  // 5. Totales por consentimiento
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

  // 5b. Totales por canal (Aceptacion y Rechazo de usuarios unicos)
  const canalesAMostrar = vCanal ? [vCanal] : DATA.canales;
  const canalData = {{}};
  canalesAMostrar.forEach(c => {{
    canalData[c] = {{}};
    DATA.estados.forEach(e => {{ canalData[c][e] = 0; }});
  }});

  if (vConsent) {{
    recordsFilt.forEach(r => {{
      if (canalData[r.c] && canalData[r.c][r.e] !== undefined) {{
        canalData[r.c][r.e] += r.n;
      }}
    }});
  }} else {{
    DATA.users_fce
      .filter(u => {{
        if (vFechaIni && u.f < vFechaIni) return false;
        if (vFechaFin && u.f > vFechaFin) return false;
        if (vAnio && !u.f.startsWith(vAnio)) return false;
        if (vMes && u.f.substring(5, 7) !== vMes) return false;
        if (vCanal && u.c !== vCanal) return false;
        return true;
      }})
      .forEach(u => {{
        if (canalData[u.c] && canalData[u.c][u.e] !== undefined) {{
          canalData[u.c][u.e] += u.n;
        }}
      }});
  }}

  // 6. Matriz Canal x Consentimiento
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
  buildLine(fechasFilt, seriesPorFecha);
  buildBarCanal(canalesAMostrar, canalData);
  buildTipo(tipoData, vConsent);
  renderTabla(rowsFilt, DATA.estados);
}}

render();

// Redibujar automaticamente cuando las fuentes web y la ventana terminen de cargar (evita texto invisible)
if (document.fonts) {{
  document.fonts.ready.then(() => {{
    [chartLine, chartBar, chartTipo].forEach(c => c && c.update('none'));
  }});
}}
window.addEventListener("load", () => {{
  [chartLine, chartBar, chartTipo].forEach(c => c && c.update('none'));
}});
</script>
</body>
</html>
"""


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    raw   = procesar_csv(CSV_FILE)
    datos = construir_datos(raw)

    print(f"Estados      : {datos['estados']}")
    print(f"Canales      : {datos['canales']}")
    print(f"Consents     : {len(datos['consentimientos'])}")
    print(f"Combinaciones: {len(datos['records'])}")
    print(f"Fechas       : {datos['fechas'][0]} -> {datos['fechas'][-1]}")
    print(f"KPIs         : {datos['kpis']}")

    OUTPUT_CSS.write_text(CSS, encoding="utf-8")
    print(f"\n[OK] CSS  -> {OUTPUT_CSS.resolve()}")

    html = generar_html(datos)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"[OK] HTML -> {OUTPUT_HTML.resolve()}")
    print("\nSube index.html + style.css a GitHub Pages.")
