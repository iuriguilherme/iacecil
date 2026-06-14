<overview>
Prompt patterns for creating approaches, roadmaps, and strategies (Plan prompts).
</overview>

<prompt_template>
```xml
<objective>
Create a plan for {topic}.

Purpose: {Inform implementation/strategy/research}
Outcome: {topic}-plan.md with structured phases and metadata
</objective>

<context>
{Chained research files}
{Existing architecture/codebase}
{Stakeholder requirements}
</context>

<requirements>
- Break work into specific, actionable phases
- Each phase must be "prompt-sized" (completable in one run)
- Identify dependencies between phases
- Capture assumptions and constraints
- Include execution hints for each phase
</requirements>

<output>
1. Write plan to: `.prompts/{num}-{topic}-{purpose}/{topic}-{purpose}.md`
2. Create SUMMARY.md with phase overview
</output>

<plan_structure>
The plan output (`{topic}-plan.md`) must include:

<roadmap>
Phase 1: {Objective}
Phase 2: {Objective}
...
</roadmap>

<phases>
<phase index="1">
<objective>{What this phase achieves}</objective>
<tasks>
- [ ] Task 1
- [ ] Task 2
</tasks>
<dependencies>None</dependencies>
<execution_hints>{Advice for the Do prompt for this phase}</execution_hints>
</phase>
...
</phases>

<metadata>
Load: [metadata-guidelines.md](metadata-guidelines.md)
</metadata>
</plan_structure>

<summary_requirements>
Create `.prompts/{num}-{topic}-{purpose}/SUMMARY.md`

Load template: [summary-template.md](summary-template.md)

For Plan prompts, include:
- Phase breakdown in Key Findings
- Assumptions in Decisions Needed
- Next step: Execute first phase prompt
</summary_requirements>

<success_criteria>
- Phases are sequential and logical
- Tasks are specific and actionable
- Dependencies are clear
- Metadata captures assumptions
- One-liner describes the approach (not just "Plan created")
</success_criteria>
```
</prompt_template>

<key_principles>
- **Prompt-sized phases**: Each phase should be a clear task that a single prompt can execute.
- **Dependency clarity**: Make it obvious what must happen before what.
- **Actionable hints**: Provide the context and constraints that will be needed by the Do prompts.
- **Explicit assumptions**: Document what you're assuming about the environment or existing code.
</key_principles>

<plan_types>

<implementation_plan>
For building features:
- Focused on code, types, and integration
- Phases: Scaffold → Core → Integration → UI → Tests
- Technical constraints prioritized
</implementation_plan>

<research_workflow_plan>
For complex investigations:
- Focused on information gathering and synthesis
- Phases: Source ID → Deep Dive A → Deep Dive B → Synthesis
- Information gaps prioritized
</research_workflow_plan>

<migration_plan>
For moving from one system to another:
- Focused on safety and parity
- Phases: Audit → Parallel Run → Cutover → Cleanup
- Risk mitigation prioritized
</migration_plan>

</plan_types>
