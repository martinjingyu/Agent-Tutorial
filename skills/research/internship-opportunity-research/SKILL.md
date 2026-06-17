---
name: internship-opportunity-research
description: Research summer internship positions for a candidate based on their CV/profile, with location preferences, and produce a structured report with recommendations, application timeline, and preparation plan.
---

# Internship Opportunity Research

Research summer internship positions for a candidate based on their CV/profile, with location preferences, and produce a structured report with recommendations, application timeline, and preparation plan.

## When to Use

- User provides a CV/resume and asks to find suitable internship positions for a specific year/summer
- User wants recommendations on where to apply, prioritized by location or company preference
- User wants a timeline and preparation plan alongside the research

## Workflow

### Step 1: Extract Candidate Profile

1. Read the CV file (supports `.tex`, `.pdf`, `.docx`, `.txt`, `.json`)
2. Extract key facts:
   - Education (school, major, GPA, graduation date)
   - Technical skills (programming languages, frameworks, tools)
   - Work experience (companies, roles, durations)
   - Projects (key projects with technologies used)
   - Research/publications (if any)
   - Notable achievements (awards, honors, leadership)

### Step 2: Identify Target Companies & Positions

Based on the candidate profile, identify suitable companies:

1. **Big Tech / FAANG**: Google, Meta, Amazon, Apple, Microsoft, Netflix
2. **AI/ML focused**: OpenAI, Anthropic, DeepMind, NVIDIA, Scale AI, Cohere, Databricks
3. **Austin-area companies** (if location preference is Austin):
   - Tesla (HQ in Austin)
   - Apple (large Austin campus)
   - Google (Austin office)
   - Amazon (Austin offices)
   - Microsoft (Austin area)
   - NVIDIA (Austin office)
   - AMD (HQ in Austin area)
   - Dell (HQ in Round Rock/Austin)
   - Indeed (Austin HQ)
   - Oracle (Austin area)
   - Other Austin tech companies
4. **Other relevant companies** based on candidate's specific skills/interests

### Step 3: Research Opening Dates & Application Windows

For each target company, research their summer internship opening timeline:

1. **Search patterns** (use bing_search or google_search):
   - `"{Company} 2027 summer internship application"`
   - `"{Company} software engineering internship 2027"`
   - `"{Company} internship application timeline 2027"`
   - `"{Company} 2027 internship when does it open"`

2. **Key dates to capture for each company**:
   - Application opening date (or typical month)
   - Application deadline (if rolling or fixed)
   - Expected interview timeline
   - Internship start date options (summer 2027)

3. **General industry timeline patterns** (for reference):
   - **July-August (Year -1)**: Some quant/trading firms open (Jane Street, Citadel, Two Sigma)
   - **August-September**: Big Tech starts opening (Google, Meta, Microsoft, Apple)
   - **October-November**: Peak application period for most companies
   - **December-January**: Late applications, some smaller companies open
   - **February-March**: Last wave, some companies still hiring
   - **April-May**: Late-stage hiring for unfilled positions

### Step 4: Browser Research on Company Career Pages

For high-priority companies, navigate to their career pages to verify.

**⚠️ Source Priority**: Always prefer official company career pages and APIs over third-party aggregators (huzzle.app, scholarshiptab.com, etc.). See `references/source-priority.md` for details.

**Google-specific pattern**: Google has a structured API endpoint that can be queried directly:
```
careers.google.com/api/v3/search/?q=intern&degree=BACHELORS,MASTERS&employment_type=INTERN
```
This returns JSON with current openings. Use `browser_navigate` to this URL, then inspect the response.

**General approach**:
1. Navigate to `careers.{company}.com` or `{company}.com/careers`
2. Search for "internship" or the target year on the page
3. Look for specific program pages (e.g., "Software Engineering Intern 2027")
4. Capture:
   - Exact position title
   - Location(s) available
   - Required qualifications
   - Preferred qualifications
   - Application link
   - Status (open/coming soon/closed)

**⚠️ Stale ref prevention**: Always call `browser_snapshot` (or use the snapshot returned by `browser_navigate`) before calling `browser_click`. Do not reuse refs from a previous navigation — they become invalid after the page changes.

### Step 5: Compile Report

Write a structured markdown report with the following sections:

```markdown
# {Candidate Name} - {Year} Summer Internship Research Report

## 1. Candidate Profile Summary
- Education: ...
- Key Skills: ...
- Target Locations: ...

## 2. Recommended Companies & Positions

### Tier 1: Strong Match (High Priority)
| Company | Position | Location | Est. Opening | Status | Notes |

### Tier 2: Good Match
| Company | Position | Location | Est. Opening | Status | Notes |

### Tier 3: Consider Applying
| Company | Position | Location | Est. Opening | Status | Notes |

## 3. Application Timeline

### Month-by-Month Plan
- **Month X (Year)**: ...

### Key Deadlines Summary
| Company | Application Opens | Deadline | Interview Window | Notes |

## 4. Preparation Recommendations

### Technical Preparation
- LeetCode / algorithm practice focus areas
- System design topics (if applicable)
- ML/AI specific preparation (if relevant)

### Application Materials
- Resume/CV updates needed
- Cover letter requirements
- Portfolio/GitHub preparation

### Timeline Strategy
- Which companies to apply to first
- How to stagger applications
- Networking / referral strategy

## 5. Austin-Area Opportunities (if applicable)
Specific notes on Austin-based positions and companies.

## 6. Additional Tips
- ...
```

## Output Location

Save the report to:
```
reports/{candidate_id}_{year}_summer_internship_report.md
```

Where `{candidate_id}` is the candidate's username or identifier from the CV filename.

## References

- Use `bing_search` or `google_search` for initial company/position discovery
- Use `browser_navigate` for company career pages to verify details
- Use `save_research_notes` after each major research step to compact context
- Use `compact_context` between major phases (profile extraction → company research → report writing)

## Related Skills

- `utilities/windows-file-operations`: For reading CV files on Windows
- `utilities/context-management`: For managing context during multi-step research
