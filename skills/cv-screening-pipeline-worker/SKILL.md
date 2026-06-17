---
name: cv-screening-pipeline-worker
description: Execute one task from a candidate-specific CVScreeningAgent Kanban board and verify its artifacts.
---

# CV Screening Pipeline Worker

Use this skill when assigned one task on a candidate-specific CV screening Kanban board.

The task prompt should include a command using:

```text
C:\Users\LX034\Code\CVScreeningAgent\ScreeningPipeline\kanban_task_runner.py
```

## Procedure

1. Read the task prompt carefully.
   - Identify candidate id or folder.
   - Identify workspace.
   - Identify runner task.
   - Identify expected output files.

2. Run the exact command from:

```text
C:\Users\LX034\Code\CVScreeningAgent
```

3. Verify expected artifacts.
   - Use `search_files` before `read_file` for large outputs or logs.
   - Do not claim success just because the command exited; check the files.

4. Handle failures narrowly.
   - Missing input, credentials, or browser login are blockers.
   - Small local code/config errors may be fixed once.
   - Do not repeatedly rerun the same failing command without changing anything.

5. Finish with `respond_to_user`.
   - Include status.
   - Include command run.
   - Include output file paths.
   - Include blockers or skipped optional sections.

## Task-Specific Checks

### ingest_profile

Expected:

- `stage1_profile.json`
- `transcript*.json` when transcripts exist
- `stage1_report.md` skeleton

### school_transcript

Expected:

- `school_reports/**/*.md` when education exists
- `transcript_analysis.md` when transcript data exists

### publication

Expected:

- `publications/*.md` when publications exist
- If no publications exist, report it as a valid skip, not an error.

### work_experience

Expected:

- `work_experience/*.md` when work/internship entries exist
- If none exist, report a valid skip.

### project_awards

Expected:

- `projects/*.md` for project evidence
- `rewards/*.md` for awards/competitions when present

### extra_info

Expected:

- `extra_info/*.md` for public evidence or unresolved questions
- Valid skip when there is no useful extra info.

### final_report

Expected:

- `stage1_report.md`
- `stage1_verdict.json` when the decision tool succeeds
- `timeline.md` when timeline synthesis is enabled

Extra final-report requirement:

- Verify `stage1_report.md` contains Markdown links to subreports where those files exist.
- Good links look like `[成绩单分析](transcript_analysis.md)` or `[论文分析](publications/xxx.md)`.
- If links are missing but subreport files exist, patch or regenerate the report if the task prompt allows it; otherwise report the blocker clearly.

## Final Response Shape

```text
Status: completed | blocked | skipped | error
Runner task: <task>
Candidate: <id/folder>
Command: <command>
Artifacts:
- <path>
Notes:
- <brief facts, skips, or blockers>
```
