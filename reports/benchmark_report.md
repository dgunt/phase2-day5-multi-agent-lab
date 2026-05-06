# Benchmark Report - Multi-Agent Research Lab

## 1. Objective

This report compares a single-agent baseline with a multi-agent workflow composed of Supervisor, Researcher, Analyst, and Writer agents.

## 2. Benchmark Queries

1. `Research GraphRAG state-of-the-art and write a 500-word summary`
2. `Compare single-agent and multi-agent systems for research tasks`
3. `Explain common failure modes of multi-agent orchestration and how to fix them`

## 3. Metrics

| Run | Latency (s) | Estimated Cost (USD) | Quality | Notes |
|---|---:|---:|---:|---|
| q1_baseline | 15.85 | 0.000363 | 7.5 | input_tokens=83; output_tokens=585; errors=0; routes=none |
| q1_multi_agent | 30.57 | 0.001082 | 9.5 | input_tokens=1704; output_tokens=1378; errors=0; routes=researcher->analyst->writer->done |
| q2_baseline | 13.27 | 0.000331 | 7.5 | input_tokens=78; output_tokens=533; errors=0; routes=none |
| q2_multi_agent | 37.66 | 0.001154 | 9.5 | input_tokens=1895; output_tokens=1450; errors=0; routes=researcher->analyst->writer->done |
| q3_baseline | 15.79 | 0.000382 | 7.5 | input_tokens=82; output_tokens=616; errors=0; routes=none |
| q3_multi_agent | 34.51 | 0.001075 | 9.5 | input_tokens=1713; output_tokens=1363; errors=0; routes=researcher->analyst->writer->done |

## 4. Run Summaries

| Run | Routes | Trace Events | Errors | Input Tokens | Output Tokens | Final Answer Chars |
|---|---|---:|---:|---:|---:|---:|
| q1_baseline | none | 1 | 0 | 83 | 585 | 3474 |
| q1_multi_agent | researcher -> analyst -> writer -> done | 9 | 0 | 1704 | 1378 | 3680 |
| q2_baseline | none | 1 | 0 | 78 | 533 | 2850 |
| q2_multi_agent | researcher -> analyst -> writer -> done | 9 | 0 | 1895 | 1450 | 3048 |
| q3_baseline | none | 1 | 0 | 82 | 616 | 3440 |
| q3_multi_agent | researcher -> analyst -> writer -> done | 9 | 0 | 1713 | 1363 | 3102 |

## 5. Analysis

The single-agent baseline is faster because it uses one LLM call to perform research, analysis, and writing in a single step. However, this makes the reasoning process less observable.

The multi-agent workflow is slower and slightly more expensive because it uses multiple LLM calls. In exchange, it provides clearer role separation, better traceability, and intermediate artifacts such as research notes and analysis notes.

## 6. Failure Modes and Fixes

### Failure Mode 1: Researcher returns vague notes
- **Cause:** The research prompt is too broad or lacks source grounding.
- **Fix:** Add external search integration and require structured notes with evidence.

### Failure Mode 2: Analyst repeats researcher notes
- **Cause:** Weak role separation between Researcher and Analyst.
- **Fix:** Force Analyst to focus on claims, trade-offs, weak evidence, and risks.

### Failure Mode 3: Writer ignores length or structure requirements
- **Cause:** No output validation after generation.
- **Fix:** Add validation for word count, sections, and citation/source coverage.

### Failure Mode 4: Cost and latency increase in multi-agent mode
- **Cause:** Multi-agent workflow uses several LLM calls instead of one.
- **Fix:** Use smaller models for intermediate agents, cache research notes, and stop early when enough information is available.


## Trace Evidence

The multi-agent workflow was executed successfully with the following route:

`researcher -> analyst -> writer -> done`

The run produced trace events for workflow start, supervisor routing, each worker agent, and workflow completion.

Screenshot evidence:

- `docs/images/multi_agent_summary.png`
- `docs/images/full_state_trace.png`

## 7. Conclusion

The multi-agent approach is more suitable for complex research tasks where traceability, decomposition, and intermediate reasoning are important. For simple tasks, the single-agent baseline remains faster and cheaper.
