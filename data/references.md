# Ground Truth Reference Material: Retrieval-Augmented Generation (RAG)

## 1. Core Definition
Retrieval-Augmented Generation (RAG) is an AI architecture that enhances Large Language Models (LLMs) by retrieving relevant facts from an external knowledge base before generating a response. It was formally introduced by Lewis et al. in 2020.

## 2. Why RAG Matters (The Problem It Solves)
1. **Knowledge Cutoff & Staleness:** Standard LLMs only know facts up to the date their training data was collected. They cannot know today's news, current company policies, or private documents.
2. **Hallucination:** When an LLM does not know an answer, it often generates plausible-sounding but completely fabricated statements.
3. **Cost & Inefficiency of Retraining:** Constantly retraining or fine-tuning models on new data is slow, expensive, and risks catastrophic forgetting. RAG allows updating knowledge simply by adding or editing documents in the knowledge base, without retraining model weights.

## 3. How RAG Works: Step-by-Step Pipeline
The RAG workflow consists of two main phases: Ingestion (Preparation) and Query (Inference).

### Phase A: Ingestion (Indexing)
1. **Document Loading:** Private or specialized documents (PDFs, text files, documentation) are gathered.
2. **Chunking:** Large documents are split into smaller, manageable text sections ("chunks") so that specific facts can be retrieved without exceeding context windows.
3. **Embedding:** Each text chunk is passed through an embedding model to convert text into a dense vector (a list of numbers) that represents its semantic meaning.
4. **Vector Database Storage:** The embeddings and their corresponding text chunks are stored in a vector database (e.g., Chroma, FAISS, Pinecone) with an index for fast similarity search.

### Phase B: Retrieval & Generation (Querying)
1. **User Query:** The learner/user asks a question.
2. **Query Embedding:** The user's question is converted into an embedding using the same embedding model.
3. **Similarity Search (Retrieval):** The system searches the vector database to find chunks whose numerical meaning is closest to the question's embedding (e.g., via cosine similarity).
4. **Prompt Augmentation:** The top matching text chunks are inserted into the system prompt alongside the user question (e.g., "Use the following context to answer the question: [Context] Question: [Query]").
5. **Generation:** The LLM reads the augmented prompt and generates an accurate, grounded answer based directly on the provided context.

## 4. Canonical Real-World Analogy
- **Open-Book Examination:**
  - A traditional LLM is like a student writing a **closed-book exam**—answering solely from memory. If memory fails, the student might guess or hallucinate.
  - A RAG system is like an **open-book exam**—the student has a reference textbook on the desk. When asked a specific question, the student flips open the book, finds the exact relevant paragraph (retrieval), reads it, and writes down the clear, correct answer (generation).

## 5. Vocabulary & Core Terms
- **LLM (Large Language Model):** A computer program trained on massive amounts of text that can understand and generate human language.
- **Hallucination:** An error where an AI model confidently states false information as if it were true.
- **Chunking:** The process of dividing a long document into smaller parts (like paragraphs or sentences).
- **Embedding:** A mathematical representation of text as numbers, where texts with similar meanings have numbers that are close to each other.
- **Vector Database:** A specialized database designed to store and quickly search numerical embeddings.
- **Retrieval:** Searching for and fetching the most relevant pieces of information from a knowledge store.
- **Augmentation:** Adding the retrieved facts into the user's prompt to give the AI fresh, accurate context.
- **Generation:** The LLM writing out the final response in plain language using the provided facts.
