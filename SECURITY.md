# Security Policy

## Supported versions

Security fixes target the default branch and the most recent tagged release.

## Reporting a vulnerability

**Do not open a public GitHub issue for an undisclosed security vulnerability.**

Use GitHub's private vulnerability reporting/security advisory mechanism when enabled for the repository. If it is not enabled, contact the maintainers privately through the repository owner account.

Please include:

- affected component/version;
- reproduction steps or proof of concept;
- impact;
- suggested mitigation if known.

Do not include real user data or secrets in reports.

## Security expectations for deployments

- Generate unique random application/JWT secrets.
- Use TLS for public traffic.
- Keep databases and queues on private networks.
- Restrict CORS and rate limits.
- Rotate credentials regularly.
- Keep dependencies patched.
- Review model/voice/avatar licenses before redistribution.
- Back up production data and test restoration.
