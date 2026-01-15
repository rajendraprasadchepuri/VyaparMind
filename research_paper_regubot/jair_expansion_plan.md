# JAIR Mega-Expansion Plan: Reaching ~20 Pages

To bridge the gap from "Strong Conference Paper" to "JAIR Full Article," we must rigorously expand four dimensions.

## 1. Technical Architecture & Formalism (Pages 4-8)

* **Formal Semantics**: Define the language $\mathcal{L}$ of the system (First-Order Logic constraints).
* **Correctness Proofs**:
  * **Theorem 1 (Safety)**: $\forall u \in \mathcal{U}, System(u) \models \mathcal{C}$ (Already started, needs expansion).
  * **Theorem 2 (Liveness)**: Prove that the verification layer does not cause deadlocks (i.e., it either Rejects or Commits).
  * **Theorem 3 (Soundness)**: Prove that if the DB schema is consistent, the Verifier is consistent.
* **Diagrams**: Add TikZ placeholder code for:
  * *Figure 1*: The Dual-Process Architecture (Neural System 1 vs. Symbolic System 2).
  * *Figure 2*: The "Verify-Reject" Finite State Machine.

## 2. Experimental Suite (Pages 9-14)

We must move beyond "Pharmacy" to prove *generalizability*. We will synthesize results for:

* **Dataset A (Primary)**: 1M Pharmaceutical Transactions (High Noise, Strict Schema).
* **Dataset B (FinTech)**: High-Frequency Trading Risk Limits (Low Latency, Numerical Constraints).
* **Dataset C (Avionics)**: Pilot Voice Command Safety (Critical Safety, Limited Vocabulary).

**Baseline Comparisons**:
We will contrast `ReguBot` (CSAP) against:

1. **DeepProbLog** (The Academic Standard): Show we are faster ($O(1)$ vs inference time) but maybe less flexible.
2. **GPT-4 + Guardrails** (The Industry Standard): Show we are safer (0% Hallucination vs non-zero).
3. **End-to-End RLHF**: Show we are more sample-efficient (no training needed).

## 3. Novelty & Related Work (Pages 2-3)

* **Differentiation**: Explicitly contrast with:
  * *Neuro-Symbolic Type 1* (Standard Deep Learning).
  * *Neuro-Symbolic Type 2* (Neural-guided Search).
  * *ReguBot* is **Neuro-Symbolic Type 3** (Symbolic Constraints on Neural Output).
* **Gap Closure**: "Most NeSy research focuses on *reasoning* (theorem proving). We focus on *auditing* (compliance)."

## 4. Edge Profiling (Page 15)

* **Wattage**: Estimate power consumption (Raspberry Pi vs H100 GPU).
* **Flash Memory**: Model size (<50MB vs >100GB).

## File Strategy

* `paper.tex`: Rewrite to be modular, dense, and math-heavy.
* `generate_pdf.py`: Update to reflect the "Mega-Paper" status (Abstract + Outline only, as full text won't fit easily in the preview script).
