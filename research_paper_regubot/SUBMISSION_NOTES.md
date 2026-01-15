# JAIR & Applied Soft Computing Submission Notes

Use the following text when asked specific questions during the submission process.

## 1. Submission Questions (JAIR)

**Why is this work important to AI researchers?** (Max 150 words)
This paper presents **ReguBot**, a practical demonstration of **Neuro-Symbolic AI** applied to a high-stakes domain (pharmaceutical compliance). It is important because it bridges the gap between the probabilistic nature of modern NLP (which struggles with strict regulatory constraints) and deterministic database auditing. AI researchers can use these results to validate hybrid architectures that prioritize auditability over conversational flexibility in edge-retail environments.

**Comparison to other papers**:
Unlike recent work on LLM agents, ReguBot integrates **strict SQL-based constraint satisfaction** as a hard guardrail. It differs from papers like *Simplex* by focusing on offline-first, low-latency compliance.

---

## 2. Elsevier (Applied Soft Computing) Requirements

If submitting to Applied Soft Computing, you must provide **Highlights** (3-5 bullet points) during upload.

**Highlights:**

* **Neuro-Symbolic Architecture**: Integrates deterministic SQL auditing with probabilistic NLP for high-stakes compliance.
* **Latency Optimization**: Achieves 1.61 ms reporting latency on standard hardware, enabling real-time edge deployment.
* **Noise Tolerance**: Demonstrates 52% zero-shot accuracy on ambiguous inputs while maintaining 100% database integrity via strict rejection logic.
* **System Design**: Proposes a modular "Compliance Sidecar" architecture compatible with legacy ERP systems.

**Note on Word Count**:
The current manuscript is concise (~1000 words). While acceptable for initial review (`Your Paper Your Way`), reviewers may request an expanded "Related Works" or "Discussion" section to meet the typical 3000+ word count for full research articles.
