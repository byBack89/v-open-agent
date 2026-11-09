# shared contracts

Language-neutral artifacts shared by the Python server, simulator, and Android client.

- `schemas`: published JSON Schema snapshots
- `fixtures`: positive and negative JSON fixtures

Python Pydantic models remain in `apps/server/src/voa/contracts`. Contract changes publish schemas and fixtures here before consumer implementations are updated.
