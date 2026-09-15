import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[4]
FIXTURES = Path(__file__).resolve().parent / 'fixtures'
PLAYBOOK = shutil.which('ansible-playbook')


PKG_SCRIPT = '''#!/bin/sh
printf 'pkg %s\\n' "$*" >> "$SAS_PROBE_LOG"
[ "$SAS_FAKE_LOCALE_WARNING" = yes ] && printf ': unknown locale\\n' >&2
case "$SAS_FAKE_IPS_RESULT" in
    installed)
        printf '             Name: %s\\n' "$2"
        printf '            State: Installed\\n'
        printf '        Publisher: OneIdentity\\n'
        printf '          Version: %s\\n' "$SAS_FAKE_IPS_VERSION"
        exit 0
        ;;
    absent)
        printf '%s\\n' \
            'pkg: info: no packages matching the following patterns you specified are' \
            'installed on the system.  Try querying remotely instead:' >&2
        printf '\\n        %s\\n' "$2" >&2
        exit 1
        ;;
    *)
        printf 'pkg: info: repository unavailable\\n' >&2
        exit 1
        ;;
esac
'''


PKGINFO_SCRIPT = '''#!/bin/sh
printf 'pkginfo %s\\n' "$*" >> "$SAS_PROBE_LOG"
[ "$SAS_FAKE_LOCALE_WARNING" = yes ] && printf ': unknown locale\\n' >&2
case "$SAS_FAKE_SVR4_RESULT" in
    installed)
        printf '   PKGINST:  %s\\n' "$2"
        printf '   VERSION:  %s\\n' "$SAS_FAKE_SVR4_VERSION"
        printf '    STATUS:  completely installed\\n'
        exit 0
        ;;
    absent)
        printf 'ERROR: information for "%s" was not found\\n' "$2" >&2
        exit 1
        ;;
    *)
        printf 'pkginfo: cannot read package database\\n' >&2
        exit 1
        ;;
esac
'''


@unittest.skipUnless(PLAYBOOK, 'ansible-playbook is required')
class SolarisPackageOwnershipTests(unittest.TestCase):

    def run_case(self, variables, ips_result, svr4_result,
                 ips_version='', svr4_version='', check_mode=False,
                 locale_warning=False):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            for name, content in (
                    ('pkg', PKG_SCRIPT), ('pkginfo', PKGINFO_SCRIPT)):
                script = temp_path / name
                script.write_text(content)
                script.chmod(script.stat().st_mode | stat.S_IXUSR)

            probe_log = temp_path / 'probes.log'
            environment = dict(os.environ)
            environment.update({
                'ANSIBLE_NOCOLOR': '1',
                'ANSIBLE_ROLES_PATH': str(ROOT / 'roles'),
                'PATH': '{}:{}'.format(temp_dir, environment['PATH']),
                'SAS_PROBE_LOG': str(probe_log),
                'SAS_FAKE_IPS_RESULT': ips_result,
                'SAS_FAKE_IPS_VERSION': ips_version,
                'SAS_FAKE_SVR4_RESULT': svr4_result,
                'SAS_FAKE_SVR4_VERSION': svr4_version,
                'SAS_FAKE_LOCALE_WARNING': (
                    'yes' if locale_warning else 'no'
                ),
            })
            command = [
                PLAYBOOK,
                '-i', 'localhost,',
                '-c', 'local',
                str(FIXTURES / 'package_ownership.yml'),
                '-e', json.dumps(variables),
            ]
            if check_mode:
                command.append('--check')
            completed = subprocess.run(
                command,
                cwd=str(ROOT),
                env=environment,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=30,
            )
            probes = probe_log.read_text() if probe_log.exists() else ''
        return completed, probes

    def test_solaris11_ips_precedes_pkginfo_compatibility_view(self):
        variables = {
            'test_solaris_major': '11',
            'test_package': 'vasclnts',
            'test_state': 'present',
            'expected_owner': 'ips',
            'expected_present': True,
            'expected_migration_required': False,
            'expected_version': '7.1.0.6700',
        }
        completed, probes = self.run_case(
            variables,
            ips_result='installed',
            svr4_result='installed',
            ips_version='7.1.0.6700',
            svr4_version='7.1.0.6700,REV=2026.07.29.08.05.1785337532',
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('pkg info vasclnts', probes)
        self.assertIn('pkginfo -l vasclnts', probes)

    def test_solaris11_detects_genuine_legacy_svr4_install(self):
        variables = {
            'test_solaris_major': '11',
            'test_package': 'vasclnts',
            'test_state': 'present',
            'expected_owner': 'svr4',
            'expected_present': True,
            'expected_migration_required': True,
            'expected_version': '6.1.0.4900',
        }
        completed, probes = self.run_case(
            variables,
            ips_result='absent',
            svr4_result='installed',
            svr4_version='6.1.0-4900',
            locale_warning=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('pkg info vasclnts', probes)
        self.assertIn('pkginfo -l vasclnts', probes)

    def test_solaris11_legacy_absent_request_does_not_require_migration(self):
        variables = {
            'test_solaris_major': '11',
            'test_package': 'vasclnts',
            'test_state': 'absent',
            'expected_owner': 'svr4',
            'expected_present': True,
            'expected_migration_required': False,
            'expected_version': '6.1.0.4900',
        }
        completed, unused_probes = self.run_case(
            variables,
            ips_result='absent',
            svr4_result='installed',
            svr4_version='6.1.0.4900,REV=2024.11.22.03.18.55',
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)

    def test_solaris11_detects_absent_package(self):
        variables = {
            'test_solaris_major': '11',
            'test_package': 'vasclnt',
            'test_state': 'present',
            'expected_owner': 'absent',
            'expected_present': False,
            'expected_migration_required': False,
            'expected_version': '',
        }
        completed, probes = self.run_case(
            variables,
            ips_result='absent',
            svr4_result='absent',
            locale_warning=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('pkg info vasclnt', probes)
        self.assertIn('pkginfo -l vasclnt', probes)

    def test_solaris10_detects_svr4_install_without_running_pkg(self):
        variables = {
            'test_solaris_major': '10',
            'test_package': 'vasclnts',
            'test_state': 'present',
            'expected_owner': 'svr4',
            'expected_present': True,
            'expected_migration_required': False,
            'expected_version': '6.1.0.4900',
        }
        completed, probes = self.run_case(
            variables,
            ips_result='error',
            svr4_result='installed',
            svr4_version='6.1.0-4900',
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertNotIn('pkg info', probes)
        self.assertIn('pkginfo -l vasclnts', probes)

    def test_solaris10_detects_absent_package(self):
        variables = {
            'test_solaris_major': '10',
            'test_package': 'vasclnt',
            'test_state': 'absent',
            'expected_owner': 'absent',
            'expected_present': False,
            'expected_migration_required': False,
            'expected_version': '',
        }
        completed, probes = self.run_case(
            variables,
            ips_result='error',
            svr4_result='absent',
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertNotIn('pkg info', probes)
        self.assertIn('pkginfo -l vasclnt', probes)

    def test_operational_probe_errors_fail_closed(self):
        cases = (
            ('11', 'error', 'absent', 'IPS registration'),
            ('11', 'absent', 'error', 'SVR4 registration'),
            ('10', 'error', 'error', 'SVR4 registration'),
        )
        for major, ips_result, svr4_result, message in cases:
            with self.subTest(major=major, message=message):
                variables = {
                    'test_solaris_major': major,
                    'test_package': 'vasclnt',
                    'test_state': 'present',
                    'expected_owner': 'absent',
                    'expected_present': False,
                    'expected_migration_required': False,
                    'expected_version': '',
                }
                completed, unused_probes = self.run_case(
                    variables,
                    ips_result=ips_result,
                    svr4_result=svr4_result,
                )
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertIn(message, completed.stdout)

    def test_success_without_one_version_field_fails_closed(self):
        for ips_result, svr4_result, message in (
                ('installed', 'absent', 'installed version'),
                ('absent', 'installed', 'installed version')):
            with self.subTest(ips_result=ips_result):
                variables = {
                    'test_solaris_major': '11',
                    'test_package': 'vasclnt',
                    'test_state': 'present',
                    'expected_owner': 'absent',
                    'expected_present': False,
                    'expected_migration_required': False,
                    'expected_version': '',
                }
                completed, unused_probes = self.run_case(
                    variables,
                    ips_result=ips_result,
                    svr4_result=svr4_result,
                )
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertIn(message, completed.stdout)

    def test_probes_execute_without_changes_in_check_mode(self):
        variables = {
            'test_solaris_major': '11',
            'test_package': 'vasclnts',
            'test_state': 'check',
            'expected_owner': 'ips',
            'expected_present': True,
            'expected_migration_required': False,
            'expected_version': '7.1.0.6700',
        }
        completed, probes = self.run_case(
            variables,
            ips_result='installed',
            svr4_result='installed',
            ips_version='7.1.0.6700',
            svr4_version='7.1.0.6700,REV=2026.07.29.08.05.1785337532',
            check_mode=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('pkg info vasclnts', probes)
        self.assertIn('pkginfo -l vasclnts', probes)
        self.assertIn('changed=0', completed.stdout)

    def test_solaris10_probe_executes_without_changes_in_check_mode(self):
        variables = {
            'test_solaris_major': '10',
            'test_package': 'vasclnts',
            'test_state': 'check',
            'expected_owner': 'svr4',
            'expected_present': True,
            'expected_migration_required': False,
            'expected_version': '6.1.0.4900',
        }
        completed, probes = self.run_case(
            variables,
            ips_result='error',
            svr4_result='installed',
            svr4_version='6.1.0-4900',
            check_mode=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertNotIn('pkg info', probes)
        self.assertIn('pkginfo -l vasclnts', probes)
        self.assertIn('changed=0', completed.stdout)

    def test_missing_solaris_major_version_fails_before_probing(self):
        variables = {
            'test_solaris_major': '',
            'test_package': 'vasclnt',
            'test_state': 'present',
            'expected_owner': 'absent',
            'expected_present': False,
            'expected_migration_required': False,
            'expected_version': '',
        }
        completed, probes = self.run_case(
            variables,
            ips_result='absent',
            svr4_result='absent',
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('distribution_major_version', completed.stdout)
        self.assertEqual(probes, '')


if __name__ == '__main__':
    unittest.main()
