# Raicho

Your Thunderbird, anywhere.

Raicho is a browser interface for Thunderbird. This repository currently holds
the brand kit, a static showcase, and containerized development tooling. It does
not yet contain a mail client, extension, or server.

The showcase is a visual reference with fictional mail. Do not treat it as
application behavior, and do not add `server/`, `web/`, `extension/`,
or `protocol/` until the
[foundation plan](docs/planning/active/20261017-thunderbird-first-foundation.md)
introduces them.

The tooling image and Compose commands are documented in
[build, test, and generate](docs/reference/build-test-generate.md).

A product change goes through a design pull request before implementation.
The [delivery workflow](docs/contributing/workflow.md) is the rule for that.

- [Architecture](docs/reference/architecture.md) describes what exists and the accepted direction.
- [Getting started](docs/contributing/getting-started.md) covers contributor and agent setup.
- [Brand guide](assets/brand/README.md) covers logos, color, and type.
