# Release Process

1. Create a release branch from `main`.
2. Run `make doctor` and the complete test suite.
3. Validate backend Compose configuration.
4. Validate Flutter analysis/tests on supported platforms.
5. Review dependency and license changes.
6. Confirm no secrets or generated local files are included.
7. Update `CHANGELOG.md` and version metadata.
8. Tag the release using semantic versioning.
9. Publish release notes with known limitations.
10. Monitor the first deployment and keep a rollback plan.
