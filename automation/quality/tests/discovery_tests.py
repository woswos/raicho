from automation.quality.tests.project_fixture import ProjectFixture


class QualityDiscoveryTests(ProjectFixture):
    def test_format_rejects_symlinks_into_excluded_content(self):
        vendor = self.root / 'vendor'
        vendor.mkdir()
        original = 'value=1\n'
        source = vendor / 'original.py'
        source.write_text(original)
        (self.root / 'linked.py').symlink_to(source)
        self.check_runner('format', successful=False, diagnostic='not symlinks')
        self.assertEqual(source.read_text(), original)

    def test_broken_source_symlinks_cannot_look_like_absent_languages(self):
        (self.root / 'missing.rs').symlink_to(self.root / 'missing-target')
        self.check_runner('lint-rust', successful=False, diagnostic='not symlinks')

    def test_unknown_targets_do_not_succeed(self):
        self.check_runner('lint-mistyped', successful=False, diagnostic='invalid choice')

    def test_missing_tools_cannot_be_reported_as_not_applicable(self):
        environment = self.git_only_environment()
        self.check_runner('lint-rust', successful=False, diagnostic='cargo is unavailable', environment=environment)
