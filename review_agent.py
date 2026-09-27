"""
Code Review Agent with Hindsight memory.

Reviews a sequence of PR diffs, using Hindsight to remember what it has
already learned about the team's coding patterns so later reviews get
sharper instead of repeating the same generic feedback every time.

Setup:
    pip install hindsight-client groq

    export HINDSIGHT_API_KEY=your_hindsight_key
    export HINDSIGHT_BASE_URL=https://your-hindsight-cloud-url   # check your dashboard
    export GROQ_API_KEY=your_groq_key

Run:
    python review_agent.py
"""

import os
import glob
from hindsight_client import Hindsight
from groq import Groq

BANK_ID = "code-review-agent-demo"
DIFFS_DIR = "sample_prs"  # folder with the .diff files, in review order
GROQ_MODEL = "openai/gpt-oss-120b"  # fall back to "qwen/qwen3-32b" if this errors

hindsight = Hindsight(
    base_url=os.environ["HINDSIGHT_BASE_URL"],
    api_key=os.environ["HINDSIGHT_API_KEY"],
)
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])


def load_diffs(directory):
    """Load all .diff files from a directory, sorted so PRs run in order."""
    paths = sorted(glob.glob(os.path.join(directory, "*.diff")))
    diffs = []
    for path in paths:
        with open(path, "r") as f:
            diffs.append({"name": os.path.basename(path), "content": f.read()})
    return diffs


def get_context(bank_id):
    """Ask Hindsight what it already knows about this team's patterns."""
    try:
        result = hindsight.reflect(
            bank_id=bank_id,
            query="What do we know about this team's coding conventions, "
                  "recurring mistakes, and past code review feedback?",
        )
        # reflect() returns a disposition-aware answer; fall back to empty
        # string if the bank has no memories yet (first run).
        return getattr(result, "text", str(result)) or ""
    except Exception as exc:
        print(f"  [memory] no prior context available yet ({exc})")
        return ""


def review_diff(diff_text, context):
    """Call Groq to review the diff, given whatever memory context we have."""
    system_prompt = (
        "You are a senior code reviewer for a software team. Review the "
        "given diff for issues: error handling, naming consistency, "
        "security (hardcoded secrets), and general code quality.\n\n"
        "You have been given prior context about this team's known "
        "patterns and past feedback. If an issue you're seeing has already "
        "been noted before, do NOT re-explain it at length — just flag it "
        "briefly (e.g. 'Same missing error handling as noted previously'). "
        "Only give full explanations for genuinely new issues. If the code "
        "shows clear improvement on a previously flagged pattern, say so.\n\n"
        f"Known context about this team:\n{context if context else '(no prior context yet)'}"
    )

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Review this diff:\n\n{diff_text}"},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


def save_findings(bank_id, pr_name, review_text):
    """Store what this review revealed so future reviews can build on it."""
    try:
        hindsight.retain(
            bank_id=bank_id,
            content=f"Code review findings for {pr_name}:\n{review_text}",
        )
    except Exception as exc:
        print(f"  [memory] failed to store findings: {exc}")


def main():
    diffs = load_diffs(DIFFS_DIR)
    if not diffs:
        print(f"No .diff files found in '{DIFFS_DIR}/'. Check the path.")
        return

    for i, pr in enumerate(diffs, start=1):
        print(f"\n{'=' * 60}")
        print(f"PR {i}: {pr['name']}")
        print("=" * 60)

        context = get_context(BANK_ID)
        review = review_diff(pr["content"], context)

        print(review)

        save_findings(BANK_ID, pr["name"], review)

    print(f"\n{'=' * 60}")
    print("Done. Compare the PR 1 review to the PR 4/5 reviews for your demo.")


if __name__ == "__main__":
    main()
