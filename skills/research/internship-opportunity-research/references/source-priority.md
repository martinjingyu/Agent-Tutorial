# Source Priority for Internship Research

When researching internship positions, prioritize sources in this order:

## Tier 1: Official Company Career Pages & APIs (Always Preferred)

- **Company career site** (e.g., `careers.google.com`, `amazon.jobs`, `metacareers.com`)
- **Official company API endpoints** (e.g., Google Careers API: `careers.google.com/api/v3/search/?q=intern&degree=BACHELORS,MASTERS&employment_type=INTERN`)
- **Official job search portal** (e.g., `google.com/about/careers/applications/`)

## Tier 2: Official Company Blog / Announcements

- Company engineering blogs announcing internship programs
- Official LinkedIn posts from company recruiting pages

## Tier 3: Aggregator Sites (Use with Caution)

- **Avoid**: huzzle.app, scholarshiptab.com, indeed.com (non-official, often stale/incomplete)
- **Use only for discovery**: LinkedIn Jobs, Glassdoor (to find position names, then verify on official site)

## Why Tier 1 Matters

- Aggregator sites often have outdated or incorrect application windows
- Official pages show exact requirements, locations, and current status (Open/Coming Soon/Closed)
- APIs provide structured data that can be parsed reliably

## Common Anti-Patterns to Avoid

1. ❌ Navigating to a third-party aggregator (huzzle.app) as the first action
2. ❌ Clicking links from search results without verifying the domain
3. ❌ Using stale browser refs from a previous snapshot — always call `browser_snapshot` before `browser_click`
4. ❌ Scrolling on pages that don't need scrolling (causes CDP timeout)
