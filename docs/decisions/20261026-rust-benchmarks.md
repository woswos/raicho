# Benchmark Rust with Criterion

- Status: accepted
- Date: 2026-10-26
- Deciders: Barkin Simsek

## Context

The connector decodes, validates, and authenticates every frame, and nothing
measures what that costs or whether a change made it slower. Rust's built-in
`#[bench]` needs a nightly compiler, while the workspace pins a stable toolchain.

## Decision

Use [Criterion](https://github.com/criterion-rs/criterion.rs) 0.8.2 as a
development dependency for Rust benchmarks. Disable its default plotting and
parallelism features and keep only `cargo bench` support, which limits the
added crates. Benchmarks live in the owning crate's `benches/` directory as
`harness = false` targets. `make benchmark` runs them in the tooling container,
and each run compares against the previous one saved in the Cargo cache volume.
Divan was the lighter alternative, but it has had no release since April 2025.
Gungraun's instruction counts are stable enough for CI, but they need Valgrind
in the image.

## Consequences

Contributors can measure per-frame costs and see regressions between local
runs. Clippy and the test suite build benchmark code, so it stays current. CI
does not run benchmarks, because shared runners make timings noisy, so
regressions are caught only when someone runs them. Plots and HTML reports
are unavailable without re-enabling Criterion features.
