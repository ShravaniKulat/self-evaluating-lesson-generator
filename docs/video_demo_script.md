# Practical Video Walkthrough Script: Self-Evaluating Lesson Content Generator

**Format:** 15–20 Minute Face-Visible Video Demonstration  
**Presenter:** GenAI Engineer / Agentic Systems Developer  
**Topic:** Introduction to RAG (Retrieval-Augmented Generation)

---

## Script Overview & Timing Breakdown

| Section | Topic | Target Duration |
| :--- | :--- | :--- |
| **Section 1** | Welcome, Role, & Assessment Objective | 0:00 – 2:30 |
| **Section 2** | Architecture Walkthrough & Component Responsibilities | 2:30 – 5:30 |
| **Section 3** | End-to-End Pipeline Demo (Successful First-Pass Run) | 5:30 – 8:30 |
| **Section 4** | Controlled Error Catching & Autonomous Regeneration | 8:30 – 12:00 |
| **Section 5** | Persistent Memory, SQLite Inspection, & Learned Insights | 12:00 – 14:30 |
| **Section 6** | Automated Test Suite Verification (Tests A to G) | 14:30 – 17:00 |
| **Section 7** | Engineering Trade-offs, Honest Limitations, & Wrap-Up | 17:00 – 19:30 |

---

## Detailed Step-by-Step Script

### Section 1: Welcome, Role, & Objective (0:00 – 2:30)
*Action: Face on camera, clear audio, screen showing GitHub repo root.*

> **Speaker:**  
> "Hello! My name is [Your Name], and today I am walking you through my submission for the GenAI Engineer – Content Systems Take-Home Assessment: the **Self-Evaluating Lesson Content Generator**.
>
> The primary objective of this project is not to build a simple one-shot text generation prompt. Rather, it is to demonstrate a production-grade, autonomous quality-control loop: an agentic system that generates educational lessons for beginners, strictly audits the content against a rigorous 12-checkpoint pass/fail rubric, regenerates flawed drafts using targeted feedback, and ships the lesson only when every single check passes.
>
> Our target learner is an Indian high school graduate (Class 12) with basic English vocabulary and zero background in AI. Our topic for today's lesson is **'Introduction to RAG (Retrieval-Augmented Generation)'**."

---

### Section 2: Architecture & Components (2:30 – 5:30)
*Action: Switch screen share to `docs/architecture.md` diagram and code structure.*

> **Speaker:**  
> "Let's examine the architectural pipeline. We deliberately separated responsibilities into modular Python components:
> 
> 1. **Input Handler (`config.py`):** Configures target audience constraints and model credentials.
> 2. **Lesson Generator (`generator.py`):** Generates lessons grounded in authoritative facts from `data/references.md`, guided by generation prompts and prior memory.
> 3. **Rubric Evaluator (`evaluator.py`, `rubric.py`):** An independent evaluation gate assessing 6 dimensions: Accuracy, Beginner-Friendly Language, Teaching Through Examples, Jargon Definition, Coverage, and Coherent Flow.
> 4. **Feedback Builder (`feedback.py`):** Extracts failed checkpoints into actionable repair instructions and tracks line diffs.
> 5. **Workflow Orchestrator (`orchestrator.py`):** Enforces our hard approval gate and strict retry limit—maximum 2 retries (3 versions total: V1, V2, V3).
> 6. **Memory Manager (`memory.py`):** A dual-tier persistent storage system combining SQLite (`history.db`) for run trajectories and JSON (`memory.json`) for reusable failure patterns."

---

### Section 3: Live End-to-End Pipeline Execution (5:30 – 8:30)
*Action: Open terminal and execute the main pipeline command.*

```bash
python app/main.py --topic "Introduction to RAG (Retrieval-Augmented Generation)"
```

> **Speaker:**  
> "Now let's run the main pipeline. Watch the terminal as our Orchestrator initializes:
> 
> - **Step 1:** The Memory Manager loads prior failure patterns.
> - **Step 2:** The Generator drafts Version 1.
> - **Step 3:** The Rubric Evaluator audits all 12 checkpoints. Notice the Rich table on screen: every checkpoint reports an explicit `PASS`, backed by verbatim evidence from the lesson.
> - **Final Decision:** Because all 12 checkpoints pass with zero failures, the system issues an `APPROVED` decision.
> 
> The lesson is automatically shipped to `docs/final_lesson.md`, and the full JSON run report is saved to `outputs/`."

---

### Section 4: Controlled Error Demonstration & Autonomous Retry (8:30 – 12:00)
*Action: Run the deliberate error demonstration command.*

```bash
python app/main.py --topic "Introduction to RAG (Retrieval-Augmented Generation)" --demo-error fact_error
```

> **Speaker:**  
> "Now let's test our quality-control loop by deliberately injecting a factual misconception: claiming that RAG dynamically retrains model weights at query time.
> 
> Notice what happens:
> 1. In Version 1, the Evaluator catches this violation and immediately fails **`CHK_ACC_01: Grounded Definition of RAG`**.
> 2. Because of our hard approval rule, the lesson is **not approved**.
> 3. The Orchestrator intercepts the failure, compiles actionable feedback via the `FeedbackBuilder`, and triggers **Regeneration Attempt 1**.
> 4. The Generator produces Version 2, fixing the retraining misconception.
> 5. The Evaluator re-audits Version 2 from scratch. All 12 checkpoints now pass!
> 6. The terminal displays `DECISION: APPROVED` with `Total Retries: 1`."

---

### Section 5: Persistent Memory & Audit Logs (12:00 – 14:30)
*Action: Run the inspection commands.*

```bash
python app/main.py --list-runs
python app/main.py --inspect-memory
```

> **Speaker:**  
> "Let's inspect our persistent memory. Notice how our runs are permanently recorded in SQLite. When we run `--list-runs`, we see our runs with their status, version count, and retries.
> 
> When we run `--inspect-memory`, we see our persistent JSON store: it captures repeated failure patterns and records recent run insights. This ensures the system learns from its own history across application restarts."

---

### Section 6: Automated Test Suite Verification (14:30 – 17:00)
*Action: Run pytest across the complete test suite.*

```bash
python -m pytest -v
```

> **Speaker:**  
> "Let's verify the entire test suite. All 13 tests execute in under 1 second using deterministic fixtures:
> - **Test A:** Successful first-pass approval (0 retries).
> - **Test B:** Successful regeneration after initial failure.
> - **Test C:** Repeated failure terminating cleanly at 2 retries with `REJECTED`.
> - **Test D:** Strict prevention of false approvals when even one checkpoint fails.
> - **Test E:** Persistent memory survival across application reinitialization.
> - **Test F:** Deliberate factual error catching.
> - **Test G:** Rejection of malformed or incomplete evaluator JSON."

---

### Section 7: Engineering Trade-offs, Limitations, & Wrap-Up (17:00 – 19:30)
*Action: Presenter face on camera with summary slide.*

> **Speaker:**  
> "To conclude, let's discuss engineering trade-offs and honest limitations:
> 
> 1. **Evaluator Reliability:** LLMs as judges can exhibit prompt sensitivity. We mitigate this using strict JSON schema validation, temperature 0, and cross-validation against programmatic ground truth.
> 2. **Retry Ceiling:** We bounded retries to 2 attempts (3 versions max) to eliminate runaway execution costs.
> 3. **Controlled Evolution:** We intentionally forbid the system from rewriting its own evaluation rubric, ensuring quality standards never degrade.
> 
> Thank you for watching!"
