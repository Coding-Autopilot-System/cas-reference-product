# Contributing

1. Create a focused branch.
2. Preserve the `cas-contracts` v0.1 lifecycle shapes.
3. Do not add Classic Assistants APIs, embedded credentials, or Azure deployment commands.
4. Update tests and documentation with behavioral changes.
5. Run the full local gate:

```powershell
./scripts/validate.ps1
```

Pull requests must pass lint, strict type checks, tests with the coverage gate, and the Linux AMD64 container build.
