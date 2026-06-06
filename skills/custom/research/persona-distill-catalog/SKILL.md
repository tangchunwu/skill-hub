---
name: persona-distill-catalog
description: Browse and recommend persona-distill skills from the awesome-persona-distill-skills ecosystem. Use when the user asks for a persona distill skill, wants help choosing among boss/ex/mentor/public-figure/family/spiritual persona skills, or references the awesome-persona-distill-skills repo. Shortlists matching repos and hands off installation to skill-installer after the user picks one.
---

# Persona Distill Catalog

Use this skill as a local index over a snapshot of `xixu-me/awesome-persona-distill-skills`.

## Quick Start

1. If the request is broad or ambiguous, read [references/selection-guide.md](references/selection-guide.md).
2. Search the local catalog:

```bash
python3 "$CODEX_HOME/skills/persona-distill-catalog/scripts/search_catalog.py" --query "$ARGUMENTS"
```

3. Recommend `3-5` entries with:
   - name
   - fit explanation
   - repo URL
   - one caution or boundary when relevant
4. If the user picks a skill to install, switch to `skill-installer` and install from the selected GitHub repo.

## Search Recipes

Broad search:

```bash
python3 "$CODEX_HOME/skills/persona-distill-catalog/scripts/search_catalog.py" --query "$ARGUMENTS" --limit 8
```

Category-first search:

```bash
python3 "$CODEX_HOME/skills/persona-distill-catalog/scripts/search_catalog.py" --category "职场与学术关系" --query "$ARGUMENTS"
```

List categories:

```bash
python3 "$CODEX_HOME/skills/persona-distill-catalog/scripts/search_catalog.py" --list-categories
```

Structured output for follow-on tooling:

```bash
python3 "$CODEX_HOME/skills/persona-distill-catalog/scripts/search_catalog.py" --query "$ARGUMENTS" --format json
```

## Routing Heuristics

- If the user says "先帮我挑一个", start with the local catalog instead of guessing.
- If the user wants a general entry point, bias toward `图鉴.skill`, `Persona Skill`, or `Forge Skill`.
- If the user wants a work or school counterpart, bias toward `老板.skill`, `导师.skill`, `大学老师.skill`, `师兄.skill`, or `HR.skill`.
- If the user wants relationship or memorial use cases, bias toward `前任.skill`, `父母.skill`, `MamaSkill`, `Reunion Skill`, `暗恋对象.skill`, or `恋爱训练营.skill`.
- If the user wants a reusable thinking lens instead of a simulated relationship, bias toward the `公众人物与方法论视角` category.
- If the user asks for命理、佛学、风水、术数, bias toward `精神性与专门化主题`.

## Output Style

- Keep recommendations short and comparative.
- Prefer a shortlist over a dump of the whole catalog.
- When a request is vague, explain the top split first:
  - self-distill
  - work/school relationship
  - intimate/family memory
  - public-figure methodology
  - spiritual/specialized

## Boundaries

- This skill is a catalog and routing layer, not the implementation of every downstream skill.
- Do not claim a listed repo is safe or private by default; if the user wants to install one, inspect its README and requested data sources first.
- The bundled catalog is a local snapshot. If precision matters, compare against the upstream repo before making strong claims about completeness.
