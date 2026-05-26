---
name: university-program-research
description: Research a university academic program using official sources, browser navigation, source cross-checking, and a structured markdown report. Supports both general program inquiries and recruitment-context evaluation (candidate background vs. job description).
---

# University Program Research

Use this skill when the user asks for a university, college, department, major, program, admissions track, employment-outcome report, or when evaluating a candidate's academic background against a job description.

## Workflow

### 1. Identify scope
- Identify the exact institution, program name, degree level, campus, and language/region.
- If in a recruitment context, note the specific **department**, **degree level**, and **JD requirements** — research targets fit, not general facts.

### 2. Browser-based research sequence

**⚠️ Always start with browser_navigate before falling back to curl/terminal.** The browser tools can handle JS-rendered pages that curl cannot. Only use curl when browser_navigate times out or returns an empty/error snapshot.

Start with the **school's main site** to confirm current organizational structure, then drill into the department.

```
browser_navigate(url="https://www.<school>.edu.cn/")
# Find "院系设置" to confirm which college/department hosts the target program
```

**⚠️ For Chinese universities:** Do NOT assume the department URL. Many Chinese universities have reorganized departments (e.g., 软件学院 merged into 计算机学院). Always verify current structure from the main site first.

**Recommended investigation order:**

1. **University main site → 院系设置** → confirm current organizational structure
2. **Department homepage** → self-description, recent news, strategic initiatives
3. **Undergraduate / Programs page** → degree types, curriculum scope, capstone/research programs
4. **Course catalog / Courses page** → identify specific AI/ML/NLP/CV courses (course codes and names)
5. **Faculty page** → scan for AI/ML professors; note award-winning faculty for prestige signals
6. **Research page / Research groups** → identify AI sub-areas actively researched
7. **Rankings** → check US News, CSRankings, QS for CS program ranking (use Wikipedia for overview)
8. **Recent news about AI investment** → strategic initiatives (new AI college, major gifts)

**If browser_navigate fails (timeout/EOF):**
- Immediately try `curl` via terminal to get raw HTML
- If the page is JS-rendered (HTML has no body content), switch to fallback sources: 招生网, Baidu Baike, Wikipedia
- Do NOT keep retrying the same failing URL
- **Check for previously saved/cached pages** in `reports/` — earlier research sessions may have saved useful HTML snapshots that can be re-analyzed

### 3. Source priority

1. Official university/school/department program page.
2. Official admissions office page, prospectus, or 招生章程.
3. Official 培养方案, course catalog, or handbook.
4. Official employment quality report or graduate destination report.
5. Education ministry, government, accreditation, or recognized ranking/database pages.
6. Reputable third-party articles only for context, never as the sole source for key facts.

For Chinese universities, verify school names, major names, and program categories against official Chinese-language pages whenever possible. See `references/chinese-university-research.md` for anti-bot workarounds (Baidu Baike fallback, etc.).

**For foreign universities, Reddit (r/{school}) can be a useful supplementary source** for student perspectives, course difficulty, program culture, and admissions experiences.

Use the reusable script `scripts/fetch-reddit-posts.py` to fetch recent posts:

```bash
# Basic usage — fetch 25 recent CS-related posts from r/UWMadison
python skills/research/university-program-research/scripts/fetch-reddit-posts.py UWMadison

# Custom query and limit, save to file (recommended on Windows)
python skills/research/university-program-research/scripts/fetch-reddit-posts.py UWMadison "AI machine learning" 15 reddit_data.json

# Then read the file to inspect results
read_file("reddit_data.json")
```

The script:
- Uses `old.reddit.com` JSON API (no auth required).
- Filters to posts within the past year (`t=year`).
- Fetches top comments (score > 1, up to 8 per post) for each result.
- On Windows, pass a 4th argument (output file path) to avoid stdout encoding issues.

**Important:** Reddit data is anecdotal and should be used as supplementary context only, not as a primary source for factual claims. Always mark Reddit-sourced information as "student perspective / anecdotal" in the report.

### 4. Cross-reference with JD (recruitment context)

Map each JD requirement against what the school offers. Be explicit:

> **JD requirement** | **School's offering** | **Match**
> Python proficiency | CS curriculum uses Python as primary teaching language | ✅ Strong
> Top 10% grades | Competitive CS admission serves as filter | ⚠️ Indirect signal

### 5. Save report

Save the final report as markdown under `reports/{学校名}/{专业名}.md`.

**Directory structure convention:**

```
reports/
├── 广东海洋大学/
│   └── 人工智能专业.md
├── University-of-Wisconsin-Madison/
│   └── Computer-Science-BS.md
└── ...
```

- **学校名**：使用学校官方中文名或英文名（保持一致即可），作为文件夹名。
- **专业名**：使用专业/项目的中文或英文名称，作为文件名。
- 如果文件夹不存在，先创建文件夹再保存文件。
- 对于同一所学校的不同专业/项目，放在同一个学校文件夹下。

## Key Dimensions to Evaluate (CS/AI Focus)

| Dimension | What to look for |
|-----------|-----------------|
| **Program selectivity** | Admission requirements, GPA thresholds to declare CS major |
| **AI/ML course depth** | Number of AI courses beyond intro level |
| **Research infrastructure** | GPU compute clusters, undergraduate research programs, summer AI labs |
| **System/OS strength** | For positions involving deployment/inference, system-strong schools produce candidates who understand infra |
| **Recent AI pivot** | Schools investing heavily in AI (new colleges, hiring sprees) signal recent graduates immersed in AI culture |
| **Notable alumni/faculty** | Prestige signal; faculty awards indicate research quality |

## Report Shape

Use `templates/program-report.md` when the user asks for a full report. Include:

- Program identity
- Official description
- Curriculum or training plan
- Admissions and eligibility
- Career outcomes
- Strengths
- Risks or uncertainty
- Source list

For recruitment-context reports, also include:
- **JD fit matrix** (requirements × school's offerings)
- **Interview guidance** (what to probe: courses taken, research projects, specific frameworks/tools used)

### 6. Report generation when sources are limited

When official sources are unreachable (network blocks, JS-only pages, anti-bot protection):

1. **Use general knowledge + limited sources explicitly.** State what is confirmed vs. assumed.
2. **Mark all uncertainties clearly** in a dedicated "Uncertainties" section.
3. **Use the JD fit matrix** to structure what you *can* confirm (e.g., school reputation, typical curriculum) vs. what needs verification (e.g., specific courses taken by this candidate).
4. **Include "Recommended Next Checks"** — what to verify with the candidate directly (e.g., "ask for transcript to confirm specific AI courses taken").
5. **Do not fabricate specific data** (e.g., exact course codes, professor names, enrollment numbers) from general knowledge. If you don't have a source, say so.
6. **Save the report anyway** — a partial report with clear uncertainty markers is more useful than no report.

## Pre-flight: Load this skill before starting

**Before any research action, load this SKILL.md and its references.** The skill contains critical workflow steps, fallback strategies, and anti-bot workarounds that prevent wasted iterations. Do not start browsing without first reviewing the relevant sections.

## Pitfalls

- **Don't confuse university overall rank with CS program rank.** A school ranked #35 overall might have a CS program ranked #11. Always check the CS-specific ranking.
- **Don't stop at the home page.** Navigate down into courses, faculty, and research pages. The surface-level "about" page is marketing material.
- **Don't forget about strategic initiatives.** A school's direction (new AI college, major gifts) tells you about the environment the candidate was immersed in — even if the initiatives are new, they signal culture and funding.
- **Don't limit to just the CS department.** Check if there's a dedicated AI/ML institute, data science school, or cross-departmental AI program.
- **Avoid stating that a tool "does not work"** if it failed due to network/setup — note the successful workaround instead.
- **Rankings sites (US News, QS) may block browser traffic.** Have fallback approaches: Wikipedia summary, CSRankings (direct site), or ShanghaiRanking.

### Chinese University Research Pitfalls (实战教训)

- **❌ 不要只试一个 URL 就放弃。** 交大计算机学院官网 `cs.sjtu.edu.cn` 是动态 JS 渲染页面，`browser_navigate` 可能超时，但 `curl` 可以获取到 HTML。如果 browser 失败，立即用 `curl` 或 `terminal` 尝试获取原始 HTML。
- **❌ 不要假设 "软件学院" 有独立域名。** 交大的软件工程专业历史上属于软件学院，但后来经历了院系合并/调整，现在归属于**计算机学院（网络空间安全学院、密码学院）**。必须先搞清楚当前的组织架构，而不是凭记忆找旧域名。
- **❌ 不要只依赖百度百科。** 百度百科可能没有独立的"软件学院"词条（已被合并），直接跳转到上级学院页面。需要灵活调整搜索策略。
- **❌ 不要忽略招生网 (zs.*)。** 中国大学的招生网 `zs.{university}.edu.cn` 通常有最准确的本科专业列表和录取分数线，且反爬虫防护较弱。这是重要的备选入口。
- **❌ 不要忽略教育部学科评估数据。** 对于中国大学，教育部学科评估（如第五轮学科评估）是衡量专业实力的权威指标，比第三方排名更可靠。应主动搜索 `{大学} {学科} 学科评估`。
- **❌ 不要只查英文名。** 中国大学的专业名称、院系名称应以中文官方名称为准。英文翻译可能不准确或过时。
- **✅ 正确做法：** 先通过学校官网的"院系设置"确认当前组织架构 → 找到目标专业所在的学院 → 再深入该学院的本科/研究生培养页面。如果官网 JS 动态加载，用 `curl` 获取 HTML 后搜索关键词。
- **✅ 正确做法：** 对于院系合并/更名频繁的中国大学，先查 Wikipedia/百度百科了解历史沿革，确认当前归属，再查官方页面。

## References

- 通用 skill: `utilities/windows-file-operations` — Windows 文件操作最佳实践（文件读取优先级、编码处理等）

- `references/source-priority.md` for source ranking and verification rules.
- `references/report-checklist.md` for final quality checks.
- `references/chinese-university-research.md` for tips on researching Chinese universities (anti-bot sites, Baidu Baike fallback, etc.).
- `references/research-troubleshooting.md` for common research pitfalls: Python stdout buffering on Windows, search engine blocking, Baidu Baike snapshot truncation, and terminal output issues.
- `scripts/fetch-reddit-posts.py` — reusable script to fetch student perspectives from a university's subreddit.
- [CSRankings](http://csrankings.org/) — research-oriented CS program rankings by sub-area

