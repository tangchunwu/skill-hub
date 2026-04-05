---
name: executive-update-generator
description: 'Create concise executive status updates using SCARF framework for clarity. Use when: executive update, leadership update, exec summary, board update.'
disable-model-invocation: true
---

# Executive Update Generator

Create concise executive status updates using SCARF framework (Status, Context, Action, Risks, Forward) for clarity.

## Output
Save to `strategy/outputs/exec-update-[YYYY-MM-DD].md`

## When to Use This Skill
- Weekly or monthly exec updates
- Project status reports
- Board or investor updates

## The Problem

Executive updates often bury the lede, lack clear asks, or surprise leadership with status changes. PMs spend hours crafting updates that execs skim in 30 seconds—or worse, don't read at all.

**This skill solves it by:** Structuring your update with SCARF framework so the status is clear, risks are surfaced early, and asks are explicit—turning updates into actionable leadership communication.

## What You'll Get

I'll generate a scannable executive update including:
- TL;DR summary (2-3 sentences)
- Overall status indicator (Green/Yellow/Red) with justification
- Accomplishments with impact
- Key metrics table with movement vs. target
- Risks and blockers with mitigation plans
- Explicit decisions needed with deadlines
- Next period priorities

## What You'll Need

**Critical inputs (ask if not provided):**
- What project/team is this update for?
- What time period are you covering?
- Overall status (Green/Yellow/Red)

**Nice-to-have inputs:**
- Specific accomplishments to highlight
- Metrics with current vs target values
- Decisions needed from leadership

## Process

### Step 1: Check Your Context
I'll start by reading your context files:
- `context/product.md` — Current metrics, roadmap items, known issues
- `context/company.md` — Strategic priorities, OKRs to align against
- `context/personas.md` — If user-facing impact, which personas benefit?

**I'll tell you what I found.** For example:
> "I found your Q2 OKRs in company.md: 'Improve retention to 95%' and 'Launch Resource Planning.' Your product.md shows current retention at 91%. I'll structure the update around progress against these goals."

### Step 2: Gather Update Details
If you haven't provided enough context, I'll ask:
> "Before I create this executive update, I need:
> 1. What project/team is this for?
> 2. What period are you covering?
> 3. What's the overall status — Green, Yellow, or Red?
>
> I can pull metrics from product.md and align to priorities from company.md."

If metrics are missing, I'll mark them as `[NEEDS DATA]` rather than guessing.

### Step 3: Gather Inputs
I'll collect:
- What you accomplished this period
- Key metrics and their movement (from product.md or provided)
- What's at risk or blocked
- What you need from leadership

### Step 4: Structure Using SCARF
- **S**tatus: Overall health (Green/Yellow/Red)
- **C**ontext: What are we working on?
- **A**ction: What did we accomplish?
- **R**isks: What might go wrong?
- **F**orward: What's next? What do we need?

### Step 5: Make it Scannable
Execs read in 2 minutes. I'll lead with the punchline.

## Output Template

I'll generate this executive update for you:

```markdown
# Status Update: [Project/Team Name]

**Period:** [Date Range]
**Author:** [Name]
**Status:** 🟢 On Track / 🟡 At Risk / 🔴 Blocked

## Context
*What I found in your files:*
- **Strategic alignment:** [From company.md — which priority this supports]
- **Key metrics baseline:** [From product.md — current state]
- **Impacted personas:** [From personas.md if user-facing]

---

## TL;DR
[2-3 sentence summary of the most important things]

---

## Status: 🟢/🟡/🔴

**Why:** [One sentence explaining the status]

---

## What We Accomplished
- ✅ [Accomplishment 1] — [Impact]
- ✅ [Accomplishment 2] — [Impact]
- ✅ [Accomplishment 3] — [Impact]

---

## Key Metrics

| Metric | Last Period | This Period | Target | Status |
|--------|-------------|-------------|--------|--------|
| [Metric 1] | [X] | [Y] | [Z] | 🟢/🟡/🔴 |
| [Metric 2] | [X] | [Y] | [Z] | 🟢/🟡/🔴 |

---

## Risks & Blockers

### 🟡 [Risk 1]
**Impact:** [What happens if this hits]
**Mitigation:** [What we're doing]
**Help Needed:** [What we need / None]

### 🔴 [Blocker 1]
**Impact:** [What's blocked]
**Help Needed:** [Specific ask]

---

## Decisions Needed

| Decision | Context | Options | Deadline |
|----------|---------|---------|----------|
| [Decision 1] | [Why needed] | [A, B, C] | [Date] |

---

## Next Period Focus
1. [Priority 1]
2. [Priority 2]
3. [Priority 3]

---

## Questions?
[Name] — [email/slack]
```

## Framework Reference
**SCARF framework**:
- Status, Context, Action, Risks, Forward
- Lead with the headline
- Make asks explicit

## Tips for Best Results

1. **Use your context files** — I'll pull metrics from product.md, priorities from company.md
2. **Lead with the punchline** — Execs read in 2 minutes. TL;DR is everything.
3. **Be honest about status** — Yellow is okay. Surprises are not.
4. **Make asks explicit** — "I need X by Y" beats "We could use help"
5. **Link to strategic priorities** — Show how your work connects to company goals

## Suggested Updates
After sending, consider:
- [ ] Update `product.md` with latest metrics if changed
- [ ] Add new risks to your risk register
