# From Zero Code to Deployed MVP in 60 Days
## A Practitioner's Journey with Claude Code

*Claude Code Central London Meetup — 8 April 2026*
*Aaditya Chintalapati*

---

## Slide 1: The Practitioner's Advantage

**"I didn't know how to code. But I knew exactly what broken looked like."**

- 15 years in upstream oil & gas M&A — ran due diligence on dozens of deals
- Every deal: same 400-page VDR, same manual slog, same questions, same missed red flags
- I wasn't trying to build "an AI product" — I was trying to stop doing the same painful work for the 50th time
- The advantage: I could look at any output and instantly tell you if it was useful or garbage
- That's the moat. Not the code. The taste.

> *When you've lived the pain, you don't need a product manager to tell you what "done" looks like.*

---

## Slide 2: The Accidental Architect

**"I spent 2 weeks designing a system I never planned to build."**

- Original plan: design the solution → hand it to my co-founder Vikram to code
- So I did what any non-coder would do: wrote specs. Detailed specs. Obsessively detailed specs.
- Domain knowledge playbooks. Data flow diagrams. Section-by-section output formats. Edge cases.
- I was essentially building the world's most thorough handover document
- Plot twist: that "handover document" became the best possible input for an AI coding assistant
- **Accidentally, I'd done the hardest part of software engineering — thinking about the problem**

---

## Slide 3: "Use The Force, Aaditya"

**The Yoda moment.**

- Walked up to Vikram with my 30-page spec, ready to hand it off
- Vikram: *"Why don't you just... build it yourself?"*
- Me: "I don't know how to code."
- Vikram: "You don't need to. Use Claude Code."

**The progression (2 weeks):**
```
Claude Desktop → "Can you write me a Python script that..."
    ↓
VS Code + Claude → "Here's my file, fix the bug on line 47"
    ↓
Claude Code CLI → "Read the spec in plan_docs/ and implement Section 6"
    ↓
tmux + Claude Code → *3 agents running in parallel, I'm just reviewing PRs*
```

- Each step felt like unlocking a new level in a game
- By week 2, I wasn't "using AI to code" — I was **engineering with an AI pair programmer**

---

## Slide 4: The Hubris Arc

**"It works! Let's make it 10x more complex!"**

- Built a 7-agent mesh architecture. Sounded brilliant on paper:
  - Agent 01: VDR Inventory & Classification
  - Agent 04: Financial Calculator (25+ metrics)
  - Agent 06: QA Engine (13-call report builder)
  - Agent 07: Well Card Analysis
  - Agent 08: DD Report Aggregator
  - ...plus a Supervisor, Memory Manager, and Audit Layer

- **The result?** A Rube Goldberg machine that produced *worse* reports than just asking Opus: "Here's a VDR. Write me a due diligence report."

- The multi-agent orchestration was impressive engineering. But impressive engineering ≠ useful product.

**Back to Square 1.5.**

- Stripped it back. One primary agent. One clear pipeline. Deterministic verification on top.
- Laser focus: does this output help a deal team make a decision? If not, delete it.
- 60 days from first ideation → deployed MVP, 6 external play-testers, 3 real VDRs validated

---

## Slide 5: What Actually Worked

**Three things I'd tell yesterday's me.**

### 1. Scaffolding Is Everything
- CLAUDE.md, MEMORY.md, plan_docs/ — your AI's long-term memory is only as good as the scaffolding you give it
- Document specs *before* you code. Not for yourself — for Claude's context window
- If Claude makes a mistake, don't just fix it. Write down *why* it was wrong so it never happens again

### 2. ELI5 — Every. Single. Time.
- "Make the report better" → garbage
- "Section 4 must contain: (a) proved reserves by category in MMbbl, (b) recovery factor vs analogues, (c) specific paragraph citing the CPR page number. Example output: [paste example]" → exactly what you need
- Enumerate. Give examples. Show the expected output format. Pretend Claude is a brilliant new hire on day one.

### 3. Learn by Doing, Fix by Shipping
- Don't build in a vacuum. Put it in front of real users immediately.
- Every tester broke something I never anticipated
- Build self-correcting systems — domain knowledge playbooks that grow with every deal
- The product isn't the code. The product is the feedback loop.

---

**Aigis Analytics** — Domain Intelligence, Deal Certainty.

*Built with Claude Code. By someone who still can't write a for-loop from memory.*
