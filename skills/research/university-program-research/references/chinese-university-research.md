# Chinese University Research Tips

## Anti-Bot / Anti-Scraping Protection

Many Chinese university websites (e.g., `.edu.cn`, `.szu.edu.cn`) deploy strong anti-bot protection including:
- Cloudflare challenges
- Custom JavaScript-based verification (e.g., `$_ts` tokens)
- IP-based rate limiting
- CAPTCHA gateways

### Workarounds

1. **Baidu Baike (百度百科)** — Often the best fallback for Chinese university facts. It is generally well-maintained for major universities and includes:
   - History and founding details
   - Faculty counts and notable professors
   - Department/school structure
   - Rankings and achievements
   - Notable alumni
   - URL pattern: `https://baike.baidu.com/item/{大学名称}` or `https://baike.baidu.com/item/{大学名称}{学院名称}`

2. **Wikipedia (中文维基百科)** — Good for overview, history, and organizational structure. May be blocked in mainland China but accessible from outside.

3. **`curl` via terminal** — Can sometimes bypass browser-based anti-bot checks. Use with `-L` (follow redirects) and a realistic `User-Agent` header. Example:
   ```
   curl -s -L --max-time 15 "https://csse.szu.edu.cn/" -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
   ```
   Note: This may still fail if the site uses JS-based challenge tokens.

4. **Official admissions sites** — Often have less aggressive protection than department pages. Try `zs.{university}.edu.cn` (招生网) as an alternative entry point.

## Source Reliability for Chinese Universities

| Source | Reliability | Notes |
|--------|-------------|-------|
| Official `.edu.cn` site | ★★★★★ | Best when accessible |
| Baidu Baike | ★★★★☆ | Generally reliable for basic facts; cross-check dates |
| Chinese Wikipedia | ★★★★☆ | Good for history and structure |
| Ministry of Education (moe.gov.cn) | ★★★★★ | For accreditation and program listings |
| University admissions site (zs.*) | ★★★★★ | For分数线 and招生计划 |

## Key Data Points to Collect

When researching Chinese university programs, prioritize:

- **历史沿革** (History) — Who founded/援建 the program? When was the school/department established?
- **学科评估** (Discipline Evaluation) — Ministry of Education ranking (e.g., 第五轮学科评估)
- **一流专业** (First-class Majors) — 国家级/省级一流本科专业建设点
- **师资队伍** (Faculty) — Number of professors, 院士 (academicians), 国家级人才
- **科研平台** (Research Platforms) — 国家重点实验室, 工程实验室, etc.
- **校企合作** (Industry Partnerships) — Notable合作企业 like 腾讯, 华为, 百度
- **知名校友** (Notable Alumni) — Especially important for Chinese university reputation
- **录取分数线** (Admission Scores) — Usually on the admissions website

## 实战流程（针对中国大学）

### 第一步：确定当前组织架构
中国大学频繁进行院系合并/更名，不要凭记忆找专业。正确做法：

1. 访问学校官网 `www.{university}.edu.cn` → 找到"院系设置"
2. 确认目标专业当前归属于哪个学院
3. 再进入该学院的官网

> 例：上海交通大学"软件工程"专业，历史上属于软件学院，但现已并入**计算机学院（网络空间安全学院、密码学院）**。如果直接搜"软件学院"会找不到。

### 第二步：多通道获取信息

按优先级尝试以下通道：

| 优先级 | 通道 | 方法 | 适用场景 |
|--------|------|------|----------|
| 1 | 学院官网 | `browser_navigate` → 如果超时/白屏，立即用 `curl` 获取 HTML | 官网可访问时 |
| 2 | `curl` 获取 HTML | `curl -s -L --max-time 15 "URL" -H "User-Agent: ..." > file.html` | 官网有 JS 动态加载/反爬 |
| 3 | 招生网 | `zs.{university}.edu.cn` | 本科专业列表、录取分数线 |
| 4 | 百度百科 | `baike.baidu.com/item/{大学名称}{学院名称}` | 历史沿革、组织架构概览 |
| 5 | Wikipedia | `en.wikipedia.org/wiki/{University}` | 国际排名、历史背景 |
| 6 | 教育部学科评估 | 搜索 `{大学} {学科} 学科评估` | 权威专业排名 |

### 第三步：从 HTML 中提取关键信息

当用 `curl` 获取到 HTML 后：

1. 先用 `python -c "print(open('file.html','r',encoding='utf-8',errors='replace').read()[:2000])"` 查看页面结构
2. 用正则或搜索关键词定位目标内容
3. 注意：很多中国大学网站是动态 JS 渲染，`curl` 获取的 HTML 可能不包含正文内容，此时需要找其他入口

### 第四步：应对动态 JS 渲染页面

如果 `curl` 获取的 HTML 没有正文（只有框架代码）：

- 尝试找该网站的静态版本或归档页面
- 尝试招生网 `zs.*` 作为替代
- 尝试百度百科获取基本事实
- 尝试教育部阳光高考网站 `gaokao.chsi.com.cn` 获取专业信息
