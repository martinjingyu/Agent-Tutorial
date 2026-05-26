# Link Deep Research Checklists

## GitHub Profile 检查清单

- [ ] 用户名是否与简历一致
- [ ] 总仓库数（含 fork vs 原创比例）
- [ ] Followers / Following 数量
- [ ] 过去一年的贡献数（点开 contribution graph 看具体分布）
- [ ] Bio / 简介信息
- [ ] Popular repositories 列表及描述
- [ ] Achievements 徽章

## GitHub Repo 深度审查清单

### S1: 仓库基本情况
- [ ] 仓库是否存在（注意：可能被重命名/删除）
- [ ] 是原创还是 fork（**原创项目才有说服力**）
- [ ] Star / Fork 数量
- [ ] Commit 数量（>50 一般说明有实际投入）
- [ ] 最近更新时间（活跃度指标）

### S2: 目录结构
- [ ] 目录结构是否合理（不只是一两个文件）
- [ ] 是否有 src/、tests/、config/ 等标准结构
- [ ] 是否有 requirements.txt / pyproject.toml / package.json

### S3: 实际代码审查
使用 `browser_navigate` 到 raw.githubusercontent.com 或直接浏览代码文件：
- [ ] 导入的库是否与项目描述匹配
- [ ] 代码是否真正实现了声称的功能
- [ ] 是否有 type hints / 类型注解
- [ ] 错误处理是否完善（try/except、边界检查）
- [ ] 代码风格和专业程度
- **关键信号**: 一个说做了 LLM 项目的 repo，实际代码应该用到 transformers/torch/vllm 等库

### S4: Commit 历史
- [ ] Commit message 质量（专业描述 vs 随意"update"/"fix"）
- [ ] 是否有多人协作（committer 信息）
- [ ] Commit 频率（一次性提交几百行 vs 渐进式开发）

### S5: Fork 差异对比
使用 compare URL:
```
https://github.com/ORIGINAL_OWNER/REPO/compare/main...CANDIDATE_USERNAME:REPO:main
```
- [ ] 有多少个 own commits
- [ ] 实际改了哪些文件、多少行代码
- [ ] 是否只是微调（README 修改、配置调整）还是真的有功能贡献
- **重要**: 简历说"开发了 X 系统"但代码只改了 README → **红旗**

### S6: README 质量
- [ ] 是否有项目描述、安装说明、使用示例
- [ ] 是否有架构图或设计文档
- [ ] 是否只是 placeholder

## 论文/出版物 深度审查清单

### 基本信息
- [ ] 页面是否存在
- [ ] 标题是否匹配简历描述
- [ ] 作者列表中是否有候选人（**第几作者** — 第1>第2>第3+）
- [ ] 机构是否与简历一致
- [ ] 发表时间/会议/期刊级别
- [ ] 是否 peer-reviewed
- [ ] 可下载 PDF / BibTeX

### PDF 深度分析
- [ ] 下载 PDF（通过 raw URL 或 curl）
- [ ] 提取全文文本
- [ ] 候选人负责什么模块？
- [ ] 论文描述是否与简历一致？
- [ ] 论文描述的系统与 GitHub 代码是否对应？
- [ ] 论文的引用量/影响力（如有）

## LinkedIn 检查清单

- [ ] 能否访问（可能需要登录）
- [ ] 姓名、学校、职位是否与简历一致
- [ ] 头像是否存在
- [ ] 联系方式（邮箱）是否与简历一致

## Kaggle 检查清单

- [ ] Writeup 是否存在
- [ ] 竞赛名称是否匹配
- [ ] 阅读完整内容 — 是否有深度技术分析
- [ ] 是否提及代码仓库链接（验证代码和 writeup 的对应关系）
- [ ] Findings/结果文件是否存在、标准是否规范

## 交叉验证清单

- [ ] GitHub 项目与论文描述是否一致？
- [ ] 项目时间线是否合理（commit 时间 vs 简历时间）？
- [ ] 简历声称的技能是否在代码/论文中实际体现？
- [ ] 不同链接之间的信息是否有矛盾？
- [ ] LinkedIn 教育经历与简历是否一致？
