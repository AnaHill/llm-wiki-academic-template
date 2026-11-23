# Wiki Log

Append-only chronological record of all wiki operations. Each entry starts with a consistent prefix for grep-parseability. When this file grows past 40 kB, `python -I scripts/rotate_log.py --write` moves the oldest entries to archive files of at most 40 kB each in `wiki/log-archive/` (`scripts/check.py` warns when it is time).

Format:
```
## [YYYY-MM-DD] ingest | Author Year — Paper Title
## [YYYY-MM-DD] query | Question summary
## [YYYY-MM-DD] draft | Section updated
## [YYYY-MM-DD] lint | pass
## [YYYY-MM-DD] grill | Decision topic
```

---

## [2026-06-17] init | Academic wiki template initialized

Bootstrapped wiki structure. No sources ingested yet.
