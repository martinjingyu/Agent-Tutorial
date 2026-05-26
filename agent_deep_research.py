"""
Python version of the Agent Deep Research flow from open-deep-research.

Flow:
1. Optimize the user's research topic into a search query and report prompt.
2. Search the web with Google Custom Search, Bing Search, or mock results.
3. Ask the model to rank the search results.
4. Select diverse high-ranking sources.
5. Fetch source content through Jina Reader.
6. Ask the model to generate a structured research report.

This file is intentionally compact and explicit so it can be used as a tutorial.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Iterable


DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "mock").lower()
MAX_RESULTS = int(os.getenv("SEARCH_RESULTS_PER_PAGE", "10"))
MAX_SELECTABLE_RESULTS = int(os.getenv("MAX_SELECTABLE_RESULTS", "3"))


@dataclass
class SearchResult:
    id: str
    url: str
    title: str
    snippet: str
    score: float = 0.0


@dataclass
class Article:
    url: str
    title: str
    content: str


def request_json(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    data = None
    request_headers = headers or {}

    if body is not None:
        data = json.dumps(body).encode("utf-8")
        request_headers = {
            "Content-Type": "application/json",
            **request_headers,
        }

    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers=request_headers,
    )

    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def request_text(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: int = 60,
) -> str:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def extract_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from a model response."""
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"Model response did not contain JSON:\n{text}")

    return json.loads(match.group(0))


def generate_with_openai(prompt: str, model: str = DEFAULT_MODEL) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Set it or run with --mock-model."
        )

    response = request_json(
        "https://api.openai.com/v1/chat/completions",
        method="POST",
        headers={"Authorization": f"Bearer {api_key}"},
        body={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        },
    )

    return response["choices"][0]["message"]["content"]


def generate_mock(prompt: str) -> str:
    """Deterministic model replacement for learning the pipeline offline."""
    if "optimizing a research topic" in prompt:
        topic = re.search(r'Given this research topic: "(.*?)"', prompt, re.DOTALL)
        topic_text = topic.group(1) if topic else "test research topic"
        return json.dumps(
            {
                "query": topic_text,
                "optimizedPrompt": f"Analyze {topic_text} with emphasis on key facts, tradeoffs, and implications.",
                "explanation": "Mock planner keeps the original topic as the search query.",
                "suggestedStructure": [
                    "Background",
                    "Current evidence",
                    "Implications",
                ],
            },
            ensure_ascii=False,
        )

    if "analyzing search results for relevance" in prompt:
        urls = re.findall(r"URL: (.+)", prompt)
        return json.dumps(
            {
                "rankings": [
                    {
                        "url": url.strip(),
                        "score": max(0.95 - index * 0.15, 0.2),
                        "reasoning": "Mock ranking based on original order.",
                    }
                    for index, url in enumerate(urls)
                ],
                "analysis": "Mock analysis ranked earlier results higher.",
            },
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "title": "Mock Deep Research Report",
            "summary": "This is a mock report generated without calling an external model.",
            "sections": [
                {
                    "title": "What happened in the pipeline",
                    "content": "The agent optimized the prompt, searched for sources, ranked them, fetched content, and synthesized a report.",
                },
                {
                    "title": "How to make it real",
                    "content": "Set OPENAI_API_KEY and a real search provider such as Google or Bing, then run without --mock-model.",
                },
            ],
            "usedSources": [1],
        },
        ensure_ascii=False,
    )


def generate(prompt: str, *, mock_model: bool, model: str = DEFAULT_MODEL) -> str:
    if mock_model:
        return generate_mock(prompt)
    return generate_with_openai(prompt, model=model)


def optimize_research(topic: str, *, mock_model: bool, model: str) -> dict[str, Any]:
    prompt = f"""You are a research assistant tasked with optimizing a research topic into an effective search query.

Given this research topic: "{topic}"

Your task is to:
1. Generate ONE optimized search query that will help gather comprehensive information
2. Create an optimized research prompt that will guide the final report generation
3. Suggest a logical structure for organizing the research

Return JSON:
{{
  "query": "the optimized search query",
  "optimizedPrompt": "the refined research prompt",
  "explanation": "brief explanation",
  "suggestedStructure": ["aspect 1", "aspect 2", "aspect 3"]
}}
"""
    return extract_json(generate(prompt, mock_model=mock_model, model=model))


def search_mock(query: str) -> list[SearchResult]:
    return [
        SearchResult(
            id="mock-1",
            url="https://example.com/background",
            title=f"Background on {query}",
            snippet="A broad overview of the topic, major terms, and context.",
        ),
        SearchResult(
            id="mock-2",
            url="https://example.com/evidence",
            title=f"Evidence and data about {query}",
            snippet="A source with statistics, examples, and supporting evidence.",
        ),
        SearchResult(
            id="mock-3",
            url="https://example.org/analysis",
            title=f"Expert analysis of {query}",
            snippet="A different domain with interpretation and implications.",
        ),
    ]


def search_google(query: str) -> list[SearchResult]:
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    cx = os.getenv("GOOGLE_SEARCH_CX")
    if not api_key or not cx:
        raise RuntimeError("GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_CX are required.")

    params = urllib.parse.urlencode(
        {
            "q": query,
            "key": api_key,
            "cx": cx,
            "num": MAX_RESULTS,
            "safe": "active",
        }
    )
    data = request_json(f"https://customsearch.googleapis.com/customsearch/v1?{params}")

    results = []
    for index, item in enumerate(data.get("items", [])):
        results.append(
            SearchResult(
                id=item.get("cacheId") or item.get("link") or str(index),
                url=item["link"],
                title=item.get("title", "Untitled"),
                snippet=item.get("snippet", ""),
            )
        )
    return results


def search_bing(query: str) -> list[SearchResult]:
    api_key = os.getenv("AZURE_SUB_KEY")
    if not api_key:
        raise RuntimeError("AZURE_SUB_KEY is required.")

    params = urllib.parse.urlencode(
        {
            "q": query,
            "count": MAX_RESULTS,
            "mkt": "en-US",
            "safeSearch": "moderate",
            "textFormat": "HTML",
            "textDecorations": "true",
        }
    )
    data = request_json(
        f"https://api.bing.microsoft.com/v7.0/search?{params}",
        headers={"Ocp-Apim-Subscription-Key": api_key, "Accept-Language": "en-US"},
    )

    return [
        SearchResult(
            id=item.get("id") or item["url"],
            url=item["url"],
            title=item.get("name", "Untitled"),
            snippet=item.get("snippet", ""),
        )
        for item in data.get("webPages", {}).get("value", [])
    ]


def search_web(query: str, provider: str) -> list[SearchResult]:
    if provider == "mock":
        return search_mock(query)
    if provider == "google":
        return search_google(query)
    if provider == "bing":
        return search_bing(query)
    raise ValueError(f"Unknown search provider: {provider}")


def analyze_results(
    prompt_text: str,
    results: list[SearchResult],
    *,
    mock_model: bool,
    model: str,
) -> dict[str, Any]:
    results_text = "\n".join(
        f"""
Result {index + 1}:
Title: {result.title}
URL: {result.url}
Snippet: {result.snippet}
---"""
        for index, result in enumerate(results)
    )

    prompt = f"""You are a research assistant tasked with analyzing search results for relevance to a research topic.

Research Topic: "{prompt_text}"

Analyze these search results and score them from 0 to 1 based on relevance, quality, credibility, and uniqueness.

{results_text}

Return JSON:
{{
  "rankings": [
    {{"url": "result url", "score": 0.85, "reasoning": "brief reason"}}
  ],
  "analysis": "brief overall analysis"
}}
"""
    return extract_json(generate(prompt, mock_model=mock_model, model=model))


def apply_rankings(
    results: list[SearchResult],
    rankings: Iterable[dict[str, Any]],
) -> list[SearchResult]:
    score_by_url = {
        str(ranking.get("url")): float(ranking.get("score", 0))
        for ranking in rankings
    }
    ranked = [
        SearchResult(
            id=result.id,
            url=result.url,
            title=result.title,
            snippet=result.snippet,
            score=score_by_url.get(result.url, 0.0),
        )
        for result in results
    ]
    return sorted(ranked, key=lambda item: item.score, reverse=True)


def select_diverse_sources(results: list[SearchResult]) -> list[SearchResult]:
    selected: list[SearchResult] = []
    selected_domains: set[str] = set()

    for result in results:
        domain = urllib.parse.urlparse(result.url).hostname or result.url
        if domain in selected_domains:
            continue
        if result.score <= 0.5:
            continue
        selected.append(result)
        selected_domains.add(domain)
        if len(selected) >= MAX_SELECTABLE_RESULTS:
            break

    return selected or results[:MAX_SELECTABLE_RESULTS]


def fetch_content(result: SearchResult, *, mock_content: bool) -> Article:
    if mock_content or result.url.startswith("https://example."):
        return Article(
            url=result.url,
            title=result.title,
            content=f"{result.title}\n\n{result.snippet}\n\nMock full text for tutorial purposes.",
        )

    jina_url = "https://r.jina.ai/" + urllib.parse.quote(result.url, safe="")
    try:
        content = request_text(jina_url, timeout=60)
        return Article(url=result.url, title=result.title, content=content)
    except urllib.error.URLError:
        return Article(url=result.url, title=result.title, content=result.snippet)


def generate_report(
    articles: list[Article],
    sources: list[SearchResult],
    prompt_text: str,
    *,
    mock_model: bool,
    model: str,
) -> dict[str, Any]:
    articles_text = "\n".join(
        f"""
[{index + 1}] Title: {article.title}
URL: {article.url}
Content: {article.content}
---"""
        for index, article in enumerate(articles)
    )

    prompt = f"""You are a research assistant tasked with creating a comprehensive report based on multiple sources.
The report should specifically address this request: "{prompt_text}"

Source articles:
{articles_text}

Return JSON:
{{
  "title": "Report title",
  "summary": "Executive summary",
  "sections": [
    {{"title": "Section title", "content": "Markdown content"}}
  ],
  "usedSources": [1, 2]
}}
"""

    report = extract_json(generate(prompt, mock_model=mock_model, model=model))
    report["sources"] = [
        {"id": source.id, "url": source.url, "name": source.title}
        for source in sources
    ]
    return report


def run_agent(topic: str, *, provider: str, mock_model: bool, mock_content: bool, model: str) -> dict[str, Any]:
    print("[1/5] Optimizing research topic...")
    plan = optimize_research(topic, mock_model=mock_model, model=model)
    query = plan["query"]
    optimized_prompt = plan["optimizedPrompt"]
    print(f"      query: {query}")
    print(f"      strategy: {plan.get('explanation', '')}")

    print("[2/5] Searching web...")
    search_results = search_web(query, provider)
    print(f"      found {len(search_results)} results")

    print("[3/5] Ranking search results...")
    analysis = analyze_results(
        optimized_prompt,
        search_results,
        mock_model=mock_model,
        model=model,
    )
    ranked_results = apply_rankings(search_results, analysis.get("rankings", []))
    selected = select_diverse_sources(ranked_results)
    print(f"      selected {len(selected)} sources")

    print("[4/5] Fetching source content...")
    articles = [fetch_content(result, mock_content=mock_content) for result in selected]

    print("[5/5] Generating report...")
    report = generate_report(
        articles,
        selected,
        optimized_prompt,
        mock_model=mock_model,
        model=model,
    )
    return {
        "plan": plan,
        "analysis": analysis,
        "selectedSources": [source.__dict__ for source in selected],
        "report": report,
    }


def save_report(result: dict[str, Any], output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent Deep Research tutorial CLI")
    parser.add_argument("topic", help="Research topic, wrapped in quotes")
    parser.add_argument(
        "--provider",
        default=SEARCH_PROVIDER,
        choices=["mock", "google", "bing"],
        help="Search provider. Default reads SEARCH_PROVIDER or uses mock.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="OpenAI model name. Ignored when --mock-model is used.",
    )
    parser.add_argument(
        "--mock-model",
        action="store_true",
        help="Use deterministic fake model responses instead of OpenAI.",
    )
    parser.add_argument(
        "--mock-content",
        action="store_true",
        help="Do not call Jina Reader; use snippets as mock content.",
    )
    parser.add_argument(
        "--output",
        default=f"deep_research_{int(time.time())}.json",
        help="Path to write the full JSON result.",
    )

    args = parser.parse_args()

    try:
        result = run_agent(
            args.topic,
            provider=args.provider,
            mock_model=args.mock_model,
            mock_content=args.mock_content,
            model=args.model,
        )
        save_report(result, args.output)
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    report = result["report"]
    print()
    print("Done.")
    print(f"Title: {report.get('title')}")
    print(f"Output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
