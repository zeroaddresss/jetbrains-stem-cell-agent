# Evolving a Stem Agent into a Python Bug-Fix Specialist

## The Goal: Specialization, Not Generalization

When I read the prompt for this challenge, the core constraint immediately stood out: *"The end result isn't a universal agent. It's an agent that became specific — through its own process."* 

This fundamentally changes how you design an agent. Instead of building a massive, complex architecture with dozens of tools, self-reflection loops, and broad planning capabilities, the architecture needs to be minimal. The "intelligence" shouldn't be hardcoded into the agent's prompts or architecture; it should emerge from the agent exploring a search space and discovering what works best for a specific domain.

I chose **repository-level Python bug fixing** as my task domain. I picked this because it provides concrete pass/fail outcomes via hidden unit tests, it offers a bounded but realistic level of complexity, and the failure modes (e.g., syntax errors, timeout loops, logic edge cases) are highly analyzable. 

My hypothesis was straightforward: If I freeze the underlying LLM, freeze the benchmark, and freeze the evaluation harness, can a simple hill-climbing search over "policy knobs" (like how many files to read, whether to read tests first, how to format prompts) yield a measurable improvement on held-out tasks?

## The Architecture: Keeping the Stem "Dumb"

I intentionally kept the Stem Agent loop small and linear:
1. Read the issue text.
2. Rank and inspect a bounded set of files (based on simple token overlap heuristics).
3. Ask the model for a JSON patch proposal.
4. Apply the edits.
5. Run tests (visible ones optionally before the patch, hidden ones for scoring).

To ensure that any improvement was genuinely due to specialization, I strictly separated the *fixed* components from the *evolvable* components. The model provider, the scoring logic, and the benchmark splits were locked. 

The evolvable policy was defined as a set of discrete parameters:
- `prompt_style`: ("concise_debug" vs. "surgical_bugfix")
- `inspect_order`: ("tests_first" vs. "source_first")
- `max_files_to_read`: (1 to 4)
- `patch_size_soft_limit`: (20 to 40 lines)
- `run_visible_tests_before_patch`: (True or False)
- `temperature`: (0.0 or 0.2)

For the evolution process itself, I implemented a simple hill-climbing neighborhood search. It takes a seed policy, generates 1-off mutations (neighbors), evaluates them on the train and validation splits, and adopts the neighbor if the validation score improves. 

## The Benchmark: Freezing the Evaluation

I built a custom benchmark of 18 small Python bug-fix tasks. I needed full control over the evaluation, so each task includes a tiny repository, an `issue.md`, visible tests (that the agent can optionally run), and hidden acceptance tests (used strictly for scoring).

I froze the splits early on to prevent data leakage:
- **Train (9 tasks):** Used by the evolution loop to evaluate candidates.
- **Validation (3 tasks):** Used to decide whether to accept a mutated policy.
- **Test (6 tasks):** Strictly held out until the final evaluation.

## Execution and the Gated Protocol

Running LLM evaluations over dozens of generations is expensive and time-consuming. To manage this, I used a gated protocol:
1. **Smoke run:** A tiny subset of tasks using a deterministic heuristic backend to ensure the pipeline works.
2. **Pilot (G1):** A single generation of evolution across the full benchmark using `deepseek/deepseek-v4-pro` via OpenRouter.
3. **Main (G2):** A deeper run (2 generations) *only* if G1 showed positive signal.

This wasn't just to save API credits; it forced me to be disciplined about checking signals before committing to deep searches.

## Outcomes: The Numbers

The results from the Pilot (G1) run strongly validated the hypothesis:

| Split | Baseline Solved | Evolved Solved | Delta |
| :--- | :---: | :---: | :---: |
| Train | 0/9 | 9/9 | +9 |
| Val | 0/3 | 3/3 | +3 |
| Test | 0/6 | 6/6 | +6 |

By simply mutating its policy parameters, the agent went from solving zero tasks on the held-out test set to solving all 6.

However, the deeper search run (G2) provided a crucial counterpoint. The G2 evolved policy scored 5/6 on the test set. It performed significantly better than the baseline, but slightly worse than the G1 policy. This highlighted a classic machine learning reality: deeper search over a small validation set can lead to overfitting, even in agentic workflows.

To maintain intellectual honesty, I report G1 as the primary result and G2 as an ablation on search depth, demonstrating that more search is not automatically better.

## Surprises, Failures, and Lessons Learned

Building this taught me several hard lessons about agent infrastructure:

### 1. "More Search" ≠ "Better Generalization"
The most surprising finding was the G2 underperformance. I assumed giving the hill-climber more generations to find an optimal policy would yield a more robust agent. Instead, it likely over-optimized for the specific quirks of the 3-task validation set. **Lesson:** The principles of overfitting apply to agent policy search just as they do to traditional model training.

### 2. Timeout Handling is crucial
During an early run, a generated patch introduced an infinite loop. The visible test execution hung, and eventually, the entire evaluation script crashed at the shell level. I lost hours of API calls. 

I had to rewrite `runner.py` to capture `subprocess.TimeoutExpired` and convert it into a controlled task-level failure (mapping it to `returncode=124`). **Lesson:** When evaluating generated code, you must assume the code is actively malicious to your evaluation loop. Reliability is as important as model quality.

### 3. JSON Parsing Must Be Paranoid
Early on, my prompt example used single-quoted pseudo-JSON (e.g., `{'diagnosis': '...'}`). Some models replicated this exactly, causing standard `json.loads` to fail. 

I updated the prompt to strict double quotes, but I also had to implement a multi-stage parsing strategy in `backends.py`: try direct parsing, then look for markdown fences, then try to extract the first valid JSON object via regex. **Lesson:** You cannot trust the LLM to format its output correctly, no matter how explicit the system prompt is. Defensive parsing is mandatory.


## If I Had More Time...

If I were to continue building out this project, I would focus on three areas:

1. **Expanding the Search Space:** I'd add architectural toggles to the policy. For instance, allowing the policy to choose between a single-shot prompt, a chain-of-thought prompt, or a multi-turn ReAct loop.
2. **Confidence Intervals:** Running the full G1/G2 protocol across 5-10 different random seeds to establish variance and confidence intervals, rather than relying on point estimates.
3. **Task Diversity:** Expanding the benchmark from 18 tasks to 100+ tasks spanning multiple languages and frameworks to see how policies specialize differently across domains (e.g., a "React bug-fix policy" vs. a "Python backend policy").

Ultimately, this project demonstrated that you don't necessarily need a complex agent architecture to solve specific problems. A minimal, dumb "stem" that is capable of exploring a constrained policy space and measuring its own success can reliably specialize itself into a highly effective tool.
