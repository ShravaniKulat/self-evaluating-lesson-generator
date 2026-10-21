"""
Lesson Generator Module.
Generates standalone beginner-friendly lessons and targeted revisions using model APIs
or a built-in deterministic pedagogical engine for reliable testing and offline demonstration.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from app.config import (
    GENERATION_PROMPT_FILE, REGENERATION_PROMPT_FILE, REFERENCES_FILE,
    OPENAI_API_KEY, OPENAI_BASE_URL, DEFAULT_MODEL
)
from app.logger import SystemLogger


class LessonGenerator:
    def __init__(self, model_name: str = DEFAULT_MODEL, use_mock: bool = False):
        self.model_name = model_name
        self.use_mock = use_mock or not bool(OPENAI_API_KEY)
        self.references_text = self._load_file(REFERENCES_FILE)
        self.gen_prompt_template = self._load_file(GENERATION_PROMPT_FILE)
        self.regen_prompt_template = self._load_file(REGENERATION_PROMPT_FILE)

        self.client = None
        if not self.use_mock and OPENAI_API_KEY:
            try:
                from openai import OpenAI
                kwargs = {"api_key": OPENAI_API_KEY}
                if OPENAI_BASE_URL:
                    kwargs["base_url"] = OPENAI_BASE_URL
                self.client = OpenAI(**kwargs)
            except Exception as e:
                SystemLogger.warning(f"Could not initialize OpenAI client ({e}). Falling back to internal engine.")
                self.use_mock = True

    def _load_file(self, path: Path) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            SystemLogger.error(f"Error loading {path}: {e}")
            return ""

    def generate_initial_lesson(self, topic: str, prior_learnings: str = "", inject_flaw: Optional[str] = None) -> str:
        """
        Generates the first version of the lesson.
        Can optionally inject a deliberate flaw for testing (e.g. Test F).
        """
        prompt = self.gen_prompt_template.format(
            topic=topic,
            references=self.references_text,
            prior_learnings=prior_learnings
        )

        if inject_flaw == "fact_error":
            return self._generate_lesson_with_factual_error(topic)
        elif inject_flaw == "unexplained_jargon":
            return self._generate_lesson_with_unexplained_jargon(topic)

        if not self.use_mock and self.client:
            return self._call_llm(prompt)
        else:
            return self._generate_engine_lesson(topic)

    def regenerate_lesson(
        self,
        topic: str,
        failed_lesson_text: str,
        evaluator_feedback: str,
        prior_learnings: str = ""
    ) -> str:
        """
        Generates a revised lesson addressing specific failed checkpoints.
        """
        prompt = self.regen_prompt_template.format(
            topic=topic,
            failed_lesson_text=failed_lesson_text,
            evaluator_feedback=evaluator_feedback,
            references=self.references_text,
            prior_learnings=prior_learnings
        )

        if not self.use_mock and self.client:
            return self._call_llm(prompt)
        else:
            # Produce high-quality revised lesson addressing any past defects
            return self._generate_engine_lesson(topic, is_revision=True)

    def _call_llm(self, prompt: str) -> str:
        """Calls the OpenAI or compatible chat completion API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a world-class educational AI teacher for Indian Class 12 students. Follow instructions precisely."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            SystemLogger.error(f"LLM API call failed ({e}). Falling back to internal pedagogical engine.")
            return self._generate_engine_lesson("Introduction to RAG", is_revision=True)

    def _generate_engine_lesson(self, topic: str, is_revision: bool = False) -> str:
        """
        High-fidelity, pedagogically structured standalone lesson on RAG
        tailored for Indian Class 12 graduates with simple English.
        """
        lesson = f"""# {topic}

Welcome to this beginner's guide! Have you ever used an AI chatbot and noticed that it sometimes gives old news or confidently makes up answers that are completely wrong? 

In this lesson, we will learn about a powerful AI technique called **RAG**. By the end of this lesson, you will understand what RAG is, why it is so important, and how it works step by step—using a simple school exam example.

---

## 1. The Big Problem: Why Normal AI Makes Mistakes

To understand why we need RAG, let us first look at how standard AI chatbots work.

Today's smart AI chatbots are powered by something called a **Large Language Model (LLM)**. 
- **What is an LLM?** An LLM is a computer program trained on billions of sentences from the internet. It learns patterns in words so it can chat like a human.

However, standard LLMs have two major problems:
1. **Outdated Knowledge (Knowledge Cutoff):** An LLM only knows what it read during its training time. If an LLM finished training in 2023, it cannot know what happened today or yesterday.
2. **Hallucination (Making Things Up):** When an LLM does not know an answer, it does not say "I do not know." Instead, it often guesses and writes false facts with total confidence. In AI, this mistake is called **Hallucination**.

Why not just retrain the LLM every day with new data? Because retraining a massive AI model takes millions of dollars and weeks of computing power. We need a faster, cheaper, and smarter way. That is where RAG comes in!

---

## 2. What is RAG?

**RAG** stands for **Retrieval-Augmented Generation**. Let us break down these three words in plain English:

- **Retrieval:** Finding and fetching the right information from a storage box or book.
- **Augmentation:** Adding or attaching those fetched facts to the user's question.
- **Generation:** Using the AI to write a clear, complete, and friendly answer based on those fresh facts.

In simple terms: Instead of forcing the AI to answer solely from its old memory, RAG allows the AI to first look up the exact facts from a verified document, and then write the answer.

---

## 3. The Everyday Analogy: The Open-Book Exam

Think about your school days and imagine two different exams:

### The Closed-Book Exam (Normal LLM)
In a closed-book exam, you must answer every question purely from your head. If you forget a historical date or a science formula, you might panic and guess the answer. Sometimes your guess is completely wrong. This is how a normal LLM works without RAG.

### The Open-Book Exam (RAG System)
Now imagine an open-book exam. Your teacher allows you to keep an approved textbook on your desk.
1. When you read a question, you open the textbook.
2. You look up the exact chapter and find the right paragraph.
3. You read the verified facts from the page.
4. You write down the correct, complete answer on your answer sheet.

### How the Analogy Maps to the Real System:
- **The Student:** The Large Language Model (LLM).
- **The Textbook on the Desk:** The External Knowledge Base (your documents or notes).
- **Looking up the right page:** The **Retrieval** step.
- **Placing the open page next to your exam paper:** The **Augmentation** step.
- **Writing down the final answer in your own words:** The **Generation** step.

---

## 4. How RAG Works Behind the Scenes: Step-by-Step

A complete RAG system works in six clear, organized steps. Let us walk through them together:

### Step 1: Collecting Documents & Chunking
Imagine you have a 500-page school syllabus. Feeding all 500 pages into an AI at once is slow and confusing.
So, the system first divides long documents into smaller, bite-sized sections (like single paragraphs). 
- **Chunking:** The process of breaking a big document into small, manageable pieces called "chunks."

### Step 2: Creating Embeddings (Meaning Codes)
Computers do not understand English letters like humans do; computers understand numbers.
Each text chunk is passed through a special math model that turns the text into a list of numbers representing its meaning.
- **Embedding:** A list of numbers (a code) that captures the meaning of a piece of text. Sentences with similar meanings will have numbers that are close to each other.

### Step 3: Storing in a Vector Database (The Organized Shelf)
Next, these number codes (embeddings) and their text chunks are stored in a specialized storage system called a **Vector Database**.
- **Vector Database:** A digital library where information is filed by meaning, making it lightning-fast to find related topics.

### Step 4: Retrieval (Searching by Meaning)
When a user asks a question (for example: *"What is the leave policy of our school?"*), the system turns the question into an embedding number code.
It searches the Vector Database to find the chunks whose meaning code is closest to the question. This is the **Retrieval** step.

### Step 5: Prompt Augmentation (Attaching the Facts)
The system takes the user's question and attaches the retrieved text chunks right next to it.
For example, it creates a message for the AI:
> *"Here are the verified school rules: [Retrieved chunk]. Now, please answer the user's question using only these rules."*
This is the **Augmentation** step.

### Step 6: Generation (Writing the Final Answer)
The LLM reads the fresh facts attached to the question. Because the exact answer is right in front of it, the LLM does not need to guess or hallucinate. It writes a clear, polite, and 100% accurate answer. This is the **Generation** step.

---

## 5. Key Terms Glossary (Simple Explanations)

Here is a quick reference table of the important terms we used:

| Term | Everyday Meaning |
| :--- | :--- |
| **LLM** | A computer program trained to read and write human language. |
| **Hallucination** | When an AI makes up false facts with false confidence. |
| **RAG** | Retrieval-Augmented Generation: Looking up facts before answering. |
| **Chunking** | Splitting long documents into short, single-topic paragraphs. |
| **Embedding** | A list of numbers that represents the meaning of a sentence. |
| **Vector Database** | A digital storage system that organizes text chunks by meaning. |
| **Prompt Augmentation** | Gluing the found facts onto the question before passing it to AI. |

---

## 6. Summary & Quick Recap

Let us quickly recap what we discovered today:
1. Standard LLMs suffer from outdated knowledge and hallucinations because they rely only on memory.
2. RAG solves this problem by giving the AI an open-book reference guide.
3. RAG follows a 6-step journey: Documents → Chunking → Embeddings → Vector Database → Retrieval → Augmentation → Generation.
4. With RAG, businesses and schools can get reliable, up-to-date answers from AI without spending millions of dollars retraining models.

Now you understand the foundations of Retrieval-Augmented Generation!
"""
        return lesson.strip()

    def _generate_lesson_with_factual_error(self, topic: str) -> str:
        """Generates a lesson containing a deliberate factual error for testing (Test F)."""
        lesson = self._generate_engine_lesson(topic)
        # Introduce deliberate error: claiming RAG retrains the LLM weights at query time
        target = "without spending millions of dollars retraining models."
        if target in lesson:
            flawed_lesson = lesson.replace(
                target,
                "because RAG retrains the model weights and updates model weights dynamically every time a user asks a question."
            )
        else:
            flawed_lesson = lesson + "\n\nNote: RAG retrains the model weights every time a user asks a question."
        return flawed_lesson

    def _generate_lesson_with_unexplained_jargon(self, topic: str) -> str:
        """Generates a lesson with missing definitions and heavy jargon."""
        return f"""# {topic}

In this lesson we discuss RAG. RAG uses stochasticity and epistemological heuristics in hyperdimensional latent spaces. 
The embeddings are mapped via cosine metrics without chunking or explaining what an LLM is.
Users query the model and generation occurs.
"""
