# 📋 PROJETO BotTO — PLANO + STATUS

**Time:** 5 jogadores (2 Fairy + 1 Wizard + 1 Tamer + 1 Assassin)
**Base:** Fork do `chestm007/GhostBot`, branch local `minha-versao-estavel`
**Stack:** Python 3.11+ no Windows 11 + Tesseract OCR + Cheat Engine + Discord Webhook + Tailscale
**Cronograma original:** 23/mai → 12/ago (12 semanas + Sprint 6 opcional)
**Última atualização do doc:** 2026-05-27

---

## 🔖 RETOMAR AQUI — 2026-05-27 (sessão 4 — Cave Boss Bot: 3 papéis + cooldown de pots)

**Onde paramos:** **Cave Boss Bot CONSTRUÍDO** — aba "Boss" dinâmica (dropdown de papel) com os **3 papéis (Tank/DPS/Fairy)**; regra "Boss é só Boss" (liga Boss → bloqueia o resto); cooldown de pots de 16s no bot todo. **Falta só o dono VALIDAR o Boss ao vivo** (avisou que testa e dá retorno). Antes: Fairy Helper validado, detecção de clients consertada. Frentes abertas: validar o Boss; Bug 1 do Defender (PRIORIDADE quando o dono pedir); distribuir o `.exe`.

- 🐉 **CAVE BOSS BOT — 3 PAPÉIS FEITOS (2026-05-27), spec em `CAVE_BOSS_BOT.md`:** aba "Boss" = runner novo separado (`functions/boss.py` + `BossConfig`); dropdown de Papel muda os campos (ideia do dono). **TANK:** trava no boss + combo + buffs a cada Xs (só aperta a tecla; NÃO pota — as Fairies curam). **DPS:** bate; puxou aggro (perdeu HP em combate) → F1 → espera sair de combate → TAB → volta; MP baixo → F1 → espera → pot → TAB → volta. **FAIRY:** spama a cura no ALVO ATUAL (jogador troca o alvo; não lê HP de outros). Regra "Boss só Boss" na UI. ⏳ A VALIDAR ao vivo (esp. DPS: gatilho de aggro pode precisar de limiar p/ AoE leve).
- 💊 **POTS: cooldown de 16s (geral)** — pot no TO é regen ao longo de ~16s; o bot re-potava (pot duplicado). Fix em attack/boss/regen (`Runner._pot_ready/_use_pot`). Vale pro farm normal também.
- ⚔️ **ABA ATTACK ganhou SELETOR DE CLASSE (DPS/Tamer/Fairy) (2026-05-27), a validar:** dropdown no topo (igual ao Boss) que adiciona os EXTRAS por classe — o combo segue genérico. **DPS** (padrão) = comportamento ATUAL intacto (`char_class=None`). **Tamer**: campo "Tecla ataque do pet" → o bot manda o pet atacar AO PEGAR cada novo alvo (`_command_pet`). **Fairy**: ao cair do "Pot HP em %", ela aperta a **tecla de cura** (em vez de pot de vida — ela se cura); MP segue por pot.
- 🐾 **PET RECONSTRUÍDO (2026-05-27), a validar ao vivo — DOIS tipos, cada um com flag (pedido do dono):** `functions/petfood.py` + aba Pet refeitas (eram cascas). **(1) Pet do TAMER (combate)** [flag `tamer_pet`]: invoca no Start, **re-invoca se morrer** (detecta `pet_active` a cada ciclo), alimenta a cada X min, re-invocação periódica OPCIONAL. **(2) Pet NORMAL (companheiro)** [flag `normal_pet`]: só alimenta a cada X min (comida própria `normal_food`). Os campos de cada bloco aparecem quando a flag é marcada. Combate do pet = aba Attack (combo). ⏳ A confirmar: o pet do Tamer ataca sozinho ou precisa de tecla no combo? expira no tempo (precisa do timer de re-invocar)?
- ✅ **Fairy auto-cura CONFIRMADA 100% ao vivo (2026-05-27):** HP da própria Fairy < 50% → **F1 → cura → aguarda conjuração → re-seleciona 1º membro → P**. Funciona. Nota: `heal_self_threshold` NÃO tem campo na UI (`fairy_frame.py`) → cai sempre no default 50% (`fairy.py:100`). Mudar o limite hoje exige código (não foi pedido). **Frente da Fairy FECHADA.**
- ✅ **BUG da detecção de clients RESOLVIDO** (`controller/bot_controller.py:_scan_for_clients`): se o bot abria ANTES dos clients, eles não apareciam na lista até reiniciar o bot. Causa: o atalho do scan pulava se o conjunto de PIDs não mudasse — mas um client aberto na tela de login (name=None) tem o mesmo PID depois de logar, então nunca era re-avaliado. Fix: só pula o scan se nada mudou **E** todo processo rodando já é um client na lista (`all_registered`). **Validado ao vivo** (abriu bot → abriu client depois → apareceu sozinho). Teste `test_async_bot_controller` passa.
- ⏪ **(05-26) BUG RAIZ do "Fairy se auto-seleciona" RESOLVIDO** (saga de VÁRIAS sessões): `get_with_case` em `lib/vk_codes.py` somava `+0x20` em letras MAIÚSCULAS → a tecla 'seguir' `P`(0x50) virava **`0x70 = F1 = auto-selecionar a si mesmo`**. Fix: `return vk_codes[_key.lower()]` sempre. Validado ao vivo.
- ⏪ **(05-26) Seleção de membros do grupo VALIDADA — tudo BACKSTAGE:** **F1** = self; **clique backstage** (`left_click` do bot = SendMessage) = membro. Coords `team_1..team_4` validadas (1024x768; ~81px). ⚠️ **NÃO usar mouse REAL** (`SetCursorPos`) — decisão do dono.
- 🧪 **AMIGOS TESTARAM o pacote `.exe` (2026-05-27) → 2 bugs reportados (prints `Bug1.png`/`Bug2.png` em `OneDrive\Desktop\TO Bot\`):**
  - 🔴 **BUG 1 (PRIORIDADE — RESOLVER ASSIM QUE O DONO PEDIR):** a **interface não abre** na máquina do amigo — só a janela preta do servidor (`run_server.exe`) abre; o `run_client.exe` não. Causa quase certa: **Windows Defender bloqueia o `run_client.exe` na execução** (falso-positivo do nuitka, JÁ conhecido — na máquina do dono foi resolvido com exclusão de pasta no Defender; os amigos não têm). O `Iniciar BotTO.bat` confere se o arquivo EXISTE (existe), mas não detecta que o Defender mata a execução. Amigo usa **Windows Defender padrão**. ⏳ Aguardando diagnóstico do amigo (dois cliques só no `run_client.exe` → o que aparece). **NÃO reempacotar ainda** — acumular mudanças antes.
  - ✅ **BUG 2 (CONSERTADO):** `Criar atalho do Talisman Bot.bat` falhava com `DirectoryNotFoundException` ao salvar o atalho — chutava `%USERPROFILE%\Desktop`, que não existe quando o OneDrive redireciona a Área de Trabalho (padrão Win11). Fix: descobre o Desktop real via `[Environment]::GetFolderPath('Desktop')` (com fallback). Aplicado nas 2 cópias (repo + pasta do pacote). Não bloqueava (já tinha plano B), só assustava.
- ▶️ **PRÓXIMOS PASSOS:** (1) dono **valida o Cave Boss ao vivo** (vai testar e dar retorno); (2) acumular mudanças no pacote (Bug 1 + Boss + pots) ANTES de gerar o novo `.exe`/zip; (3) quando o dono pedir: atacar o **Bug 1 (Defender)** e só então reempacotar + redistribuir pros amigos.
- ⚠️ **Importante:** o ícone "Talisman Bot" (`start_botto.bat`) roda os console scripts (`ghost-bot-server.exe`/`ghost-bot-client.exe` da pasta Python) = **install editável = roda o FONTE ao vivo**. NÃO é o `run_server.exe` velho da raiz. Clicar no ícone JÁ roda o código novo.

---

## 📦 Sessão anterior (2026-05-26 manhã) — pacote `.exe` pros amigos

**Onde paramos:** montando o **pacote `.exe` pros amigos**. Server validado, client buildando.

- ✅ **`gh` CLI instalado** (`winget install GitHub.cli`, v2.92.0) **e logado** como `LpiresUrt` (escopos repo+workflow). Fica em `C:\Program Files\GitHub CLI\gh.exe` (não entra no PATH sozinho → `$env:Path += ';C:\Program Files\GitHub CLI'`). ⚠️ Repo tem 2 remotes → **sempre `-R LpiresUrt/BotTO`** no `gh` (senão mira no upstream `chestm007` = HTTP 403). Agora dá pra disparar/baixar build pela linha de comando.
- ✅ **SERVER BUILD #2 = SUCCESS** (run `26450634537`, 15m16s, correção `43e4afb`). `run_server.exe` (55,7 MB) instalado em `C:\Bot\BotTO` (build #1 → `.build1.bak`). **Smoke test passou:** log = `Images path detected...` + `Server listening...`, **sem** o `ModuleNotFoundError: pytesseract` do build #1. Imagens embutidas + IPC OK.
  - 📥 **Download do artifact:** `gh run download` FALHA (`archive: false` no workflow → artifact é o exe CRU, não zip). Baixar pela API: `Invoke-WebRequest .../actions/artifacts/<id>/zip -Headers @{Authorization="Bearer $(gh auth token)"}` (o arquivo vem com assinatura `MZ` = exe direto).
- 🔴 **DESCOBERTA: o Tesseract NÃO embute no `.exe`.** O nuitka (`--include-data-dir`/`--include-data-files`) **ignora `.dll`/`.exe`** de propósito → só o `tessdata/` entrou no binário, o `tesseract.exe`+DLLs ficaram de fora. Passava despercebido na máquina de dev (cai no Tesseract do sistema), mas quebraria o OCR na máquina do amigo.
  - ✅ **SOLUÇÃO (validada): Tesseract vai como PASTA `Tesseract-OCR/` AO LADO do `.exe`** no zip (não dentro). O `_find_tesseract` já procura `pasta_do_exe/Tesseract-OCR/tesseract.exe` antes do fallback. Pro amigo é idêntico (extrai, clica, zero instalação). **`run_server.exe` atual já serve** — não precisa rebuildar por isso. Pasta montada com `python tools/make_portable_tesseract.py` (72 MB, roda sozinha).
  - 🧹 TODO (não bloqueia): tirar o passo de embutir Tesseract do `build-executable.yml` (não funciona, só infla o .exe).
- ✅ **CLIENT BUILD OK** (run `26452436569`; 1ª tentativa o Upload Artifact falhou — transitório — `gh run rerun --failed` resolveu). Smoke test passou.
- ⚠️ **Defender bloqueou o `run_client.exe`** (falso-positivo de nuitka; o server passou). Resolvido com exclusão escopada na pasta do pacote (`C:\Bot\Talisman Bot`) + rebaixar lá. ⚠️ exclusão ainda ativa: `Remove-MpPreference -ExclusionPath "C:\Bot\Talisman Bot"` quando não precisar.
- ✅ **PACOTE MONTADO E VALIDADO: `C:\Bot\Talisman Bot.zip` (139 MB).** Extração testada (motor do Explorer) = estrutura correta.
- ▶️ **PRÓXIMO PASSO:**
  1. Dono sobe o `Talisman Bot.zip` num link (Drive/WeTransfer — 139 MB não cabe no Discord 25 MB) e manda pros 4 amigos.
  2. **Validar OCR ao vivo** (pendente): rodar `run_server.exe` da pasta do pacote com o JOGO aberto + farmar → drop no painel/Discord = Tesseract da pasta-irmã OK.
  3. (Opcional) limpar o passo de embutir Tesseract do `build-executable.yml`; remover a exclusão do Defender.

**📦 PACOTE PARA OS AMIGOS (versão `.exe` — ZERO instalação):**
O dono monta e **manda o zip COMPLETO** pros 4 amigos. Conteúdo:
  - `run_server.exe` + `run_client.exe`
  - **pasta `Tesseract-OCR/`** (ao lado dos exes — o OCR de drop depende dela; ~72 MB)
  - `Images/`? NÃO — as imagens (.bmp) já estão embutidas nos exes.
  - `Iniciar BotTO.bat` (abre servidor + interface com 1 clique, pede admin) — local, gitignorado
  - `LEIAME.txt` (instruções) — local, gitignorado
  - `alertas_drop.txt` (lista de alertas default)
  - ✅ `discord_webhook.txt` **do dono, COMPARTILHADO** (decisão 2026-05-26) → feed central; se vazar, apagar+recriar.
  - Amigos só precisam do **jogo instalado** (site oficial). NÃO abrem o servidor na mão (o `.bat` sobe os dois).
- 🎨 **ÍCONES:** os `.exe` já saem com a logo (build embute `logo.ico`). O `.bat` não aceita ícone próprio → incluir um **`Criar atalho do Talisman Bot.bat`** que o amigo roda 1× e gera um atalho com a logo na Área de Trabalho dele (atalho `.lnk` feito aqui quebra lá por caminho absoluto).
- 🏷️ **Renomear "GhostBot"?** Decidido NÃO mexer no nome interno (pacote/imports, ~398×): risco alto, zero ganho visível. O que o amigo vê já é "Talisman Bot" (título, logo, ícone, LEIAME). Único semi-visível = pasta de config `~/GhostBot`.

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

## ✅ SPRINT 0 — Fundação (23/mai → 03/jun) — **100% concluída** ("Inventory Full" via OCR FEITO)

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

### Bug fixes (sessão 2026-05-26 — empacotamento `.exe` pros amigos)
- 🐛 **Dashboard travado em "loading." no `.exe`** (combate funcionava, mas sem dados na tela) — um **submódulo externo** (`GhostBot/lib/talisman_online_python` → repo do `chestm007`) empacotava uma versão ANTIGA do `pointers.py` SEM `get_xp` → `to_json` estourava `AttributeError` a cada poll → a interface nunca recebia os dados. Fix: submódulo **REMOVIDO** (fork autossuficiente) + `submodules: recursive` tirado dos 3 workflows (commit `d625eed`).
- 🐛 **Discord não postava + watchlist vazia no `.exe`** — `discord_webhook.txt` e `alertas_drop.txt` não eram achados (o código não olhava na pasta do `.exe`, só em `~/GhostBot`, raiz-do-repo e temp). Fix: candidatos passam a incluir a pasta do exe (`sys.argv[0]`), igual o `_find_tesseract` (commit `8ba1d4a`).
- 🐛 **Tesseract não embutia no `.exe`** — nuitka ignora `.dll`/`.exe` no `include-data-dir`. Fix: Tesseract vai como **pasta ao lado** do exe no pacote (`_find_tesseract` já procura lá); validado.
- 🐛 **Build #1 do server crashava** — `pytesseract` faltava nas deps do `pyproject.toml` + `Images/` não-embutida. Fix: commit `43e4afb`.
- ✨ **Interface auto-recupera a lista de personagens** — fechar e reabrir a interface não some mais com o char (pede a lista a cada ~3s) (commit `cfd34e9`).

### Bug fixes (sessão 2026-05-26 — parte 2: Fairy "auto-select" + auto-cura)
- 🐛 **Fairy se auto-selecionava / curava a SI MESMA** (bug histórico, várias sessões de debug) — `get_with_case` (`lib/vk_codes.py`) somava `+0x20` em letras MAIÚSCULAS → a tecla 'seguir' `P`(0x50) virava **`0x70 = F1 = auto-selecionar a si mesmo`**. Cada P (seguir) → se selecionava → o `2` (cura) seguinte curava ela. Fix: `return vk_codes[_key.lower()]` sempre (VK não tem caixa; consertou TODA letra maiúscula, ex.: 'A' virava numpad). Validado ao vivo. **NÃO era** clique fantasma / código velho / `.exe` stale / TAB / auto-login (todos descartados no caminho).
- 🧹 Removida a instrumentação de debug do `left_click` (`client_window.py`) que sobrou do diagnóstico.
- ✨ **Fairy Helper: AUTO-CURA** (`fairy.py`, pendente teste ao vivo) — se a HP DELA < `heal_self_threshold` (default 50%): **F1 → cura → aguarda conjuração → clica 1º membro → P**. + o Helper agora SELECIONA o aliado (clique backstage no 1º membro, `_select_ally`) a cada ciclo — não depende mais de pré-seleção manual.

### Bug fixes (sessão 2026-05-27 — Fairy auto-cura confirmada + detecção de clients + bugs dos amigos)
- ✅ **Fairy auto-cura validada 100% ao vivo** — o fluxo F1→cura→re-seleciona 1º membro→P funciona. Frente da Fairy fechada.
- 🐛 **Clients não apareciam na lista se o bot abria ANTES deles** (`controller/bot_controller.py:_scan_for_clients`) — o atalho que pula o scan comparava só o conjunto de PIDs; um client aberto na tela de login (name=None) mantém o mesmo PID depois de logar → nunca era re-avaliado → só aparecia reiniciando o bot. Fix: só pula o scan se nada mudou **E** todo processo rodando já virou client na lista (`all_registered`). Validado ao vivo; teste `test_async_bot_controller` passa.
- ✅ **(amigo) Atalho não criava — `DirectoryNotFoundException`** (`Criar atalho do Talisman Bot.bat`) — chutava `%USERPROFILE%\Desktop`, inexistente quando o OneDrive redireciona a Área de Trabalho. Fix: Desktop real via `[Environment]::GetFolderPath('Desktop')` + fallback. Nas 2 cópias (repo + pacote).
- 🔴 **(amigo) PENDENTE/PRIORIDADE — interface não abre (`run_client.exe`)** — só o servidor abre; Defender bloqueia o client (falso-positivo nuitka). Resolver quando o dono pedir; aguardando diagnóstico do amigo. Ver bloco "RETOMAR AQUI".
- 💊 **POTS: cooldown de 16s (geral — attack/boss/regen)** — pots no TO são regen ao longo de ~16s, não instantâneos. O bot via a % ainda baixa logo após potar e **potava de novo** (pot duplicado, "acontecia muito"). Fix: cooldown de 16s por tecla de pot (`Runner._pot_ready`/`_use_pot`, `POT_DURATION_SECS=16`); a espera de recuperação (`_wait_resource_refill`) passou a usar 16s. Vale pro farm normal também, não só pro boss.

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
| **Fairy Helper (cura + segue + AUTO-CURA, 1 membro)** | ✅ FEITO e validado 100% ao vivo (2026-05-27) | Seleciona o 1º membro (clique backstage) → cura → P; auto-cura (HP dela <50%): F1→cura→volta pro 1º membro. Bug do "auto-select" (P→F1) RESOLVIDO. SEM UI nova (decisão do dono). |
| **Seleção de membros do grupo (backstage)** | ✅ validado ao vivo | F1 = self; clique backstage (`left_click`) = membro. Coords `team_1..4` validadas (1024x768, ~81px). ⚠️ NÃO usar mouse real. |
| **🐉 Cave Boss Bot (aba "Boss", 3 papéis)** | ✅ CONSTRUÍDO (2026-05-27), a validar ao vivo | Aba dinâmica (dropdown Tank/DPS/Fairy → campos mudam). TANK: boss-lock + combo + buffs/Xs (não pota). DPS: boss-lock + recuo por aggro (perdeu HP→F1→espera→TAB) + recuperar MP. FAIRY: spam de cura no alvo atual. Regra "Boss só Boss". Spec em `CAVE_BOSS_BOT.md`. |
| **POTS com cooldown de 16s** | ✅ FEITO | Pot = regen de ~16s; cooldown por tecla evita pot duplicado. Em attack/boss/regen. |
| **⚔️ Attack: seletor de Classe (DPS/Tamer/Fairy)** | ✅ FEITO (2026-05-27), a validar | Dropdown no topo da aba Attack. DPS=atual. Tamer: tecla de ataque do pet (ao pegar alvo novo). Fairy: cura-se com skill em vez de pot HP. Combo segue genérico. |
| **🐾 Pet: Tamer + Normal (2 tipos, flags)** | ✅ RECONSTRUÍDO (2026-05-27), a validar | `petfood.py` + aba Pet. **Tamer** (flag): invoca/re-invoca-se-morrer/alimenta. **Normal** (flag): só alimenta (comida própria). Campos aparecem por flag. Combate = aba Attack (combo). |
| **Fairy buff em GRUPO (TODOS os membros)** | reservado p/ uma rotina futura | Buffar todo o grupo (F1 self + clique em cada membro). NÃO entrou no Cave Boss (o tank/dps se buffam sozinhos; a Fairy do boss cura, não buffa em grupo). Separado do Helper. |
| **Dashboard com Kills + Tempo** | Funcionando | Detecta kill via transição HP alvo positivo→morto |
| **Categorização de itens (Lixo/Bons/Raros)** | UI completa + drag-and-drop | Lógica de auto-vender/alertar vem em Sprint 4. Precisa task #6 (nomes de itens). |
| **Pausa após pot pra HP encher** | Implementado em `attack.py` | Por detecção, não tempo |
| **Set de team** (configurar nomes dos 4 amigos pra Fairy buffar) | Não iniciado | Aguarda time conectar pra validar TEAM_NAME |
| **Pacote `.exe` autocontido pros amigos** | ✅ FEITO e validado ao vivo | run_server + run_client + Tesseract (pasta ao lado) + launcher 1-clique + ícone; zip 139 MB no Drive. Fork autossuficiente (sem submódulo externo). |
| **Interface auto-recupera a lista de chars** | ✅ FEITO | fecha/reabre sem o char sumir (pede a lista a cada ~3s) — commit `cfd34e9` |
| **`gh` CLI (disparar/baixar builds)** | ✅ FEITO | logado como LpiresUrt; builds e download do `.exe` pela linha de comando |

---

## 🎯 ORDEM DE PRIORIDADE (atualizada 2026-05-26)

Reordenado pelo dono. O que atacar, em ordem:
1. **Sprint 1 — FINALIZAR** (em andamento): amigos testando o `.exe` → 5 farmando juntos + classes + montaria + blacklist + Star Paths + Helper.
2. **Sprint 2 — Cave Bot Genérico.**
3. **Sprint 7 — "Bots prontos" (Scripts/Presets) + Save robusto** ⬆️ (SUBIU — no lugar da Segurança).
4. **Sprint 4 (resto)** — Auto-relog + ajustes da Auto-Venda + filtro por cor de raridade + resiliência.
5. **Sprint 5 — Buffer + Login + Discord Bot interativo + tag v1.0.**
6. **Sprint 3 — Segurança** ⬇️ (foi pro FIM — "não tão importantes").

💡 **IDEIAS (sem previsão, não faremos agora):** acesso mobile via Tailscale (cada um usa o próprio PC), dashboard HTML local, e a Sprint 6 (BC dedicada, Hollow Residuals, anti-detecção avançado).

---

## 📅 SPRINT 1 — Multi-classe + Loot + Logística (04/jun → 17/jun)

**Status:** não iniciado. Algumas tarefas relacionadas já adiantadas via UX revolution.

- ⏳ Configuração das 5 classes — **SIMPLIFICADO (insight do dono 2026-05-26):** o bot é por TECLA → o combo é genérico; cada jogador configura as próprias teclas e salva o próprio **SCRIPT** (Sprint 7). NÃO precisa de código por classe (Wizard/Monk/Assassin/Tamer). **Exceção: a Fairy** precisa de lógica especial — modo **Helper** ✅ **FEITO** (seleciona o 1º membro por clique backstage → cura → segue com P → rebufa; + **auto-cura** via F1 quando a HP dela cai <50%). Por tecla/clique, sem ler HP do aliado → serve cross-PC. A lógica antiga `_heal_team_member` (lia HP de outro bot na MESMA máquina) foi substituída.
- 🔄 Instalação nos PCs dos 4 amigos — **EM ANDAMENTO:** pacote `.exe` autocontido FEITO E VALIDADO ao vivo (`C:\Bot\Talisman Bot.zip`, 139 MB, zero instalação). Falta só o dono subir num link e os amigos rodarem.
- ⏳ Teste: os 5 farmando simultaneamente
- ⏳ Item Blacklist (Discovery Mode) — **UI parcialmente pronta** via Sell tab (Lixo/Bons/Raros). Falta: lógica de "pegar tudo + log de drops + UI checkbox".
- ⏳ Sistema de Montaria (montar/desmontar + auto-mount em viagem)
- ✅ Detecção de Mochila Cheia via OCR — **FEITA** (lê "Your item box is full." no mesmo OCR do chat → 📦 Discord + venda automática; timer = rede de segurança)
- ⏳ Star Paths (Farm Spot ↔ Cidade ↔ NPC) — estrutura existe no código
- ⏳ Petfood como módulo independente — **já existe no código**, UI feita
- ✅ **Helper Mode v1 FEITO** (cura + segue + auto-cura o 1º membro do grupo; tudo por tecla/clique backstage). O bug `P→F1` que travava tudo (Fairy se curava sozinha) foi RESOLVIDO; Helper validado ao vivo. Auto-cura pendente só de teste ao vivo.
- ⏳ Cheat Engine: pointers de boss + nome do item no chão

---

## 📅 SPRINT 2 — Cave Bot Genérico (18/jun → 01/jul) — **GRANDE PARTE FEITA via Cave Boss Bot**

O **Cave Boss Bot** (aba "Boss") foi construído em 2026-05-27 e cobre o coração do Sprint 2.
Spec viva em `CAVE_BOSS_BOT.md`.

- ✅ **Toggle "Cave Mode" separado do Farm** — virou a **aba "Boss"** + checkbox "Boss" na Dashboard, com a regra **"Boss é só Boss"** (liga Boss → desmarca/bloqueia Attack/Sell/etc.).
- ✅ **Dropdown "Papel: Tank / DPS / Fairy" por char** — FEITO (aba dinâmica; os campos mudam pelo papel).
- ✅ **Boss Target Lock por nome configurável** — FEITO (commit `0f186e2`): "Travar no Boss" + "Nome do Boss" na aba Attack (e reusado no Boss); + botão **"🎯 Pegar alvo"** (`0d95dc7`). Testado ao vivo.
- ✅ **Lógica TANK / DPS / FAIRY específica** — FEITA (a validar ao vivo):
  - TANK: boss-lock + combo + buffs a cada Xs (auto-cast, sem pot — Fairies curam).
  - DPS: boss-lock + recuo por aggro (perdeu HP em combate → F1 → espera sair de combate → TAB → volta) + recuperar MP (F1 → espera → pot → TAB).
  - FAIRY: spam de cura no ALVO ATUAL (jogador troca o alvo; não lê HP de outros).
- ⏳ **3 rotações por char (Farm / Boss-DPS / Boss-Tank)** — parcial: Farm (aba Attack) + Boss (aba Boss) prontos; "rotações salvas/preset" casa com o Sprint 7.
- ⏳ **Painel Debug em tempo real / Auto-stop / Cave Stats** — não iniciados.
- ⏭️ **Buff em GRUPO da Fairy (todos os membros)** — base pronta (`team_1..4`, `get_team_size`/`team_name_N`); NÃO entrou no Cave Boss (lá a Fairy cura, não buffa em grupo). Fica pra uma rotina futura se o dono quiser.

---

## 📅 SPRINT 3 — Segurança — ⬇️ PRIORIDADE BAIXA, movida pro FIM (decisão do dono 2026-05-26: "não são tão importantes")

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
- ✅ Discord Webhook — **COMPLETO (sessão 2026-05-25):** detecção de drop por OCR + webhook (`discord_notify.py`) + thread paralela + dashboard (painel de drops + triagem ✅/❌ + barra de ação + alerta de morte 💀) + **alerta de MOCHILA CHEIA 📦 (vende automático)** + **alertas em EMBEDS** (cards com cor/char/horário; cor por tipo, pronta pra raridade). Falta: **filtro por cor de raridade** (depende da detecção de raridade) e **fechar o Tesseract no `.exe`** — caminho ZIP pronto (`tools/make_portable_tesseract.py` monta `src/GhostBot/Tesseract-OCR/` portátil, gitignorada; código já a acha). CI (`build-executable.yml`) já embute Tesseract+Images via `include-data-dir`; **`.exe` autocontido FEITO E VALIDADO ao vivo (2026-05-26):** Tesseract vai como PASTA ao lado do exe (nuitka não embute `.dll`/`.exe`), webhook/lista achados na pasta do exe, fork autossuficiente (submódulo removido). Pacote `C:\Bot\Talisman Bot.zip` testado (dashboard + drop no Discord + morte). **Falta só:** filtro por cor de raridade.
- 💡 **[IDEIA — não faremos por enquanto]** Acesso Mobile via Tailscale — cada um usa o próprio PC (decisão do dono 2026-05-26).
- 💡 **[IDEIA — não faremos por enquanto]** Dashboard HTML local (5 chars em tempo real).
- ✅ **Auto-Venda — FEITA e rodando ótimo** (ciclo de venda em produção + venda automática na mochila cheia). Resta só **AJUSTES** finos se aparecerem.
- ⏳ Resiliência (retry + modo "só voltar")
- 🔜 **Auto-relog básico — FAREMOS** (na fila; decisão do dono 2026-05-26).

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

## 📅 SPRINT 7 — "Bots prontos" (Scripts/Presets de config) + Save robusto — ⬆️ PRIORIDADE ALTA (subiu no lugar da Segurança; decisão do dono 2026-05-26)

**Pedido do dono (2026-05-26):** poder salvar uma configuração de bot como um "script" reutilizável ("bots simples prontos") e trocar entre eles com 1 clique.

**Requisitos:**
1. **Botão "Salvar script":** salva a configuração ATUAL (todas as abas — Attack, Regen, Buff, Fairy, Pet, Sell) como um preset com NOME.
2. **Lista de scripts na LATERAL DIREITA:** espelha a lista de personagens logados da esquerda. Cada item mostra o **NOME do script** + a **última atualização** em formato abreviado **`dd/mm/yy hh:mm`**.
3. **Aplicar por clique:** clicar num script da lista **SUBSTITUI** a configuração atual (carrega o preset nas abas do personagem selecionado).
4. **🔴 Save SUPER confiável (crítico nesta sprint):** o botão **Save tem bugs hoje** — falha em **silêncio** se `config.validate()` barrar (o `.yml` não salva e o usuário não sabe). Como o save é o coração desta feature, esta sprint precisa:
   - **Feedback VISÍVEL** de sucesso/erro na própria interface (não só no log do servidor).
   - Mostrar **o que** falhou na validação (campo/motivo).
   - Nunca salvar pela metade; confirmar que o arquivo foi gravado.

**Notas de design (pra quando implementar):**
- Guardar scripts como `.yml` nomeados (ex.: `~/GhostBot/scripts/<nome>.yml`), separados dos `<charname>.yml` por personagem.
- Timestamp = `mtime` do arquivo (ou campo salvo no `.yml`), formatado `dd/mm/yy hh:mm`.
- "Substituir o atual" = carregar o preset na config do char selecionado + atualizar as abas da UI + salvar. Reusa o load/save do `config.py`.
- Respeitar **Stop = emergência**: provavelmente exigir o bot **parado** pra trocar de script (não trocar config no meio do farm).
- Bug do Save: ver as notas do save silencioso (memória `reference-save-must-succeed`).

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
