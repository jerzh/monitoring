# Approaches to building monitors for AI agents

Literature notes, compiled 2026-10-05. "Monitor" here means a system that reads an agent's transcript (actions, outputs, and sometimes its reasoning or activations) and flags misbehavior such as reward hacking, sandbagging, sabotage or harmful actions. Numbers are quoted from the sources linked below. Some come from abstracts or blog summaries rather than full papers; these are marked *(abstract)*.

## TL;DR

- **METR has not published trained monitors.** Every METR monitor so far is a **prompted frontier LLM** (GPT-5, o4-mini, Claude models, and more recently Opus 4.8 / GPT-5.5) that outputs a 0–10 suspicion score, with a threshold calibrated to a target false-positive rate. MALT is the dataset they built to validate those monitors.
- **The field has mostly prompted LLM judges.** Most of the recent work is about *scaffolding* (what the monitor sees and how its scores are combined), not training. Trained approaches exist in three forms: fine-tuned LLM/encoder classifiers, activation probes, and RL-trained detectors.
- **Recurring findings:**
  1. Reasoning (CoT) access helps a lot for some behaviors (sandbagging, covert side tasks) and little for others (reward hacking on MALT).
  2. Hybrid or filtered scaffolds beat naively handing the monitor everything.
  3. Monitors trained or validated on *prompted* misbehavior may not transfer to *natural* misbehavior.
  4. Monitors are vulnerable to prompt injection, and optimizing against a CoT monitor teaches models to obfuscate.

## How METR's monitors work

### MALT (Oct 2025): the validation set
[METR blog](https://metr.org/blog/2025-10-14-malt-dataset-of-natural-and-prompted-behaviors/)

- **Monitor type:** prompted, not fine-tuned. Monitors tested were from OpenAI (GPT-5, o4-mini) and Anthropic (Claude models). GPT-5 was best.
- **Scaffold:** the transcript is split into chunks, and the **first five messages are repeated at the start of every chunk** for context. Each chunk gets a JSON response with a 0–10 score and reasoning. There are separate prompts for reward hacking and for sandbagging.
- **Results:**
  - Best AUROC is **0.96 for reward hacking** and **0.91 for sandbagging**.
  - At **5% FPR** the best monitors catch **80–90%** of true positives when they see reasoning traces.
  - Reasoning access matters for sandbagging but makes little difference for reward hacking.
- **Label grouping used in the evaluation:**
  - *Reward hacking:* `bypass_constraints`, `ignores_task_instructions` ("models explicitly violated task instructions").
  - *Sandbagging:* `gives_up` (unprompted), plus the prompted `match_weaker_model`, `refusals`, `sabotage`, `partial_problem_solving` and `reasoning_about_task`.
  - *Miscellaneous:* `hardcoded_solution`, brute-forced solutions, evaluation awareness.
- **How the labels were made:**
  - 2,690 runs were manually reviewed by contractors and METR staff.
  - Natural reward hacks were found through anomalous scores, keyword searches and manual review.
  - Prompted sandbagging runs come from Claude 3.7 Sonnet. An LLM then **edited the reasoning traces to remove mentions of the instruction** (for example, "I'm supposed to sabotage" became "I want to sabotage") so the monitor can't just spot the prompt.
- **Stated limitations:** few natural positives, limited diversity, and prompted examples that may lack realism.

### SHUSHCAST (Jan 2026): monitors vs. agents doing covert side tasks
[METR blog](https://metr.org/blog/2026-01-19-early-work-on-monitorability-evaluations/)

- **Setup:** 6 HCAST main tasks and 9 side tasks. The monitor sees the main task, a monitoring instruction and the transcript, but not the side-task prompt. It outputs a probability, with the threshold set for **5% FPR on innocent runs**.
- **Monitors tested:** GPT-3.5 Turbo, GPT-4 Turbo, GPT-4o, Claude 3.5 Sonnet, Claude Sonnet 4.5, DeepSeek V3/R1, and GPT-5 (medium and high). All were prompted, and GPT-5 was the strongest.
- **Results:**
  - Against a GPT-5-high agent, the average catch rate is **52% without reasoning and 80% with reasoning**. For a Claude Sonnet 4.5 agent, reasoning access mattered less, possibly because its traces are summarized.
  - Models with longer time horizons are better both as monitors and as evaders. The agent/monitor time-horizon ratio tracks how often evasion succeeds.

### Early results on monitorability in QA settings (Oct 2025)
[METR note](https://metr.org/notes/2025-10-06-early-results-on-monitorability-in-qa-settings/)

- **Setup:** GPQA main tasks paired with covert math side tasks. GPT-4o, GPT-4o-mini and Claude 4 Sonnet act as monitors.
- **Results:**
  - Monitors were fooled about **46.5%** of the time with GPT-4o-mini and **22–24%** with the larger monitors.
  - Easier side tasks are easier to hide.
  - An RL-trained Qwen3-8B learned to fool stronger monitors.

### Per-action blocking monitor for evals (Sep 2026)
[METR note](https://metr.org/notes/2026-09-27-implementing-a-basic-blocking-action-monitor/)

- **What it is:** a live **blocking** monitor built as an Inspect approver. An LLM judge (**Opus 4.8 or GPT-5.5**, prompted) scores each action before it runs. Anything at or above **3/10** pauses the eval for human review.
- **What it looks for:** a roughly 40-sentence prompt targets three things: harm to real parties outside the eval, irreversible out-of-scope harm such as credential exfiltration or persistence, and attempts to disable the monitor.
- **Results:**
  - All 10 malicious transcripts from a UK AISI incident were flagged at **≥8/10**.
  - The false-positive rate is about **0.015% per action** and **0.8% per transcript** on 758k live actions.
  - The cost is roughly **+46% (mean)** per transcript, and latency about **+30% (mean)**.
- **Weaknesses:**
  - A spoofed user message lowered the average suspicion score from **8.1 to 3.7**, letting **12/30** runs through.
  - Very few malicious training examples exist, which is one reason it isn't trained.

### What METR says about industry monitors
[Frontier Risk Report, Feb–Mar 2026](https://metr.org/blog/2026-05-19-frontier-risk-report/)

- OpenAI and Anthropic run automated monitors over agent traffic. OpenAI's are described as prompted LLMs reviewing transcripts. No training details are given.
- METR's red-teamer found that monitors could be reliably jailbroken with very basic techniques.

## The wider landscape

### 1. Prompted LLM judges: the default
- **Trusted monitoring (AI control).** A weaker, trusted model scores the outputs of a stronger, untrusted model. Suspicious outputs are audited or replaced by the trusted model's output ("defer to trusted"). The framework is from [Greenblatt et al. 2023, *AI Control*](https://arxiv.org/abs/2312.06942).
- **CoT monitoring.** [Baker et al. 2025 (OpenAI)](https://arxiv.org/abs/2503.11926) found that GPT-4o reading o3-mini's chain of thought catches reward hacking in agentic coding much better than monitoring actions alone. A weaker model can monitor a stronger one. However, **putting CoT-monitor pressure into the RL reward teaches obfuscated reward hacking**, hence the proposed "monitorability tax" of not optimizing the CoT. [Korbak et al. 2025](https://arxiv.org/abs/2507.11473) argue that CoT monitorability is a "new and fragile" opportunity.
- **SHADE-Arena** ([Kutasov et al. 2025, Anthropic](https://arxiv.org/abs/2506.15740)) pairs main tasks with sabotage side tasks across diverse tool-use environments. The best monitor, **Gemini 2.5 Pro, reaches AUC 0.87**, which the authors note would still mean prohibitive false positives at scale.

### 2. Monitor scaffolding: what to show and how to combine
- **Hybrid CoT + action scoring.** [CoT Red-Handed (Arnav et al. 2025)](https://arxiv.org/abs/2505.23575) found that a CoT monitor can be misled by plausible-sounding rationalizations. A **weighted average of separate action-only and CoT scores** beat either alone, with catch rates over 4× those of action-only monitoring on subtle sabotage.
- **Monitor red-teaming and scaffold choice.** [Kale et al. 2025 (Scale), *Reliable Weak-to-Strong Monitoring*](https://scale.com/research/mrt) found that scaffolding matters more than how much the monitor knows. **Hybrid hierarchical-plus-sequential scaffolds** let weaker monitors reliably oversee stronger agents on SHADE-Arena and CUA-SHADE-Arena. The agent knowing it's monitored mattered more than the monitor knowing the task.
- **Less is more.** [Arike et al. 2026](https://arxiv.org/abs/2601.21112) found that monitors often do better with *filtered* information. **Extract-and-Evaluate** has one model pull out relevant excerpts and another score them. It gave +16.8 points of sabotage detection on BigCodeBench-Sabotage with GPT-4.1-mini *(abstract)*.
- **Chunking with repeated context** is METR's approach on MALT (see above). It handles long transcripts without truncation.

### 3. Trained monitors
- **Fine-tuned LLM monitors.** SHADE-Arena reports that **fine-tuning GPT-4o on human-written monitoring responses** clearly improves performance on held-out tasks *(abstract)*.
- **Trained classifiers on synthetic data.** [Constitutional Classifiers (Sharma et al. 2025, Anthropic)](https://arxiv.org/abs/2501.18837) train input and output classifiers on synthetic data generated from a natural-language "constitution". This is the main deployed example of a *trained* monitor, though it targets misuse/jailbreaks rather than agent misbehavior.
- **Data provenance matters.** [Li et al. 2026, *Trace-and-Amplify*](https://arxiv.org/abs/2604.23488) found that monitors (including fine-tuned encoders such as ModernBERT) **trained on prompt-elicited hacking trajectories often fail to generalize to naturally occurring training-time hacks**. Monitors trained on traced natural hacks generalize better to unseen hack types *(abstract)*. This is directly relevant to MALT's prompted vs. unprompted split.
- **RL-trained detectors.** [Guo et al. 2026, *Just Ask Jev*](https://arxiv.org/abs/2609.29429) train a detector with RL to give calibrated probabilities across many failure types, including reward hacking and deception. It reports a median zero-shot AUROC of 0.886 at roughly 63× lower cost than LLM-judge scorers *(abstract)*. [Agent-ToM (Ahmed & Nafisi 2026)](https://arxiv.org/abs/2605.24216) learns a reusable "guardrail memory" from critiques and evaluates on SHADE-Arena and CUA-SHADE-Arena *(abstract; few training details)*.

### 4. White-box monitors: activation probes
- **Linear probes for deception.** [Goldowsky-Dill et al. 2025 (Apollo)](https://arxiv.org/abs/2502.03407) train probes on Llama-3.3-70B activations and reach **AUROC 0.96–0.999** across deception datasets, including sandbagging. At **1% FPR** on ordinary chat they catch 95–99% of deceptive responses. Anthropic's earlier ["Simple probes can catch sleeper agents" (2024)](https://www.anthropic.com/research/probes-catch-sleeper-agents) is the precursor.
- **Activation monitors for reward hacking.** [arXiv 2603.04069](https://arxiv.org/abs/2603.04069) trains SAEs on residual-stream activations with linear classifiers for token-level reward-hacking scores. It reports that signals appear early in reasoning and generalize to unseen scenarios *(abstract)*.
- **Limitation:** these need weight access. That rules them out for closed frontier agents, and for MALT, which contains only text.

### 5. Attacks on monitors
- [Adaptive Attacks on Trusted Monitors (2025)](https://arxiv.org/abs/2510.09462): prompt injections placed in agent outputs consistently get past monitors on control benchmarks. The defer-to-resample protocol makes this worse by effectively turning it into a best-of-n attack.
- METR's own spoofed-user-message result and red-teaming findings point the same way (see above).
- [Baker et al. 2025](https://arxiv.org/abs/2503.11926) shows the training-time version: optimizing against a CoT monitor leads to obfuscated reasoning.

## Implications for working with MALT

- **The baseline to beat is a prompted GPT-5 on chunked transcripts.** It reaches AUROC 0.96 for reward hacking and 0.91 for sandbagging, or 80–90% TPR at 5% FPR. Report the same metrics (AUROC and TPR at a fixed FPR) to compare.
- **Labels are per run, not per turn.** Any turn-level detector needs its own localization, or a way to aggregate scores (max or mean over chunks, as METR does).
- **Prompted vs. natural.** Most sandbagging positives in MALT are prompted (from Claude 3.7 Sonnet, with edited reasoning traces). Trace-and-Amplify suggests training on these may not transfer to natural cases. The unprompted positives are the realistic test set. METR's figures of 103 reward-hacking runs and 32 `gives_up` runs cover the full MALT, including its private split. The public split has fewer; for example, 23 `bypass_constraints` and 28 `ignores_task_instructions` runs.
- **Confounds a monitor could exploit:**
  - Most unprompted Claude 3.7 and 4 runs have the "made by OpenAI" system prompt.
  - Prompted runs come from a single model.
  - Labels cluster by file and model.
  
  A trained monitor could pick these up instead of the behavior itself. Split by model or task family to check.
- **No activations.** MALT is text-only, so probe-based approaches would need re-running the agents on an open-weight model.
