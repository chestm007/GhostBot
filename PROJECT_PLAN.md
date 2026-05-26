# 📋 PROJETO BotTO — PLANO + STATUS

**Time:** 5 jogadores (2 Fairy + 1 Wizard + 1 Tamer + 1 Assassin)
**Base:** Fork do `chestm007/GhostBot`, branch local `minha-versao-estavel`
**Stack:** Python 3.11+ no Windows 11 + Tesseract OCR + Cheat Engine + Discord Webhook + Tailscale
**Cronograma original:** 23/mai → 12/ago (12 semanas + Sprint 6 opcional)
**Última atualização do doc:** 2026-05-25

---

## 📌 ONDE ESTAMOS AGORA — RESUMO RÁPIDO (2026-05-24)

**Sprint 0 concluída + grande avanço no ciclo de venda/farm e dashboard.** O bot roda, a UI foi reconstruída (PT-BR gamer), e nesta sessão o **ciclo completo de venda foi feito e migrado pra produção**: navegar até o NPC → vender → voltar ao spot, tudo robusto a tamanho/posição de janela.

### 🔥 Feito na sessão 2026-05-24
- ✅ **Navegação por TEMPLATE + OFFSET** (âncora = título do painel): Surroundings, janela "Dialogue" do NPC, dialog de venda, mapa. Resolve coords fixas quebradas. Validado em 4 testes (resize + arrastar painel + reabrir jogo). Δ da barra de título (captura=window coords, clique=client coords) se cancela com offset calibrado por cursor.
- ✅ **Ciclo de venda em PRODUÇÃO** (`sell.py`): Surroundings → "Dialogue" → "Sell Item" → vende 3 bags (slot inicial configurável, clica 30× com reflow) → confirma → volta ao spot pelo mapa (clique-isca pra furar bug do jogo de clique repetido) → espera chegar. Montaria via `mounted()`. Attack pausa/retoma sozinho (loop sequencial + run_at_interval).
- ✅ **Dashboard funcionando 100%**: Target HP (corrigido o gate `is_target_selected` que oscilava), Mobs mortos, Tempo de farm, Energy, **XP ganho (pontos)**, **Gold ganho separado em Gold/Silver/Copper**. Corrigidos 2 bugs que travavam TUDO: lista de chars repovoando a cada poll (tupla≠lista) e **RLock entre threads** travando o refresh automático (só atualizava ao clicar).
- ✅ **XP_POINTER achado** (char struct offset `0x3C8`, int; XP atual no nível, zera ao upar; máximo não é legível → % depende de tabela XP-por-nível, amigos montando). Gold via `get_gold()` (0x410).
- ✅ **Delete REMOVIDO** do app (risco de apagar item sem querer): sem aba, sem checkbox, sem execução. `DeleteConfig` fica dormente só p/ compat de load.
- ✅ **UI**: aba de venda reorganizada (2 sobreposições corrigidas), campo "Spot de farm (mapa)" + botão "Capturar spot" (client-side, sem IPC), aviso "deixe os diálogos à esquerda/visíveis", borda azul nos botões, **atalho "BotTO" no desktop** (pede admin) + `start_botto.bat`.
- ✅ **Pacote pros amigos**: `BotTO_para_amigos.zip` (código + imagens/BMPs + install.bat + start_botto.bat + LEIAME). 0,5 MB, cabe no Discord.

### 🔥 Feito na sessão 2026-05-24 (parte 2 — tarde/noite) — commit `4dee204`
- ✅ **3 bugs reportados pelo dono, corrigidos:**
  1. **Regen "sentava e não voltava a atacar"** — saía do descanso só com HP **e** MP em 100% cravado; se o MP nunca enchia (ex: **Assassin não tem mana**), travava sentado pra sempre. Agora sai ao recuperar **acima do limite com folga** + **timeout de 60s** de segurança. Nova caixa **"Classe sem mana"** (`RegenConfig.ignore_mana`) na aba Regen ignora o MP no descanso. Raio de farm ("Distância máx do spot") agora **40–100** (default 60).
  2. **Sell não achava "Sell Item" (PC do amigo)** — o offset fixo apontava pra **1ª linha do menu** = "Purchase Item" no Blacksmith (abria a janela errada → voltava ao spot). Agora acha "Sell Item" por **IMAGEM** (`sell_items_button.bmp`, threshold 0.85) + novo **`window_to_client()`** converte coord da captura (janela inteira) → área cliente antes de clicar (corrige o Δ da barra de título — a tese antiga estava certa, o palpite de "resolução" estava errado). **Venda REAL validada ao vivo** (gold subiu 435→448). ✅ tarefa "venda real" concluída.
  3. **Stop = botão de EMERGÊNCIA** — checagens de `running` no loop de venda (30 cliques) e no pathing pelo mapa; `trigger_sell_now` roda em **thread registrada** que não ressuscita `running` após Stop; `stop_bot` **força** a parada e espera loop principal + venda manual.
- ✅ **Multi-conta confirmada**: 2+ chars logados rodam em paralelo (threads independentes), cada um na lista à esquerda com seu dashboard. Corrigido o bug de **seleção desselecionando** (set da lista limpava a seleção → preserva por nome agora).
- ✅ **Branding "Talisman Bot"** (pivot de "Automation SpAl"): logo do dono → `logo.png`/`logo.ico`, ícone na janela + barra de tarefas + build do `.exe` (nuitka). **Tema ESCURO** centralizado em `UX/theme.py` (verde/dourado do logo), aplicado em todas as abas. Banner do logo no topo da lista. Start verde / Stop vermelho. Atalho "Talisman Bot" no desktop.
- ✅ **UX**: scroll da **aba inteira** (`ScrollableFrame`; combo achatado, sem scroll próprio); bug do scroll-pra-cima corrigido (só rola com overflow). **Fontes +2** no app todo. Campos **espalhados** (faixas HP/MP full-width, "Tecla Pot" na borda). **Autologin** reorganizado (grid + barra de botões no lugar de `place()` fixo). Tooltip com fonte **preta** (era branco no claro).

### 🔥 Feito na sessão 2026-05-25 — Farm overnight OK + Detecção de drop por OCR
- ✅ **GATE CUMPRIDO: o bot rodou a MADRUGADA INTEIRA (24→25/mai) sem travar** — ciclo farm+venda em produção validado na prática. Destravou o próximo milestone (Sprint 4).
- ✅ **Detecção de DROP pelo chat System (Sprint 4, Etapa 1) — FEITA e validada ao vivo.**
  - **Pivot ponteiro → OCR:** tentamos achar pointer do chat via CE (scan nível 6, base única `client.exe+0x00C7C6CC`), mas **morre no 2º restart** — cada linha do chat é heap realocado (mesmo problema dos itens da bag). OCR é mais robusto e **não quebra em update do TO**.
  - **Como ficou:** acha o chat por **ÂNCORA** (template dos 3 ícones do chat, `Images/misc/chat_anchor.bmp`, match 0.98) + região calibrada por offset relativo à âncora; recorta; trata a imagem (cinza + ampliar 4x + Otsu, `--psm 6`); OCR; extrai nome de `You got the item: [Nome(lvl X)]` casando pelo `[colchete]` (tolerante a erro de OCR; ignora linhas "Congratulations").
  - **Código:** `src/GhostBot/drop_watcher.py` (classe `DropWatcher.poll()` + helpers). Tools: `tools/test_ocr_chat.py` (testa tratamentos), `tools/calibrate_chat_region.py` (calibra a região ao vivo via mouse + âncora), `tools/test_drop_watch.py` (loop ao vivo).
  - **Listas:** `alertas_drop.txt` (raiz) — `[QUERO ALERTA]` (Medium/Large Ruby+Emerald) / `[NAO QUERO]` / fora das duas = "item novo (decidir)". Cada jogador terá a própria cópia.
  - **Teste 60s ao vivo:** detectou `Animal Fur` como NOVO, **dedup OK** (1 alerta em ~35 leituras), priming descarta o que já está na tela, não perdeu drop.
  - **⚠️ capture_window() = ÁREA DO CLIENTE** (não a janela toda); converter cursor com `ScreenToClient`, não `GetWindowRect` (esse inclui borda invisível do DWM).
  - **Raridade pela cor:** o **nome do item vem na COR da raridade** (Animal Fur = nome BRANCO = comum; o prefixo "You got the item:" é amarelo fixo). Filtro "branco não avisa" é viável → **DEFERIDO** (amostrar só o trecho do nome via `image_to_data`; calibrar com mais raridades; fundo de chat opaco ajuda).
- ✅ **Etapa 2 (Discord webhook) FEITA:** `discord_notify.py` (urllib + header `User-Agent` p/ furar o HTTP 403 do Discord). URL em `discord_webhook.txt` (gitignored, nunca commitar). Validado ao vivo (drops postados no canal). Alerta want=🎯, novo=❓, pula "não quero".
- ✅ **Etapa 3 (integração no bot) FEITA:** DropWatch + DeathAlert rodam em **THREAD PARALELA** (`ThreadedBotController._run_monitor`, ~2s, independente do loop, respeita Stop) — resolveu o "às vezes detecta, às vezes não". Dashboard ganhou: painel **"Drops da sessão"** (lista + **contagem x2**) + botões **✅ Quero / ❌ Não quero** (triagem 1 clique → escreve no `alertas_drop.txt`, vira tag) + **barra de AÇÃO ATUAL grifada** (mostra o que o bot faz) + **alerta de MORTE** 💀 (HP=0 → Discord).
- ✅ **"Spot de farm (mapa)" na aba Attack, sincronizado com a Sell** (1 captura = X,Y + offset do mapa); offset movido pra `AttackConfig` (salva mesmo com a aba Sell desativada).
- ✅ **Lote grande de fixes do bot (achados testando):** Regen — recupera até ~95% (não desperdiça pot), descanso máx **16s**, volta a atacar na hora se mob agressivo, recupera ANTES de voltar ao spot, nunca descansa/volta em combate. RETORNO ao spot **HÍBRIDO** (perto=minimapa passos curtos / longe=MAPA aberto com clique-isca), gatilho = slider "Distância máx do spot" (liberado **15-100**), + modo **"voltando"** que insiste até CENTRALIZAR (não para pra brigar no caminho; anti-trava após 6 ciclos). Matou o `_move_to_pos_via_map` (mapa-calculado antigo do upstream que ia pro lugar errado). Contagem de drop **x2** separada do anti-spam do Discord.
- ⏭️ **PRÓXIMO:** **Boss target-lock** (frente 4): flag + caixa de nome na aba Attack → dá TAB até o nome bater e ataca só ele. Depois: mensagem **bonita** no Discord (embeds + cor de raridade + emojis), **filtro por cor de raridade** ("branco não avisa"), e **embutir o Tesseract no `.exe`** (ninguém instala nada). Tudo commitado LOCAL (sem push ainda).

### Próxima sessão começa por:
1. **Tabela de XP-por-nível** (amigos montando) → ligar a **% do XP** no dashboard
2. ✅ ~~Teste do ciclo de venda REAL~~ FEITO. Falta: rodar o ciclo **3-bags automático** no farm real (1 bag validada).
3. **Validar Fairy team buff** + `TEAM_NAME` quando o time conectar
4. ✅ ~~**Detecção de drop + Discord**~~ **COMPLETA** (Etapas 1-3: OCR + webhook + thread paralela + dashboard com triagem + alerta de morte). Próximo grande: **Boss target-lock** (frente 4). Depois: msg bonita Discord (embeds/raridade), filtro por raridade, Tesseract no `.exe`.
5. 🎯 **DECIDIDO: gerar o .exe** (pra os amigos não precisarem instalar Python). Via GitHub Actions → **Build Executable** (rodar 2x: `client` e `server`). Branch `minha-versao-estavel` já está pushado no fork. Falta: disparar o workflow, baixar os 2 .exe, testar (atenção ao path das imagens no binário — já houve bug antes, ver commits #30/#31). Como os .exe são grandes, distribuir por link (não cabe no Discord).

### Como rodar:
- Atalho **BotTO** no desktop (pede admin sozinho) ou `start_botto.bat`.
- Config em `C:\Users\<user>\GhostBot\<charname>.yml` ($HOME, não LOCALAPPDATA — quirk).

---

## ✅ SPRINT 0 — Fundação (23/mai → 03/jun) — **~98% concluída** (só falta "Inventory Full" via OCR)

### Concluído
- ✅ Python 3.11+ instalado + `pip install .` do fork
- ✅ Patches `game.exe → client.exe` (3 lugares: `client_launcher.py`, `threaded_bot_controller.py`, `lib/win32/process.py`)
- ✅ Permissão Admin pra `pymem` (Claude Code + bot rodam como admin)
- ✅ Tesseract OCR instalado (binding `pytesseract` ainda não testado em runtime)
- ✅ Primeira execução `ghost-bot-server` + `ghost-bot-client`
- ✅ **Pointers validados em runtime:**
  - CHAR: name, level, HP, MAX_HP, MP, MAX_MANA, X, Y, location, gold, bag_1, bag_2
  - TARGET: select, ID, **HP (chain original funciona!)**, **name (POINTER_3)**
  - State: dialog, system_menu, notification, in_battle (lê mas retorna 0 sempre — broken)
- ✅ **Sessão CE pro TARGET_HP** — descobriu que o chain `0x012CE2E0 + [0x18, 0x59C, 0x0, 0xC, 0x1F4, 0x15C, 0x480]` **já funcionava**. O `597` que parecia lixo era **HP máximo em escala interna**; o cálculo em `client_window.py` (`(value - 461) / (597 - 461) * 100`) normaliza pra 0-100.
- ✅ **Bot rodou e atacou de fato** com `teste1231245` (Lv 2 em Green Scarp)
- ✅ Char de teste subiu de Lv 1 → Lv 2 durante a validação

### Pendente Sprint 0
- 🔄 OCR: **`pytesseract` validado em runtime + tratamento tunado pro chat** (drop detection, 2026-05-25). ✅ Nome de mob/alvo **resolvido por POINTER** (`get_target_name`, usado no Boss-lock + botão "Pegar alvo"). **Falta só "Inventory Full".**
- ✅ ~~Tutoriais RaaskiBot v3.0 no YouTube~~ — concluído (referência pras features absorvida).
- ✅ ~~Primeiro farm de teste do **Assassin real** do dono~~ — concluído (farm real validado, não mais só char de teste).

---

## 🎨 UX REVOLUTION (extra, não estava no plano original)

Aplicada nesta sessão sobre tudo que o bot já tinha:

### Helpers reutilizáveis em `src/GhostBot/UX/utils.py`
- **`Tooltip`** — popup amarelo seguindo o cursor, fonte 11
- **`create_int_slider`** — slider min-max + entry editável + sufixo. Suporta `hint=` (tooltip) e `bg=` (cor da linha)
- **`create_entry`** — entry de texto/booleano com label, suporta `entry_width=`, `hint=`, `bg=`
- **`ComboWidget`** — combo dinâmico (linhas de tecla+intervalo+remover) com scroll interno (~6 visíveis), botão `+ Adicionar tecla`. Flag `show_tab_button=False` esconde TAB (usado no Buff).
- **`NamedListWidget`** — listbox + entry add + botão `+`/`×`. Usado nas categorias de item.
- **`setup_drag_from_listbox`** + **`widget_in_container`** — drag-and-drop de uma listbox pra outro widget

### Tabs renovadas (todas com PT-BR gamer + tooltips + alinhamento esquerda)
- ✅ **Dashboard** (era Functions) — char info + barra HP do alvo + indicador "EM COMBATE" + stats da sessão (Mobs mortos, Tempo de farm). XP ainda placeholder.
- ✅ **Attack** — faixa vermelha HP / azul MP, sliders %, "Sem dano por (s)" slider, "Distância máx do spot" com tooltip de marcos, Combo dinâmico (com botão "+ TAB" pra trocar alvo), "Spot (X,Y)" com botão "Posição atual"
- ✅ **Regen** — mesmas faixas vermelha/azul (mas com threshold pra sentar fora de combate). "Tecla Sentar" abaixo.
- ✅ **Buff** — slider "Re-buffar a cada", Combo dinâmico **sem TAB** (buff não troca alvo)
- ✅ **Fairy** — heal team + heal self (faixas vermelhas), teclas heal/cure/revive, spot. **NOVO: seção Team Buff** (combo + intervalo + checkbox "Buffar a si"). Lógica em `fairy.py` (`_buff_team`, `_should_buff_team`) — validar quando time conectar.
- ✅ **Pet** — sliders pra resummonar e alimentar (em minutos)
- ✅ **Sell** — config existente + **NOVO: lista de itens da bag (full-width) + 3 categorias (🗑️ Lixo / 📦 Bons / ✨ Super raros) + drag-and-drop** entre bag → categoria
- ✅ **Delete** — só checkbox + slider intervalo

### Janela principal (`main.py`)
- 🎨 **TEMA ESCURO** (2026-05-24, cores do logo) centralizado em `UX/theme.py`: bg `#14201C`, paineis `#1B2B24`, verde `#7CB518`/`#B4FB00`, dourado `#FCB400`. (Era claro azul `#4a90e2` antes.)
- 📐 Layout responsivo (grid + weights) — **redimensionável**
- 🪟 Tabs e log em `tk.PanedWindow` — **divisor arrastável**
- 🔘 Botão Start em estilo "Accent" (azul)
- 📏 Janela 980×680 (min 820×560)

### Bug fixes
- 🐛 `bot_config.rege.hp_key` → `bot_config.regen.hp_key` (typo que fazia Save crashar silencioso)
- 🐛 `_battle_pots` tinha condições HP/MP swapped (checava `battle_hp_pot` mas comparava `battle_mana_threshold`)
- 🐛 Threshold sliders ficavam triggering sempre (ui mandava `60` mas código esperava `0.6`) — agora `_as_decimal` converte automaticamente se valor > 1
- 🐛 Dead code removido: `target_hp_full()` e `is_target_dead()` em `pointers.py`

### Bug fixes (sessão 2026-05-25 — retorno ao spot / regen / venda / drop)
- 🐛 **Regen "sentava e não voltava a atacar"** — `_goto_start_location` exigia dist ≤ 2, mas o clique no minimapa só EMPURRA o char (sem precisão fina) → ficava em nudge infinito, nunca terminava o descanso, nunca atacava. Fix: chega com dist ≤ 8 + desiste se não aproxima + teto de tentativas (commit `21c5090`).
- 🐛 **Retorno ia pro LUGAR ERRADO** ("local que não escolhi") — `move_to_pos` pra dist > 50 caía no `_move_to_pos_via_map` (mapa-calculado do upstream, que erra de lugar). Fix: novo `move_to_pos_minimap()` (só minimapa, relativo ao char); mapa-calculado banido pra movimento in-zone (commit `5463278`).
- 🐛 **Runaway (char andava sem parar "pra esquerda")** — clicar na BORDA do minimapa = auto-walk contínuo no TO + sem timeout. Fix: clique recuado pra DENTRO do minimapa (70% do alcance, char vai e PARA) + timeout 5s (commit `c8e9dbc`).
- 🐛 **Parava pra farmar no meio do caminho de volta** — mob no caminho cancelava a viagem (anti-trava desistia dentro do raio → farmava ali). Fix: modo "voltando" persiste até CENTRALIZAR no spot (não ataca enquanto volta; anti-trava após 6 ciclos) (commit `7b7397c`).
- 🐛 **Congelamento pós-venda (até ~60s parado no spot sem atacar)** — a volta da venda exigia dist ≤ 3, impossível pelo clique no mapa. Fix: reconhece a chegada quando o char PARA de andar (`block_while_moving`) (commit `0f186e2`).
- 🐛 **"Spot de farm (mapa)" sumia com a aba Sell desativada** — o campo salvava na config da Sell; com Sell off o Save descartava (virava None). Fix: campo movido pra `AttackConfig.return_spot_map_offset` (commit `5c77cac`).
- 🐛 **Drop "às vezes detecta, às vezes não"** — o DropWatch lia o chat só ENTRE as ações do loop; em combate pesado lia raramente e o drop sumia. Fix: DropWatch + DeathAlert rodam em THREAD paralela própria (~2s fixos) (commit `7ceb920`).
- 🐛 **Drop contado errado (2 iguais = 1)** — dedup pro Discord também suprimia a contagem do Dashboard. Fix: `poll()` retorna `(alerts, deltas)` — alerts com dedup (Discord não spamma), deltas conta cada ocorrência nova (commit `0bdc26a`).
- 🐛 **Regen desperdiçava pot / sentava demais** — saía do descanso cedo demais e re-sentava. Fix: recupera até ~95% antes de voltar (commit `f4a1340`) + descanso máx 16s e volta a atacar na hora se mob agressivo (commit `045ccbb`).
- 🐛 **Discord HTTP 403** — User-Agent padrão do urllib bloqueado pelo Discord. Fix: header `User-Agent: TalismanBot/1.0` em `discord_notify.py`.

### Nova lógica em `attack.py`
- ✨ **`_wait_resource_refill`** — depois de usar pot HP/MP, bot **para de atacar** e espera o recurso encher (≥95%). Por detecção, não tempo. Sai se HP cai de novo (sob ataque) ou após 30s. Resolve o problema de "atacar interrompe regen do pot".

---

## 🎯 TASKS PENDENTES — Sessão Cheat Engine (consolidado)

| # | Task | Prioridade | O que precisa |
|---|---|---|---|
| #3 | `TEAM_NAME_1` pointer | Baixa | Atual lê `'p2'` quando sozinho. Validar quando time conectar antes de re-achar. |
| #4 | `BATTLE_STATUS` pointer | Baixa | Lê sempre 0. Não crítico (combate detectado indiretamente por HP do alvo caindo). Achar pra UI indicar "EM COMBATE". |
| #5 | ~~`XP_POINTER`~~ ✅ **FEITO** | — | Achado 2026-05-24 no offset `0x3C8` da char struct (sonda dos vizinhos do ENERGY, sem CE). XP atual no nível (zera ao upar). Dashboard mostra XP ganho em PONTOS. Falta só a % (depende da tabela XP-por-nível, amigos montando). |
| #6 | ~~Pointer de **nome de item** na bag~~ ❌ **ABANDONADO** | — | Pivot pra template matching (BMPs em `Images/SELL`). Pointer scan level 4 não sobrevive a restart neste jogo. NÃO re-tentar via CE. |

**Estratégia recomendada:** uma sessão CE única faz todos os 4. Lições aprendidas da sessão do TARGET_HP:
- Scan progressivo (Unknown initial value → Decreased value → Unchanged value) funciona, mas demora
- Para valores que mudam por "evento" (battle status, XP), usar transição 0→1 / N→N+X como filtro
- O endereço calculado pelo chain pode estar certo MAS o offset final estar errado — sempre ler bytes ao redor antes de descartar

---

## 🚧 ITENS NOVOS DISCUTIDOS (não estavam no plano original)

| Feature | Status | Notas |
|---|---|---|
| **Fairy Team Buff** | UI + lógica feitos | Valida quando time conectar |
| **Dashboard com Kills + Tempo** | Funcionando | Detecta kill via transição HP alvo positivo→morto |
| **Categorização de itens (Lixo/Bons/Raros)** | UI completa + drag-and-drop | Lógica de auto-vender/alertar vem em Sprint 4. Precisa task #6 (nomes de itens). |
| **Pausa após pot pra HP encher** | Implementado em `attack.py` | Por detecção, não tempo |
| **Set de team** (configurar nomes dos 4 amigos pra Fairy buffar) | Não iniciado | Aguarda time conectar pra validar TEAM_NAME |

---

## 📅 SPRINT 1 — Multi-classe + Loot + Logística (04/jun → 17/jun)

**Status:** não iniciado. Algumas tarefas relacionadas já adiantadas via UX revolution.

- ⏳ Configuração das 5 classes (Wizard, Monk, Assassin, Fairy, Tamer)
- ⏳ Instalação nos PCs dos 4 amigos
- ⏳ Teste: os 5 farmando simultaneamente
- ⏳ Item Blacklist (Discovery Mode) — **UI parcialmente pronta** via Sell tab (Lixo/Bons/Raros). Falta: lógica de "pegar tudo + log de drops + UI checkbox".
- ⏳ Sistema de Montaria (montar/desmontar + auto-mount em viagem)
- ⏳ Detecção de Mochila Cheia via OCR — **OCR instalado mas não wired**
- ⏳ Star Paths (Farm Spot ↔ Cidade ↔ NPC) — estrutura existe no código
- ⏳ Petfood como módulo independente — **já existe no código**, UI feita
- ⏳ Helper Mode v1 (link 1-pra-1 entre 2 chars)
- ⏳ Cheat Engine: pointers de boss + nome do item no chão

---

## 📅 SPRINT 2 — Cave Bot Genérico (18/jun → 01/jul)

Plano original mantido. Não iniciado.

- Toggle "Cave Mode" separado de Farm Mode
- Dropdown "Papel: TANK / HEALER / DPS" por char
- 3 rotações por char: Farm / Boss-DPS / Boss-Tank
- ✅ **Boss Target Lock por nome configurável** — FEITO (commit `0f186e2`): checkbox "Travar no Boss" + campo "Nome do Boss" na aba Attack; dá TAB até o nome bater e ataca SÓ ele. + botão **"🎯 Pegar alvo"** (commit `0d95dc7`) preenche o nome com o alvo selecionado no jogo (zero digitação). Testado ao vivo, funcionou.
- Lógica TANK / DPS / FAIRY específica
- Painel Debug em tempo real
- Auto-stop e Cave Stats

---

## 📅 SPRINT 3 — Segurança (02/jul → 15/jul)

Plano original mantido. Não iniciado.

- Auto-logoff a 20% HP
- Panic Stop (F12 global)
- Delays variados entre skills
- Detecção de PvP (logoff se atacado)

---

## 📅 SPRINT 4 — Telemetria + Discord + Auto-Venda (16/jul → 29/jul)

**Status:** UI parcial já feita.

- ⏳ Telemetria sessão + histórico + por papel — **Dashboard já tem kills + tempo**
- ⏳ Tier de Itens (5 níveis) — **3 categorias já existem na UI (Lixo/Bons/Raros), expandir pra 5 níveis**
- ✅ Discord Webhook — **COMPLETO (sessão 2026-05-25):** detecção de drop por OCR + webhook (`discord_notify.py`) + thread paralela + dashboard (painel de drops + triagem ✅/❌ + barra de ação + alerta de morte 💀) + **alerta de MOCHILA CHEIA 📦 (vende automático)** + **alertas em EMBEDS** (cards com cor/char/horário; cor por tipo, pronta pra raridade). Falta só: **filtro por cor de raridade** (depende da detecção de raridade) e **Tesseract no .exe**.
- ⏳ Acesso Mobile via Tailscale
- ⏳ Dashboard HTML local (5 chars em tempo real)
- ⏳ Auto-Venda Completa (13 etapas)
- ⏳ Resiliência (retry + modo "só voltar")
- ⏳ Auto-relog básico

---

## 📅 SPRINT 5 — Buffer + Login + Discord Bot (30/jul → 12/ago)

Plano original mantido. Não iniciado.

- Bug fixes
- Lista de contas (senhas encriptadas localmente)
- Discord Bot interativo: `/status`, `/drops`, `/parar`, `/stats`
- Documentação interna pros amigos
- Tag v1.0 no fork

---

## 📅 SPRINT 6 — Pós-Lançamento (opcional)

- BC dedicada (Farmer + Reseter + Shortcuts + Stats)
- Hollow Residuals (quest diária)
- Sistemas anti-detecção avançados

---

## 🔒 SEGURANÇA — Diretrizes Permanentes

- Senha do Talisman diferente de email/outros sites
- Cliente do jogo só do site oficial
- Não compartilhar login entre amigos
- Pausas longas diárias (4-8h desligado)
- Não fazer top 1 de ranking
- Bot **nunca** lê/escreve senha
- Discord do grupo privado, fechado
- Re-auditar diffs antes de puxar update do upstream

---

## 🗂️ ARQUITETURA — Mapa Rápido

```
src/GhostBot/
├── run_server.py             # entry: ghost-bot-server (backend)
├── run_client.py             # entry: ghost-bot-client (UI tkinter)
├── controller/
│   └── bot_controller.py     # BotClientWindow: properties hp/mana/target_hp/etc.
│                             # to_json() envia tudo pro UI via IPC
├── functions/
│   ├── attack.py             # loop principal de combate + _battle_pots + _wait_resource_refill
│   ├── regen.py              # sentar fora de combate
│   ├── fairy.py              # heal team + buff team (NOVO)
│   ├── buffs.py              # buff próprio
│   ├── petfood.py            # Tamer pet
│   ├── sell.py               # path NPC + vender
│   └── delete.py             # deletar lixo
├── lib/talisman_online_python/
│   └── pointers.py           # ★ todos os memory pointers
├── UX/
│   ├── main.py               # janela principal + IPC client UI
│   ├── utils.py              # ★ helpers reutilizáveis (Tooltip, sliders, ComboWidget, NamedList, drag-and-drop)
│   └── tabbed_widget/
│       ├── functions.py      # Dashboard (renomeado)
│       ├── attack_frame.py
│       ├── regen_frame.py
│       ├── buff_frame.py
│       ├── fairy_frame.py
│       ├── pet_frame.py
│       ├── sell_frame.py     # bag + 3 categorias + drag-and-drop
│       └── delete_frame.py
└── config.py                 # dataclasses Config, AttackConfig, FairyConfig, SellConfig…
```

**Config persistido em:** `C:\Users\Owner\GhostBot\{charname}.yml` (HOME, não LOCALAPPDATA)
**Reload de código:** server e client são processos separados. Mudança em `functions/*.py` → reinicia server. Mudança em `UX/*.py` → reinicia client.

---

## 🎬 PRÓXIMA SESSÃO — CHECKLIST DE RETOMADA

1. Ler este `PROJECT_PLAN.md`
2. Confirmar com o dono: time conectado? Assassin pronto pra teste real?
3. Se SIM team conectado → validar `team_name_X` e Fairy team buff
4. Se SIM Assassin pronto → primeiro farm real (não mais char teste)
5. Sessão CE focada nos 4 pointers pendentes (tasks #3, #4, #5, #6)
6. Se tudo OK → começar Sprint 1 (Loot Discovery + auto-mount)

---

## 📚 REFERÊNCIAS

- **Upstream:** https://github.com/chestm007/GhostBot
- **Memory pointers:** `src/GhostBot/lib/talisman_online_python/pointers.py`
- **Glossário rápido:**
  - **Spot:** ponto fixo X,Y onde o bot fica
  - **Combo:** sequência de teclas que o bot dispara em loop
  - **Tier de item:** classificação Lendário > Raríssimo > Raro > Incomum > Comum
  - **Cave Bot:** modo boss runs (cave = caverna)
  - **Helper Mode:** 1 char humano + 1 char bot ajudando
