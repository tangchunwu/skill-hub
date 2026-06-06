# Selection Guide

This guide helps route broad persona-distill requests into a narrower shortlist before installation.

## Category Map

### 自我蒸馏与元工具

Use when the user wants to:
- distill themselves from chats, notes, or digital traces
- build a reusable self-portrait or digital twin
- orchestrate or compare multiple persona skills

Fast picks:
- `图鉴.skill`: broad router across many persona skills
- `Persona Skill`: general-purpose persona distill / synthesis / roleplay layer
- `Forge Skill`: explicit split between self-distill and other-distill
- `自己.skill`: simple personal assistant angle
- `数字人生.skills` / `数字生命开源计划`: self-portrait from tool exhaust

### 职场与学术关系

Use when the user wants to model:
- boss expectations
- mentor or supervisor style
- team context from coworkers
- class, professor, lab, or recruiting workflows

Fast picks:
- `老板.skill`
- `导师.skill`
- `大学老师.skill`
- `师兄.skill`
- `HR.skill`
- `roast-cold-email-skill`

### 亲密关系与家庭记忆

Use when the user wants:
- emotional reflection
- relationship rehearsal
- memorial companionship
- family voice/style preservation

Fast picks:
- `前任.skill`
- `暗恋对象.skill`
- `恋爱训练营.skill`
- `父母.skill`
- `MamaSkill`
- `Reunion Skill`
- `兄弟.skill`

### 公众人物与方法论视角

Use when the user wants:
- a thinking framework
- a decision lens
- a style of analysis
- a creator or public figure's heuristics

Fast picks by intent:
- startup / product: `PG.skill`, `张一鸣.skill`, `乔布斯.skill`
- AI / engineering: `Karpathy.skill`, `Ilya.skill`, `罗布派克.skill`
- investing / judgment: `巴菲特思维操作系统`, `芒格.skill`, `纳瓦尔.skill`, `塔勒布.skill`
- political or ideological analysis: `毛选.skill`, `毛泽东.skill`, `KarlMarx Skill`, `新青年.Skill`, `求是 Skill`, `zizek-skill`
- creator growth / media: `MrBeast.skill`, `X 导师.skill`, `内娱.skill`

### 精神性与专门化主题

Use when the user wants:
- divination or compatibility readings
- Buddhist commentary
- feng shui
- traditional numerology systems

Fast picks:
- `赛博算命 Skill`
- `月老·姻缘测算 Skills`
- `金刚经.skill`
- `Master-skill`
- `堪舆子`
- `Numerologist Skills`

## Recommendation Pattern

When the user is vague, answer in this order:

1. name the relevant category split
2. give `3-5` candidate skills
3. explain why each one fits
4. say which one is the safest starting point

## Safety Notes

- Distill interaction patterns or methods, not claims of perfect identity reconstruction.
- For private chat logs, voice notes, or family archives, remind the user to review the downstream repo's privacy and local-processing story before installation.
- If the user already knows the exact repo they want, skip broad routing and move directly to inspection or installation.
