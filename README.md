# Code Review Agent — Powered by Hindsight Memory

An AI code review agent that gets smarter with every pull request. Instead of repeating the same generic feedback on every diff, it remembers what it has already told your team and builds up institutional knowledge over time — just like a senior engineer who's reviewed your codebase for months.

Built for the **AI Agents That Learn Using Hindsight** hackathon, using [Hindsight](https://hindsight.vectorize.io/) as the memory layer and [Groq](https://groq.com/) for fast LLM inference.

---

## The Problem

Generic AI code review tools re-explain the same issues on every PR. If your team always forgets to add error handling, a stateless reviewer will lecture you about it in exhaustive detail — PR after PR after PR — as if it's never seen your codebase before. That's noisy, and it buries genuinely new issues under repeated boilerplate advice.

## The Solution

This agent uses Hindsight to **remember what it has already told your team**, so its reviews evolve:

- **First PR:** thorough, generic feedback — the agent has no context yet.
- **Later PRs:** the agent recognizes recurring patterns ("same missing error handling as noted previously") and gives them a brief flag instead of a full explanation, while still going in-depth on genuinely new issues.
- **When the team improves:** the agent notices and acknowledges the improvement instead of repeating stale advice.

This mirrors how a real senior reviewer builds context on a team over time, rather than treating every PR as a cold start.

## How Hindsight Memory Is Used

The agent calls Hindsight's three core operations around every review:

| Operation | When | Purpose |
|---|---|---|
| `reflect()` | Before reviewing a PR | Asks Hindsight what it already knows about this team's coding conventions and past issues, returning a disposition-aware summary used as context for the LLM prompt. |
| *(LLM call to Groq)* | During review | The diff + the memory context are sent to the LLM, which is explicitly instructed to flag recurring issues briefly and reserve full explanations for new ones. |
| `retain()` | After reviewing a PR | Stores a summary of what was found in this PR back into the memory bank, so the next `reflect()` call has richer context. |

Each PR review is one full **retain → reflect → retain** cycle, and the memory bank (`bank_id`) persists across runs — the agent's understanding of the team compounds with every PR it reviews.

## Demo

Run the agent against 5 sample PRs from a fictional inventory-management codebase, all written by the same (fictional) author with intentionally recurring habits (inconsistent naming, missing error handling) plus one new issue introduced partway through (a hardcoded API key) and a final PR showing real improvement.

Compare the PR 1 output to PR 4/5:
- **PR 1** — full, generic breakdown of every issue, no memory yet.
- **PR 4/5** — issues are explicitly labeled "recurring — flag only" vs. "new — full explanation," and improvements are called out.

*(See `/demo` for the recorded walkthrough.)*

## Project Structure

```
.
├── review_agent.py       # Main script: loads diffs, queries/stores memory, calls Groq
├── sample_prs/           # 5 synthetic PR diffs used for the demo
│   ├── pr_1_load_inventory.diff
│   ├── pr_2_sync_warehouse.diff
│   ├── pr_3_reorder_calc.diff
│   ├── pr_4_pricing_api.diff
│   └── pr_5_stock_alert.diff
├── requirements.txt
└── README.md
```

## Setup

**1. Get your API keys**
- [Hindsight Cloud](https://ui.hindsight.vectorize.io/signup) — sign up, then find your base URL and API key on the **Connect** page.
- [Groq](https://groq.com/) — sign up and create an API key.

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Set environment variables**
```bash
export HINDSIGHT_API_KEY=your_hindsight_key
export HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
export GROQ_API_KEY=your_groq_key
```

**4. Run it**
```bash
python review_agent.py
```

The script reviews all 5 sample PRs in order, printing each review to the console. Watch how the tone and depth of the feedback shift from PR 1 to PR 5.

## Tech Stack

- **[Hindsight](https://hindsight.vectorize.io/)** — persistent memory layer (retain / recall / reflect)
- **[Groq](https://groq.com/)** — LLM inference (`openai/gpt-oss-120b`)
- **Python** — agent logic

## Future Improvements

- Pull real PRs from a connected GitHub repo instead of static sample diffs
- Web UI showing the memory bank's evolving understanding of the team
- Multi-repo / multi-team memory isolation via separate `bank_id`s
- Slack/GitHub bot integration for real-time review comments
