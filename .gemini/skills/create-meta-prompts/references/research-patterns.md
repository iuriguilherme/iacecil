<overview>
Prompt patterns for gathering information and understanding topics (Research prompts).
</overview>

<prompt_template>
```xml
<objective>
{Clear research goal}

Purpose: {Why it's being done}
Outcome: {topic}-research.md with structured findings and metadata
</objective>

<research_scope>
<include>
{Key areas to investigate}
</include>
<exclude>
{Areas to ignore}
</exclude>
</research_scope>

<requirements>
- Enumerate known possibilities first
- Verify findings across multiple authoritative sources
- Provide URLs for all official documentation claims
- Use high-quality tools (mcp_context7_query-docs, WebFetch, WebSearch)
- Distinguish verified facts from assumptions with confidence levels
- List explicit next actions based on findings
</requirements>

<output>
1. Write research to: `.prompts/{num}-{topic}-{purpose}/{topic}-{purpose}.md`
2. Create SUMMARY.md with key recommendations
</output>

<research_structure>
The research output (`{topic}-research.md`) must include:

<summary>
{Substantive one-liner}
{Key recommendations}
</summary>

<findings>
{Detailed findings with citations}
</findings>

<code_examples>
{Relevant patterns for implementation}
</code_examples>

<next_actions>
{Actionable next steps}
</next_actions>

<metadata>
Load: [metadata-guidelines.md](metadata-guidelines.md)
</metadata>
</research_structure>

<summary_requirements>
Create `.prompts/{num}-{topic}-{purpose}/SUMMARY.md`

Load template: [summary-template.md](summary-template.md)

For Research prompts, include:
- Key recommendations in Key Findings
- Most important decision in Decisions Needed
- Next step: Create planning prompt
</summary_requirements>

<verification_checklist>
□ Sources are current ({current_year})
□ All scope questions answered
□ Metadata captures uncertainties
□ Actionable recommendations included
□ URLs provided for official docs
</verification_checklist>

<success_criteria>
- Research scope fully covered
- Findings are verified and cited
- Recommendations are actionable
- Metadata correctly reflects confidence
- SUMMARY.md captures the "so what"
</success_criteria>
```
</prompt_template>

<key_principles>
- **Authority first**: Prioritize official documentation over blogs/third-party sites.
- **Cite your sources**: Every critical claim should have a URL or source reference.
- **Be honest about unknowns**: Metadata is for capturing what you DIDN'T find too.
- **Action over data**: Research should lead directly to decisions and plans.
</key_principles>

<research_types>

<technology_research>
Evaluating libraries or frameworks:
- Check for security, performance, community support
- Look for current version patterns
- Verify TypeScript/environment compatibility
</technology_research>

<best_practices_research>
Understanding standards and patterns:
- Consult authoritative bodies (OWASP, vendor docs)
- Look for consensus across sources
- Identify current industry standards
</best_practices_research>

<api_service_research>
Understanding external services:
- Check endpoints, auth, webhooks, rate limits
- Look for SDK availability and patterns
- Verify sandbox/testing capabilities
</api_service_research>

</research_types>

<tool_usage>
<context7_mcp>
For library documentation:
```
Use mcp_context7_resolve-library-id to find library
Then mcp_context7_query-docs for current patterns
```
</context7_mcp>

<web_fetch>
For specific documentation pages:
```
Fetch official docs, API references, changelogs with exact URLs
```
</web_fetch>

<web_search>
For recent updates and comparisons:
```
Search: "{topic} best practices {current_year}"
```
</web_search>
</tool_usage>

<pitfalls_reference>
Before completing research, review: [research-pitfalls.md](research-pitfalls.md)
</pitfalls_reference>
