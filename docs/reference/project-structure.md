# Project structure

Raicho contains a runnable diagnostics foundation, an independent Thunderbird
image, brand assets, and the shared workflow. Mail integration is still planned.

```text
AGENTS.md          Always-loaded instructions and pointers to task-specific docs
CHANGELOG.md       Product changelog used to cut semantic versions
compose*.yaml      Base deployment and its administration overlay
.agents/skills/    Canonical shared workflow skills
.github/           Pull request templates and GitHub Actions workflows
assets/brand/      Production identity masters, fonts, guides, and prototypes
deploy/            Per-service image recipes, runtime code, configuration, and tests
server/            Rust diagnostics, SQLite queries, migrations, and tests
web/               TypeScript diagnostics, public files, and behavioral tests
protocol/          Connector and status schemas, limits, fixtures, generators, implementations
automation/        Development commands and support packages grouped by responsibility
docs/contributing/ Contribution workflow, working agreements, and project invariants
docs/reference/    Current structure, tooling, CI, and architecture
docs/coding/       Engineering principles and coding and formatting conventions
docs/decisions/    Decision records and their template
docs/planning/     Active and completed staged plans
```

## Placement rules

Use these locations when adding files or moving existing code:

| Material | Location |
| --- | --- |
| Deployed service recipe, filter, runtime code, configuration, and tests | `deploy/<service>/` |
| Base Compose deployment and operator overlays | Repository root |
| Test-only Compose overlays | Beside the acceptance driver that uses them |
| Application sources | Their owning `server/` or `web/` component |
| Shared connector and status schemas, limits, fixtures, and implementations | `protocol/` |
| Protocol generation scripts and support modules | `protocol/generator/` |
| Component-specific build scripts and packaging | The owning component's root |
| Shared development commands and their support modules | `automation/<responsibility>/` |

Each deployed service owns one directory under `deploy/`: `raicho/` and
`thunderbird/`. The directory holds the image recipe, its `Dockerfile.dockerignore`,
the service's runtime code and configuration such as
`deploy/thunderbird/policies.json`, and their tests. Build filters list explicit
files or source directories from the owning components. A bare parent such as
`!server/` would re-include that whole tree. The
[repository layout decision](../decisions/20261026-repository-layout.md) records
this organization.

Shared protocol implementations belong together in `protocol/rust/` and
`protocol/typescript/`, with their own sources and tests. Keep them independent
of Thunderbird APIs. See the [protocol placement decision](../decisions/20261026-protocol-contracts.md).
Protocol generation belongs to `protocol/generator/`, beside the schema and
implementations it produces.

Apply the [source filename](../coding/coding-standards.md#source-filenames),
[directory name](../coding/coding-standards.md#directory-names), and
[documentation naming](../contributing/documentation-organisation.md#naming)
conventions within these locations.

## Automation

Keep component-specific builders with their sources, such as `web/build.mjs`. The
[component ownership decision](../decisions/20261026-repository-layout.md#tests)
records this placement.

Group shared development automation by responsibility, including its import-only
support modules. Use Make as the main developer command interface. It invokes Python
modules directly from the repository root with `python3 -B -m`, and Bash or
JavaScript entry points by path. Keep Bash for substantive host/Docker orchestration.
Do not add thin compatibility wrappers or restore a flat helper directory.

| Responsibility | Package |
| --- | --- |
| Agent, naming, changelog, and pull request guards | `automation/repository/` |
| Language linting, formatting, and type checking | `automation/quality/` |
| Development tooling image, entrypoint, and Compose files | `automation/tooling/` |
| Cross-component application build/test dispatch | `automation/build/` |
| Versioning, changelogs, and release preparation | `automation/release/` |
| Cross-service disposable deployment checks | `automation/acceptance/` |
| Fixtures shared by automation tests | `automation/testing/` |

Cross-service acceptance drivers use a `runtime/` subpackage.
The shared repository-path helper lives at
`automation/paths.py`.

The
[automation decision](../decisions/20261026-repository-layout.md#automation) records this
organization and the replacement of the former `devbin/` tree.

## Compose deployments

The root `compose.yaml` runs the application and Thunderbird with separate
volumes and networks, so `docker compose` works from the repository root without
`-f`. `compose.admin.yaml` adds local desktop administration.

Test overlays live with their drivers. `automation/acceptance/runtime/compose.test.yaml`
adds the isolated runtime fixture driver. Compose resolves every
overlay's paths from the first file, so these overlays use repository-relative
paths. `automation/tooling/compose.yaml` provides checks and formatting, with
`automation/tooling/compose.ci.yaml` adding the GitHub event mount.
The [runtime guide](../operations/local-runtime.md) and
[tooling commands](build-test-generate.md) show their combinations.

The [brand guide](../../assets/brand/README.md) describes asset locations and
[showcase guide](../../assets/brand/showcase/README.md) describes editable pages.
See [architecture](architecture.md) for the distinction between the prototype
and the intended product.

The [connector contract](connector-contract.md) describes the schema, generated
modules, and their current integration boundary. Component responsibilities and
persistence are defined in [architecture](architecture.md).

## Test code

Keep tests, mocks, fixture controllers, and profile setup with their owning
component, using its `tests/` subtree. Do not create a repository-root test tree.
Automation tests live in the owning package's `tests/` subtree. Changelog guard
regressions belong in `automation/repository/tests/`, beside the other PR policy
tests. Shared guard fixtures and the `docker` command mock live in `automation/testing/`.

`server/tests/` and `web/tests/` own their respective application and
integration tests. Rust test support lives under
`server/tests/support/`.

`protocol/rust/tests/` and `protocol/typescript/tests/` run the shared protocol
fixtures against their respective implementations. TypeScript protocol tests
compile independently. See the
[contract commands](build-test-generate.md#connector-contract).
Generator regressions live in `protocol/generator/tests/`.
`protocol/fixtures/configuration/connector.json` lists valid and invalid connector
tokens and endpoints, and the server's `Credential::parse` tests against it.

Token-file recovery, file-safety, and live-check tests live with the Rust
implementation in `server/tests/`. `deploy/thunderbird/tests/` tests the production `thunderbird`
package beside it.

Python modules are packages imported from the repository root, including those
that run inside containers. `make test-python` discovers every `*_tests.py` in
them, so a new Python test directory needs only the `__init__.py` files on its
import path.

## Tooling and image boundaries

Use the shared tooling image for linters, formatters, test runners, and fixture
drivers locally and in CI. Independent fixture processes can use separate
containers from that image. Thunderbird retains its runtime image. The
[shared tooling decision](../decisions/20261026-repository-layout.md#tooling-image)
records the image boundary.

The tooling image's build-context filter includes only tooling dependencies,
excluding host Docker orchestration. Keep fixture code
out of production runtime images. The Thunderbird recipe copies its explicit runtime modules,
and its filter excludes test directories. Rebuild and execution commands live in
[build, test, and generate](build-test-generate.md#tooling-image).

Module boundaries follow the
[coding standards](../coding/coding-standards.md#naming-and-structure).
