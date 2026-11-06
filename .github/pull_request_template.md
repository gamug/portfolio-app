## Summary

What changes and why.

## Traceability

- FR: FR-0xx
- Work Item: WI-0xx
- Tasks: TASK-0xx

## Verification

Commands run and their result:

- [ ] `uv run --directory backend pre-commit run --all-files`
- [ ] Tests added or updated for the change

## Checklist

- [ ] Commit subjects follow `type(scope): summary [FR-xxx][WI-xxx][TASK-xxx]`
- [ ] No secrets committed; `.env` stays local and `KG_USER` is a read-only GraphDB user
- [ ] A change to `config.yaml` updates its row in `docs/PRODUCT.md` and re-renders `.sdd/constitution.md`
- [ ] An architecture change has a `Proposed` ADR in `adr.md` approved before it is implemented
- [ ] `.sdd/TASKS.md` and `.sdd/CHANGELOG.md` are updated
