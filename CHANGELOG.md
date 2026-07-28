# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1-beta] - 2026-07-28

### Fixed

- Version file not properly updated

## [1.0.0] - 2026-07-17

### Added

- Import project config, core utils, api config, and tests
- API run entrypoint with Python 3.9 compatibility fixes
- Bruno collection to test api endpoints
- Readme with updated license
- Build script and CI test workflow
- Deidentify handler with tests
- Shared deidentify instance manager
- Correct tags to terminal output & tracker
- Mypy lint fixes & missing stubs
- Shared workflows for beta and stable release
- Mypy lint fixes & missing stubs

### Changed

- Setup uv environment, deidentify pipeline (py3.9), and docker
- Wire deidentify handler to shared instance manager
- Refactor handler
- Update readme
- Version 1.0.0-beta
- Increase chunk size
- Wire deidentify handler to shared instance manager
- Update readme
- Prepare v1.0.0-beta (chunk size, workflow fixes, data collection)

### Fixed

- Worker logger, license header, and lint cleanup
- Deidentify pandas warning not silenced
- Long progress updates fixed
- Collect deidentify needed data files
- Deidentify pandas warning not silenced
- Long progress updates fixed

## [v0.0.1-beta] - 2026-07-14

### Initial Release

- REST API for text pseudonymization using Deidentify and FastAPI
- Polars-based high-performance vectorized data processing
- Automatic OpenAPI/Swagger documentation
- Build on Python 3.9
