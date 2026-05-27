# 🐉 Cave Boss Bot — Contexto e Design

> Documento de trabalho. A gente constrói **passo a passo**; cada etapa é confirmada antes de codar.
> Criado 2026-05-27 a partir do briefing do dono.

## O que é

Modo para lutas de **BOSS em cave** — diferente do farm normal de spot. No boss ninguém fica
andando: cada um fica parado no seu lugar fazendo seu papel. Vai virar uma **aba nova "Boss"**
na interface (separada das outras, pra organizar bem).

**Time padrão (5):** 1 Tank + 2 DPS + 2 Fairies.

## Os 3 papéis (roles)

### 1. 🛡️ TANK (1)
- Bate **só no boss**, sem parar → usa o **boss target-lock por nome** (já temos: checkbox
  "Travar no Boss" + nome, dá TAB até achar e ataca só ele).
- Usa **alguns buffs de tank**, tipo **a cada ~30s** (nada demais).
- **Base:** reusa o Attack (com boss-lock ligado) + um buff periódico. É o papel mais simples.

### 2. ⚔️ DPS (2)
- Bate sem parar no boss (também com boss-lock no nome do boss).
- **Controle de aggro:** se um DPS **puxar o aggro sem querer** → aperta **F1 na hora** (tira o
  alvo/para de bater) + **espera SAIR de combate** → o tank repuxa o aggro pela ameaça dele →
  o DPS volta a bater.
- **Controle de MP:** se o **MP baixar** → mesma coisa: **F1 → espera sair de combate → usa pot**
  → volta a bater.
- É o papel mais **complexo** (precisa inferir o aggro — ver "Limitações").

### 3. 🧚 FAIRY (2)
- **Cura quem levou dano** durante a luta.
- Plano inicial do dono: "**basta ela spamar a cura e o jogador troca de alvo**". Ou seja, a
  versão mais simples = spam da tecla de cura no alvo atual.
- ⚠️ **A definir:** como a Fairy escolhe QUEM curar (ver "Limitações" — não dá pra ler a vida
  dos outros pela memória).

## ✅ O que o bot CONSEGUE ler/fazer (fundamenta o design)

| Capacidade | Como | Uso no boss |
|---|---|---|
| Estado de combate | `client.in_battle` (✅ já usado pelo Regen) | "espera sair de combate" (DPS) |
| Vida/Mana próprias | `client.hp_percent`, `client.mana_percent` | gatilho de pot e de "estou apanhando" |
| Alvo selecionado | `get_target_name`, `target_hp`, `is_target_selected` | boss-lock (TAB até o nome do boss) |
| Quem está no grupo | `client.team_size`, `client.team_members` (nomes) | saber quantos/quais membros |
| Selecionar membro | clique backstage `team_1..team_4` + `F1` (self) | trocar alvo da cura, F1 do DPS |
| Apertar tecla | `client.press_key(...)` backstage | skills, pot, buffs |

## ⚠️ Limitações (importante saber ANTES de prometer)

- ❌ **Não dá pra ler a vida de OUTRO membro** pela memória — cada bot só lê a **própria** vida.
  → A Fairy **não sabe sozinha** "quem está ferido".
- ❌ **Não dá pra ler em quem o boss está mirando** — não existe pointer de "aggro do inimigo".

### Como contornar o AGGRO (a pergunta do dono: "dá pra puxar/ler o aggro?")
Ler o aggro do boss **direto: não dá**. MAS dá pra **INFERIR**: se um DPS está **apanhando**
(a vida DELE cai) enquanto está `in_battle`, é sinal de que o boss virou pra ele = puxou o aggro.
→ Regra do DPS: "perdi vida em combate (sem ser o tank)" → **F1 + espera `in_battle` virar falso**
→ volta. O tank repuxa naturalmente. Não precisa "puxar o aggro" ativamente — só **parar e esperar**.

### Como a FAIRY escolhe quem curar (decisão pendente)
Como não lê HP dos outros, as opções são:
- **(a)** Spam de cura no **alvo atual**; um humano (ou o próprio fluxo) troca o alvo. *(plano inicial do dono — mais simples)*
- **(b)** A Fairy **cicla os retratos** (clica membro → cura → próximo → ...), curando todos em rodízio.
- **(c)** Outra ideia a discutir.

## 🧱 Plano de construção (passo a passo — ordem do mais simples ao mais complexo)

1. ✅ **Aba "Boss"** — FEITO. Seletor de **papel** (dropdown Tank/DPS/Fairy) + campos que **mudam
   conforme o papel** (ideia do dono). Nome do boss + combo compartilhados (Tank/DPS).
2. ✅ **Papel TANK** — FEITO (2026-05-27, UI/UX validada pelo dono; lógica = reaproveitamento provado
   do Attack). Trava no boss (TAB até o nome) → ataca com o combo → reaplica os buffs do tank a cada
   X s (só aperta a tecla, auto-cast, sem trocar de alvo). Pots HP/MP opcionais (tecla vazia = off).
3. ✅ **Papel FAIRY** — FEITO (2026-05-27). Opção (a): spama a tecla de cura no ALVO ATUAL a cada
   `heal_interval_secs`; o jogador troca o alvo (clica em quem precisa). Sem mira automática (não lê
   HP de outros). Pots HP/MP próprios opcionais. Na aba, papel Fairy esconde Nome do Boss + Combo.
4. ✅ **Papel DPS** — FEITO (2026-05-27). Bate no boss (boss-lock + combo); **aggro automático**:
   detecta "puxei aggro" por **perder vida em combate** → F1 → espera sair de combate (`in_battle`
   → False) → o tank repuxa → volta. **MP**: usa o Pot MP comum — ao cair do %, F1 → espera sair de
   combate → pot → volta. Reaproveita os campos comuns (sem campo novo); aggro sempre ligado.

## ✅ TODOS OS 3 PAPÉIS PRONTOS (2026-05-27). Falta só validar o DPS ao vivo + ajustes finos.

## 🔓 Decisões (resolvidas)
- ✅ **Arquitetura:** runner novo (`functions/boss.py` + `BossConfig`), separado do farm.
- ✅ **Tank buff:** só aperta a tecla (auto-cast, sem F1). Buffs + intervalo = config na aba.
- ✅ **MP opcional:** pot só dispara com tecla preenchida; tank deixa MP vazio.
- ✅ **Fairy:** opção (a) — spam no alvo atual, jogador troca.
- ✅ **DPS aggro:** gatilho = **queda de HP em combate** (`hp` caiu desde o último tick do combo).
  Sem limiar fino por ora (qualquer queda recua). Aggro **sempre ligado** (sem toggle) — adicionar
  liga/desliga e/ou limiar SE der falso-positivo no teste ao vivo (ex.: AoE leve do boss).

## ⚠️ A VALIDAR ao vivo (DPS) / possíveis ajustes
- **Falso-positivo de aggro:** se o boss tem AoE que tira um tiquinho de todos, o DPS pode recuar à
  toa. Ajuste fácil se acontecer: exigir queda > X% pra contar como aggro (vira config).
- **Tempo de "sair de combate":** `_wait_out_of_combat` espera até 20s. Se o tank demora a repuxar,
  ajustar o timeout.
- **F1 = self:** confirmar ao vivo que F1 realmente tira o alvo do boss e para o dano (era o mesmo
  F1 que a Fairy usa pra se selecionar — já validado lá).

## ⚠️ Uso: ligar SÓ o "Boss"
Pro modo boss, deixar **só o checkbox "Boss"** marcado na Dashboard (desmarcar Attack/Sell/etc.) —
senão o farm normal e o Boss rodam juntos e brigam pelo controle do char.
