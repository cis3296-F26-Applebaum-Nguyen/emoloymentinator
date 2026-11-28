---
sidebar_position: 1
sidebar_label: System Overview
---

# System Overview

## Persistent Job Storage
- Purpose: To preserve the results of a user's previous queries for easy recollection and to save up on the requests afforded to via the free version of Gemini we are utilizing
- Technology: SQLite, Python sqlite3 module
- Initialization: Database is created during startup by default in job_history.db
- User Association: All searches are saved to a user's Discord ID
- Storage Efficiency: No identical job postings are stored; separate searches do not affect this
- Current Scope: Database internally preserves individual search history, but currently user has no way to access history directly via Discord command