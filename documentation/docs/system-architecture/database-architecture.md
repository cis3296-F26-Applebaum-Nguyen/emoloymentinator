---
sidebar_position: 3
sidebar_label: Database Architecture
---

# Database Architecture

## Database Schema
- searches: Stores all user searches with a record of their Discord ID, the timestamp, and what was searched for
- jobs: Stores all jobs retrieved by searches for future recollection using job ID; identical job postings are not duplicated
- search_results: Record which job IDs belong to which search- preserves orignal result order as well
## Storage and Retrieval
- initialize_database(): create/initialize database if not already present
- save_search(): saves searches, results, and everything associated with them while checking for duplicate job postings before saving
- get_search_history(): retrieves a user's search history starting with the latest query
- get_search_jobs(): retrieves all job postings from a search from a particular user
## Data Isolation
- The retrieval functions check a user's Discord ID, and then retrieving results associated with the ID found by the check
## Current Limitations
- No automatic database cleanup- runs risk of using up bot host computer's disc space
- Stored results are not reused yet to reduce API requests
- No command to access stored results