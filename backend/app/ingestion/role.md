# Ingestion Module

This module is responsible for **fetching repository data from GitHub**. It handles API communication, file tree retrieval, content downloading, and filtering to prepare raw repository data for the analysis pipeline in gitEQ.

---

## File Roles

### `github_client.py`
**GitHub API Client**  
Provides an async HTTP client wrapper (`GitHubClient`) for GitHub API requests. Handles authentication via GitHub tokens, rate limiting detection, and request configuration.

---

### `repo_meta.py`
**Repository Metadata Fetcher**  
Fetches basic repository information (default branch, size, fork/archived status) from GitHub's repository endpoint.

---

### `tree_fetcher.py`
**Repository File Tree Fetcher**  
Retrieves the complete file tree structure using GitHub's Git Trees API with recursive mode. Handles truncation errors for extremely large repositories.

---

### `tree_normalizer.py`
**Tree Structure Normalizer**  
Normalizes the raw tree data from GitHub into a consistent format with `path`, `type`, `sha`, and `size` fields for downstream processing.

---

### `glob_filter.py`
**File Path Filter**  
Filters files using glob patterns (gitignore-style wildcards). Uses `pathspec` library to apply include/exclude patterns, filtering out non-blob items and unwanted paths.

---

### `binary_rules.py`
**Binary File Detector**  
Defines a set of binary file extensions (images, fonts, archives, etc.) and provides `is_binary_path()` to identify files that should be skipped during content fetching.

---

### `content_fetcher.py`
**Individual File Content Fetcher**  
Fetches the content of a single file from GitHub. Handles:
- Binary file exclusion
- Large file handling (raw mode for files > 1MB)
- Base64 decoding for standard API responses
- Size limits to prevent memory issues

---

### `content_loader.py`
**Batch Content Loader**  
Orchestrates parallel fetching of multiple file contents with concurrency limits (semaphore-based). Returns a dict of `{path: content}` for all successfully fetched files.
