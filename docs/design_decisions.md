# Design Decisions Document: Self-Evaluating Lesson Content Generator

## 1. Technology Stack Selection

### Why Python 3.13?
Python is the industry standard for GenAI engineering and agentic systems. It provides first-class support for LLM SDKs, data validation, relational databases, and testing frameworks.

### Why Pydantic v2?
Pydantic enforces strict type safety and schema validation. The evaluator output is parsed directly into Pydantic models (`EvaluationReport`, `CheckpointResult`). If a model produces malformed or missing JSON keys, Pydantic immediately rejects the output rather than allowing silent data corruption.

### Why SQLite + JSON for Memory?
- **SQLite (`data/history.db`):** Relational, zero-configuration local database that survives application restarts. It allows structured querying of run trajectories, versions, and checkpoint scores across thousands of runs without requiring external server infrastructure.
- **JSON (`data/memory.json`):** Simple, human-readable, and git-inspectable format for evolving failure patterns and learning insights. This makes it trivial for human reviewers to inspect what the system has learned.

### Why Dual-Mode Execution (LLM API + Deterministic Engine)?
Production AI systems must be robust against external outages, rate limits, and network issues. The system supports live model APIs (`gpt-4o-mini`, custom endpoints via `OPENAI_BASE_URL`) while including a deterministic internal pedagogical engine. Automated test suites execute offline deterministically, while live demos can call real LLM APIs.

---

## 2. Rubric Design & Hard Approval Rules

### 6 Dimensions, 12 Binary Checkpoints
Rather than asking a model "Is this lesson good?", the rubric defines 12 specific, verifiable checkpoints across 6 dimensions:
1. **Accuracy & Grounding:** Verified against `data/references.md`. Explicitly prohibits common myths (e.g., claiming RAG retrains model weights at query time).
2. **Beginner-Friendly Language:** Restricts vocabulary to high school English and flags run-on sentences (>32 words).
3. **Teaching Through Examples:** Demands a relatable analogy (Open-Book Exam) and requires explicit mapping between analogy parts and system components.
4. **No Unexplained Jargon:** Enforces that technical terms (LLM, Chunking, Embedding, Vector DB) are defined immediately when introduced.
5. **Coverage:** Checks that all 6 stages of the RAG pipeline are explained.
6. **Coherent Flow:** Verifies standalone completeness and logical flow.

### Why Zero Partial Credit?
In educational content, a lesson that is 90% accurate but contains one critical hallucination can severely mislead a beginner. Therefore, if even 1 mandatory checkpoint fails, the lesson is rejected and must be regenerated.

---

## 3. Separation of Generation and Evaluation

In naive LLM workflows, the same prompt often asks the model to "Write a lesson and review it." This suffers from severe confirmation bias: LLMs tend to validate their own reasoning.

By isolating the **LessonGenerator** and **RubricEvaluator** into distinct modules with separate system instructions:
- The Generator focuses purely on pedagogy, tone, and clarity.
- The Evaluator acts as a strict auditor armed with the ground truth facts (`data/references.md`) and the rubric schema.

---

## 4. Controlled Self-Evolution & Memory

The system learns from its own history without modifying its own code or lowering its evaluation standards:
1. **Bounded Adaptation:** The evaluation rubric is immutable. The system cannot lower the bar to artificially achieve a pass.
2. **Feedback Memory:** When a run fails, the failed checkpoints and reasons are recorded in `data/memory.json`.
3. **Prompt Injection:** Future generation runs retrieve these historical failure patterns (e.g. "Avoid unexplained jargon in Section 2; explicitly map the open-book exam analogy") and prepend them as guidelines to prevent repeating the same mistakes.

---

## 5. What the System Cannot Guarantee (Honest Limitations)

1. **LLM Evaluator Nuance:** When running in live LLM mode, LLM evaluators can occasionally misinterpret subtle nuances or show slight prompt sensitivity. While structured schema enforcement and temperature=0 minimize this, LLM-as-a-judge is not a 100% formal mathematical verifier.
2. **Infinite Knowledge Coverage:** Grounding is strictly bounded by `data/references.md`. If a question or topic is outside this reference, the system relies on general principles.
3. **Subjective Learner Perception:** While readability scores and sentence-length heuristics ensure simplicity, individual human learners with different linguistic backgrounds may still find certain analogies more intuitive than others.
