#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="data/startup_strategy_pack"
mkdir -p "$OUT_DIR"

topics=(go_to_market product pricing growth fundraising retention ops)

for topic in "${topics[@]}"; do
  for i in 1 2 3 4 5; do
    file="$OUT_DIR/${topic}_playbook_${i}.md"
    cat > "$file" <<EOF
# ${topic} Playbook ${i}

## Thesis
For early-stage technical startups, ${topic} decisions should follow an iterative loop: hypothesis -> test -> measurement -> adjustment.

## Strategy Principles
1. Prioritize a narrow ICP before broad expansion.
2. Define one primary success metric per quarter.
3. Keep execution cycles short (1-2 weeks) and documented.
4. Convert qualitative feedback into quantitative experiments.

## Practical Checklist
- Define customer segment and buying trigger.
- Write a clear value proposition statement.
- Set a weekly review cadence with owners.
- Record assumptions and invalidated hypotheses.
- Build decision logs for future fundraising diligence.

## Common Failure Modes
- Trying to scale before proving repeatability.
- Weak messaging that does not match user pain.
- Unclear ownership across product, engineering, and GTM.
- Ignoring retention while optimizing top-of-funnel.

## Execution Notes
- Use a weekly dashboard with leading and lagging indicators.
- Keep scope constrained to preserve runway.
- Tie each spend item to an explicit expected outcome.

## Topic Tag
${topic}
EOF
  done
done

echo "Generated strategy pack in $OUT_DIR"
