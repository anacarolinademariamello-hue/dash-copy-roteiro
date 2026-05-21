"""
scripts_db.py — Persistência de roteiros no Supabase.

Tabela: script_copies
  status = 'aprovado' | 'rejeitado'
  reason = motivo da rejeição (apenas para rejeitados)

SQL para criar a tabela:

create table script_copies (
  id              serial primary key,
  client_name     text    default '',
  client_key      text    default '',
  produto_tema    text    default '',
  formato         text    default '',
  plataforma      text    default '',
  objetivo        text    default '',
  pilar           text    default '',
  copy_index      int     default 0,
  tipo_nome       text    default '',
  hook_texto      text    default '',
  roteiro         text    default '',
  legenda         text    default '',
  hashtags        text    default '',
  status          text    default '',
  reason          text    default '',
  hook_score      text    default '',
  hook_score_num  int     default 0,
  created_at      timestamptz default now()
);
create index on script_copies (client_name, status);
create index on script_copies (client_key);
"""
from __future__ import annotations

import re
import requests
import streamlit as st


# ── Credenciais ───────────────────────────────────────────────────────────────

def _creds() -> tuple[str, str]:
    try:
        url = st.secrets.get("supabase_url", "") or ""
        key = st.secrets.get("supabase_service_key", "") or ""
        return url, key
    except Exception:
        return "", ""


def _configured() -> bool:
    url, key = _creds()
    return bool(url and key)


def _headers() -> dict:
    _, key = _creds()
    return {
        "apikey":        key,
        "Authorization": f"Bearer {key}",
        "Content-Type":  "application/json",
        "Prefer":        "return=minimal",
    }


def _rest() -> str:
    url, _ = _creds()
    return f"{url}/rest/v1/script_copies"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_score_num(hook_score: str) -> int:
    """Extrai o número inteiro de strings como '8/10 — justificativa'."""
    m = re.search(r"(\d+)\s*/\s*10", hook_score)
    return int(m.group(1)) if m else 0


# ── Montar payload base ────────────────────────────────────────────────────────

def _build_payload(
    form_data: dict,
    script: dict,
    script_index: int,
    status: str,
    reason: str = "",
) -> dict:
    return {
        "client_name":   form_data.get("client_name") or "",
        "client_key":    form_data.get("client_key") or "",
        "produto_tema":  form_data.get("produto_tema", ""),
        "formato":       form_data.get("formato", ""),
        "plataforma":    form_data.get("plataforma", ""),
        "objetivo":      form_data.get("objetivo", ""),
        "pilar":         form_data.get("pilar", ""),
        "copy_index":    script_index,
        "tipo_nome":     script.get("tipo_nome", ""),
        "hook_texto":    script.get("hook_texto", ""),
        "roteiro":       script.get("roteiro", ""),
        "legenda":       script.get("legenda", ""),
        "hashtags":      script.get("hashtags", ""),
        "status":        status,
        "reason":        reason,
        "hook_score":    script.get("hook_score", ""),
        "hook_score_num": _extract_score_num(script.get("hook_score", "")),
    }


# ── Salvar roteiro aprovado ───────────────────────────────────────────────────

def save_approved_script(form_data: dict, script: dict, script_index: int) -> bool:
    """Salva um roteiro aprovado. Chamada ao clicar Aprovar."""
    if not _configured():
        return False
    try:
        r = requests.post(
            _rest(),
            headers=_headers(),
            json=_build_payload(form_data, script, script_index, "aprovado"),
            timeout=10,
        )
        return r.status_code in (200, 201)
    except Exception:
        return False


# ── Salvar roteiro rejeitado ──────────────────────────────────────────────────

def save_rejected_script(
    form_data: dict, script: dict, script_index: int, reason: str
) -> bool:
    """Salva um roteiro rejeitado com motivo. Chamada ao confirmar rejeição."""
    if not _configured():
        return False
    try:
        r = requests.post(
            _rest(),
            headers=_headers(),
            json=_build_payload(form_data, script, script_index, "rejeitado", reason),
            timeout=10,
        )
        return r.status_code in (200, 201)
    except Exception:
        return False


# ── Carregar histórico ────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def load_saved_scripts(
    status: str = "", client_name: str = "", client_key: str = "", limit: int = 50
) -> list[dict]:
    """
    Carrega roteiros salvos.
    status: 'aprovado' | 'rejeitado' | '' (todos)
    Prefere filtrar por client_key quando disponível.
    """
    if not _configured():
        return []

    url_base, key = _creds()
    params = {
        "order":  "created_at.desc",
        "limit":  str(limit),
        "select": (
            "id,client_name,client_key,produto_tema,formato,plataforma,"
            "objetivo,pilar,copy_index,tipo_nome,hook_texto,roteiro,"
            "legenda,hashtags,status,reason,hook_score,hook_score_num,created_at"
        ),
    }
    if status:
        params["status"] = f"eq.{status}"
    if client_key:
        params["client_key"] = f"eq.{client_key}"
    elif client_name:
        params["client_name"] = f"eq.{client_name}"

    try:
        r = requests.get(
            f"{url_base}/rest/v1/script_copies",
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
            params=params,
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


# ── Padrões de rejeição agregados ─────────────────────────────────────────────

def get_rejection_patterns(client_key: str, client_name: str = "") -> str:
    """
    Analisa os motivos de rejeição do cliente e retorna um resumo
    dos padrões mais frequentes para incluir no prompt do Claude.
    Filtra por client_key (preferencial) ou client_name como fallback.
    Retorna string vazia se não houver rejeições suficientes.
    """
    if not _configured() or (not client_key and not client_name):
        return ""

    url_base, key = _creds()
    filter_param = (
        {"client_key": f"eq.{client_key}"}
        if client_key
        else {"client_name": f"eq.{client_name}"}
    )
    try:
        r = requests.get(
            f"{url_base}/rest/v1/script_copies",
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
            params={
                **filter_param,
                "status":      "eq.rejeitado",
                "order":       "created_at.desc",
                "limit":       "30",
                "select":      "reason",
            },
            timeout=10,
        )
        r.raise_for_status()
        rows = r.json()
    except Exception:
        return ""

    reasons = [row.get("reason", "").strip() for row in rows if row.get("reason", "").strip()]
    if len(reasons) < 3:
        return ""

    keywords = [
        ("formal", ["formal", "sério", "corporativo", "frio"]),
        ("genérico", ["genérico", "vago", "superficial", "geral", "sem especificidade"]),
        ("longo", ["longo", "extenso", "grande demais", "comprido", "muito texto"]),
        ("curto", ["curto demais", "faltou", "incompleto", "raso"]),
        ("tom errado", ["tom", "linguagem", "voz", "estilo errado", "não combina"]),
        ("hook fraco", ["hook fraco", "sem impacto", "sem força", "sem gancho", "abertura fraca"]),
        ("clichê", ["clichê", "batido", "óbvio", "lugar-comum"]),
        ("sem criatividade", ["sem criatividade", "previsível", "monótono", "entediante"]),
        ("não é orgânico", ["parece anúncio", "muito vendedor", "publicitário demais", "não é orgânico"]),
    ]

    counts = {}
    for label, terms in keywords:
        count = sum(
            1 for reason in reasons
            if any(t in reason.lower() for t in terms)
        )
        if count >= 2:
            counts[label] = count

    if not counts:
        return ""

    sorted_patterns = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    lines = [f"Padrões identificados nas últimas {len(reasons)} rejeições deste cliente:"]
    for label, count in sorted_patterns[:5]:
        lines.append(f"  • '{label}' mencionado {count}x — evite esse padrão proativamente")
    lines.append("  → Ajuste o tom e estrutura desde o início para não repetir esses erros.")

    return "\n".join(lines)
