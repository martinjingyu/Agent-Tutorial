# URL Discovery Strategies for University Program Research

## Overview

When researching a university program, you often don't know the exact URL. This reference documents systematic strategies to find the correct page.

## 1. Standard URL Pattern Construction

Many universities follow predictable URL patterns. Try these before searching:

### US Universities

```
# Catalog-based (most common for program details)
catalog.{school}.edu/undergraduate/{college}/{department}/{program}-bs/
guide.{school}.edu/undergraduate/{college}/{department}/{program}-bs/
bulletin.{school}.edu/undergraduate/{college}/{department}/{program}/

# Direct department
www.{school}.edu/academics/{department}/
www.{school}.edu/departments/{department}/
www.{school}.edu/{college}/{department}/

# Admissions
admissions.{school}.edu/academics/{program}/
www.{school}.edu/admissions/undergraduate/majors/{program}/
```

**Examples:**
- `guide.wisc.edu/undergraduate/letters-science/computer-sciences/computer-sciences-bs/`
- `catalog.berkeley.edu/...`
- `bulletin.duke.edu/...`

### Chinese Universities

```
# 招生网（最可靠的本科专业入口）
zs.{school}.edu.cn/
zsb.{school}.edu.cn/

# 院系设置
www.{school}.edu.cn/jgsz/yxsz.htm
www.{school}.edu.cn/xxgk/jgsz.htm

# 本科教育
jwc.{school}.edu.cn/
www.{school}.edu.cn/jyjx/bkjy.htm

# 学院官网
cs.{school}.edu.cn/
sist.{school}.edu.cn/
se.{school}.edu.cn/
```

### UK Universities

```
www.{school}.ac.uk/study/undergraduate/courses/{program}/
www.{school}.ac.uk/subjects/{department}/
```

## 2. Search Engine Strategy

When pattern construction fails, use targeted search queries.

### Browser-based search

Navigate to a search engine and search:

```
site:{school domain} "{program name}" undergraduate
site:{school domain} "{program name}" bachelor
site:{school domain} "{program name}" 本科
site:{school domain} "course catalog" computer science
```

**Example:**
```
site:wisc.edu "Computer Sciences" undergraduate
site:berkeley.edu "Computer Science" BA
```

### For Chinese universities (Baidu/Bing)

```
site:{school}.edu.cn 计算机科学与技术 本科 培养方案
site:{school}.edu.cn 人工智能 专业介绍
{大学名} 计算机学院 官网
```

## 3. Official Catalog / Bulletin Discovery

Many universities have a dedicated catalog system that hosts all program details.

**How to find the catalog:**
1. Navigate to the university's main site
2. Look for links like "Academics" → "Programs A-Z" or "Majors"
3. Search for "catalog" or "bulletin" or "academic programs"
4. The catalog URL often follows patterns like:
   - `catalog.{school}.edu`
   - `guide.{school}.edu`
   - `bulletin.{school}.edu`
   - `programs.{school}.edu`

**Why catalogs are better than department pages:**
- More structured data (requirements, courses, learning outcomes)
- Less marketing fluff
- Often more stable URLs
- Usually not JS-heavy (easier to scrape)

## 4. Wikipedia as a Starting Point

Wikipedia often has the official program URL in the infobox.

```
Wikipedia → "{University}" → "Academics" section → click through to official site
Wikipedia → "{University} {Department}" → external links
```

**Example workflow:**
```
browser_navigate("https://en.wikipedia.org/wiki/University_of_Wisconsin–Madison")
# Scroll to "Academics" or "Organization" section
# Find link to "College of Letters & Science" or "Computer Sciences"
# Click through to official site
```

## 5. Breadcrumb Traversal (Manual Navigation)

When you have a partial URL or know the college but not the program:

1. Navigate to the college/school homepage
2. Look for "Academics", "Programs", "Majors", "Degrees" navigation
3. Find the program in the list
4. Click through

**Example:**
```
browser_navigate("https://www.wisc.edu/")
# Find "Academics" → "Majors" → search/find "Computer Sciences"
# Or navigate directly to college: https://ls.wisc.edu/
# Then "Academics" → "Majors" → "Computer Sciences"
```

## 6. Chinese University Specific: 招生网 (Admissions Site)

For Chinese universities, the **招生网** (admissions website) is often the most reliable source for undergraduate program information.

**Pattern:**
```
zs.{school}.edu.cn → 招生专业 → 专业介绍
zsb.{school}.edu.cn → 本科招生 → 专业目录
```

**Advantages:**
- Less anti-bot protection than the main site
- Contains official program names and codes
- Often has admission scores and requirements
- More stable than department pages

## 7. Fallback: Third-Party Aggregators

If all official sources are unreachable:

- **US:** CollegeBoard, Niche, US News (for basic program facts)
- **China:** 阳光高考 (gaokao.chsi.com.cn), 教育部学科评估
- **Global:** QS, THE subject rankings (for overview only)

**⚠️ Always prefer official sources.** Third-party aggregators are fallbacks only.

## Decision Tree

```
Do you know the exact URL?
├── Yes → browser_navigate(url)
└── No → 
    ├── Is it a US university?
    │   ├── Try catalog/guide/bulletin pattern
    │   ├── Try department pattern
    │   └── Search: site:{school} "{program}"
    ├── Is it a Chinese university?
    │   ├── Try zs.{school}.edu.cn
    │   ├── Try 院系设置 from main site
    │   └── Search: site:{school}.edu.cn {专业名}
    └── Is it a UK/European university?
        ├── Try www.{school}.ac.uk/subjects/{dept}
        └── Search: site:{school}.ac.uk "{program}"
```
