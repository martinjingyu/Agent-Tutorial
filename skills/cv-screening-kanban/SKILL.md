---
name: cv-screening-kanban
description: Create one Kanban board per candidate and orchestrate CVScreeningAgent stage-1 research/report tasks as a dependency graph.
---

# CV Screening Kanban Orchestration

Use this skill when the user wants the research agent to run or manage the CV screening pipeline agentically.

Important design rule: **one candidate gets one Kanban board**. The tasks on that board are the candidate's internal screening workflow, not "one candidate = one task".

The Kanban tool is generic. This skill translates CVScreening work into generic `kanban_create_pipeline` tasks.

## Board Naming

Use a stable candidate-specific board name:

```text
cv-candidate-<candidate-id-or-folder-name>
```

Examples:

```text
cv-candidate-1
cv-candidate-zhangsan
```

## Candidate Task Graph

Create these tasks for each candidate board.

1. `ingest-profile`
   - Extract CV/transcripts.
   - Run profile enrichment and targeted web search if needed.
   - Produce `stage1_profile.json` and transcript JSONs.
   - Also create `stage1_report.md` skeleton.

2. `school-transcript`
   - Depends on `ingest-profile`.
   - Generate school/major reports and transcript analysis.
   - Produce `school_reports/**/*.md` and `transcript_analysis.md`.

3. `publication`
   - Depends on `ingest-profile`.
   - Analyze publications, papers, candidate author role, and evidence quality.
   - Produce `publications/*.md`.

4. `work-experience`
   - Depends on `ingest-profile`.
   - Analyze internships/jobs/company evidence and experience depth.
   - Produce `work_experience/*.md`.

5. `project-awards`
   - Depends on `ingest-profile`.
   - Analyze projects, GitHub/product evidence, awards/competitions.
   - Produce `projects/*.md` and `rewards/*.md`.

6. `extra-info`
   - Depends on `school-transcript`, `publication`, `work-experience`, and `project-awards`.
   - Search for extra public evidence and unresolved questions.
   - Produce `extra_info/*.md`.

7. `final-report`
   - Depends on every report-producing task.
   - Generate final markdown report.
   - Must link to subreports using Markdown links.
   - Produce `stage1_report.md`, `stage1_verdict.json`, and optionally `timeline.md`.

## Runner

Use this runner inside task prompts:

```text
C:\Users\LX034\Code\CVScreeningAgent\ScreeningPipeline\kanban_task_runner.py
```

Run commands from:

```text
C:\Users\LX034\Code\CVScreeningAgent
```

Command shape:

```text
python C:\Users\LX034\Code\CVScreeningAgent\ScreeningPipeline\kanban_task_runner.py <task> <candidate> --workspace <workspace> --json
```

Available runner tasks:

```text
ingest_profile
school_transcript
publication
work_experience
project_awards
extra_info
final_report
```

## Generic Tool Call Template

Call `kanban_create_pipeline` with `board`, `tasks`, and dependency aliases.

```json
{
  "board": "cv-candidate-1",
  "default_skill": "cv-screening-pipeline-worker",
  "tasks": [
    {
      "id": "ingest-profile",
      "title": "Extract CV/transcripts and build structured profile",
      "prompt": "Candidate: 1\nWorkspace: C:\\Users\\LX034\\Code\\CVScreeningAgent\\workspace\\candidates\nRun from C:\\Users\\LX034\\Code\\CVScreeningAgent:\npython C:\\Users\\LX034\\Code\\CVScreeningAgent\\ScreeningPipeline\\kanban_task_runner.py ingest_profile 1 --workspace C:\\Users\\LX034\\Code\\CVScreeningAgent\\workspace\\candidates --json\nExpected outputs: stage1_profile.json, transcript*.json, stage1_report.md skeleton."
    },
    {
      "id": "school-transcript",
      "title": "Generate school/major report and transcript analysis",
      "depends_on": ["ingest-profile"],
      "prompt": "Candidate: 1\nRun: python C:\\Users\\LX034\\Code\\CVScreeningAgent\\ScreeningPipeline\\kanban_task_runner.py school_transcript 1 --workspace C:\\Users\\LX034\\Code\\CVScreeningAgent\\workspace\\candidates --json\nExpected outputs: school_reports/**/*.md and transcript_analysis.md."
    },
    {
      "id": "publication",
      "title": "Analyze publications and paper evidence",
      "depends_on": ["ingest-profile"],
      "prompt": "Candidate: 1\nRun: python C:\\Users\\LX034\\Code\\CVScreeningAgent\\ScreeningPipeline\\kanban_task_runner.py publication 1 --workspace C:\\Users\\LX034\\Code\\CVScreeningAgent\\workspace\\candidates --json\nExpected outputs: publications/*.md, or a clear skipped/no-publications note."
    },
    {
      "id": "work-experience",
      "title": "Analyze work and internship experience",
      "depends_on": ["ingest-profile"],
      "prompt": "Candidate: 1\nRun: python C:\\Users\\LX034\\Code\\CVScreeningAgent\\ScreeningPipeline\\kanban_task_runner.py work_experience 1 --workspace C:\\Users\\LX034\\Code\\CVScreeningAgent\\workspace\\candidates --json\nExpected outputs: work_experience/*.md."
    },
    {
      "id": "project-awards",
      "title": "Analyze projects and awards",
      "depends_on": ["ingest-profile"],
      "prompt": "Candidate: 1\nRun: python C:\\Users\\LX034\\Code\\CVScreeningAgent\\ScreeningPipeline\\kanban_task_runner.py project_awards 1 --workspace C:\\Users\\LX034\\Code\\CVScreeningAgent\\workspace\\candidates --json\nExpected outputs: projects/*.md and rewards/*.md."
    },
    {
      "id": "extra-info",
      "title": "Search and write extra public evidence",
      "depends_on": ["school-transcript", "publication", "work-experience", "project-awards"],
      "prompt": "Candidate: 1\nRun: python C:\\Users\\LX034\\Code\\CVScreeningAgent\\ScreeningPipeline\\kanban_task_runner.py extra_info 1 --workspace C:\\Users\\LX034\\Code\\CVScreeningAgent\\workspace\\candidates --json\nExpected outputs: extra_info/*.md."
    },
    {
      "id": "final-report",
      "title": "Generate final markdown screening report with links to subreports",
      "depends_on": ["school-transcript", "publication", "work-experience", "project-awards", "extra-info"],
      "prompt": "Candidate: 1\nRun: python C:\\Users\\LX034\\Code\\CVScreeningAgent\\ScreeningPipeline\\kanban_task_runner.py final_report 1 --workspace C:\\Users\\LX034\\Code\\CVScreeningAgent\\workspace\\candidates --json\nFinal report requirement: stage1_report.md must summarize all evidence and include Markdown links to subreports in school_reports, transcript_analysis.md, publications, work_experience, projects, rewards, and extra_info where present. Also verify stage1_verdict.json."
    }
  ]
}
```

For other candidates, replace board, candidate id, and workspace in every prompt.

## Dispatch Pattern

Start/continue work:

```json
{"board": "cv-candidate-1", "max_spawn": 2}
```

Suggested concurrency:

- `max_spawn=1` if browser/login state or rate limits are fragile.
- `max_spawn=2` or `3` after `ingest-profile` is done, because publication/work/project/school tasks are mostly independent.

## Final Report Rules

The final report task must not just say "done". It must verify:

- `stage1_report.md` exists.
- The report references subreports with Markdown links where files exist.
- `stage1_verdict.json` exists or the final report contains enough decision text for the pipeline to infer a verdict.
- Missing optional sections are explicitly noted, e.g. "no publications found".

## Generalization Rule

This is a domain-specific task template built on a general Kanban primitive. Do not add candidate/stage-specific fields to Kanban tools. Encode domain details in task prompts, skills, dependencies, and metadata.
