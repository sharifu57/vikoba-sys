# Security review — 3 October 2026

Reviewed the local Spring Boot backend, Next.js frontend, and Flutter app. This
review includes source/configuration inspection, resolved dependency advisory
queries, regression tests, and a production web build. It does not establish the
security of the deployed servers or replace a penetration test.

## Fixed findings

| Finding | Change |
| --- | --- |
| Database, JWT, Redis and SMS credentials in committed configuration | Replaced values with environment variables, removed the shared test signing secret, and made the development database default local. |
| SMS API key logging | Removed the provider-key logging statements. |
| Cross-group reads and financial writes | Added membership checks for group settings, contributions, payments, accounting, fines and dividends, and permission checks for administrative writes, reports and audit logs. Payment/journal entry API writes require `CONTRIBUTION_MANAGE`; legitimate internal approval workflows keep their existing authorization. |
| Cross-group contribution periods | Recording a contribution verifies that its period and member belong to the same group. |
| Disabled/suspended/locked accounts retained sessions | JWT authentication and refresh now check account status and temporary locks. Phone-verification OTPs cannot reactivate disabled accounts. Deleted accounts produce HTTP 401. |
| OTP replay and concurrent guessing | Issuing/verifying codes locks the user row in a transaction. Issuing a new code invalidates previous unused codes across purposes. Added a 60-second send cooldown, an account-wide five-failure/15-minute lockout, and a supported-purpose allowlist. |
| Plaintext verification codes and notification history | OTPs now store password hashes. Verification notifications, provider responses and exhausted-delivery queue messages redact codes. Queue/parse errors avoid logging verification payloads. A migration expires and redacts old plaintext database records. |
| Spoofable audit client IP | Audit records use the servlet-resolved remote address instead of accepting arbitrary `X-Forwarded-For` values. Configure trusted proxies at the container when needed. |
| Executable receipt uploads | Restricted proofs to PNG, JPEG, WebP and PDF, checked signatures, and sandboxed responses. Legacy unsupported files download as opaque attachments. Receipt responses cannot be cached. |
| Unbounded spreadsheet imports | Added a 10 MB limit and a 10,000-row processing limit to contribution imports. |
| Flutter tokens stored in plaintext preferences | Moved both tokens into `flutter_secure_storage`, migrated old values, and removed plaintext copies. Serialized token operations prevent a migration/logout race. |
| Flutter API cache shared across accounts | Cache keys include a hashed bearer identity so another account cannot reuse cached data for the same URL. |
| Production client logging and exception details | Flutter request logging is debug-only; removed permission logging and raw exception messages in HTTP 500 responses. |
| Missing browser protections | Added anti-framing, MIME-sniffing, referrer and permissions headers, plus CSP restrictions on framing, objects and base URLs. This is a partial CSP, not a full script policy. |
| Credential files and crash diagnostics | Ignored local environment files and JVM crash/replay logs. Ignore rules do not erase tracked files or repository history. The existing client `.env` files contain public API URLs only. |

## Dependencies

| Component | Previous | Patched |
| --- | --- | --- |
| Jackson 3 BOM | 3.1.4 | 3.1.7 |
| Jackson 2 BOM | 2.21.4 | 2.21.7 |
| Tomcat | 11.0.22 | 11.0.25 |
| PostgreSQL JDBC | 42.7.11 | 42.7.12 |
| Log4j 2 | 2.25.4 | 2.25.5 |
| LZ4 Java | 1.10.1 | 1.11.1 |
| Next.js | 16.3.0 | 16.3.6 |
| Sharp | 0.35.3 | 0.35.4 |
| SheetJS | 0.18.5 | 0.20.3 |

Removed the component-generator CLI dependency and its vulnerable transitive
dependency chain. Preserved the exact component stylesheet locally with its MIT
license. The publisher's patched SheetJS tarball is vendored with its source and
SHA-512 integrity, and both npm and pnpm lockfiles were regenerated.

The final live npm audit reports zero vulnerabilities. The cross-ecosystem OSV
scan checked 467 resolved dependency versions and reports no unresolved matches.
Two npm SheetJS advisories still match its publisher-distributed version because
their npm ranges contain no fixed release. These matches remain visible as
`triaged` in `security-dependency-audit.json`, with the publisher's documented
fixes. This is not a blanket suppression for future SheetJS advisories.

Dependency matching identifies published advisories; it cannot prove the absence
of vulnerabilities or that every advisory is exploitable in this application.

## Validation

- Backend: 81 tests passed, including real database concurrency tests proving
  exactly one session for simultaneous correct OTP submissions and no lost
  attempts under concurrent guesses.
  Added regression checks for OTP hashing, notification/queue-error redaction
  and forged forwarding headers. The PostgreSQL migration was inspected but was
  not executed against a PostgreSQL instance during this review.
- Flutter: all 22 tests passed, including secure storage migration, logout and
  cache separation.
- Web: TypeScript validation and production build passed.
- Flutter analysis: one existing style suggestion in
  `lib/features/member/presentation/group_selection_page.dart:32`; no errors or
  warnings from the security changes.
- Source credential/logging pattern check: no remaining matches in the inspected
  backend configuration and application source. This was a targeted check, not
  an exhaustive secret scanner or a Git-history scan.

## Required deployment actions

1. Rotate the previously committed database password, JWT signing key, Redis
   password and SMS provider key. Removing the values from the current files
   does not revoke them or remove them from Git history or old logs.
2. Set `DB_PASSWORD`, `JWT_SECRET_KEY`, `REDIS_PASSWORD` and `SMS_API_KEY` in the
   deployment environment. `vikoba/.env.example` lists the variables; Spring Boot
   does not automatically load that file. Use a newly generated random JWT
   secret of at least 32 bytes. The database password and JWT key are required
   at startup; Redis is required for the production profile; SMS must be set to
   deliver OTPs.
3. Set `DB_URL` for development when using a database other than local PostgreSQL.
   Deploy the rebuilt backend and clients. JWT key rotation invalidates existing
   sessions, so users must sign in again.
4. Before deploying the hashed-OTP backend, apply
   `vikoba/src/main/resources/db/migration/V20261003_01__protect_verification_codes.sql`
   through your migration process. It expands the OTP column, invalidates old
   plaintext codes and redacts verification notification history. Users with
   outstanding codes must request new ones. Although Flyway settings exist,
   the current Maven dependencies do not include Flyway; do not assume this SQL
   runs automatically. Schedule the migration and backend rollout together.

No production services or credentials were changed during this local review.

## Remaining security work

- Browser access/refresh tokens remain in JavaScript-readable `localStorage`.
  A server-managed HttpOnly cookie/session design and a full nonce-based script
  CSP are still needed to reduce the impact of XSS.
- Refresh tokens remain reusable until expiration; issuing a replacement does
  not revoke the old token, and client logout cannot revoke a stolen token.
  Add server-side refresh-token rotation/revocation with a database migration.
- Active/retry SMS queue messages still contain the code needed for delivery.
  Configure short Kafka retention, restricted access and transport/storage
  encryption; address historical queues and backups when rolling out redaction.
- Add trusted-proxy-aware IP/global limits for registration, account lookup and
  SMS issuance, plus distributed daily delivery quotas. The new account-level
  cooldown/lockout does not stop abuse spread across many phone numbers. The
  registration lookup deliberately reveals whether a phone number is registered.
- Validate production TLS, firewall rules, database/Redis/Kafka exposure and
  trusted proxy headers. These deployment settings were not inspected remotely.
- Receipt signature checks and response sandboxing do not perform malware
  scanning or fully decode/validate every uploaded file.

## Repeating the checks

Use Java 21 for Maven; this machine's default `JAVA_HOME` points to Java 17.

```powershell
$env:JAVA_HOME = 'C:\Program Files\Java\jdk-21.0.12'
cd vikoba
.\mvnw.cmd test
.\mvnw.cmd dependency:list '-DincludeScope=runtime' '-DoutputFile=target/security-dependencies.txt'
cd ..
python tools/security/dependency_audit.py
cd vikoba-web
npm audit --offline=false
npx tsc --noEmit --incremental false
npm run build
cd ../vikoba_app
flutter test
flutter analyze
```

The dependency script sends public package names and versions to the
[OSV API](https://google.github.io/osv.dev/api/). Security practices were checked
against the [OWASP authentication guidance](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
and [secrets guidance](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html).
OTP handling was checked against [OWASP OTP storage guidance](https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html#one-time-password-otp-handling-and-storage).
SheetJS installation and patch guidance comes from the
[publisher](https://docs.sheetjs.com/docs/getting-started/installation/nodejs/).
