<overview>
Prompt patterns for executing tasks and producing artifacts (Do prompts).
</overview>

<prompt_template>
```xml
<objective>
{Clear statement of what to build/fix/add}

Purpose: {Why it's being done}
Outcome: {Specific artifact created}
</objective>

<context>
{Chained research/plan files}
{Existing code to modify}
{Libraries/patterns to follow}
</context>

<requirements>
{Detailed instructions}
{Constraints and standards}
{Security/Performance requirements}
</requirements>

<output>
1. Create/Modify files: {paths}
2. Run verification: {test commands}
3. Create SUMMARY.md
</output>

<summary_requirements>
Create `.prompts/{num}-{topic}-{purpose}/SUMMARY.md`

Load template: [summary-template.md](summary-template.md)

For Do prompts, include:
- Files Created section
- Substantive one-liner about implementation choices
- Next step for verification or next phase
</summary_requirements>

<verification>
{Specific commands to run}
{Manual tests to perform}
</verification>

<success_criteria>
- All requirements met
- Verification passes
- Code follows project standards
- SUMMARY.md reflects implementation details
</success_criteria>
```
</prompt_template>

<key_principles>
- Be specific about file paths and symbol names
- Reference research/plans explicitly (@)
- Include verification logic (tests/linters)
- Explain WHY constraints matter
- Ensure prompt is sized for single-shot execution
</key_principles>

<do_types>

<new_feature>
Building something new:
- Define structure and types first
- Implement core logic
- Add tests
- Document exported symbols
</new_feature>

<bug_fix>
Fixing an issue:
- Reproduce first
- Identify root cause
- Implement fix
- Verify fix with regression test
</bug_fix>

<refactor>
Improving existing code:
- Maintain behavior (no feature changes)
- Run baseline tests first
- Implement refactor in logical steps
- Run verification at each step
</refactor>

</do_types>

<tool_usage>
<context7_mcp>
For library documentation:
```
Use mcp_context7_resolve-library-id to find library
Then mcp_context7_query-docs for current patterns
```
</context7_mcp>

<shell_commands>
For execution and verification:
```
Explain modifying commands before running
Run tests, linters, type checkers
```
</shell_commands>
</tool_usage>
