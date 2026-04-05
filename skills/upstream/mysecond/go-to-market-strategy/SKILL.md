---
name: go-to-market-strategy
description: 'Creates a complete GTM plan with channels, messaging, timeline, and success metrics Use when: go-to-market strategy, gtm strategy, gtm plan, launch strategy, product launch.'
effort: high
disable-model-invocation: true
---

# Go-to-Market Strategy

Creates a complete GTM plan with channels, messaging, timeline, and success metrics.

## Output
Save to `strategy/outputs/gtm-[product]-[YYYY-MM-DD].md`

## When to Use This Skill
- Product launches
- Market expansion
- Major feature releases
- Enterprise sales plays
- New segment targeting

## The Problem

GTM plans are either 50-page decks nobody reads or back-of-napkin ideas that miss critical channels. Most launches fail from poor GTM, not bad products.

## What You'll Need

**Critical inputs (ask if not provided):**
- What you're launching (product, feature, expansion)
- Target customers and segments
- Launch date/timeline

**Nice-to-have inputs:**
- Available resources (budget, team)
- Competitive positioning
- Sales motion (PLG, sales-led, etc.)

## Process

### Step 1: Check Your Context
First, read the user's context files:
- `context/product.md` — What you're launching, value prop, pricing
- `context/personas.md` — Target segments, buyer profiles, pain points
- `context/competitors.md` — Competitive positioning, differentiation
- `context/company.md` — Team structure, sales motion, marketing channels

**Tell the user what you found.** For example:
> "I found 'Resource Planning v2' in your product.md as the launch. Your Jordan persona (PM) is the primary buyer — they care about 'workload visibility.' Your competitors.md shows Monday.com as the main threat. I'll build a GTM plan targeting Jordan with positioning vs Monday."

### Step 2: Gather GTM Context
If you don't have enough context, ask:
> "Before I create this GTM strategy, I need:
> 1. What are you launching? (I found [X] in product.md)
> 2. Who's the target buyer? (I found [personas] in personas.md)
> 3. When do you want to launch?
>
> I can pull positioning from competitors.md and channel strategy from company.md."

**Context quality gate:**
If 2+ context files are missing (no personas, no competitors, no product details), don't generate the full GTM plan. Instead, produce a **GTM Readiness Brief**:
1. What I know (from available context)
2. What's missing and why it matters
3. The 1-2 recommendations I'm confident making with current data
4. Specific next steps to fill gaps before building the full plan
5. A one-sentence preview of what the full GTM plan includes (messaging matrix with customer language, competitive positioning, segment revenue estimates, launch timeline with owners) — so the PM knows what they unlock by filling context

## What You'll Get

- GTM one-pager + detailed plan
- Target segment prioritization
- Channel strategy with owners
- Messaging matrix by persona
- Launch timeline with milestones
- Sales enablement checklist
- Success metrics (30/60/90 day)

## Process (continued)

### Step 3: Define Launch Type and Goals
Clarify what you're launching:
- New product
- Major feature
- Market expansion
- Pricing/packaging change

Set measurable goals.

### Step 4: Identify Target Segments
Prioritize segments:
- Who benefits most?
- Who's easiest to reach?
- Who has buying authority?
- What's the buying process?

### Step 5: Map Channels to Segments
For each segment:
- How do they discover products?
- What channels reach them?
- What's the cost per acquisition?
- Who owns each channel?

### Step 6: Create Messaging by Persona
Tailor messaging:
- Different personas care about different things
- Map features to benefits per persona
- Create proof points per persona

**Grounding rule:** For each messaging claim and proof point, extract a verbatim quote or data point from context files first. When an entire section lacks source data (e.g., no personas at all), add ONE section-level warning instead of marking every row. Use per-cell ⚠️ markers only when some rows have evidence and others don't.

### Step 7: Build Timeline with Milestones
Plan the launch:
- Pre-launch activities
- Launch day activities
- Post-launch activities
- Checkpoints and decision points

### Step 8: Define Success Metrics
Set measurement plan:
- 30-day metrics (leading indicators)
- 60-day metrics (engagement)
- 90-day metrics (business outcomes)

## Output Template

```markdown
# GTM Strategy: [Launch Name]

**Launch Date:** [Date]
**GTM Owner:** [Name]
**Status:** Planning / Executing / Launched

## Context
*What I found in your files:*
- **What's launching:** [From product.md]
- **Value prop:** [From product.md]
- **Target buyer:** [From personas.md]
- **Buyer pain points:** [From personas.md]
- **Competitive positioning:** [From competitors.md]
- **Sales motion:** [From company.md]

## GTM One-Pager

| Element | Summary |
|---------|---------|
| **What** | [Product/feature being launched] |
| **Who** | [Primary target segment] |
| **Why Now** | [Urgency/timing rationale] |
| **Key Message** | [Single sentence value prop] |
| **Success Metric** | [Primary success metric] |
| **Launch Date** | [Date] |

## Target Segments

### Segment 1: [Name] (Primary)

| Attribute | Detail |
|-----------|--------|
| Description | [Who they are] |
| Problem | [What problem they have] |
| Why Us | [Why we're the solution] |
| Buying Process | [How they buy] |
| Est. Opportunity | $[X] / [N] customers |

### Segment 2: [Name] (Secondary)

[Same structure]

### Segment Prioritization

| Segment | Priority | Rationale |
|---------|----------|-----------|
| [Segment 1] | P1 | [Why first] |
| [Segment 2] | P2 | [Why second] |

## Channel Strategy

| Channel | Segment | Owner | Budget | Timeline |
|---------|---------|-------|--------|----------|
| [Channel 1] | [Segment] | [Name] | $[X] | [Dates] |
| [Channel 2] | [Segment] | [Name] | $[X] | [Dates] |
| [Channel 3] | [Segment] | [Name] | $[X] | [Dates] |

### Channel Details

**[Channel 1]:**
- Activities: [Specific activities]
- Assets needed: [What to create]
- Expected results: [Targets]

[Same for each channel]

## Messaging Matrix

| Persona | Key Message | Proof Point | CTA | Source |
|---------|-------------|-------------|-----|--------|
| [Persona 1] | [Message] | [Evidence] | [Action] | [personas.md / interview / ⚠️ Inferred] |
| [Persona 2] | [Message] | [Evidence] | [Action] | [personas.md / interview / ⚠️ Inferred] |
| [Persona 3] | [Message] | [Evidence] | [Action] | [personas.md / interview / ⚠️ Inferred] |

### Positioning Statement

**For** [target customer]
**who** [has this need]
**[Product] is a** [category]
**that** [key benefit].
**Unlike** [alternative],
**we** [differentiator].

## Launch Timeline

### Pre-Launch (T-[X] weeks)

| Week | Activities | Owner | Deliverable |
|------|------------|-------|-------------|
| T-4 | [Activities] | [Name] | [Deliverable] |
| T-3 | [Activities] | [Name] | [Deliverable] |
| T-2 | [Activities] | [Name] | [Deliverable] |
| T-1 | [Activities] | [Name] | [Deliverable] |

### Launch Week

| Day | Activities | Owner |
|-----|------------|-------|
| Monday | [Activities] | [Name] |
| Tuesday | [Activities] | [Name] |
| [Launch Day] | [Activities] | [Name] |

### Post-Launch

| Week | Activities | Owner | Checkpoint |
|------|------------|-------|------------|
| L+1 | [Activities] | [Name] | [Decision] |
| L+2 | [Activities] | [Name] | [Decision] |
| L+4 | [Activities] | [Name] | [Decision] |

## Sales Enablement Checklist

- [ ] Sales deck updated
- [ ] Demo environment ready
- [ ] Pricing/packaging finalized
- [ ] FAQ document created
- [ ] Competitive battle cards updated
- [ ] Sales team trained
- [ ] Objection handling guide
- [ ] Customer reference stories
- [ ] Email templates for outreach
- [ ] Talk track for discovery calls

## Success Metrics

### 30-Day Metrics (Leading Indicators)

| Metric | Target | Tracking |
|--------|--------|----------|
| [Metric 1] | [Target] | [How tracked] |
| [Metric 2] | [Target] | [How tracked] |

### 60-Day Metrics (Engagement)

| Metric | Target | Tracking |
|--------|--------|----------|
| [Metric 1] | [Target] | [How tracked] |
| [Metric 2] | [Target] | [How tracked] |

### 90-Day Metrics (Business Outcomes)

| Metric | Target | Tracking |
|--------|--------|----------|
| [Metric 1] | [Target] | [How tracked] |
| [Metric 2] | [Target] | [How tracked] |

### Decision Points

| Date | Checkpoint | Decision Criteria |
|------|------------|-------------------|
| L+30 | [Checkpoint] | [What determines success/pivot] |
| L+60 | [Checkpoint] | [What determines success/pivot] |
| L+90 | [Checkpoint] | [What determines success/pivot] |

## Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| [Risk 1] | H/M/L | H/M/L | [Mitigation] |
| [Risk 2] | H/M/L | H/M/L | [Mitigation] |

## Budget Summary

| Category | Amount |
|----------|--------|
| [Channel 1] | $[X] |
| [Channel 2] | $[X] |
| Content/Creative | $[X] |
| Events | $[X] |
| **Total** | **$[X]** |
```

## Framework Reference

**GTM Strategy Components:**
- **Segment:** Who you're targeting and why
- **Channel:** How you reach them
- **Message:** What you say to them
- **Timeline:** When it happens
- **Metrics:** How you measure success

**Common GTM Motions:**
- **Product-Led:** Trial → conversion → expansion
- **Sales-Led:** Outbound → demo → close
- **Marketing-Led:** Content → MQL → SQL → close
- **Channel-Led:** Partner → referral → close

## Tips for Best Results
1. **Use your context files** — I'll build on personas, positioning, and competitive context
2. **Focus on primary segment first** — Spreading thin kills launches
3. **Own the timeline** — Launches without dates don't happen
4. **Metrics at each stage** — Leading indicators before lagging
5. **Sales enablement is critical** — They can make or break launch
6. **Plan the post-launch** — Day 2-90 matters as much as day 1

## Suggested Updates
After creating the GTM plan:
- [ ] Update `product.md` with launch date and success metrics
- [ ] Create sales enablement using the sales enablement kit skill
- [ ] Create launch checklist using the launch checklist skill
