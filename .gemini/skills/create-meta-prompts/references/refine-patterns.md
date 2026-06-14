<overview>
Prompt patterns for improving existing research or plan outputs based on feedback (Refine prompts).
</overview>

<prompt_template>
```xml
<objective>
Refine {topic}-{original_purpose} based on feedback.

Target: @.prompts/{num}-{topic}-{original_purpose}/{topic}-{original_purpose}.md
Current summary: @.prompts/{num}-{topic}-{original_purpose}/SUMMARY.md

Purpose: {What improvement is needed}
Output: Updated {topic}-{original_purpose}.md with improvements
</objective>

<context>
Original output: @.prompts/{num}-{topic}-{original_purpose}/{topic}-{original_purpose}.md
</context>

<feedback>
{Specific issues to address}
{What was missing or insufficient}
{Areas needing more depth}
</feedback>

<preserve>
{What worked well and should be kept}
{Structure or findings to maintain}
</preserve>

<requirements>
- Address all feedback points
- Maintain original structure and metadata format
- Keep what worked from previous version
- Update confidence based on improvements
- Clearly improve on identified weaknesses
</requirements>

<output>
1. Archive current output to: `.prompts/{num}-{topic}-{original_purpose}/archive/{topic}-{original_purpose}-v{n}.md`
2. Write improved version to: `.prompts/{num}-{topic}-{original_purpose}/{topic}-{original_purpose}.md`
3. Create SUMMARY.md with version info and changes from previous
</output>

<summary_requirements>
Create `.prompts/{num}-{topic}-{original_purpose}/SUMMARY.md`

Load template: [summary-template.md](summary-template.md)

For Refine prompts, include:
- Version with iteration info (e.g., "v2 (refined from v1)")
- Changes from Previous section listing what improved
- Updated confidence if gaps were filled
</summary_requirements>

<success_criteria>
- All feedback points addressed
- Original structure maintained
- Previous version archived
- SUMMARY.md reflects version and changes
- Quality demonstrably improved
</success_criteria>
```
</prompt_template>

<key_principles>
- **Context preservation**: Don't throw away what worked.
- **Actionable feedback**: Map feedback points directly to improvements.
- **Version tracking**: Always archive before overwriting.
- **Incremental improvement**: Focus on filling specific gaps identified by the user.
</key_principles>

<refine_types>

<deepen_research>
When research was too surface-level:
- Add specific vulnerability patterns or CVEs
- Include performance benchmarks
- Expand on missing technical areas
</deepen_research>

<expand_scope>
When research missed important areas:
- Add new sections for missed requirements
- Include new code examples
- Cross-reference with additional sources
</expand_scope>

<update_plan>
When plan needs adjustment:
- Insert new phases or tasks
- Re-order based on new priorities
- Adjust dependencies
</update_plan>

</refine_types>
