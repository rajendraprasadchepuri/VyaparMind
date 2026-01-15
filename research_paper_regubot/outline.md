# Research Paper: ReguBot (Standalone)

## Title

**ReguBot: A Neuro-Symbolic Framework for Automated Regulatory Compliance in Pharmaceutical Retail**

## Abstract

Pharmaceutical retailers in developing economies face significant challenges in adhering to stringent regulatory norms (e.g., Schedule H1/X drug reporting). Manual record-keeping is error-prone, time-consuming, and often leads to non-compliance penalties. This paper presents **ReguBot**, a standalone compliance module designed to automate regulatory reporting through a hybrid approach. ReguBot combines deterministic SQL-based auditing with lightweight Natural Language Processing (NLP) for voice-assisted transaction logging. The system automatically categorizes sensitive drug sales, enforces patient data collection, and generates standardized "Drug Inspector" reports in real-time. Deployed in a simulated enterprise environment, ReguBot demonstrates a reduction in reporting latency and an increase in compliance accuracy, offering a scalable solution for modernizing pharmaceutical supply chains.

## 1. Introduction

- **Background**: The critical importance of monitoring Schedule H1 (Antibiotics) and Schedule X (Narcotics) drugs.
- **Problem Statement**: Small and medium-sized pharmacies (SMBs) struggle with complex regulatory reporting.
- **Objective**: To design a low-latency, offline-capable system that integrates compliance into the daily workflow.

## 2. System Architecture

### 2.1 Independent Architecture

- **Standalone Design**: How ReguBot operates as a modular agent, independent of specific ERP monoliths.
- **Database Schema**: Use of standard relational logic for `products` and `schedule_type` attributes.
- **Transaction Flow**: Real-time interception of sales data.

### 2.2 The ReguBot Engine

- **Data Query Layer**: The SQL logic that aggregates fragmented transaction data.
- **NLP Interface**: The `nlp_engine.py` component allowing pharmacists to log stock changes or sensitive sales using voice commands (e.g., *"Sold 5 strips of Alprazolam"*).

## 3. Methodology

- **Fuzzy Product Matching**: Implementation of `difflib` for error-tolerant drug name recognition.
- **Intent Classification**: Rule-based parsing for high-speed, deterministic action execution.
- **Automated Reporting**: Generation of CSV reports compliant with government formats.

## 4. Implementation & Results

- **Case Study**: Simulation of sales data involving Schedule H1 drugs (using synthesized data).
- **Performance**: Query execution time and system responsiveness.
- **Accuracy**: Success rate of the NLP engine in parsing commands.

## 5. Conclusion

- Summary of impact on reducing compliance burden.
- Future work: Integration of Large Language Models (LLMs).
