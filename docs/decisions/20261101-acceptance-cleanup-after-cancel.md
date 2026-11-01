# Remove acceptance deployments after a cancelled job

- Status: accepted
- Date: 2026-11-01
- Deciders: Barkin Simsek

## Context

The acceptance runners trap exit, interrupt, and termination to remove their
disposable Compose projects. On 2026-10-27, cancelled runs 40464346133 and
40465015269 left two connector deployments on the self-hosted runner's Docker
host, each with three containers, four networks, and two volumes. Their state
directories, which hold credentials owned by container users, stayed in the
runner's temporary directory, where the runner cannot delete them.

On cancellation the runner sends SIGINT and then SIGTERM only to the entry shell
of the running step. That shell exits, and the acceptance runner below it never
receives a signal. It keeps going until the runner's orphan sweep kills it at
the end of the job, so its trap never runs. Steps marked `if: always()` still run
after a cancellation.

Two simpler options do not close the gap. Running the runner with `exec` makes it
the entry process, but its trap waits for the foreground Docker command, which can
run for ten minutes during the idle check. GitHub kills the process tree ten
seconds after the first signal, so the trap still cannot finish. An `always()`
step that only removes resources races with the orphaned runner, which can
continue past a failed command and recreate a volume or containers after the
step.

## Decision

Each acceptance step runs its Make target under `setsid`, which gives the runner
its own process group. Runners append their process group, the start time of its
leader, their Compose project, and an optional state directory to the file in
`RAICHO_ACCEPTANCE_RECORD` before they create any Docker resource. The final
step of each acceptance job runs with `if: always()` and handles every recorded
entry. It kills the recorded process group only while a leader with the recorded
start time still runs, because Linux can reuse the group ID after a runner
exits. It then removes containers attached to the project's networks or volumes,
removes the resources with the project's exact Compose label or the `<project>_`
name prefix that Compose gives them, removes the images in the project's
repository, and removes the state directory. The prefix also covers a volume
that a fixture container created before Compose did, without the label.

The step refuses entries that name its own process group, a project outside the
disposable naming pattern, or a directory that is not an acceptance state
directory beside the record. The record lives in the runner's temporary
directory, which the runner empties at the start of each job, so the step only
reaches this job's projects.

## Consequences

A cancelled or timed-out acceptance job leaves no containers, networks, volumes,
project images, or state directories behind. Runner hosts need `setsid`. Local
runs record nothing and keep their traps, and `make clean` still removes
interrupted local projects. A new acceptance runner must call `record_project`.
The workflow tests check that its CI step uses `setsid` and the shared record.
