# Repository configuration rules

- Never put literal IP addresses, numeric network ports, real database names,
  usernames, passwords, API keys, or other credentials in public source,
  configuration, examples, or documentation.
- Resolve runtime connection settings through environment variables. Keep local
  values in ignored `.env` files; use deployment environment variables or secret
  settings when deploying. Do not print their contents in logs or tool output.
- Keep connection and credential fields blank in `.env.example` files. Require
  runtime values instead of introducing hardcoded connection defaults.
- `NEXT_PUBLIC_*` values are visible in the browser and must never contain secrets.
- Keep PostgreSQL private, with no published host ports.
- Run `python scripts/check_public_config.py` and its unittest suite after changing
  configuration. CI must retain this check. Review changes for secrets beyond the
  patterns the check recognizes.
