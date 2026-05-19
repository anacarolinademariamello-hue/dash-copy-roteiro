from __future__ import annotations

import json
import requests
import streamlit as st


# ── Supabase ──────────────────────────────────────────────────────────────────

def _supabase_creds() -> tuple[str, str]:
    try:
        url = st.secrets.get("supabase_url", "") or ""
        key = st.secrets.get("supabase_service_key", "") or ""
        return url, key
    except Exception:
        return "", ""


def _supabase_configured() -> bool:
    url, key = _supabase_creds()
    return bool(url and key)


def _supabase_headers() -> dict:
    _, key = _supabase_creds()
    return {
        "apikey":        key,
        "Authorization": f"Bearer {key}",
        "Content-Type":  "application/json",
        "Prefer":        "return=representation",
    }


@st.cache_data(ttl=120)
def load_clients() -> list[dict]:
    """Carrega clientes ativos do Supabase."""
    if not _supabase_configured():
        return []
    url, _ = _supabase_creds()
    try:
        resp = requests.get(
            f"{url}/rest/v1/clients",
            headers=_supabase_headers(),
            params={
                "active": "eq.true",
                "order":  "name.asc",
                "select": (
                    "key,name,handle,tone_of_voice,bio,tags,observations,"
                    "goals,nicho,sub_nicho,publico_alvo,competitors"
                ),
            },
            timeout=10,
        )
        resp.raise_for_status()
        rows = resp.json()
        return [
            {
                "name":          r["name"],
                "key":           r.get("key") or "",
                "handle":        r.get("handle") or "",
                "tone_of_voice": r.get("tone_of_voice") or "",
                "bio":           r.get("bio") or "",
                "tags":          r.get("tags") or [],
                "observations":  r.get("observations") or "",
                "goals":         r.get("goals") or {},
                "nicho":         r.get("nicho") or "",
                "sub_nicho":     r.get("sub_nicho") or "",
                "publico_alvo":  r.get("publico_alvo") or "",
                "competitors":   r.get("competitors") or "",
            }
            for r in rows
        ]
    except Exception:
        return []


def delete_client_supabase(client_key: str, client_name: str = "") -> tuple[bool, str]:
    """Desativa cliente no Supabase (soft delete — marca active=false)."""
    if not _supabase_configured():
        return False, "Supabase não configurado."
    url, key = _supabase_creds()
    label = client_name or client_key
    try:
        r = requests.patch(
            f"{url}/rest/v1/clients",
            headers={
                "apikey":        key,
                "Authorization": f"Bearer {key}",
                "Content-Type":  "application/json",
                "Prefer":        "return=minimal",
            },
            params={"key": f"eq.{client_key}"},
            json={"active": False},
            timeout=10,
        )
        if r.status_code in (200, 204):
            load_clients.clear()
            return True, f"Cliente '{label}' desativado."
        return False, f"Erro {r.status_code}: {r.text}"
    except Exception as e:
        return False, f"Erro: {e}"


@st.cache_data(ttl=120)
def load_latest_organic_metrics(client_key: str) -> str:
    """
    Busca as métricas orgânicas mais recentes do relatório do cliente no Supabase
    (tabela report_history) e retorna um resumo formatado como texto para o prompt da IA.
    Retorna string vazia se não houver histórico ou Supabase não configurado.
    """
    if not _supabase_configured() or not client_key:
        return ""
    url, key = _supabase_creds()
    try:
        r = requests.get(
            f"{url}/rest/v1/report_history",
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
            params={
                "client_key": f"eq.{client_key}",
                "order":      "generated_at.desc",
                "limit":      "1",
                "select":     "date_from,date_to,metrics",
            },
            timeout=10,
        )
        r.raise_for_status()
        rows = r.json()
        if not rows:
            return ""
        row = rows[0]
        m = row.get("metrics", {})
        if isinstance(m, str):
            try:
                m = json.loads(m)
            except Exception:
                return ""

        period = f"{row.get('date_from', '')[:10]} → {row.get('date_to', '')[:10]}"
        lines = [f"Dados orgânicos do último relatório ({period}):"]

        # Alcance orgânico
        if m.get("total_reach"):
            org_pct = m.get("organic_pct", 0)
            lines.append(
                f"- Alcance total: {int(m['total_reach']):,} ({org_pct:.0f}% orgânico)".replace(",", ".")
            )
        if m.get("org_reach"):
            lines.append(f"- Alcance orgânico: {int(m['org_reach']):,}".replace(",", "."))

        # Taxa de engajamento
        if m.get("org_eng_rate"):
            lines.append(f"- Taxa de engajamento orgânico: {float(m['org_eng_rate']):.2f}%")

        # Seguidores
        if m.get("followers_gained"):
            lines.append(f"- Seguidores ganhos no período: +{int(m['followers_gained'])}")

        # Salvamentos e compartilhamentos (indicadores de conteúdo de valor)
        if m.get("total_saves"):
            lines.append(f"- Salvamentos: {int(m['total_saves']):,}".replace(",", "."))
        if m.get("total_shares"):
            lines.append(f"- Compartilhamentos: {int(m['total_shares']):,}".replace(",", "."))

        # Frequência de postagem
        posting_days = m.get("posting_days", 0)
        total_posts = m.get("total_posts", 0)
        days = m.get("days", 0)
        if posting_days and days:
            lines.append(
                f"- Frequência: {total_posts} posts em {days} dias ({posting_days} dias com publicação)"
            )

        # Performance por formato
        formats = m.get("content_formats", [])
        best_format = m.get("best_format", "")
        if formats:
            lines.append("\nPerformance por formato de conteúdo:")
            for f in formats:
                lines.append(
                    f"  • {f.get('type','')}: {f.get('count',0)} posts | "
                    f"alcance médio {float(f.get('avg_reach', 0)):.0f} | "
                    f"{float(f.get('avg_interactions', 0)):.0f} interações/post | "
                    f"engaj. {float(f.get('avg_eng_rate', 0)):.2f}%"
                )
            if best_format:
                lines.append(f"  → Melhor formato orgânico: {best_format}")
                lines.append(
                    f"  → Priorize criar roteiros nesse formato para maximizar alcance orgânico."
                )

        # Top posts (se disponível)
        top_posts = m.get("top_posts", [])
        if top_posts:
            lines.append("\nTop 3 posts do período (maior alcance):")
            for i, post in enumerate(top_posts[:3], 1):
                topic = post.get("caption_preview", post.get("topic", "sem descrição"))
                reach = post.get("reach", 0)
                eng = post.get("eng_rate", 0)
                fmt = post.get("format", "")
                lines.append(
                    f"  {i}. [{fmt}] Alcance: {int(reach):,} | Engaj: {float(eng):.2f}% — {str(topic)[:80]}".replace(",", ".")
                )
            lines.append(
                "  → Analise o tema e formato desses posts para entender o que ressoa com a audiência."
            )

        # Melhores horários
        best_hours = m.get("best_hours", [])
        if best_hours:
            lines.append("\nMelhores horários para publicar:")
            for h in best_hours[:3]:
                lines.append(
                    f"  • {h.get('label', '')} — média de {float(h.get('avg_interactions', 0)):.0f} interações"
                )

        # Perfil da audiência
        aud = m.get("audience", {})
        if aud:
            aud_parts = []
            pct_f = aud.get("pct_female", 0)
            pct_m = aud.get("pct_male", 0)
            if pct_f or pct_m:
                aud_parts.append(f"{float(pct_f):.0f}% feminino / {float(pct_m):.0f}% masculino")
            if aud.get("dominant_age"):
                aud_parts.append(f"faixa etária dominante: {aud['dominant_age']} anos")
            if aud.get("top_country"):
                pct = aud.get("top_country_pct", 0)
                aud_parts.append(f"{aud['top_country']} ({float(pct):.0f}% da audiência)")
            if aud_parts:
                lines.append(f"\nPerfil real da audiência: {' | '.join(aud_parts)}")
                lines.append(
                    "  → Use esse perfil para calibrar referências culturais, exemplos e tom dos roteiros."
                )

        # Análise estratégica da IA
        ai = m.get("ai_strategic")
        if ai and isinstance(ai, dict):
            strengths = ai.get("strengths", [])
            attentions = ai.get("attentions", [])
            if strengths or attentions:
                import re as _re
                lines.append("\nAnálise estratégica do último relatório:")
                if strengths:
                    lines.append("  Pontos fortes do conteúdo orgânico:")
                    for item in strengths[:3]:
                        text = item[1] if isinstance(item, (list, tuple)) else item.get("text", "")
                        text = _re.sub(r"<[^>]+>", "", str(text))
                        lines.append(f"  • {text}")
                if attentions:
                    lines.append("  Oportunidades e pontos de atenção:")
                    for item in attentions[:3]:
                        text = item[1] if isinstance(item, (list, tuple)) else item.get("text", "")
                        text = _re.sub(r"<[^>]+>", "", str(text))
                        lines.append(f"  • {text}")
                lines.append(
                    "  → Use esses insights para decidir quais temas abordar e como estruturar os roteiros."
                )

        return "\n".join(lines)

    except Exception:
        return ""
