# Label acceptance containers created outside Compose

- Status: accepted
- Date: 2026-11-02
- Deciders: Barkin Simsek

## Context

The [cancel cleanup decision](20261101-acceptance-cleanup-after-cancel.md)
removes each recorded project by its Compose label. The credential fixture, the
connector and runtime probes, and the connector's address holder start with
plain `docker run`, so they carry no project label. A fixture that mounts the
project's data volume before Compose creates it leaves a volume without the
label. The cleanup step therefore also found networks and volumes by the
`<project>_` name prefix and removed the containers attached to them, in three
functions beside the label-based removal.

## Decision

Containers and volumes that acceptance runners create outside Compose carry the
project's Compose label. `prepare_credential_deployment` adds the label to every
hardened `docker run` and creates the project's data volume with the project and
volume labels before a fixture can mount it. The runtime probes and the
connector's address holder carry the same label. The cleanup step finds every
resource of a project by that label alone, and the name-prefix discovery is
removed. This replaces only the resource discovery of the earlier record. Its
process handling and refusal rules stay.

## Consequences

The cleanup step and `make clean` find fixture, probe, and holder containers like
any other project resource. Compose adopts the pre-created data volume without a
warning, and `down --volumes` removes it. Compose ignores the labelled containers
because they have no service label, so `down` leaves them to the runner's own
cleanup or the cleanup step. A new runner that creates containers or volumes outside
Compose must give them the project label, or cleanup misses them.
