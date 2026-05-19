def get_sidebar_css() -> str:
    return """
/* ── Sidebar base ──────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] { background: #0d2137 !important; }

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] summary { color: #fff !important; }

/* Expanders */
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
    margin-bottom: 8px !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"]:hover {
    border-color: rgba(255,255,255,0.22) !important;
}

/* Textarea na sidebar */
[data-testid="stSidebar"] textarea {
    background-color: #0a1929 !important;
    color: #d1dbe8 !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 8px !important;
    font-size: 0.84rem !important;
    line-height: 1.6 !important;
}

/* ── Botões na sidebar — contraste correto ─────────────────────────────────── */
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.10) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.28) !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    padding: 10px !important;
    transition: all 0.2s !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.18) !important;
    border-color: rgba(255,255,255,0.45) !important;
}

/* Botão download na sidebar */
[data-testid="stSidebar"] .stDownloadButton > button {
    background: rgba(248,185,64,0.12) !important;
    color: #f8b940 !important;
    border: 1px solid rgba(248,185,64,0.35) !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    padding: 10px !important;
    transition: all 0.2s !important;
}
[data-testid="stSidebar"] .stDownloadButton > button:hover {
    background: rgba(248,185,64,0.22) !important;
}

div[data-testid="stSidebarNav"] { display: none; }
"""


def get_main_css() -> str:
    return """
.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1000px;
}

/* ── Page header ─────────────────────────────────────────────────────────────*/
.page-header {
    background: linear-gradient(135deg, #003f7c 0%, #1a5a9a 60%, #0d4080 100%);
    border-radius: 16px;
    padding: 26px 32px;
    color: #fff;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.page-header::after {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse at 85% 15%, rgba(255,255,255,0.10) 0%, transparent 60%);
    pointer-events: none;
}
.page-header-title { font-size: 1.45rem; font-weight: 700; color: #fff; margin-bottom: 4px; }
.page-header-sub   { font-size: 0.88rem; color: rgba(255,255,255,0.62); }

/* ── Form sections ───────────────────────────────────────────────────────────*/
.form-section {
    background: #fff;
    border: 1px solid #dde3ed;
    border-radius: 14px;
    padding: 20px 24px 16px;
    margin-bottom: 16px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}
.form-section-title {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #003f7c;
    margin-bottom: 14px;
    padding-bottom: 8px;
    border-bottom: 1px solid #eef1f6;
}

/* ── Client mode section ─────────────────────────────────────────────────────*/
.client-section {
    background: #fff;
    border: 1.5px solid #003f7c22;
    border-radius: 14px;
    padding: 20px 24px 16px;
    margin-bottom: 16px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}
.client-loaded-badge {
    display: inline-block;
    background: #d1fae5;
    color: #065f46;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 20px;
    margin-top: 6px;
}

/* ── Botão principal (gerar) ─────────────────────────────────────────────────*/
.main .stButton > button {
    background: linear-gradient(135deg, #f8b940, #d99a20) !important;
    color: #003f7c !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 14px !important;
    font-size: 1rem !important;
    width: 100% !important;
    transition: all 0.2s !important;
}
.main .stButton > button:hover {
    background: linear-gradient(135deg, #ffc94d, #e8aa30) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(248,185,64,0.35) !important;
}

/* ── Sidebar brand ───────────────────────────────────────────────────────────*/
.sb-brand { display: flex; align-items: center; gap: 10px; padding: 4px 0 10px; }
.sb-icon  { font-size: 1.6rem; }
.sb-title { font-size: 1rem; font-weight: 700; color: #fff; }
.sb-sub   { font-size: 0.72rem; color: rgba(255,255,255,0.5); margin-top: 1px; }
.sb-divider { border: none; border-top: 1px solid rgba(255,255,255,0.12); margin: 10px 0; }
.sb-section-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.45) !important;
    margin-bottom: 6px;
}

/* ── Labels dentro dos expanders da sidebar ──────────────────────────────────*/
.copy-block-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.45) !important;
    margin: 10px 0 3px;
}
"""


def get_page_header_html() -> str:
    return """
<div class="page-header">
  <div class="page-header-title">🎬 Gerador de Roteiros Org&acirc;nicos</div>
  <div class="page-header-sub">Preencha o briefing e clique em Gerar &mdash; os 5 roteiros aparecem na barra lateral</div>
</div>
"""


def get_sidebar_welcome_html() -> str:
    return """
<div style="padding:16px 4px;color:rgba(255,255,255,0.4);font-size:0.82rem;line-height:1.7;text-align:center;">
  Preencha o briefing e clique em<br>
  <strong style="color:rgba(255,255,255,0.7)">Gerar 5 Roteiros</strong><br>
  para ver os roteiros org&acirc;nicos aqui.<br><br>
  <span style="font-size:0.74rem;color:rgba(255,255,255,0.3);">
    Reels &middot; Stories &middot; Carrossel<br>
    Post Feed &middot; YouTube Short
  </span>
</div>
"""


def get_sidebar_copy_header_html(fd: dict) -> str:
    client_line = (
        f'<div style="font-size:.7rem;color:rgba(255,255,255,.5);margin-top:4px;">Cliente: {fd["client_name"]}</div>'
        if fd.get("client_name") else ""
    )
    formato = fd.get("formato", "")
    plataforma = fd.get("plataforma", "")
    return f"""
<div style="background:linear-gradient(135deg,#003f7c,#1a5a9a);border-radius:10px;padding:12px 14px;margin-bottom:10px;">
  <div style="font-size:.68rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,255,255,.55);margin-bottom:3px;">
    {formato} &rsaquo; {plataforma}
  </div>
  <div style="font-size:1rem;font-weight:700;color:#fff;line-height:1.3;">{fd.get('produto_tema', 'Roteiro')}</div>
  {client_line}
  <div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap;">
    <span style="background:rgba(255,255,255,.1);color:rgba(255,255,255,.8);font-size:.7rem;padding:2px 8px;border-radius:12px;">{fd.get('objetivo', '')}</span>
    <span style="background:rgba(248,185,64,.18);color:#f8b940;font-size:.7rem;padding:2px 8px;border-radius:12px;">{fd.get('pilar', '')}</span>
  </div>
</div>
"""
