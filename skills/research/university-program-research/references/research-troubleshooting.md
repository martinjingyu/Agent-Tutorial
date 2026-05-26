# Research Troubleshooting Reference

## Python stdout on Windows

When running `python -c "..."` in the terminal, stdout may be buffered and not appear before the process exits.

**Symptoms:** The command succeeds (returncode 0) but stdout is empty even though the code should print output.

**Fix:** Use the `-u` (unbuffered) flag:
```bash
python -u -c "print('hello')"
```

**Alternative:** Use `sys.stdout.flush()` after prints, or redirect stderr to stdout with `2>&1`.

## Python stdout encoding on Windows (GBK issue)

When a Python script writes UTF-8 output (e.g., Chinese characters, emoji, special Unicode) to stdout, the agent's terminal tool may fail with `UnicodeDecodeError: 'gbk' codec can't decode byte`.

**Symptoms:** `TypeError: 'NoneType' object is not subscriptable` when accessing `result.stdout`, or a `UnicodeDecodeError` traceback in the subprocess reader thread. The script itself runs fine but the agent cannot capture its output.

**Root cause:** The agent's terminal tool captures stdout using the system default encoding (GBK on Chinese Windows), which cannot decode all UTF-8 bytes.

**Best fix — support file output in scripts:** Add an optional output file argument to your script. When provided, write JSON/text to a file instead of stdout. The agent can then use `read_file()` to inspect the result.

```python
# In your script:
output_file = sys.argv[4] if len(sys.argv) > 4 else None
# ...
if output_file:
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output)
else:
    # fallback to stdout
    print(output)
```

Then from the agent:
```bash
python script.py arg1 arg2 arg3 output.json
# Then:
read_file("output.json")
```

**Less robust alternatives:**
- `sys.stdout.buffer.write(output.encode("utf-8"))` — still fails because the agent's subprocess capture decodes with GBK.
- `sys.stdout.reconfigure(encoding="utf-8")` — only works if the underlying stream supports it; may fail when stdout is piped/redirected.

## Search Engine Blocking

Google, DuckDuckGo, and Baidu may present CAPTCHA/blocking pages to automated browsers.

**Symptoms:** Browser navigates to a "sorry" page, CAPTCHA page, or a page with only a "Why did this happen?" link.

**Fallback strategy (in order):**

1. **Bing** (`bing.com`) — Usually the least aggressive with blocking. Try `https://www.bing.com/search?q={query}`.
2. **Baidu** (`baidu.com`) — May work for Chinese queries but also has CAPTCHA.
3. **Direct site navigation** — Skip search engines entirely. Navigate directly to the target site if you know the URL.
4. **Baidu Baike** — For Chinese university facts, navigate directly to `https://baike.baidu.com/item/{name}`.
5. **Wikipedia** — For general facts, navigate directly to `https://en.wikipedia.org/wiki/{name}`.

## Baidu Baike Snapshot Truncation

Baidu Baike pages are very long. `browser_snapshot({"full": true})` may still truncate.

**Workaround:**
1. Scroll down the page in chunks before taking a snapshot.
2. Use `browser_scroll({"direction": "down"})` multiple times.
3. After scrolling, take a snapshot to see more content.
4. Alternatively, use terminal/curl to fetch the page HTML and parse it locally.

## Terminal Command Output Not Showing

If a terminal command succeeds but produces no visible output:

1. Check if the command uses `python` or `python3` — on Windows, `python` is typically correct, `python3` may fail with error 9009.
2. Use `python -u` for unbuffered output.
3. Add `2>&1` to merge stderr into stdout.
4. Test with a minimal command first: `python -u -c "print('test')"`.

## Chinese University Subdomain Blocking

Many Chinese university subdomains (e.g., `sjsjxy.gdou.edu.cn`, `cs.sjtu.edu.cn`) may be inaccessible from external networks or return `ERR_CONNECTION_CLOSED`.

**Symptoms:** `browser_navigate` fails with `ERR_CONNECTION_CLOSED` or timeout.

**Fallback strategy (in order):**

1. **招生网** (`zs.{university}.edu.cn`) — Usually has the most reliable access and contains college/department listings and admission info.
2. **Baidu Baike** — Navigate directly to `https://baike.baidu.com/item/{大学名}` for basic organizational structure (院系设置).
3. **University main site** (`www.{university}.edu.cn`) — Try `xxgk/zzjg.htm` or `xxgk/xxxz.htm` paths for organizational structure pages.
4. **Accept incomplete data** — If the department site is blocked, clearly mark all curriculum/course info as "inferred from general knowledge" in the report, and recommend verifying with the candidate directly.

## `read_file` for .docx Files

The `read_file` tool supports `.docx` files via the `python-docx` library. If a docx read fails with "Recovered missing tool result from a previous interrupted run":

1. This is likely a **context compaction artifact** — the actual read succeeded in an earlier session but the result was lost during compaction.
2. Simply re-read the file — it will likely succeed on the second attempt.
3. Verify `python-docx` is installed: check `requirements.txt` or run `pip install python-docx`.
