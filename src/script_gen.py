from __future__ import annotations

import re
import anthropic
import streamlit as st

SCRIPT_TYPES = [
    {
        "id": "curiosidade",
        "nome": "Hook de Curiosidade",
        "cor": "#8b5cf6",
        "cor_bg": "#f5f3ff",
        "instrucao": (
            "Abra com uma lacuna de curiosidade irresistível — algo que o público precisa saber "
            "mas não sabe que não sabe. O hook deve criar uma 'itch' que só é resolvida assistindo/"
            "lendo até o final. Use perguntas, afirmações incompletas ou revelações parciais que forcem "
            "a audiência a continuar."
        ),
    },
    {
        "id": "educacional",
        "nome": "Educacional Rápido",
        "cor": "#3b82f6",
        "cor_bg": "#eff6ff",
        "instrucao": (
            "Entregue 1 insight prático e aplicável de forma direta e clara. Comece pelo valor principal — "
            "não construa até ele, entregue logo. Estrutura: hook → ensinamento → exemplo concreto → "
            "aplicação prática → CTA. O público deve sair sabendo fazer algo que não sabia antes."
        ),
    },
    {
        "id": "storytelling",
        "nome": "Storytelling Pessoal",
        "cor": "#f59e0b",
        "cor_bg": "#fffbeb",
        "instrucao": (
            "Conte uma história real ou verossímil com a qual o público se identifique profundamente. "
            "Arco narrativo: situação inicial → problema/conflito → virada/descoberta → resultado. "
            "Use detalhes específicos que criem imagens mentais. Gera identificação e compartilhamento "
            "porque as pessoas se veem na história."
        ),
    },
    {
        "id": "contraintuicao",
        "nome": "Contra-intuição / POV",
        "cor": "#ef4444",
        "cor_bg": "#fef2f2",
        "instrucao": (
            "Apresente um ponto de vista que vai contra o senso comum do nicho. O hook deve ser "
            "polêmico o suficiente para parar o scroll, mas fundamentado o suficiente para não parecer "
            "clickbait. Explique o raciocínio com clareza e dados. Gera comentários, debates e "
            "compartilhamentos por quem concorda ou discorda."
        ),
    },
    {
        "id": "tendencia",
        "nome": "Tendência / Viral",
        "cor": "#10b981",
        "cor_bg": "#ecfdf5",
        "instrucao": (
            "Adapte um formato viral, trend, meme ou referência cultural ao nicho/tema do conteúdo. "
            "O conteúdo deve parecer completamente nativo da plataforma — alguém que não soubesse que "
            "é um roteiro deveria achar que é espontâneo. Equilibre a tendência com a identidade e "
            "posicionamento do criador."
        ),
    },
]


def _build_prompt(form: dict) -> str:
    # ── Especificações dos tipos de roteiro ──────────────────────────────────
    scripts_spec = "\n".join(
        f"{i + 1}. **{s['nome']}**: {s['instrucao']}"
        for i, s in enumerate(SCRIPT_TYPES)
    )

    # ── Informações do formato ────────────────────────────────────────────────
    formato = form.get("formato", "")
    duracao = form.get("duracao", "")
    formato_tip = form.get("formato_tip", "")
    output_label = form.get("output_label", "Roteiro")

    formato_instrucao = _get_formato_instrucao(formato, duracao, output_label)

    # ── Linhas condicionais ───────────────────────────────────────────────────
    client_line = f"\n- Cliente: {form['client_name']}" if form.get("client_name") else ""
    kw_line = f"\n- Palavras/expressões-chave: {form['palavras_chave']}" if form.get("palavras_chave") else ""
    saz_line = f"\n- Sazonalidade: {form['sazonalidade']}" if form.get("sazonalidade") else ""
    contexto_line = f"\n- Contexto/Tendência atual: {form['contexto_tendencia']}" if form.get("contexto_tendencia") else ""
    nao_fazer_line = f"\n- O que NÃO fazer: {form['nao_fazer']}" if form.get("nao_fazer") else ""
    pontos_chave_line = f"\n\n### Pontos-chave para cobrir:\n{form['pontos_chave']}" if form.get("pontos_chave") else ""
    referencias_line = (
        f"\n\n### Referências de conteúdo (tom/estrutura para se inspirar, não copiar):\n{form['referencias']}"
        if form.get("referencias") else ""
    )
    ideia_line = f"\n\n### Ideia principal:\n{form['ideia_principal']}" if form.get("ideia_principal") else ""

    # ── Tom de voz ────────────────────────────────────────────────────────────
    tov_line = (
        f"\n\n## TOM DE VOZ DO CLIENTE — SIGA RIGOROSAMENTE\n{form['client_tone_of_voice']}"
        if form.get("client_tone_of_voice") else ""
    )

    # ── Métricas orgânicas ────────────────────────────────────────────────────
    metrics_line = (
        f"\n\n## DADOS REAIS DO ÚLTIMO RELATÓRIO ORGÂNICO — USE PARA PERSONALIZAR\n"
        f"{form.get('client_organic_metrics', '')}"
        if form.get("client_organic_metrics") else ""
    )

    # ── Padrões de rejeição ───────────────────────────────────────────────────
    patterns_line = (
        f"\n\n## PADRÕES DE REJEIÇÃO RECORRENTES — EVITE PROATIVAMENTE\n"
        f"{form.get('client_rejection_patterns', '')}"
        if form.get("client_rejection_patterns") else ""
    )

    # ── Perfil do cliente ─────────────────────────────────────────────────────
    client_profile_parts = []
    if form.get("client_bio"):
        client_profile_parts.append(f"- Descrição: {form['client_bio']}")
    if form.get("client_publico_alvo"):
        client_profile_parts.append(f"- Público-alvo cadastrado: {form['client_publico_alvo']}")
    if form.get("client_tags"):
        tags = form["client_tags"]
        if isinstance(tags, list):
            tags = ", ".join(tags)
        client_profile_parts.append(f"- Áreas de atuação: {tags}")
    if form.get("client_competitors"):
        client_profile_parts.append(f"- Concorrentes/Referências: {form['client_competitors']}")
    if form.get("client_observations"):
        client_profile_parts.append(f"- Observações importantes: {form['client_observations']}")

    client_profile_line = (
        f"\n\n## PERFIL DO CLIENTE\n" + "\n".join(client_profile_parts)
        if client_profile_parts else ""
    )

    # ── Roteiros aprovados ────────────────────────────────────────────────────
    approved_scripts = form.get("client_approved_scripts", [])
    approved_line = ""
    if approved_scripts:
        sorted_scripts = sorted(
            approved_scripts,
            key=lambda c: int(c.get("hook_score_num") or 0),
            reverse=True,
        )
        examples = []
        for s in sorted_scripts[:5]:
            hook = s.get("hook_texto", "").strip()
            roteiro = s.get("roteiro", "").strip()
            tipo = s.get("tipo_nome", "")
            score = s.get("hook_score", "").strip()
            score_str = f" | Hook: {score}" if score else ""
            if hook:
                examples.append(
                    f"[{tipo}{score_str}]\n"
                    f"Hook: {hook}\n"
                    f"Roteiro: {roteiro[:200]}{'...' if len(roteiro) > 200 else ''}"
                )
        if examples:
            approved_line = (
                "\n\n## ROTEIROS APROVADOS PARA ESTE CLIENTE — REFERÊNCIA DE ESTILO E TOM\n"
                "Ordenados por hook score. Os primeiros são os mais eficazes.\n\n"
                + "\n\n".join(examples)
            )

    # ── Roteiros rejeitados ───────────────────────────────────────────────────
    rejected_scripts = form.get("client_rejected_scripts", [])
    rejected_line = ""
    if rejected_scripts:
        examples = []
        for s in rejected_scripts[:5]:
            hook = s.get("hook_texto", "").strip()
            reason = s.get("reason", "").strip()
            tipo = s.get("tipo_nome", "")
            if hook and reason:
                examples.append(f"[{tipo}]\nHook rejeitado: {hook}\nMotivo: {reason}")
        if examples:
            rejected_line = (
                "\n\n## ROTEIROS REJEITADOS — EVITE ESTES PADRÕES\n"
                "Estes roteiros foram reprovados. Entenda os motivos e não repita os erros.\n\n"
                + "\n\n".join(examples)
            )

    # ── Emoji preference ──────────────────────────────────────────────────────
    emoji_pref = form.get("emoji_pref", "Usar emojis")
    emoji_instrucao = {
        "Usar emojis": "Use emojis de forma moderada e estratégica — apenas onde agregam contexto real.",
        "Mínimo de emojis": "Use no máximo 1-2 emojis por roteiro, apenas se absolutamente necessário.",
        "Sem emojis": "NÃO use emojis em hipótese alguma — nem no roteiro, nem na legenda.",
    }.get(emoji_pref, "Use emojis de forma moderada.")

    prompt = f"""Você é um estrategista de conteúdo orgânico sênior especialista no mercado brasileiro de redes sociais. \
Você cria EXCLUSIVAMENTE conteúdo orgânico — posts que não parecem anúncios, que educam, entretêm, inspiram e constroem comunidade. \
Seu trabalho é criar roteiros que geram alcance orgânico, salvamentos, compartilhamentos e seguidores fiéis.

IMPORTANTE: Este NÃO é conteúdo pago. É conteúdo orgânico que deve parecer autêntico, nativo da plataforma e humano. \
Nunca use linguagem publicitária, nunca crie urgência artificial, nunca use frases de vendedor.

## BRIEFING DO CONTEÚDO

- **Nicho:** {form.get('nicho', '')} › {form.get('sub_nicho', '')}
- **Tema/Produto:** {form.get('produto_tema', '')}
- **Público-Alvo:** {form.get('publico_alvo', '')}
- **Formato:** {formato} ({duracao})
- **Plataforma:** {form.get('plataforma', '')}
- **Objetivo:** {form.get('objetivo', '')} — {form.get('objetivo_desc', '')}
- **Pilar de conteúdo:** {form.get('pilar', '')}
- **Tipo de hook preferido:** {form.get('tipo_hook', '')}
- **CTA orgânico:** {form.get('cta', '')}
- **Tom de voz:** {form.get('tom', '')}{client_line}{kw_line}{saz_line}{contexto_line}{nao_fazer_line}
{ideia_line}{pontos_chave_line}{referencias_line}
{client_profile_line}{tov_line}{metrics_line}{patterns_line}{approved_line}{rejected_line}

## FORMATO ESPECÍFICO: {formato}

{formato_tip}

{formato_instrucao}

## SUA TAREFA

Gere EXATAMENTE 5 variações de roteiro para este conteúdo, cada uma com abordagem distinta:

{scripts_spec}

Para cada variação, entregue:

**HOOK:** Os primeiros 2-3 segundos do vídeo OU a primeira linha do texto — o elemento mais crítico. \
Deve parar o scroll imediatamente. Escreva exatamente o que será dito/mostrado.

**ROTEIRO:** O desenvolvimento completo do conteúdo adaptado ao formato ({output_label}). \
Seja específico e detalhado conforme as instruções do formato acima.

**LEGENDA:** A legenda completa para o post (com hook, corpo e CTA). \
Deve funcionar como conteúdo independente mesmo sem ver o vídeo/imagem.

**HASHTAGS:** 5 a 10 hashtags relevantes (sem o #).

## REGRAS OBRIGATÓRIAS PARA CONTEÚDO ORGÂNICO

**Autenticidade:**
- O conteúdo deve parecer espontâneo e humano — nunca roteirizado demais
- Evite linguagem corporativa ou publicitária
- Use a voz e o vocabulário real do criador/cliente
- Detalhes específicos sempre vencem generalidades

**Hook orgânico:**
- Primeiros 2-3 segundos são tudo — se não prender, ninguém assiste
- Tipos de hook que funcionam: curiosidade, contra-intuição, promessa de valor, storytelling, dado chocante
- NUNCA comece com "Olá", "E aí", saudações ou apresentações
- O hook deve criar uma pergunta na mente do espectador que ele PRECISA responder

**Estrutura:**
- Ritmo: frases curtas, pausas estratégicas, uma ideia por vez
- Entregue valor REAL — o público deve aprender, se divertir ou se inspirar de verdade
- CTA orgânico ao final: "{form.get('cta', 'Salva esse post!')}"

**Proibições:**
- Não use: "não perca", "corra", "oportunidade única", "revolucionário", "milagroso"
- Não faça promessas que o criador não pode cumprir
- Não use a estrutura "Não é X. É Y." em nenhuma variação
- Não escreva de forma genérica — cada roteiro deve ser específico para {form.get('produto_tema', 'o tema')}

**Emojis:** {emoji_instrucao}

## FORMATO DE RESPOSTA

Use EXCLUSIVAMENTE o formato XML abaixo. Não use JSON. Não adicione texto fora das tags XML.

Para cada roteiro, inclua <hook_score> com pontuação de 1 a 10 seguida de justificativa de 1 linha \
(ex: "9/10 — abre lacuna de curiosidade irresistível sobre tema específico do nicho").

<scripts>
<script>
<tipo_id>curiosidade</tipo_id>
<tipo_nome>Hook de Curiosidade</tipo_nome>
<hook_texto>Texto exato dos primeiros 3 segundos / primeira linha do conteúdo</hook_texto>
<roteiro>Desenvolvimento completo do roteiro/conteúdo adaptado ao formato</roteiro>
<legenda>Legenda completa para o post (com hook, corpo e CTA)</legenda>
<hashtags>hashtag1, hashtag2, hashtag3, hashtag4, hashtag5</hashtags>
<hook_score>X/10 — justificativa de 1 linha</hook_score>
</script>
<script>
<tipo_id>educacional</tipo_id>
<tipo_nome>Educacional Rápido</tipo_nome>
<hook_texto>...</hook_texto>
<roteiro>...</roteiro>
<legenda>...</legenda>
<hashtags>...</hashtags>
<hook_score>...</hook_score>
</script>
<script>
<tipo_id>storytelling</tipo_id>
<tipo_nome>Storytelling Pessoal</tipo_nome>
<hook_texto>...</hook_texto>
<roteiro>...</roteiro>
<legenda>...</legenda>
<hashtags>...</hashtags>
<hook_score>...</hook_score>
</script>
<script>
<tipo_id>contraintuicao</tipo_id>
<tipo_nome>Contra-intuição / POV</tipo_nome>
<hook_texto>...</hook_texto>
<roteiro>...</roteiro>
<legenda>...</legenda>
<hashtags>...</hashtags>
<hook_score>...</hook_score>
</script>
<script>
<tipo_id>tendencia</tipo_id>
<tipo_nome>Tendência / Viral</tipo_nome>
<hook_texto>...</hook_texto>
<roteiro>...</roteiro>
<legenda>...</legenda>
<hashtags>...</hashtags>
<hook_score>...</hook_score>
</script>
</scripts>"""

    return prompt


def _get_formato_instrucao(formato: str, duracao: str, output_label: str) -> str:
    """Retorna instruções específicas de roteiro para cada formato."""
    if "Reels" in formato or "Short" in formato:
        return f"""Para este {output_label} ({duracao}), estruture assim:

**[HOOK — 0 a 3 segundos]**
Escreva a fala exata de abertura. Deve prender imediatamente.

**[DESENVOLVIMENTO]**
Escreva cada trecho falado em blocos curtos, como o criador vai falar.
Use indicações de pausa/corte entre os blocos se necessário.
Ritmo rápido — máximo 15-20 palavras por trecho.

**[CTA — últimos 3 segundos]**
Fala exata do CTA. Direto e natural.

Obs: Escreva exatamente o que será dito — como um roteiro de teatro. Não use descrições de câmera ou direção."""

    elif "Stories" in formato:
        return f"""Para esta {output_label} ({duracao}), estruture slide por slide:

Para cada slide, escreva:
- **Slide X:** Texto exato que aparece na tela (máximo 2-3 frases curtas)
- Se tiver fala narrada: escreva o áudio separado do texto na tela
- Indique onde há suspense ou cliffhanger entre slides

Use a lógica: Slide 1 = hook → slides do meio = desenvolvimento → último slide = CTA/revelação"""

    elif "Carrossel" in formato:
        return f"""Para este {output_label} ({duracao}), estruture slide por slide:

**Slide 1 (Capa/Hook):** Headline irresistível — o único motivo para alguém passar o dedo
**Slides intermediários:** Um insight/ensinamento por slide. Título + 2-3 linhas de texto
**Último slide:** CTA claro + identidade do criador

Escreva os textos exatos de cada slide. Priorize clareza e simplicidade."""

    elif "Post Feed" in formato:
        return f"""Para este {output_label} ({duracao}), o roteiro É a legenda. Estruture assim:

**[HOOK — 1ª linha]**
A primeira linha precisa ser a mais forte — é o que aparece antes do "ver mais".

**[CORPO]**
Desenvolva o conteúdo com parágrafos curtos (2-3 linhas máximo).
Deixe linhas em branco entre parágrafos para facilitar a leitura.

**[CTA]**
Termine com um CTA que gere engajamento (salvar, comentar, compartilhar).

Obs: Para Post Feed, o campo "legenda" será o mesmo que o "roteiro"."""

    else:
        return f"""Para este {output_label}, escreva o conteúdo completo adaptado ao formato {formato} ({duracao})."""


def _extract_tag(text: str, tag: str) -> str:
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return match.group(1).strip() if match else ""


def _parse_xml_response(raw: str) -> list[dict]:
    scripts = []
    blocks = re.findall(r"<script>(.*?)</script>", raw, re.DOTALL)
    for block in blocks:
        scripts.append(
            {
                "tipo_id":   _extract_tag(block, "tipo_id"),
                "tipo_nome": _extract_tag(block, "tipo_nome"),
                "hook_texto": _extract_tag(block, "hook_texto"),
                "roteiro":   _extract_tag(block, "roteiro"),
                "legenda":   _extract_tag(block, "legenda"),
                "hashtags":  _extract_tag(block, "hashtags"),
                "hook_score": _extract_tag(block, "hook_score"),
            }
        )
    return scripts


def generate_scripts(form: dict) -> list[dict]:
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY") or st.secrets.get("anthropic_api_key")
    except Exception:
        api_key = None

    if not api_key:
        raise ValueError(
            "Chave ANTHROPIC_API_KEY não encontrada em .streamlit/secrets.toml."
        )

    client = anthropic.Anthropic(api_key=api_key)
    prompt = _build_prompt(form)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=7000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    scripts = _parse_xml_response(raw)

    if not scripts:
        raise ValueError(
            f"Não foi possível interpretar a resposta da IA. Trecho:\n{raw[:500]}"
        )

    type_map = {s["id"]: s for s in SCRIPT_TYPES}
    for script in scripts:
        tid = script.get("tipo_id", "")
        if tid in type_map:
            script["cor"] = type_map[tid]["cor"]
            script["cor_bg"] = type_map[tid]["cor_bg"]

    return scripts
