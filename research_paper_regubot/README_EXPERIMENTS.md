# ReguBot Experimentation Package

This folder contains the source code, experimental scripts, and result logs used to validate the claims made in the ReguBot research paper.

## Directory Structure

- `source_code/`: Contains the isolated module code (`27_ReguBot.py`, `nlp_engine.py`) and a mock database adapter.
- `experiments/`: Contains the reproduction script `reproduce_results.py`.
- `paper.tex`: The LaTeX source code for the research paper.
- `ReguBot_Paper.pdf`: The compiled PDF of the research paper.

## Reproducing Results

To generate the synthetic dataset and run the benchmarks (Query Latency and NLP Accuracy):

1. Ensure you have Python installed.
2. Run the reproduction script:

   ```bash
   python experiments/reproduce_results.py
   ```

3. The script will:
   - Create a temporary SQLite database `research_experiment.db`.
   - Seed it with 5,000 synthetic transactions and 200 products.
   - Execute the SQL compliance query 100 times to measure latency.
   - Run 500 random voice command simulations against the `nlp_engine`.
4. Results are saved to `experiment_results.txt`.

## Latest Benchmark Results (2026-01-15)

- **Dataset Size**: 5,000 Transactions
- **Query Latency**: 1.61 ms (Avg)
- **NLP Accuracy**: 52.20% (Zero-shot, Ambiguous Input)
  *Note: High accuracy in paper assumes specific, non-ambiguous command structures.*
