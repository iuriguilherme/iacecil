<overview>
Guidelines for determining prompt complexity, tool usage, and optimization patterns.
</overview>

<complexity_assessment>

<simple_prompts>
Single focused task, clear outcome. Use for straightforward CRUD, basic utilities, or following well-defined patterns.
</simple_prompts>

<complex_prompts>
Multi-step tasks, multiple considerations, or architectural decisions. Use for features with many dependencies, security-sensitive code, or research involving multiple candidate technologies.
</complex_prompts>

</complexity_assessment>

<extended_thinking_triggers>
Use these phrases in `<requirements>` to activate deeper reasoning for complex tasks:
- "Thoroughly analyze..."
- "Consider multiple approaches..."
- "Deeply consider the implications..."
- "Explore various solutions before..."
- "Carefully evaluate trade-offs..."
</extended_thinking_triggers>

<parallel_tool_calling>
Instruct prompts to use tools in parallel for efficiency:
```xml
<efficiency>
For maximum efficiency, invoke all independent tool operations simultaneously rather than sequentially. Multiple file reads, searches, and API calls that don't depend on each other should run in parallel.
</efficiency>
```
</parallel_tool_calling>

<output_optimization>

<streaming_writes>
For research and plan outputs that may be large, instruct incremental writing:
1. Create output file with XML skeleton.
2. Write each section as completed (Findings, Recommendations, etc.).
3. Append immediately to prevent lost work.
4. Finalize summary and metadata at the end.
</streaming_writes>

<claude_to_claude>
Optimize for machine parsing:
- Use heavy XML structure for sections.
- Include structured metadata.
- Be explicit about dependencies and next steps.
</claude_to_claude>

<human_consumption>
Optimize for human scanning:
- Create SUMMARY.md for every prompt.
- Use clear headings and bullet points.
- Include executive summaries in research/plan outputs.
</human_consumption>

</output_optimization>

<verification_patterns>

<for_code>
Run existing test suites, type checkers, and linters. Include specific manual test cases.
</for_code>

<for_research>
Verify sources are current, all scope items are addressed, and URLs are provided for citations.
</for_research>

<for_plans>
Ensure phases are sequential, logical, and prompt-sized with clear dependencies.
</for_plans>

</verification_patterns>
