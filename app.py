import streamlit as st
import base64

from src.formats import FORMATOS, PLATAFORMAS, OBJETIVOS, TIPOS_HOOK, TONS, CTAS_ORGANICO, NICHOS, PILARES
from src.script_gen import generate_scripts, SCRIPT_TYPES
from src.clients import load_clients, delete_client_supabase, load_latest_organic_metrics
from src.scripts_db import (
    save_approved_script,
    save_rejected_script,
    load_saved_scripts,
    get_rejection_patterns,
)
from src.styles import (
    get_sidebar_css,
    get_main_css,
    get_page_header_html,
    get_sidebar_welcome_html,
    get_sidebar_copy_header_html,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Gerador de Roteiros · Orgânico",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"<style>{get_sidebar_css()}{get_main_css()}</style>",
    unsafe_allow_html=True,
)


def get_logo_base64():
    try:
        with open("assets/logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""


# ── HTML de download ───────────────────────────────────────────────────────────
def _build_download_html(scripts: list, fd: dict) -> str:
    cards_html = ""
    for i, script in enumerate(scripts, 1):
        cor = script.get("cor", "#003f7c")
        cor_bg = script.get("cor_bg", "#eff6ff")
        tipo_nome = script.get("tipo_nome", "")
        hook = script.get("hook_texto", "").replace("<", "&lt;").replace(">", "&gt;")
        roteiro = (
            script.get("roteiro", "")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )
        legenda = (
            script.get("legenda", "")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )
        hashtags = script.get("hashtags", "").replace("<", "&lt;").replace(">", "&gt;")
        hook_score = script.get("hook_score", "")

        cards_html += f"""
        <div class="card">
          <div class="card-accent" style="background:linear-gradient(90deg,{cor},{cor}88)"></div>
          <div class="card-inner">
            <div class="card-header">
              <span class="copy-num">Roteiro {i} de 5</span>
              <span class="badge" style="background:{cor_bg};color:{cor}">{tipo_nome}</span>
              {"<span class='hook-score'>🎯 Hook: " + hook_score + "</span>" if hook_score else ""}
            </div>
            <div class="slabel">Hook (primeiros 2-3 segundos)</div>
            <div class="hook" style="border-color:{cor}">{hook}</div>
            <div class="slabel">Roteiro / Conteúdo</div>
            <div class="body-text">{roteiro}</div>
            <div class="slabel">Legenda</div>
            <div class="criativo-box">{legenda}</div>
            <div class="slabel" style="margin-top:12px;">Hashtags</div>
            <div class="hashtag-box">{hashtags}</div>
          </div>
          <div class="approval-box">
            <div class="approval-label">Feedback do cliente</div>
            <div class="approval-options">
              <label><input type="radio" name="approval_{i}"> Aprovado</label>
              <label><input type="radio" name="approval_{i}"> Requer ajuste</label>
              <label><input type="radio" name="approval_{i}"> Reprovado</label>
            </div>
            <div class="approval-note">Observações: _______________________________________________</div>
          </div>
        </div>"""

    tags = [
        fd.get("formato", ""),
        fd.get("plataforma", ""),
        fd.get("objetivo", ""),
        fd.get("pilar", ""),
    ]
    tags_html = "".join(f'<span class="tag">{t}</span>' for t in tags if t)
    client_line = (
        f'<div style="font-size:.8rem;color:rgba(255,255,255,.6);margin-top:4px;">'
        f'Cliente: {fd["client_name"]}</div>'
        if fd.get("client_name") else ""
    )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Roteiros — {fd.get('produto_tema', 'Conteúdo')}</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Segoe UI',system-ui,sans-serif;background:#f0f3f8;color:#1a1a2e;padding:32px 16px}}
  .container{{max-width:820px;margin:0 auto}}
  .ph{{background:linear-gradient(135deg,#003f7c,#1a5a9a);border-radius:16px;padding:28px 32px;color:#fff;margin-bottom:24px}}
  .nl{{font-size:.75rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,255,255,.65);margin-bottom:4px}}
  .pn{{font-size:1.5rem;font-weight:700}}
  .tags{{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}}
  .tag{{background:rgba(255,255,255,.12);color:rgba(255,255,255,.9);font-size:.75rem;padding:4px 12px;border-radius:20px;border:1px solid rgba(255,255,255,.2)}}
  .card{{background:#fff;border:1px solid #dde3ed;border-radius:16px;margin-bottom:20px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.06)}}
  .card-accent{{height:4px}}
  .card-inner{{padding:22px 26px 20px}}
  .card-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:8px}}
  .copy-num{{font-size:.7rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#9ca3af}}
  .badge{{font-size:.78rem;font-weight:700;padding:4px 14px;border-radius:20px}}
  .hook-score{{font-size:.72rem;color:#6b7280;font-style:italic}}
  .slabel{{font-size:.65rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#9ca3af;margin-bottom:4px;margin-top:14px}}
  .hook{{font-size:1.05rem;font-weight:700;line-height:1.45;padding-left:12px;border-left:3px solid;margin-bottom:4px;color:#1a1a2e}}
  .body-text{{font-size:.92rem;color:#374151;line-height:1.7;white-space:pre-wrap}}
  .criativo-box{{background:#f8fafc;border:1px solid #e5e9f0;border-radius:8px;padding:12px 14px;font-size:.9rem;color:#374151;line-height:1.65;white-space:pre-wrap}}
  .hashtag-box{{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:8px 12px;font-size:.85rem;color:#065f46}}
  .approval-box{{background:#f8fafc;border:1px dashed #dde3ed;border-radius:10px;padding:14px 18px;margin:8px 26px 20px}}
  .approval-label{{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#9ca3af;margin-bottom:8px}}
  .approval-options{{display:flex;gap:20px;font-size:.85rem;color:#374151;margin-bottom:8px}}
  .approval-options label{{display:flex;align-items:center;gap:6px;cursor:pointer}}
  .approval-note{{font-size:.82rem;color:#9ca3af;padding-top:8px;border-top:1px solid #e5e9f0}}
  .pf{{text-align:center;margin-top:32px;font-size:.78rem;color:#9ca3af}}
</style>
</head>
<body>
<div class="container">
  <div class="ph">
    <div class="nl">{fd.get('nicho', '')} › {fd.get('sub_nicho', '')} · {fd.get('formato', '')}</div>
    <div class="pn">{fd.get('produto_tema', 'Roteiros')}</div>
    {client_line}
    <div class="tags">{tags_html}</div>
  </div>
  {cards_html}
  <div class="pf">Gerado por Roteiro Generator · Dash Digital</div>
</div>
</body>
</html>"""


# ── Session state ──────────────────────────────────────────────────────────────
for key, default in [
    ("scripts", None),
    ("form_data", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ── SIDEBAR — roteiros ─────────────────────────────────────────────────────────
with st.sidebar:
    _logo_b64 = get_logo_base64()
    if _logo_b64:
        st.markdown(
            f'<div class="sb-brand"><img src="data:image/png;base64,{_logo_b64}" '
            f'style="height:38px;"></div>'
            f'<hr class="sb-divider">',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
    <div class="sb-brand">
      <span class="sb-icon">🎬</span>
      <div>
        <div class="sb-title">Roteiro Generator</div>
        <div class="sb-sub">Conteúdo Orgânico · Dash Digital</div>
      </div>
    </div>
    <hr class="sb-divider">
    """,
            unsafe_allow_html=True,
        )

    if st.session_state.scripts:
        fd = st.session_state.form_data
        scripts = st.session_state.scripts

        st.markdown(get_sidebar_copy_header_html(fd), unsafe_allow_html=True)

        for i, script in enumerate(scripts, 1):
            tipo_nome = script.get("tipo_nome", f"Roteiro {i}")
            with st.expander(f"Roteiro {i} — {tipo_nome}"):
                st.markdown('<div class="copy-block-label">Hook (abertura)</div>', unsafe_allow_html=True)
                st.text_area(
                    "hook",
                    value=script.get("hook_texto", ""),
                    height=80,
                    label_visibility="collapsed",
                    key=f"hook_{i}",
                )
                st.markdown('<div class="copy-block-label">Roteiro / Conteúdo</div>', unsafe_allow_html=True)
                st.text_area(
                    "roteiro",
                    value=script.get("roteiro", ""),
                    height=200,
                    label_visibility="collapsed",
                    key=f"roteiro_{i}",
                )
                st.markdown('<div class="copy-block-label">Legenda</div>', unsafe_allow_html=True)
                st.text_area(
                    "legenda",
                    value=script.get("legenda", ""),
                    height=130,
                    label_visibility="collapsed",
                    key=f"legenda_{i}",
                )
                st.markdown('<div class="copy-block-label">Hashtags</div>', unsafe_allow_html=True)
                st.text_area(
                    "hashtags",
                    value=script.get("hashtags", ""),
                    height=60,
                    label_visibility="collapsed",
                    key=f"hashtags_{i}",
                )

                # ── Botões de aprovação ───────────────────────────────────────
                col_ap1, col_ap2, col_ap3 = st.columns(3)
                status_key    = f"approval_{i}"
                rejecting_key = f"rejecting_{i}"
                adjusting_key = f"adjusting_{i}"
                if status_key not in st.session_state:
                    st.session_state[status_key] = None
                if rejecting_key not in st.session_state:
                    st.session_state[rejecting_key] = False
                if adjusting_key not in st.session_state:
                    st.session_state[adjusting_key] = False

                with col_ap1:
                    if st.button("✅ Aprovar", key=f"btn_aprove_{i}", use_container_width=True):
                        st.session_state[status_key] = "aprovado"
                        st.session_state[rejecting_key] = False
                        st.session_state[adjusting_key] = False
                        save_approved_script(st.session_state.form_data, script, i)
                        load_saved_scripts.clear()

                with col_ap2:
                    if st.button("⚠️ Ajuste", key=f"btn_adjust_{i}", use_container_width=True):
                        st.session_state[adjusting_key] = not st.session_state[adjusting_key]
                        st.session_state[rejecting_key] = False

                with col_ap3:
                    if st.button("❌ Rejeitar", key=f"btn_reject_{i}", use_container_width=True):
                        if st.session_state[status_key] != "rejeitado":
                            st.session_state[rejecting_key] = True
                            st.session_state[adjusting_key] = False

                # ── Fluxo: Requer Ajuste — apenas mostra nota, não salva ────
                if st.session_state[adjusting_key]:
                    st.text_area(
                        "Nota de ajuste",
                        placeholder="Descreva o que precisa ser ajustado...",
                        key=f"adjust_note_{i}",
                        height=70,
                        help="Esta nota é apenas visual — não é salva no banco.",
                    )
                    st.caption("Nenhuma ação será salva. Use para registrar o feedback do cliente durante a reunião.")

                # ── Fluxo de rejeição: campo de motivo ────────────────────────
                if st.session_state[rejecting_key]:
                    reason_input = st.text_area(
                        "Motivo da rejeição",
                        placeholder="Ex: hook muito genérico, tom não combina, muito longo...",
                        key=f"reason_{i}",
                        height=80,
                    )
                    rc1, rc2 = st.columns(2)
                    with rc1:
                        if st.button(
                            "Confirmar rejeição",
                            key=f"btn_confirm_reject_{i}",
                            use_container_width=True,
                            type="primary",
                        ):
                            if reason_input.strip():
                                st.session_state[status_key] = "rejeitado"
                                st.session_state[rejecting_key] = False
                                save_rejected_script(
                                    st.session_state.form_data,
                                    script,
                                    i,
                                    reason_input.strip(),
                                )
                                load_saved_scripts.clear()
                            else:
                                st.warning("Escreva o motivo antes de confirmar.")
                    with rc2:
                        if st.button("Cancelar", key=f"btn_cancel_reject_{i}", use_container_width=True):
                            st.session_state[rejecting_key] = False

                status = st.session_state.get(status_key)
                if status:
                    color_map = {"aprovado": "#d1fae5", "rejeitado": "#fee2e2"}
                    text_map  = {"aprovado": "#065f46", "rejeitado": "#991b1b"}
                    label_map = {"aprovado": "APROVADO", "rejeitado": "REJEITADO"}
                    st.markdown(
                        f'<div style="background:{color_map.get(status,"#f3f4f6")};'
                        f'color:{text_map.get(status,"#374151")};'
                        f'font-size:.75rem;font-weight:700;padding:4px 12px;border-radius:8px;'
                        f'text-align:center;margin-top:4px;">Status: {label_map.get(status, status.upper())}</div>',
                        unsafe_allow_html=True,
                    )

            score = script.get("hook_score", "")
            if score:
                st.markdown(
                    f'<div style="font-size:.72rem;color:rgba(255,255,255,.55);margin-top:2px;">🎯 Hook: {score}</div>',
                    unsafe_allow_html=True,
                )

        st.markdown('<hr class="sb-divider">', unsafe_allow_html=True)

        st.download_button(
            label="Baixar todos em HTML",
            data=_build_download_html(scripts, fd),
            file_name=f"roteiros_{fd.get('produto_tema','roteiro')[:20].replace(' ', '_').lower()}.html",
            mime="text/html",
            use_container_width=True,
        )
        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
        if st.button("Gerar novamente", use_container_width=True):
            with st.spinner("Gerando..."):
                try:
                    st.session_state.scripts = generate_scripts(st.session_state.form_data)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
    else:
        st.markdown(get_sidebar_welcome_html(), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        '<div style="font-size:.68rem;font-weight:700;color:rgba(255,255,255,.4);letter-spacing:.08em;margin-bottom:8px;">NAVEGAÇÃO</div>'
        '<a href="https://dash-painel.streamlit.app/" target="_blank" style="display:block;padding:7px 10px;border-radius:8px;text-decoration:none;color:rgba(255,255,255,.8);font-size:.82rem;background:rgba(255,255,255,.06);margin-bottom:4px;">📊 Painel de Clientes</a>'
        '<a href="https://anacarolinademariamello-hue.github.io/hub-dash/" target="_blank" style="display:block;padding:7px 10px;border-radius:8px;text-decoration:none;color:rgba(255,255,255,.8);font-size:.82rem;background:rgba(255,255,255,.06);">🏠 Central de Ferramentas</a>',
        unsafe_allow_html=True,
    )


# ── MAIN — briefing ────────────────────────────────────────────────────────────
st.markdown(get_page_header_html(), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 1 — Modo de uso
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="client-section"><div class="form-section-title">Modo de uso</div>', unsafe_allow_html=True)

modo = st.radio(
    "",
    ["Consulta avulsa", "Cliente cadastrado"],
    horizontal=True,
    label_visibility="collapsed",
    key="modo",
)

selected_client = None

if modo == "Cliente cadastrado":
    st.info("📋 Os dados do cliente (tom de voz, nicho, público) serão usados para personalizar os roteiros.")

    all_clients = load_clients()

    if all_clients:
        names = [c["name"] for c in all_clients]
        chosen = st.selectbox(
            "Selecionar cliente",
            names,
            label_visibility="collapsed",
            key="chosen_client",
        )
        selected_client = next((c for c in all_clients if c["name"] == chosen), None)
    else:
        st.info("Nenhum cliente cadastrado. Acesse o hub para cadastrar.")

    if selected_client:
        has_tov = bool(selected_client.get("tone_of_voice", "").strip())
        badge = "Tom de voz carregado" if has_tov else "Sem tom de voz"
        color = "#d1fae5" if has_tov else "#fef3c7"
        text_color = "#065f46" if has_tov else "#92400e"
        col_badge, col_del = st.columns([5, 1])
        with col_badge:
            st.markdown(
                f'<span style="background:{color};color:{text_color};font-size:.75rem;'
                f'font-weight:700;padding:4px 12px;border-radius:20px;">{badge}</span>',
                unsafe_allow_html=True,
            )
        with col_del:
            if st.button("🗑️ Excluir", key="btn_delete_client", use_container_width=True):
                st.session_state["confirm_delete"] = selected_client["name"]

        if st.session_state.get("confirm_delete") == selected_client["name"]:
            st.warning(
                f"Tem certeza que deseja excluir **{selected_client['name']}**? Esta ação não pode ser desfeita."
            )
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("✅ Sim, excluir", key="btn_confirm_delete", use_container_width=True):
                    _del_key = selected_client.get("key", "").strip()
                    if not _del_key:
                        st.session_state["confirm_delete"] = None
                        st.error("Este cliente não possui identificador (key). Verifique o cadastro.")
                        st.rerun()
                    ok, msg = delete_client_supabase(_del_key, selected_client["name"])
                    st.session_state["confirm_delete"] = None
                    if ok:
                        st.success(f"Cliente '{selected_client['name']}' desativado.")
                    else:
                        st.error(msg)
                    st.rerun()
            with col_no:
                if st.button("Cancelar", key="btn_cancel_delete", use_container_width=True):
                    st.session_state["confirm_delete"] = None
                    st.rerun()

        # ── Painel: métricas orgânicas do último relatório ────────────────────
        _client_key_panel = selected_client.get("key", "")
        _metrics_raw = load_latest_organic_metrics(_client_key_panel) if _client_key_panel else ""
        if _metrics_raw:
            with st.expander(
                "📊 Último relatório orgânico — dados que a IA vai usar", expanded=False
            ):
                st.markdown(
                    f'<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;'
                    f'padding:12px 16px;font-size:.82rem;white-space:pre-wrap;color:#374151;line-height:1.7;">'
                    f'{_metrics_raw}</div>',
                    unsafe_allow_html=True,
                )
                st.caption(
                    "Esses dados são injetados automaticamente no prompt toda vez que você gerar roteiros para este cliente."
                )

st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 2 — Formato & Plataforma
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="form-section"><div class="form-section-title">Formato & Plataforma</div>', unsafe_allow_html=True)

_formato_keys = list(FORMATOS.keys())
col_f1, col_f2 = st.columns(2)
with col_f1:
    formato = st.selectbox("Formato de conteúdo", options=_formato_keys, key="formato")
with col_f2:
    plataforma = st.selectbox("Plataforma", options=PLATAFORMAS, key="plataforma")

_formato_data = FORMATOS[formato]
col_f3, col_f4 = st.columns(2)
with col_f3:
    duracao = st.selectbox(
        "Duração / Comprimento",
        options=_formato_data["duracoes"],
        key="duracao",
    )
with col_f4:
    pilar = st.selectbox("Pilar de conteúdo", options=PILARES, key="pilar")

st.markdown(
    f'<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;'
    f'padding:8px 12px;font-size:.82rem;color:#065f46;margin-top:4px;">'
    f'💡 <strong>Dica para {formato.split()[0]} {formato.split()[1] if len(formato.split()) > 1 else ""}:</strong> '
    f'{_formato_data["tip"]}</div>',
    unsafe_allow_html=True,
)

st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 3 — Tema & Nicho
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="form-section"><div class="form-section-title">Tema & Nicho</div>', unsafe_allow_html=True)

_client_nicho = selected_client.get("nicho", "") if selected_client else ""
_client_sub_nicho = selected_client.get("sub_nicho", "") if selected_client else ""
_niche_keys = list(NICHOS.keys())
_niche_index = _niche_keys.index(_client_nicho) if _client_nicho in _niche_keys else 0

col_n1, col_n2 = st.columns(2)
with col_n1:
    nicho = st.selectbox("Nicho", options=_niche_keys, index=_niche_index, key="nicho")
with col_n2:
    _sub_opts = NICHOS[nicho]
    _sub_index = _sub_opts.index(_client_sub_nicho) if _client_sub_nicho in _sub_opts else 0
    sub_nicho = st.selectbox("Sub-nicho", options=_sub_opts, index=_sub_index, key="sub_nicho")

col_n3, col_n4 = st.columns(2)
with col_n3:
    produto_tema = st.text_input(
        "Produto / Tema do conteúdo",
        placeholder="Ex: Como emagrecer sem academia, Método de estudo para concursos...",
        key="produto_tema",
    )
with col_n4:
    _pub_default = selected_client.get("publico_alvo", "") if selected_client else ""
    publico_alvo = st.text_input(
        "Público-alvo",
        value=_pub_default,
        placeholder="Ex: Mulheres 30-45 que querem perder peso sem abrir mão da vida social",
        key="publico_alvo",
        help="Auto-preenchido com o público-alvo cadastrado. Edite se necessário.",
    )

st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 4 — Estratégia do Conteúdo
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="form-section"><div class="form-section-title">Estratégia do Conteúdo</div>', unsafe_allow_html=True)

col_s1, col_s2 = st.columns(2)
with col_s1:
    objetivo = st.selectbox("Objetivo do conteúdo", options=list(OBJETIVOS.keys()), key="objetivo")
with col_s2:
    tipo_hook = st.selectbox("Tipo de hook preferido", options=TIPOS_HOOK, key="tipo_hook")

col_s3, col_s4 = st.columns(2)
with col_s3:
    cta = st.selectbox("CTA orgânico", options=CTAS_ORGANICO, key="cta")
with col_s4:
    contexto_tendencia = st.text_input(
        "Contexto / Tendência atual (opcional)",
        placeholder="Ex: trend do 'girl dinner', viral do momento, meme...",
        key="contexto_tendencia",
    )

sazonalidade = st.text_input(
    "Sazonalidade (opcional)",
    placeholder="Ex: Verão, Volta às aulas, Dia dos Pais, período de provas...",
    key="sazonalidade",
)

st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 5 — Briefing do Roteiro
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="form-section"><div class="form-section-title">Briefing do Roteiro</div>', unsafe_allow_html=True)

ideia_principal = st.text_area(
    "Ideia principal",
    placeholder="O que você quer que o público aprenda, sinta ou faça ao terminar de ver/ler esse conteúdo?",
    height=80,
    key="ideia_principal",
)

pontos_chave = st.text_area(
    "Pontos-chave para cobrir",
    placeholder="Liste os tópicos/pontos principais que devem estar no roteiro:\n• Ponto 1\n• Ponto 2\n• Ponto 3",
    height=110,
    key="pontos_chave",
)

referencias = st.text_area(
    "Referências de conteúdo / Transcrição da concorrência (opcional)",
    placeholder="Cole transcrições de vídeos da concorrência, links ou descreva conteúdos que funcionaram bem no seu nicho. A IA vai usar como referência de estrutura e tom — nunca copiará.",
    height=200,
    key="referencias",
)

nao_fazer = st.text_input(
    "O que NÃO fazer (opcional)",
    placeholder="Ex: não mencionar concorrentes, evitar termos técnicos, não usar tom agressivo...",
    key="nao_fazer",
)

st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 6 — Tom & Identidade
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="form-section"><div class="form-section-title">Tom & Identidade</div>', unsafe_allow_html=True)

col_t1, col_t2, col_t3 = st.columns(3)
with col_t1:
    if selected_client and selected_client.get("tone_of_voice"):
        st.markdown("**Tom de Voz**")
        st.markdown(
            f'<span style="background:#d1fae5;color:#065f46;font-size:.78rem;'
            f'font-weight:600;padding:5px 12px;border-radius:8px;display:inline-block;">'
            f'Definido pelo perfil de {selected_client["name"]}</span>',
            unsafe_allow_html=True,
        )
        tom = "Definido pelo perfil do cliente"
    else:
        tom = st.selectbox("Tom de voz", options=TONS, key="tom")

with col_t2:
    palavras_chave = st.text_input(
        "Palavras / expressões-chave (opcional)",
        placeholder="Ex: autenticidade, resultado real, sem frescura...",
        key="palavras_chave",
    )

with col_t3:
    emoji_pref = st.radio(
        "Emojis",
        options=["Usar emojis", "Mínimo de emojis", "Sem emojis"],
        key="emoji_pref",
    )

st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# BOTÃO GERAR
# ══════════════════════════════════════════════════════════════════════════════
if st.button("🎬 Gerar 5 Roteiros", use_container_width=True):
    if not produto_tema.strip():
        st.error("Preencha o campo Produto / Tema do conteúdo.")
    else:
        if not ideia_principal.strip():
            st.warning(
                "Sem ideia principal — o modelo vai usar seu julgamento com base no tema e formato."
            )

        with st.spinner("Gerando roteiros orgânicos com IA..."):
            try:
                # ── Busca histórico de roteiros do cliente ────────────────────
                client_approved = []
                client_rejected = []
                client_organic_metrics = ""
                client_rejection_patterns = ""

                if selected_client:
                    _client_key = selected_client.get("key", "")
                    all_saved = load_saved_scripts(
                        client_key=_client_key, limit=20
                    )
                    client_approved = [s for s in all_saved if s.get("status") == "aprovado"]
                    client_rejected = [s for s in all_saved if s.get("status") == "rejeitado"]
                    if _client_key:
                        client_organic_metrics = load_latest_organic_metrics(_client_key)
                    client_rejection_patterns = get_rejection_patterns(
                        client_key=_client_key, client_name=selected_client["name"]
                    )

                # ── Tom de voz ────────────────────────────────────────────────
                _tom_final = tom if "tom" in dir() else "Definido pelo perfil do cliente"

                form_data = {
                    "nicho":           nicho,
                    "sub_nicho":       sub_nicho,
                    "produto_tema":    produto_tema.strip(),
                    "publico_alvo":    publico_alvo.strip() or f"Público interessado em {produto_tema}",
                    "formato":         formato,
                    "duracao":         duracao,
                    "formato_tip":     _formato_data["tip"],
                    "output_label":    _formato_data["output_label"],
                    "plataforma":      plataforma,
                    "pilar":           pilar,
                    "objetivo":        objetivo,
                    "objetivo_desc":   OBJETIVOS[objetivo],
                    "tipo_hook":       tipo_hook,
                    "cta":             cta,
                    "contexto_tendencia": contexto_tendencia.strip(),
                    "sazonalidade":    sazonalidade.strip(),
                    "ideia_principal": ideia_principal.strip(),
                    "pontos_chave":    pontos_chave.strip(),
                    "referencias":     referencias.strip(),
                    "nao_fazer":       nao_fazer.strip(),
                    "tom":             _tom_final,
                    "palavras_chave":  palavras_chave.strip(),
                    "emoji_pref":      emoji_pref,
                    # ── Dados do cliente ──────────────────────────────────────
                    "client_name":          selected_client["name"] if selected_client else "",
                    "client_key":           selected_client.get("key", "") if selected_client else "",
                    "client_tone_of_voice": selected_client.get("tone_of_voice", "") if selected_client else "",
                    "client_bio":           selected_client.get("bio", "") if selected_client else "",
                    "client_tags":          selected_client.get("tags", []) if selected_client else [],
                    "client_observations":  selected_client.get("observations", "") if selected_client else "",
                    "client_goals":         selected_client.get("goals", {}) if selected_client else {},
                    "client_competitors":   selected_client.get("competitors", "") if selected_client else "",
                    "client_publico_alvo":  selected_client.get("publico_alvo", "") if selected_client else "",
                    # ── Métricas e histórico ──────────────────────────────────
                    "client_organic_metrics":    client_organic_metrics,
                    "client_approved_scripts":   client_approved,
                    "client_rejected_scripts":   client_rejected,
                    "client_rejection_patterns": client_rejection_patterns,
                }

                scripts = generate_scripts(form_data)
                st.session_state.scripts = scripts
                st.session_state.form_data = form_data

                # Limpa status individuais da sessão anterior
                for _k in [f"approval_{j}" for j in range(1, 6)]:
                    st.session_state.pop(_k, None)
                st.rerun()

            except Exception as e:
                st.error(f"Erro ao gerar roteiros: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# HISTÓRICO DE ROTEIROS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)
with st.expander("📋 Banco de Roteiros Salvos", expanded=False):
    tab_apr, tab_rej = st.tabs(["✅ Aprovados", "❌ Rejeitados"])

    with tab_apr:
        aprovados = load_saved_scripts(status="aprovado", limit=50)
        if not aprovados:
            st.info("Nenhum roteiro aprovado ainda. Clique em ✅ Aprovar para salvar.")
        else:
            for row in aprovados:
                created = row.get("created_at", "")[:10] if row.get("created_at") else ""
                client_str = f" · {row['client_name']}" if row.get("client_name") else ""
                fmt_str = f" · {row.get('formato', '')}" if row.get("formato") else ""
                with st.expander(
                    f"**{row.get('produto_tema', 'Sem título')}**{client_str}{fmt_str} — {row.get('tipo_nome', '')} — {created}",
                    expanded=False,
                ):
                    st.markdown(
                        f'<div style="font-size:.78rem;color:#6b7280;margin-bottom:10px;">'
                        f'{row.get("nicho","")} · {row.get("plataforma","")} · {row.get("objetivo","")}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    if row.get("hook_score"):
                        st.markdown(
                            f'<div style="font-size:.78rem;color:#6b7280;margin-bottom:8px;">🎯 Hook: {row["hook_score"]}</div>',
                            unsafe_allow_html=True,
                        )
                    if row.get("hook_texto"):
                        st.markdown("**Hook**")
                        st.code(row["hook_texto"], language=None)
                    if row.get("roteiro"):
                        st.markdown("**Roteiro**")
                        st.code(row["roteiro"], language=None)
                    if row.get("legenda"):
                        st.markdown("**Legenda**")
                        st.code(row["legenda"], language=None)
                    if row.get("hashtags"):
                        st.markdown("**Hashtags**")
                        st.code(row["hashtags"], language=None)

    with tab_rej:
        rejeitados = load_saved_scripts(status="rejeitado", limit=50)
        if not rejeitados:
            st.info("Nenhum roteiro rejeitado ainda.")
        else:
            for row in rejeitados:
                created = row.get("created_at", "")[:10] if row.get("created_at") else ""
                client_str = f" · {row['client_name']}" if row.get("client_name") else ""
                with st.expander(
                    f"**{row.get('produto_tema', 'Sem título')}**{client_str} — {row.get('tipo_nome', '')} — {created}",
                    expanded=False,
                ):
                    st.markdown(
                        f'<div style="font-size:.78rem;color:#6b7280;margin-bottom:10px;">'
                        f'{row.get("nicho","")} · {row.get("formato","")}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    if row.get("reason"):
                        st.markdown(
                            f'<div style="background:#fee2e2;color:#991b1b;border-radius:8px;'
                            f'padding:8px 12px;font-size:.85rem;margin-bottom:10px;">'
                            f'❌ Motivo: {row["reason"]}</div>',
                            unsafe_allow_html=True,
                        )
                    if row.get("hook_texto"):
                        st.markdown("**Hook**")
                        st.code(row["hook_texto"], language=None)
                    if row.get("roteiro"):
                        st.markdown("**Roteiro**")
                        st.code(row["roteiro"], language=None)

st.markdown(
    '<p style="text-align:center;font-size:.72rem;color:#9ca3af;margin-top:16px;">'
    "Desenvolvido por Dash Digital · @dashdgt · Todos os direitos reservados</p>",
    unsafe_allow_html=True,
)
