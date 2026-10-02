# Phase 11: Benchmark

## Objective
The objective of Phase 11 is to quantitatively measure the effectiveness of the Tripline security boundary. It seeks to answer: "How often does each defense configuration actually stop the attack, how often does an unauthorized side effect occur, and what utility/false-positive tradeoffs are observed?" 

## The Benchmark Protocol
The benchmark is structured around a three-arm evaluation against a suite of attacks and benign actions.
For each task, we conduct `N=5` runs in a controlled sandbox.

### Arms
* **Arm A**: No Defense. The agent connects directly to the MCP server.
* **Arm B**: ArmorIQ Only. The agent connects to ArmorIQ. Tripline boundaries are disabled.
* **Arm C**: ArmorIQ + Tripline. The complete architecture is running, with Path Jail, Canary checking, Replan lock, Egress checks, and Witness logic.

### Modes
* **M1**: Real LLM (Claude). Tests if the LLM is susceptible to the attack.
* **M2**: Forced Compliance. Uses an attacker stub that intentionally forces a malicious proposal. This tests the security boundary without relying on LLM unreliability.

### Benchmark Data
The benchmark pipeline stores runs in `benchmark/results/benchmark_runs.jsonl`.
It outputs a summary in `benchmark/results/benchmark_summary.csv`.
It plots the overall attack success rate in `benchmark/results/attack-success-by-arm.png`.
It outputs a final report at `benchmark/results/benchmark_report.md`.

## What We Could Not Stop
The `benchmark/results/could_not_stop.md` lists every attack that was successful on the highest defense settings.

## Execution
To run tests:
`make bench-test`

To run the full suite:
`make phase11`
