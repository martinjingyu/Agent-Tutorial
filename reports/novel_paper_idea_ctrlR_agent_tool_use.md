# Ctrl-Agent: Bridging Structured Reasoning Trajectory Control and Agent Tool-Use

## A Novel Research Direction for NeurIPS/ICLR 2027

---

## 1. The Core Idea

**Ctrl-Agent**: A framework that applies *structured reasoning trajectory control* (Ctrl-R's tractable behavior policy + importance-sampled RL) to the *agent planning/grounding/execution pipeline* (Lumos's modular architecture), enabling agents to systematically learn and internalize diverse reasoning patterns (backtracking, backward chaining, induction, counterfactual) during multi-tool interactions.

### The Gap (Why This Is Novel)

| Area | Existing Work | Missing |
|------|--------------|---------|
| **Structured reasoning** | Ctrl-R (NeurIPS 2026 Spotlight) controls reasoning trajectories for math/QA via lexical constraints + importance-sampling RL | Only applied to *monolithic reasoning* (text generation), never to *agent tool-use* with planning→grounding→execution |
| **Agent training** | Lumos (ACL 2024) trains modular planning/grounding/execution; Magnet (ACL 2025) synthesizes multi-turn tool-use data | Both use SFT/DPO on static data — no *RL-based trajectory control* over agent reasoning patterns |
| **Agentic RL** | DAC-RL (ACL 2026) uses end-to-end RL for divide-and-conquer reasoning | Focused on *decomposition structure*, not on diverse reasoning *patterns* (backtracking, counterfactual, etc.) |
| **Data recipes** | OpenThoughts (ICLR 2026) studies SFT data curation for reasoning models | Does not address *agent tool-use trajectories* or *RL-based exploration* |

**The key insight**: No existing work uses *structured trajectory control* (backtracking, backward chaining, induction, counterfactual exploration with tractable importance sampling) to improve agent *planning/grounding/execution* in multi-tool environments.

---

## 2. Technical Approach

### 2.1 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                 Trajectory Controller                │
│  (Ctrl-R-style tractable behavior policy)            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │Backtrack │  │Backward  │  │Induction │  │Count-│ │
│  │          │  │Chaining  │  │          │  │erfac.│ │
│  └──────────┘  └──────────┘  └──────────┘  └──────┘ │
└─────────────────────┬───────────────────────────────┘
                      │ guides rollout distribution
                      ▼
┌─────────────────────────────────────────────────────┐
│              Agent Pipeline (Lumos-style)            │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐       │
│  │ Planning │───▶│Grounding │───▶│Execution │       │
│  │ Module   │    │ Module   │    │ Module   │       │
│  └──────────┘    └──────────┘    └──────────┘       │
│       │               │               │              │
│       ▼               ▼               ▼              │
│  Subgoal Gen.    Action Sel.     Tool Calls          │
└─────────────────────┬───────────────────────────────┘
                      │ produces trajectories
                      ▼
┌─────────────────────────────────────────────────────┐
│          Agentic GRPO (RL Training Loop)             │
│  • Tool-call rewards (correctness + efficiency)      │
│  • Importance-sampled policy updates                 │
│  • Power-scaled advantage shaping                    │
└─────────────────────────────────────────────────────┘
```

### 2.2 Key Technical Components

#### Component A: Trajectory Controller for Agent Pipelines

Ctrl-R defines reasoning structures as **lexical constraints** over generated tokens (e.g., "let me go back" → backtracking). We extend this to **agentic structures** — patterns that manifest across the planning→grounding→execution pipeline:

| Agentic Reasoning Pattern | Definition | Lexical/Structural Signal |
|--------------------------|------------|--------------------------|
| **Backtracking** | Agent retracts a previous subgoal/action and tries an alternative tool or approach | "Let me undo that tool call...", "That API returned an error, trying another..." |
| **Backward Chaining** | Agent starts from the desired output and works backward to determine which tools to call | "To get X, I first need Y from tool A, then Z from tool B..." |
| **Induction** | Agent tests a simple case or probes the environment before full execution | "Let me first call the search API with a small query to see the format..." |
| **Counterfactual** | Agent simulates alternative tool-use paths and compares outcomes | "What if I call API A instead of API B here? Let me compare..." |
| **Recovery** | Agent detects execution failure and adapts its plan | "The tool returned an unexpected schema, I need to reformat..." |

The **tractable guidance model** estimates the likelihood of satisfying these agentic constraints during rollout, reshaping the rollout distribution toward trajectories that exhibit these patterns.

#### Component B: Agentic GRPO with Tool-Call Rewards

Standard GRPO uses outcome rewards (correct/incorrect). We extend this to **tool-call-aware rewards**:

- **Tool correctness reward**: Did the agent call the right tool with the right parameters?
- **Tool efficiency reward**: Did the agent solve the task with minimal redundant tool calls?
- **Pattern diversity reward**: Does the trajectory exhibit diverse reasoning patterns (bonus for exploring underused patterns)?
- **Task outcome reward**: Final answer correctness (sparse, as in standard RL)

The **power-scaling factor** on importance-sampling weights (from Ctrl-R) allows selective amplification of learning signals from exploratory, out-of-distribution agent trajectories while maintaining stable optimization.

#### Component C: Magnet-Inspired Seed Data via Graph Translation

Use Magnet's graph-translation approach to synthesize **structured seed trajectories**:

1. Define a **function signature path graph** for multi-tool scenarios
2. Translate graph paths into agent trajectories that *explicitly* exhibit target reasoning patterns
3. Generate both positive trajectories (correct tool use with pattern X) and negative trajectories (correct outcome but no structured reasoning)
4. Use these as cold-start initialization for RL training

#### Component D: Self-Evolving Exploration Strategy

Leverage Jingyu's Guardian-Worker architecture as a **Controller-Worker** framework:

- **Controller** (Guardian): The tractable behavior policy that decides *which reasoning pattern to explore* at each rollout
- **Worker** (Agent): The Lumos-style agent pipeline executing the actual tool-use
- **Self-evolution**: After each RL iteration, the Controller updates its policy based on which patterns yielded the highest reward, dynamically shifting exploration toward more effective patterns

This mirrors the puppeteer-style orchestration (NeurIPS 2025) but applied at the *reasoning-pattern level* rather than the agent level.

---

## 3. Why This Leverages Jingyu's Strengths

| Jingyu's Strength | How It Maps to Ctrl-Agent |
|-------------------|--------------------------|
| **LLM Agent pipeline building** | Designing the Lumos-style planning→grounding→execution pipeline with tool integration |
| **Multi-agent orchestration** (puppeteer-style) | Controller-Worker architecture where Controller orchestrates which reasoning pattern the Worker explores |
| **Context management** | Managing the trajectory state graph — tracking which patterns have been explored, which tools have been called, and the evolving context window |
| **RL post-training (GRPO)** | Implementing Agentic GRPO with tool-call rewards and importance-sampled policy updates |
| **Multi-turn jailbreak** (MultiBreak, ICML 2026) | Understanding multi-turn interaction dynamics transfers directly to multi-turn tool-use scenarios |
| **Self-evolving agent framework** (Guardian-Worker) | The Controller-Worker architecture is a direct analog — the Controller evolves its exploration policy over time |

---

## 4. What Makes This A-Class Conference Worthy

### 4.1 Novelty (Strong)

- **First work** to bridge structured reasoning trajectory control (Ctrl-R) with agent tool-use (Lumos)
- **New problem formulation**: "Agentic reasoning patterns" as first-class citizens in RL-based agent training
- **Technical novelty**: Extending Ctrl-R's tractable importance-sampling from token-level constraints to *agentic-level structural constraints* (subgoal sequences, tool-call patterns, execution feedback loops)

### 4.2 Technical Depth

- **Principled**: Tractable behavior policy with provable importance-sampling guarantees (inherited from Ctrl-R)
- **End-to-end**: From seed data synthesis (Magnet-style) through RL training (Agentic GRPO) to self-evolving exploration
- **Modular**: Each component (Controller, Worker, Reward, Data Synthesis) is independently improvable

### 4.3 Empirical Impact

- **Benchmarks**: ToolBench, BFCL-v3, ToolQuery, AgentBench, WebArena — all multi-tool, multi-turn scenarios where current models struggle
- **Expected results**: Ctrl-Agent should outperform both (a) standard SFT/DPO agent training and (b) Ctrl-R applied to monolithic reasoning, demonstrating that *structured trajectory control for agents* is a distinct and valuable contribution
- **Ablations**: Which reasoning patterns matter most for which tool-use scenarios? (e.g., backtracking for API error recovery, backward chaining for multi-step tool composition)

### 4.4 Positioning

**Target venue**: NeurIPS 2027 or ICLR 2027 (methods paper with strong empirical results)

**Narrative**:
> "Just as Ctrl-R showed that controlling *what reasoning patterns* a model explores during RL improves math reasoning, we show that controlling *what agentic reasoning patterns* an agent explores during RL improves multi-tool task completion. This is not a trivial extension — agent trajectories have a fundamentally different structure (planning→grounding→execution with tool feedback loops) that requires new formulations of tractable control, new reward designs, and new seed data synthesis."

**Related work positioning**:
- Ctrl-R: Our foundation for trajectory control, but limited to monolithic text reasoning
- Lumos: Our foundation for modular agent training, but limited to SFT without RL-based pattern control
- Magnet: Our inspiration for seed data, but limited to static data synthesis without RL exploration
- DAC-RL: Complementary — DAC controls *decomposition structure*, we control *reasoning patterns*; could be combined
- OpenThoughts: Complementary — their data recipes inform our seed trajectory design

---

## 5. Suggested Next Steps

1. **Proof-of-concept**: Implement a simplified version with 2-3 reasoning patterns (backtracking + counterfactual) on a single benchmark (e.g., ToolBench)
2. **Seed data**: Use Magnet-style graph translation to synthesize 1K structured trajectories per pattern
3. **Baseline comparison**: Compare against (a) Lumos-style SFT, (b) standard GRPO without trajectory control, (c) Ctrl-R applied to monolithic agent prompts
4. **Full pipeline**: Integrate Controller-Worker architecture with Agentic GRPO

---

*Proposed by: Jingyu Xu*
*Date: 2026-06-30*
*Based on: Ctrl-R (NeurIPS 2026 Spotlight), Lumos (ACL 2024), Magnet (ACL 2025), DAC-RL (ACL 2026), OpenThoughts (ICLR 2026)*
