# Prioritized Fixes

## Goal
Fix blocking runtime/test failures first, then reduce type issues.

## Tasks
- [ ] Fix HistoryService save/delete failures on Windows temp dirs -> Verify: `pytest tests/unit/test_history_service.py -v`
- [ ] Fix SessionManager pipeline completion flag -> Verify: code path review
- [ ] Make toxicity filter effective in pipeline flow -> Verify: logic review + test impact check
- [ ] Reduce mypy errors (interfaces/UTC/type mismatches) -> Verify: `mypy src`
- [ ] Run full verification -> Verify: `ruff check src tests`, `pytest`, `mypy src`

## Done When
- [ ] HistoryService tests pass
- [ ] Key runtime bugs fixed
- [ ] mypy errors reduced or cleared
