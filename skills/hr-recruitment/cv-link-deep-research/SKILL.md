---
name: cv-link-deep-research
category: hr-recruitment
description: 接收结构化 CV JSON，提取其中的所有链接（GitHub、LinkedIn、论文、项目等），逐一进行浏览器深度调研，验证内容真实性并评估候选人能力水平，输出结构化验证报告。
---

# CV Link Deep Research（简历链接深度调研）

## 何时使用

当需要基于一份结构化的 CV JSON 文件，对候选人简历中的每个外部链接进行深度验证时使用。适用于：

- 招聘关键岗位前的背景核实
- 验证候选人声称的项目/成果是否真实存在
- 判断候选人的实际技术深度 vs 简历描述
- 面试前的准备工作，识别需要重点追问的方向

## 输入格式

本 skill 接收一个结构化的 JSON 文件，来自简历解析 pipeline 的输出。实际格式如下：

```json
{
  "candidate": {
    "name": "候选人姓名",
    "links": [
      {
        "type": "linkedin" | "github" | "other",
        "url": "https://...",
        "label": "显示名称",
        "source_span": "原文片段"
      }
    ]
  },
  "education": [ ... ],
  "work_experience": [ ... ],
  "projects": [
    {
      "name": "项目名",
      "description": "项目描述",
      "contributions": ["贡献1", "贡献2"],
      "tech_stack": ["技术1", "技术2"],
      "links": ["https://...", "https://..."]
    }
  ],
  "publications_or_reports": [
    {
      "title": "论文标题",
      "venue_or_context": "发表会议/期刊",
      "link": "https://...",
      "peer_reviewed": false
    }
  ]
}
```

### 链接提取规则

链接分布在 JSON 的多个位置，需要全部提取：

| 位置 | 字段路径 | 类型推断 |
|------|---------|---------|
| 顶层 links | `candidate.links[].url` | 按 `type` 字段（linkedin/github/other） |
| 项目 links | `projects[].links[]` | 按 URL 模式推断（github.com → github, kaggle.com → kaggle） |
| 出版物 link | `publications_or_reports[].link` | paper |
| 邮件 | `candidate.emails[]` | 跳过（不作为调研目标） |

### 链接去重

同一个 URL 可能出现在多个位置（如 GitHub repo 同时在 `candidate.links` 和 `projects[].links` 中出现）。去重规则：
- 以 URL 为 key 去重
- 保留所有关联的上下文描述（项目描述、贡献列表等），用于后续对比验证

## 工作流程

### Step 1: 读取并解析 CV JSON

- 使用 `read_file` 读取 CV JSON 文件
- 从以下位置提取所有链接：
  1. `candidate.links[]` — 顶层链接（linkedin, github, email）
  2. `projects[].links[]` — 项目关联链接（GitHub repo, Kaggle, 等）
  3. `publications_or_reports[].link` — 论文/报告链接
- 按 URL 去重，合并上下文描述
- 跳过 `mailto:` 链接（不作为调研目标）
- 为每个链接关联其来源上下文（项目描述、贡献列表、技术栈），用于后续对比验证

### Step 2: 按优先级排序链接

调研顺序（优先级从高到低）：

1. **GitHub** — 最能反映实际技术能力
2. **论文/出版物** — 验证学术成果真实性
3. **LinkedIn** — 验证教育/工作经历
4. **Kaggle** — 验证竞赛经历
5. **个人网站/作品集** — 综合展示
6. **其他项目链接** — 按需验证

### Step 3: 逐一深度调研（核心！）

对每个链接，使用 `browser_navigate` 访问并记录。**不仅要看页面是否存在，还要深入内容本身。你的目标是找出任何可疑之处，而不是验证简历说的都是对的。**

详细的检查清单见 `references/link-checklists.md`。

#### 核心原则：必须读实际代码

**不要只看 README！README 可以写得天花乱坠，代码才是真相。**

对于每个 GitHub 仓库，必须：
1. 浏览目录结构 → 确认项目不是空壳
2. **读取至少 3-5 个核心代码文件**（用 `browser_navigate` 到 raw.githubusercontent.com）
3. 检查 import/依赖 → 确认技术栈与描述匹配
4. 检查代码是否真正实现了声称的功能
5. 检查 commit 历史 → 频率、message 质量、时间线

#### GitHub 深度调研要点

1. **Profile 页** — 用户名、仓库数、followers、贡献图、bio、**账号创建时间**
2. **仓库列表** — 原创 vs fork 比例、star 数、最近更新
3. **关键仓库深度审查**：
   - 目录结构是否合理
   - **读取实际代码文件**（raw.githubusercontent.com）— 必须读！
   - 检查 commit 历史（频率、message 质量、时间分布）
   - 如果是 fork，**对比与上游的差异**（用 compare URL）
   - 检查 README 质量（是否过度包装）
   - **检测可疑模式**：AI 生成代码、复制粘贴、空壳项目
4. **与简历描述的对比** — 简历说的和实际代码是否一致

#### 论文/出版物深度调研要点

1. **页面是否存在** — 标题、作者列表、发表时间/会议
2. **作者排名** — 第几作者（第1 > 第2 > 第3+）
3. **下载 PDF 并阅读** — 候选人负责什么模块？与简历描述是否一致？
4. **论文与代码的对应关系** — 论文描述的系统是否有对应 GitHub 仓库？
5. **区分论文级别**：Challenge proceedings ≠ 顶会论文

#### LinkedIn 调研要点

1. **个人资料是否存在** — 姓名、头像、教育、工作经历
2. **与简历的一致性** — 是否有矛盾或夸大
3. **教育经历时间线** — 是否与简历一致
4. **联系方式** — 是否与简历一致

#### Kaggle 调研要点

1. **竞赛页面** — 竞赛名称、排名、writeup
2. **Writeup 内容** — 是否有深度技术分析
3. **与代码的对应关系** — writeup 中引用的代码仓库是否真实
4. **排名真实性** — 简历说的排名是否与实际一致

### Step 4: 交叉验证（核心！）

**这是最重要的步骤。** 不要只看单个链接，要把所有信息放在一起对比：

- **跨链接一致性检查**：GitHub 上的项目是否与论文/简历描述一致？
- **时间线检查**：项目时间、论文发表时间、GitHub commit 时间是否合理？
- **技能匹配检查**：简历声称的技能是否在代码/论文中实际体现？
- **Contributor 检查**：声称团队合作的项目，GitHub 上是否有其他 contributor？
- **"过度包装"检测**：README 是否写得比实际代码好得多？
- **AI 生成代码检测**：代码是否有大量注释、命名不一致、模板化等 AI 生成特征？

### Step 5: 输出结构化报告

使用 `templates/link-verification-report.md` 生成报告。

**存储路径规则（重要！必须遵守）**：
- **所有报告文件必须统一保存在候选人专属文件夹下**，路径为 `candidates/{候选人姓名}/`
- 示例：`candidates/Lei Shen/link-verification.md`
- **绝对不要** 将候选人报告保存到 `reports/` 目录下。`reports/` 目录仅用于学校/专业调研报告（由 `university-program-research` skill 生成），不用于候选人链接验证报告。
- 如果 `candidates/` 目录不存在，先创建它。
- 使用 `write_file` 写入时，路径必须包含 `candidates/{候选人姓名}/` 前缀。

报告包含：
- 链接清单及状态总览
- 每个链接的详细分析
- 交叉验证发现
- 综合判断（可信度评分）
- 面试建议（重点追问方向）

## 红旗/绿旗信号

### 绿旗（加分项）
- 原创项目有真实代码、多 commits、结构清晰
- 论文/出版物真实存在且候选人是有实质性贡献的作者（前 3 位）
- GitHub 活跃度高（近期有更新，渐进式 commit 历史）
- 项目 README 详细、有架构说明
- 代码质量高（类型注解、错误处理、测试）
- 跨链接信息一致
- Commit 历史自然（渐进式开发，message 有实质内容）
- 有测试代码（单元测试、集成测试）

### 红旗（严重警告 — 必须标注）
- 链接 404 或无法访问
- 仓库是空仓库或只有 README
- 大部分项目是 fork 且无个人贡献
- Fork 项目却声称"开发了 X"（没有明确标注是 fork）
- Commit message 质量极差（"update"/"fix"/拼写错误）
- 简历声称的 repo 名与实际不一致
- 论文作者列表中无候选人
- 简历描述与实际代码差距过大
- 跨链接信息矛盾
- **代码看起来像 AI 生成的**（过度注释、命名不一致、模板化）
- **所有 commit 集中在几天内**（一次性提交大量代码 → 可能是复制粘贴）
- **代码与描述的技术栈不匹配**（说用了 PyTorch 但代码里只有 numpy）
- **硬编码 API key / token 在代码里**
- **README 过度包装但代码空洞**（大量 emoji、花哨格式、但只有几个文件）
- **声称团队项目但 GitHub 上只有候选人一个人 commit**
- **账号创建时间晚于简历声称的项目开始时间**

### 黄旗（需追问 — 不一定有问题但需要解释）
- 仓库被重命名（可能合理，需确认原因）
- Fork 项目但声称是自己的（需面试追问具体贡献）
- 项目描述模糊
- 贡献量低但声称大项目
- 代码有基础功能但缺少工程化（无测试、无错误处理）
- 项目最后更新时间较早（可能合理，但需确认是否已停止维护）
- 依赖列表看起来"堆砌"（为了显得专业而加了很多不必要的依赖）

## 注意事项

1. **不要止于表面** — 访问 URL 说"页面存在"是不够的，必须深入内容。**README 可以造假，代码不会。**
2. **区分 fork 和原创** — 用 compare URL 查看实际贡献
3. **404 不一定是造假** — 可能是 private repo、改名、或临时故障
4. **GitHub 贡献数低不一定代表能力差** — 学生可能有多个账号
5. **论文/报告级别区分** — "Proceedings of a Challenge" ≠ 顶会论文。Challenge proceedings 需额外验证：竞赛页面、writeup、代码仓库三者交叉验证
6. **时间敏感性** — 验证结果在发布时有效，页面可能后续变更
7. **LinkedIn 可能需登录** — 部分地区需要登录才能查看完整资料
8. **仓库名不一致** — 简历中的链接与实际仓库名可能略有差异（如大小写、连字符），这通常是重命名导致，不一定是造假。但需在报告中标注并确认内容一致
9. **不要假设"好学校 = 好候选人"** — 名校生也可能造假。必须基于代码和事实判断，而不是学校名气
10. **"完美"项目最可疑** — 如果所有项目都 README 完美、代码整洁、但 commit 历史异常（1-2 次提交），很可能是从别处复制后改名的

## References

- `references/link-checklists.md` — 各类型链接的详细检查清单
- `templates/link-verification-report.md` — 结构化报告模板
- 通用 skill: `utilities/windows-file-operations` — Windows 文件操作最佳实践（文件读取优先级、编码处理等）
