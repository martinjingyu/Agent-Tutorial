# Ctrl-Agent: Structured Trajectory Control for Multi-Tool Agentic Reasoning

## Refined Paper Proposal — July 2026

---

## Executive Summary

**Ctrl-Agent** is the first framework to apply *tractable trajectory control* (Ctrl-R's behavior policy + importance-sampled RL) to *multi-tool agent training* (Lumos-style planning→grounding→execution). The core technical leap: Ctrl-R operates at the **token level** (vocabulary V = 32K-128K), while Ctrl-Agent operates at the **tool-call level** (tool T × parameters P, a combinatorial space). This requires a fundamentally new **hierarchical guidance model** — a contribution that goes well beyond "Ctrl-R on a new benchmark."

---

## Part 1: Kai-Wei Chang Expert — Technical Differentiation

### 1.1 How Ctrl-Agent Differentiates From Each Lab Paper

#### vs. Ctrl-R (NeurIPS 2026 Spotlight) — The Fundamental Leap

Ctrl-R's guidance model operates at the **token level**:
```
µα(xt | x<t) ∝ πθ_old(xt | x<t) · γ(α | xt, x<t)
```
The partition function `Zt = Σ_{x∈V} πθ_old(x | x<t)γ(α | x, x<t)` is tractable because V is a finite vocabulary.

**Ctrl-Agent requires a fundamentally different guidance model** because tool calls are structured actions spanning many tokens:

```
<tool_call>
{"name": "search_flights", "arguments": {"from": "LAX", "to": "JFK"}}
</tool_call>
```

| Dimension | Ctrl-R | Ctrl-Agent | Technical Implication |
|-----------|--------|------------|----------------------|
| **Action space** | Token-level (vocabulary V = 32K-128K) | Tool-call-level (tool T × parameters P, combinatorial) | Partition function over T×P is intractable → need **hierarchical factorization** |
| **State space** | Token sequence | Structured context graph (plan state, tool history, return values, errors) | Need **structured state representation** with dependency tracking |
| **Constraints** | Lexical patterns in text | Tool-call patterns (success/failure, ordering, composition) | Need **tool-level constraint functions**, not token-level regex |
| **Guidance** | Per-token probability | Hierarchical: tool selection + parameter generation | Need **two-level guidance model** |
| **Backtracking** | "Let me go back" in text | Actual state restoration + tool retry | Need **state checkpointing and restoration** |
| **Counterfactual** | "What if I" in reasoning | Actual alternative tool invocation | Need **branching and comparison** in trajectory space |

**The key technical novelty**: A **hierarchical guidance model** with three levels:

| Level | What it guides | Action space | Tractability |
|-------|---------------|--------------|-------------|
| **L1: Tool Selection** | Which tool to call | Finite (50-200 tools) | **Easier than Ctrl-R** — partition over 200 items vs. 32K tokens |
| **L2: Parameter Generation** | JSON arguments within a tool call | Token-level (vocabulary V) | **Same as Ctrl-R** — reuse Ctrl-G's HMM+DFA machinery |
| **L3: Trajectory Pattern** | When to backtrack/re-plan | Rule-based intervention | Heuristic but effective |

**Level 1 is actually *easier* than Ctrl-R** because the tool set is smaller than the vocabulary. Level 2 directly reuses Ctrl-R's existing code. The novelty is in **combining them hierarchically** — the L1 guidance selects which tool to call, then L2 guidance shapes the parameter generation within that tool call.

#### vs. Lumos (ACL 2024) — From Static SFT to Online RL with Structure Control

Lumos provides the **modular architecture** (planning → grounding → execution) that Ctrl-Agent optimizes. The critical difference:

- **Lumos**: SFT on static demonstrations → no exploration, no recovery from failures
- **Ctrl-Agent**: Online RL with trajectory control → active exploration of alternative tool-use patterns

The Lumos modules become the **policy network** that Ctrl-Agent's RL optimizes. The Planner generates subgoals conditioned on trajectory state (including backtracking state). The Grounder selects tools guided by the trajectory controller's exploration strategy.

**Concrete improvement**: Lumos's grounding module translates subgoals to tool calls via SFT. If the training data only shows `search_flights` for flight queries, the model never learns to try `search_trains` when flights fail. Ctrl-Agent's trajectory controller actively explores alternative tool choices during RL training, discovering patterns the static data doesn't cover.

#### vs. Magnet (ACL 2025) — From Static Synthesis to Dynamic Exploration

Magnet generates **static seed trajectories** via graph translation. Ctrl-Agent uses these as **starting points for structured exploration**:

```
Magnet:  Graph → static trajectories → SFT/DPO
Ctrl-Agent:  Graph → seed trajectories → Ctrl-R guided exploration (N branches per seed) → RL
```

For each seed trajectory, the trajectory controller generates N branches:
- **Forward-only** (baseline): Follow the seed path
- **Backtracking**: On tool failure, try alternative tool
- **Counterfactual**: Try different tool ordering
- **Backward-chaining**: Plan from goal state

This is impossible in Magnet because graph translation produces a single deterministic path.

#### vs. DAC-RL (ACL 2026) — From Pure Reasoning to Tool-Use with Recovery

DAC-RL trains divide-and-conquer reasoning for **math problems**. Ctrl-Agent extends this to **tool-use environments** where:
- **Decomposition** = planning (breaking task into tool-achievable subgoals)
- **Subproblem solving** = grounding + execution (calling tools)
- **Conquering** = aggregating tool outputs

But Ctrl-Agent goes beyond DAC-RL by adding **trajectory control** — the ability to backtrack when a subproblem can't be solved with the chosen tool, or explore counterfactual tool choices. DAC-RL assumes decomposition is correct; Ctrl-Agent allows the agent to **discover and recover from incorrect decompositions**.

#### vs. OpenThoughts (ICLR 2026) — From Reasoning Data to Agentic Data Recipes

OpenThoughts studies data recipes for reasoning models. Ctrl-Agent extends this to **agentic data recipes** — what kinds of multi-turn tool-use trajectories (with backtracking, counterfactuals, etc.) produce the best agent policies. The trajectory controller itself becomes a **tunable data recipe generator**.

### 1.2 What Kai-Wei Would See as the Key Technical Novelty

Three axes of evaluation:

**Axis 1 — New problem?** ✅ Yes. Structured trajectory control for tool-use agents is unsolved. Current agents (ReAct, SWE-agent, CodeAct) all use forward-only rollouts. When a tool fails, they retry the same call, give up, or use a generic response — no structured exploration or learning from failure.

**Axis 2 — Sound and non-trivial?** ✅ Yes, with three hard technical challenges:

1. **Hierarchical guidance model**: The partition function `Zt` over tool × parameter space is intractable. Solution: factorize into tool selection (finite, tractable) and parameter generation (reuse Ctrl-R's token-level guidance).

2. **Structured state representation for backtracking**: Ctrl-R's "backtracking" is a lexical pattern. Ctrl-Agent requires **actual state restoration** — knowing which prior state to return to, which context to preserve, which tool call to retry. Solution: maintain a **structured dependency graph** tracking which tool outputs feed into which subsequent calls.

3. **Tool-level credit assignment**: When a 10-step trajectory succeeds, which tool calls were critical? Ctrl-R's token-level credit assignment doesn't apply. Solution: **tool-level process rewards** using a learned verifier that evaluates each tool call's contribution.

**Axis 3 — Convincing experiments?** The make-or-break. Required:
- **Ablation of each reasoning pattern**: Remove backtracking → how much drop? Remove counterfactual → how much?
- **Strong baselines**: ReAct, Lumos, SWE-agent, CodeAct with equivalent compute
- **Analysis of when each pattern helps**: Backtracking critical for API-heavy tasks; counterfactual for search tasks
- **Scaling behavior**: Does Ctrl-Agent benefit more from more compute than baselines?

### 1.3 Risks of Overlap with Concurrent Work

| Risk | Severity | Mitigation |
|------|----------|------------|
| "This is just ReAct + RL" | **High** | ReAct is a prompting strategy. Ctrl-Agent is an RL training framework with structured exploration via a tractable guidance model. Ctrl-Agent : ReAct :: Ctrl-R : CoT. |
| "SWE-agent already does backtracking" | **Medium** | SWE-agent's backtracking is **heuristic** (retry same command), not **learned** (explore alternative tools). No counterfactual exploration, no backward chaining, no importance-sampled RL. |
| "This is too incremental on Ctrl-R" | **High** — biggest risk | The leap from token-level to tool-call-level guidance is **not incremental**. It requires fundamentally new techniques for hierarchical guidance, structured state graphs, and tool-level credit assignment. Frame as **Ctrl-R × Agent** — a new problem domain. |
| Concurrent work from Apple/Google | **Medium** | Ctrl-R is UCLA+Apple. Magnet is UCLA+Google. Move fast — 6 months to first results, 12 months to submission. |

---

## Part 2: Agent Research Expert — Technical Novelty vs. Current SOTA

### 2.1 Is This Technically Novel? Yes — Here's Why

**No existing agent system has a principled mechanism for controlling *which reasoning patterns* an agent explores during training.** Every current system falls into one of three categories:

| Approach | Examples | Limitation |
|----------|----------|------------|
| **Forward-only rollouts** | ReAct, CodeAct, SWE-agent | No recovery from dead ends; retry same action or give up |
| **Static data** | Lumos, Magnet | Never learns from own mistakes (no exploration during training) |
| **Standard RL rollouts** | Agent-R1, DAC-RL | No *control* over which patterns are explored — model exploits known patterns, never discovers novel ones |

**Ctrl-Agent's key novelty**: A tractable behavior policy that *actively guides* the agent toward trajectories exhibiting specific reasoning patterns (backtracking, backward chaining, induction, counterfactual) during RL training, with provable importance-sampling guarantees.

### 2.2 Concrete Failure Modes This Addresses

| Failure Mode | Current Behavior | Ctrl-Agent Behavior |
|---|---|---|
| **Tool error → infinite retry** | Calls same API → error → retry → timeout | **Backtracks** to planning state, tries alternative tool/approach |
| **Wrong tool → wrong answer** | Calls `get_weather` instead of `get_flight_delay` | **Counterfactual**: "What if I call the other API? Let me compare." |
| **Missing subgoal** | Calls `book_flight()` without `search_flights()` first | **Backward chaining**: "To book, I need a flight ID. To get that, I search first." |
| **Unknown API format** | Hallucinates parameter names → fails | **Induction**: "Let me probe the API with a minimal call first." |
| **Context overflow** | 10K+ tokens of tool output → loses track of goal | **Context-Refine**: Summarize intermediate results, maintain goal focus |

### 2.3 Recommended Benchmarks

| Benchmark | Why | Current Ceiling | Ctrl-Agent Expected Gain |
|-----------|-----|----------------|-------------------------|
| **BFCL-v3** (multi-turn FC) | Tests all 5 patterns; nested calls, long dependencies | ~47% proprietary, ~10% open | +15-20% on open models |
| **ToolBench** (16K+ APIs) | Multi-tool composition; tests planning+grounding+execution | ~50-60% | +10-15% |
| **WebArena** (web environments) | Long-horizon planning with tool feedback | ~30-40% open models | +8-12% |
| **ToolQuery** (multi-turn + clarification) | Tests recovery and adaptation | ~73% (Magnet-14B) | +5-10% |

### 2.4 Key Ablations (Make-or-Break Experiments)

| Ablation | What It Tests | Expected Result |
|----------|--------------|-----------------|
| Remove backtracking | Is recovery from tool errors learned or memorized? | Big drop on BFCL-v3 (error recovery) |
| Remove counterfactual | Is alternative tool selection learned? | Big drop on ToolBench (tool selection) |
| Remove induction | Is API probing learned? | Drop on unfamiliar APIs |
| Remove backward chaining | Is goal decomposition learned? | Drop on multi-step tasks |
| Remove importance sampling | Does Ctrl-R's IS correction matter? | Smaller drop, but unstable training |
| β = 0 (no power scaling) | Does selective exploration matter? | Moderate drop |

---

## Part 3: ML Systems Expert — Concrete Training Pipeline

### 3.1 Training Pipeline (4 Phases)

```
Phase 0: Warm-start SFT (Magnet-style data synthesis)
  ├─ Graph translation → 5K-10K structured trajectories
  ├─ Each trajectory annotated with pattern labels
  └─ SFT on base model (Qwen3-8B-Base)

Phase 1: Base RL (standard GRPO on tool tasks)
  ├─ Reproduce Agent-R1-style GRPO baseline
  ├─ ToolBench subset (5K tasks)
  └─ Establish lower bound for comparison

Phase 2: Ctrl-R Guided RL (trajectory-controlled) ← CORE
  ├─ Initialize guidance model from Phase 0
  ├─ Hierarchical guidance (L1: tool selection, L2: parameters)
  ├─ GRPO with importance-sampled policy updates
  ├─ Power-scaling (β) for selective exploration
  └─ Self-evolving structure distribution

Phase 3: Evaluation & Ablations
  ├─ BFCL-v3, ToolBench, WebArena, ToolQuery
  ├─ 6 ablation conditions (see 2.4)
  ├─ 3 baseline comparisons (ReAct, Lumos, Agent-R1)
  └─ Analysis: structure distribution evolution, failure modes
```

### 3.2 Reward Design

| Reward | Type | Value | Purpose |
|--------|------|-------|---------|
| Task success | Sparse | +1.0 / -1.0 | Primary objective |
| Pattern diversity | Dense | +0.1 per distinct pattern | Encourage structured reasoning |
| Tool efficiency | Dense | -0.01 per tool call | Minimize wasted API calls |
| Verification accuracy | Dense | +0.2 | Correct tool output validation |
| Backtracking success | Dense | +0.3 | Successful recovery from failure |

### 3.3 Resource Requirements

| Component | GPUs | Time | Data |
|-----------|------|------|------|
| Phase 0: Data synthesis | 0 (GPT-4o API) | 2-4 weeks | 5K-10K trajectories |
| Phase 1: Base RL | 8× A100-80GB | 2-4 weeks | 5K tasks (ToolBench subset) |
| Phase 2: Ctrl-R guided RL | 8× A100-80GB | 4-8 weeks | Same + synthesized branches |
| Phase 3: Evaluation | 1× A100-80GB | 1-2 weeks | All benchmarks |
| **Total** | **8× A100-80GB** | **3-4 months** | **~30K trajectories total** |

**Software stack**: veRL (RL framework, Ctrl-R uses this), Ctrl-G (guidance model, open-source), vLLM (inference), Qwen3-8B-Base (base model).

### 3.4 Feasibility: Can a Single MSCS Student + Advisor Complete This?

**Assessment: Yes, within 18 months.**

**What makes it feasible:**
- Ctrl-R's codebase (Ctrl-G + veRL) is **open-source** — the token-level guidance machinery is ready-made
- Jingyu already has the **agent infrastructure** (Guardian-Worker, GRPO pipeline concepts)
- **8B models** are manageable on 8× A100s
- The core novelty is **focused**: extending guidance from token-level to tool-call-level

**What's risky:**
1. **Hierarchical guidance integration** (L1 + L2) — the hardest engineering part
2. **Tool environments are flaky** — API failures, rate limits, timeouts
3. **Ablation experiments are numerous** — 20+ training runs

**Mitigation strategy:**
- Start with **L1 only** (tool selection guidance, no parameter guidance) as MVP
- Use **simulated tool environments** (ToolBench's built-in sim) for training; real APIs only for final eval
- Start with **β=0** (no importance sampling, just guided exploration); add IS as extension

---

## Part 4: Jingyu Huang — Build vs. Adapt Assessment

### 4.1 What I Already Have

| Asset | Status | Reusability |
|-------|--------|-------------|
| **Guardian-Worker architecture** | ✅ Working (research_agent/guardian.py) | Controller-Worker pattern directly maps to Trajectory Controller + Agent Worker |
| **Context management** | ✅ Working (research_agent/context.py) | Structured state graph for tool call history |
| **Multi-agent orchestration** | ✅ Working (Kanban pipeline, meeting moderator) | Synthesizer/Validator/Diversity agents for data generation |
| **GRPO pipeline concepts** | ✅ Conceptual understanding | Need to implement actual veRL integration |
| **Tool environment integration** | ✅ Browser tools, file tools | Need to add ToolBench/API environments |

### 4.2 What I Need to Build vs. Adapt vs. Reuse

| Component | Action | Effort | Risk |
|-----------|--------|--------|------|
| **L1 guidance model** (tool selection classifier) | **Build from scratch** | ~500 lines | Medium — need to define tool-level constraint functions |
| **L2 guidance integration** (Ctrl-G for parameters) | **Adapt** (Ctrl-G already open-source) | ~300 lines | Low — Ctrl-G's HMM+DFA machinery is ready-made |
| **Hierarchical rollout wrapper** (L1+L2 integration) | **Build from scratch** | ~1000 lines | **High** — the core technical contribution |
| **Tool environment interface** (ToolBench, BFCL-v3, WebArena) | **Build from scratch** | ~500 lines/env | Medium — environments are well-documented |
| **Pattern annotation pipeline** (label trajectories with structure tags) | **Build from scratch** | ~300 lines | Low — rule-based + LLM-based annotation |
| **veRL integration** (add Ctrl-R loss to GRPO) | **Adapt** | ~200 lines | Medium — need to understand veRL internals |
| **Guardian → Controller adaptation** | **Adapt** | ~500 lines | Low — architectural pattern is the same |
| **Seed data synthesis** (Magnet-style graph translation) | **Build from scratch** | ~500 lines | Medium — need to define function signature graphs |
| **Evaluation harness** (run all benchmarks, collect metrics) | **Build from scratch** | ~500 lines | Low — standard benchmarking infrastructure |

### 4.3 Riskiest Component

**The hierarchical rollout wrapper** (L1 + L2 integration) is the riskiest because:

1. **Timing**: The L1 guidance (tool selection) must fire *before* the tool call, while L2 guidance (parameter generation) fires *during* the tool call's parameter tokens. This requires careful orchestration of the rollout loop.

2. **State synchronization**: The L1 guidance model needs access to the trajectory state (which tools have been called, what errors occurred), while L2 guidance operates at the token level. Keeping these in sync across the rollout is non-trivial.

3. **Importance weight computation**: The IS weight for a trajectory is the product of L1 weights (tool selection) × L2 weights (parameter tokens). Computing this correctly requires careful log-space arithmetic and clipping.

**Mitigation**: Start with **L1-only guidance** (no parameter-level guidance). This already provides significant value (tool selection is the most impactful decision in agentic tasks). Add L2 guidance as an extension once L1 is working.

### 4.4 Timeline Estimate

| Month | Milestone | Deliverable |
|-------|-----------|-------------|
| 1-2 | Phase 0: Data synthesis | 5K-10K structured trajectories with pattern labels |
| 3-4 | Phase 1: Base RL | Reproduce Agent-R1-style GRPO on ToolBench |
| 5-6 | Build L1 guidance model | Tool selection classifier + constraint functions |
| 7-8 | Build hierarchical rollout wrapper | L1+L2 integration, importance weight computation |
| 9-10 | Phase 2: Full Ctrl-R guided RL | Training runs on ToolBench + BFCL-v3 |
| 11-12 | Phase 3: Evaluation + Ablations | All benchmarks, 6 ablation conditions, 3 baselines |
| 13-14 | Analysis + Writing | Paper draft, figures, tables |
| 15-16 | Rebuttal preparation | Additional experiments, analysis |
| 17-18 | Buffer | Re-runs, reviewer feedback, camera-ready |

**Total: 18 months** — fits within a 2-year MSCS timeline.

### 4.5 Concrete Next Steps (This Week)

1. **Clone Ctrl-R's codebase** (Ctrl-G + veRL) and verify it runs on a simple math task
2. **Set up ToolBench environment** and verify a simple ReAct baseline
3. **Define the 5 agentic reasoning patterns** as formal constraint functions (what lexical/structural signals indicate each pattern?)
4. **Implement a minimal L1 guidance model** — a classifier that predicts which tool should be called next given the current trajectory state
5. **Run a small-scale proof of concept**: L1 guidance + GRPO on 100 ToolBench tasks with 1 tool category (e.g., search APIs only)

### 4.6 Success Criteria for First 3 Months

| Milestone | Success Criterion | Fallback |
|-----------|-------------------|----------|
| Ctrl-R codebase runs | Can reproduce Ctrl-R results on GSM8K | Debug with Ctrl-R authors (UCLA connection) |
| ToolBench baseline | ReAct achieves 50%+ on 100-task subset | Use simpler benchmark (BFCL-v3) |
| L1 guidance model | 80%+ accuracy on tool selection prediction | Use rule-based guidance as fallback |
| Small-scale PoC | L1-guided GRPO outperforms standard GRPO on 100 tasks | Reduce scope to 1 tool category |

---

## Summary: Why This Paper Will Be Accepted

| Criterion | How Ctrl-Agent Satisfies It |
|-----------|----------------------------|
| **Novel problem** | First to apply tractable trajectory control to multi-tool agentic environments |
| **Non-trivial solution** | Hierarchical guidance model (L1 tool selection + L2 parameter generation) is a fundamental extension of Ctrl-R's token-level approach |
| **Strong empirical validation** | 4 benchmarks, 6 ablations, 3 baselines, comprehensive analysis |
| **Clear positioning** | Ctrl-R × Agent — a new problem domain, not Ctrl-R on a new benchmark |
| **Feasible scope** | 18 months, 8× A100s, single student + advisor, leveraging existing open-source code |

**Target venue**: NeurIPS 2027 (methods focus) or ICLR 2027 (representation learning focus).
