# BotTO — Bot de farm para Talisman Online

## O que é este projeto

Fork de [chestm007/GhostBot](https://github.com/chestm007/GhostBot) adaptado pro time do dono do repo, com foco em **farm de spot fixo** e **cave bot** no MMORPG Talisman Online.

- **Branch local estável:** `minha-versao-estavel`
- **Branch principal upstream:** `master`
- **Plataforma:** **Windows-only** (testaram Wine no Linux, UI funciona mas o server não acha os clients do TO)

## Stack

- **Python 3.11+** (com pip)
- **pymem** — leitura/escrita de memória do processo do jogo (HP, MP, posição, alvo, etc.)
- **pywin32** — APIs Windows (janelas, input simulado)
- **opencv-python + Pillow + numpy** — template matching de ícones (`src/GhostBot/Images/`)
- **tkinter** (stdlib) — UI gráfica em janela (700x490) com abas e botões. `npyscreen + windows-curses` aparecem no `pyproject.toml` mas não são usados pelo `UX/main.py` atual — provavelmente resíduo de uma versão anterior.
- **Tesseract OCR + pytesseract** — leitura de texto da tela (instalado no Sprint 0; Tesseract não fica no PATH por padrão, então o código vai precisar setar `pytesseract.pytesseract.tesseract_cmd`)
- **Build:** `nuitka` (gera `.exe`)

## Como rodar

Dois processos separados que conversam via IPC:

- `ghost-bot-server` (`run_server.py`) — backend, faz a lógica do bot e mexe na memória do jogo
- `ghost-bot-client` (`run_client.py`) — janela tkinter, configura e dispara comandos

Comunicação em `src/GhostBot/IPC/`.

## Onde mora cada coisa em `src/GhostBot/`

| Pasta | Função |
|---|---|
| `IPC/` | Cliente ↔ Servidor |
| `controller/` | Loop principal do bot (`bot_controller.py`), threading, login |
| `functions/` | Comportamentos: `attack`, `buffs`, `regen`, `fairy` (heal de party), `petfood`, `sell`, `delete`, `runner`, `script` |
| `lib/talisman_online_python/pointers.py` | **★ Endereços de memória do TO — quebram a cada update do jogo. Sempre validar.** |
| `lib/` | `vk_codes.py` (teclas), `talisman_ui_locations.py`, `talisman_location_names.py`, `win32/process.py` |
| `UX/` | Tabs da UI: attack, buff, fairy, pet, regen, sell, delete + autologin |
| `Images/` | BMPs pra template-matching (`DELETE/`, `SELL/`, `BC_DELETE/`, `misc/`) |
| `enums/bot_status.py` | Estados do bot |
| `map_navigation.py` | Pathing — só MDV implementado no upstream |
| `image_finder.py` | Wrapper de template matching |

## As 5 classes do jogo

A bot precisa suportar as 5 classes do Talisman Online:

1. **Wizard** — ranged magic DPS
2. **Monk** — melee/híbrido
3. **Assassin** — burst melee, stealth (classe do dono do repo)
4. **Fairy** — healer/support (`functions/fairy.py` cobre parte)
5. **Tamer** — combate com **pet**. Mecânica especial: summon, food, sustain, re-summon se morrer

### Time atual (5 jogadores)
2 Fairy + 1 Wizard + 1 Tamer + 1 Assassin. **Sem Monk no roster ativo** (mas suportado no código).

**2 Fairies no time atual:** ambas focam no tank em modo "tank-focus" e rodam em paralelo. Não precisa de coordenação entre instâncias — basta a config certa nas duas. Detalhe no Sprint 2.

## Roadmap

`PROJECT_PLAN.md` na raiz tem os 6 sprints (Sprint 0 → Sprint 5, mais Sprint 6 opcional, 23/mai → 12/ago).

**Sprint atual: 0 — Fundação** (instalação, Tesseract, validar memory pointers, primeiro farm do Assassin). **Não pule pra mexer em código de feature antes disso.**

## Como trabalhar com o dono do repo

- **Idioma:** responda em **PT-BR** por padrão.
- **Não programa:** explique o "porquê" e o "o quê" antes de fazer. Glossário curto pra jargão (memory pointer, OCR, webhook, etc.) na primeira aparição da sessão.
- **Fluxo preferido:** **explorar → confirmar → executar.** Não edite arquivo sem mostrar o plano antes.
- **Não over-engineerar:** comece com a versão mais simples possível e só adicione coordenação/IPC/dedup quando o dono pedir explicitamente.
- **Memory pointers quebram a cada update do TO** — sempre validar antes de assumir que `pointers.py` está correto.
- **Nunca tocar em senha, autologin, ou contas dos amigos sem confirmação explícita.**

## Subagentes do projeto

Em `.claude/agents/` (já criados, 7 agentes):

| Agente | Quando usar |
|---|---|
| `memory-pointer-finder` | Achar/validar pointers em `pointers.py` |
| `class-rotation-designer` | Desenhar rotações de skill por classe (todas as 5, com atenção especial pro Tamer) |
| `ocr-helper` | Configurar/tunar Tesseract pra texto do jogo |
| `discord-integrator` | Webhook + canais + alertas (escopo Sprint 4, só webhook) |
| `safety-auditor` | Revisar mudanças contra as diretrizes de segurança |
| `cheat-engine-companion` | Guiar sessões de Cheat Engine passo a passo |
| `talisman-online-specialist` | Conhecimento do jogo (mapas, mobs, drops, mecânicas, meta de party) |

## Segurança — princípios duros

- Bot **nunca** lê/escreve a senha do jogo.
- Cliente do jogo só do site oficial.
- Diffs vindos do upstream passam pelo `safety-auditor` antes de merge.
- Pausas longas diárias (4-8h off). Não fazer top 1 de ranking.
- Detalhes completos: ver seção "SEGURANÇA" no `PROJECT_PLAN.md`.

## Referências

- **Upstream:** https://github.com/chestm007/GhostBot
- **Plano completo:** `PROJECT_PLAN.md`
- **Tutoriais externos:** RaaskiBot v3.0 no YouTube (fonte de inspiração de features)
