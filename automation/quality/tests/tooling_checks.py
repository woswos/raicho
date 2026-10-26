import json

from automation.quality.tests.quality_fixture import QualityFixture

RUST_SOURCE = 'pub fn answer() -> u32 {\n    42\n}\n'
TYPESCRIPT_SOURCE = 'export const answer = 42;\n'
CARGO_MANIFEST = (
    '[package]\nname = "quality-fixture"\nversion = "0.1.0"\nedition = "2024"\n'
)
CARGO_LOCK = 'version = 4\n\n[[package]]\nname = "quality-fixture"\nversion = "0.1.0"\n'


class ToolingChecks(QualityFixture):
    def rust_project(self, source=RUST_SOURCE):
        self.write('Cargo.toml', CARGO_MANIFEST)
        self.write('Cargo.lock', CARGO_LOCK)
        return self.write('src/lib.rs', source)

    def typescript_project(self, include=None):
        configuration = {
            'compilerOptions': {'strict': True, 'target': 'ES2022', 'noEmit': True},
            'include': include if include is not None else ['src/**/*.ts'],
        }
        self.write('tsconfig.json', json.dumps(configuration))
        return self.write('src/example.ts', TYPESCRIPT_SOURCE)

    def test_missing_languages_are_reported_as_skipped(self):
        for target in (
            'lint-rust',
            'format-check-rust',
            'lint-typescript',
            'typecheck',
        ):
            with self.subTest(target=target):
                self.check(target, diagnostic='SKIP')

    def test_rust_sources_without_a_manifest_fail(self):
        self.write('nested/example.rs', RUST_SOURCE)
        for target in ('lint-rust', 'format-check-rust'):
            with self.subTest(target=target):
                self.check(target, successful=False)

    def test_valid_rust_passes_lint_and_format_checks(self):
        self.rust_project()
        self.check('lint-rust')
        self.check('format-check-rust')

    def test_clippy_warnings_fail(self):
        self.rust_project('pub fn answer() -> u32 {\n    return 42;\n}\n')
        self.check('lint-rust', successful=False, diagnostic='needless_return')

    def test_nested_cargo_projects_are_also_linted(self):
        self.rust_project()
        self.write('nested/Cargo.toml', CARGO_MANIFEST + '\n[workspace]\n')
        self.write('nested/Cargo.lock', CARGO_LOCK)
        self.write('nested/src/lib.rs', 'pub fn answer() -> u32 {\n    return 42;\n}\n')
        self.check('lint-rust', successful=False, diagnostic='needless_return')

    def test_rust_format_check_does_not_modify_source(self):
        source = 'pub fn answer()->u32{42}\n'
        path = self.rust_project(source)
        self.check('format-check-rust', successful=False)
        self.assertEqual(path.read_text(), source)

    def test_typescript_sources_without_configuration_fail(self):
        self.write('nested/example.ts', TYPESCRIPT_SOURCE)
        for target in ('lint-typescript', 'typecheck'):
            with self.subTest(target=target):
                self.check(target, successful=False)

    def test_valid_nested_typescript_passes(self):
        self.typescript_project()
        self.write('src/nested/example.ts', 'export const otherAnswer = 43;\n')
        self.check('lint-typescript')
        self.check('typecheck')

    def test_type_errors_fail(self):
        path = self.typescript_project()
        path.write_text('export const answer: number = "forty-two";\n')
        self.check('typecheck', successful=False, diagnostic='TS2322')

    def test_explicit_any_fails_typescript_lint(self):
        path = self.typescript_project()
        path.write_text('export const answer: any = 42;\n')
        self.check('lint-typescript', successful=False, diagnostic='no-explicit-any')

    def test_excluded_nested_typescript_does_not_silently_pass(self):
        self.typescript_project(include=['src/example.ts'])
        self.write('src/nested/excluded.ts', 'export const answer: number = "wrong";\n')
        self.check('typecheck', successful=False)

    def test_javascript_format_check_accepts_formatted_source(self):
        self.write('src/example.js', 'export const answer = 42;\n')
        self.check('format-check-javascript')

    def test_javascript_format_check_does_not_modify_source(self):
        source = 'export const answer=42\n'
        path = self.write('src/example.js', source)
        self.check('format-check-javascript', successful=False)
        self.assertEqual(path.read_text(), source)
