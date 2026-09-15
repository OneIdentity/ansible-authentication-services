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
if [ "$1" = info ]; then
    package=$2
    state=$(cat "$SAS_LEGACY_STATE_DIR/$package")
    if [ "$state" = ips ]; then
        printf '          Name: %s\\n' "$package"
        printf '       Version: %s\\n' "$(cat "$SAS_LEGACY_STATE_DIR/$package.version")"
        exit 0
    fi
    printf 'pkg: info: no packages matching the following patterns you specified are\\n' >&2
    printf 'installed on the system.  Try querying remotely instead:\\n\\n' >&2
    printf '        %s\\n' "$package" >&2
    exit 1
fi
if [ "$1" = install ]; then
    printf 'pkg' >> "$SAS_LEGACY_OPERATION_LOG"
    for argument in "$@"; do
        printf '\\t%s' "$argument" >> "$SAS_LEGACY_OPERATION_LOG"
        case "$argument" in
            pkg://*)
                package_version=${argument#pkg://}
                package_version=${package_version#*/}
                package=${package_version%@*}
                version=${package_version#*@}
                if [ "$SAS_FAKE_INSTALL_RC" -eq 0 ]; then
                    printf 'ips\\n' > "$SAS_LEGACY_STATE_DIR/$package"
                    printf '%s\\n' "$version" \
                        > "$SAS_LEGACY_STATE_DIR/$package.version"
                fi
                ;;
        esac
    done
    printf '\\n' >> "$SAS_LEGACY_OPERATION_LOG"
    exit "$SAS_FAKE_INSTALL_RC"
fi
exit 97
'''


PKGINFO_SCRIPT = '''#!/bin/sh
package=$2
state=$(cat "$SAS_LEGACY_STATE_DIR/$package")
if [ "$1" = -l ] && [ "$state" = legacy ]; then
    printf '   PKGINST:  %s\\n' "$package"
    printf '   VERSION:  %s\\n' "$(cat "$SAS_LEGACY_STATE_DIR/$package.version")"
    exit 0
fi
printf 'ERROR: information for "%s" was not found\\n' "$package" >&2
exit 1
'''


PKGRM_SCRIPT = '''#!/bin/sh
previous=
package=
printf 'pkgrm-argv' >> "$SAS_LEGACY_OPERATION_LOG"
for argument in "$@"; do
    printf '\\t%s' "$argument" >> "$SAS_LEGACY_OPERATION_LOG"
    if [ "$previous" = '-a' ]; then
        admin_file=$argument
    elif [ "$argument" != '-a' ] && [ -n "$previous" ]; then
        package=$argument
    fi
    previous=$argument
done
printf '\\n' >> "$SAS_LEGACY_OPERATION_LOG"
printf 'pkgrm\\t%s\\t%s\\n' "$package" "$(IFS= read -r answer; printf '%s' "$answer")" \
    >> "$SAS_LEGACY_OPERATION_LOG"
cat "$admin_file" >> "$SAS_LEGACY_OPERATION_LOG"
printf '%s\\n' 'admin-end' >> "$SAS_LEGACY_OPERATION_LOG"
case "$SAS_FAKE_PKGRM_RC" in
    0|2|10|20) printf 'absent\\n' > "$SAS_LEGACY_STATE_DIR/$package" ;;
esac
exit "$SAS_FAKE_PKGRM_RC"
'''


def removal_entry(package, owner='svr4'):
    return {
        'package': package,
        'state': 'absent',
        'installed_version': '6.1.0.4900' if owner != 'absent' else '',
        'owner': owner,
        'migration_required': False,
        'target_version': '',
        'source_path': '',
        'source_file': '',
        'source_publisher': '',
        'action': 'remove' if owner != 'absent' else 'none',
        'requires_source': False,
        'may_remove_installed': owner != 'absent',
    }


def migration_entry(package, installed_version='6.1.0.4900',
                    target_version='7.0.0.8900', action='upgrade',
                    source_path='/media/solaris11-sparc/sas_site.p5p'):
    return {
        'package': package,
        'state': 'present',
        'installed_version': installed_version,
        'owner': 'svr4',
        'migration_required': True,
        'target_version': target_version,
        'source_path': source_path,
        'source_file': os.path.basename(source_path),
        'source_publisher': 'OneIdentity',
        'action': action,
        'requires_source': True,
        'may_remove_installed': True,
    }


@unittest.skipUnless(PLAYBOOK, 'ansible-playbook is required')
class SolarisLegacySvr4MigrationTests(unittest.TestCase):

    def run_case(self, plan, expected_processed, expected_owners=None,
                 expected_versions=None, expected_actions=None, pkgrm_rc=0,
                 install_rc=0, staged_sources=None,
                 expected_rebuilt_plan=False, expected_failure=False,
                 check_mode=False, expected_plan_actions=None):
        with tempfile.TemporaryDirectory(prefix='sas legacy migration ') as temp_dir:
            temp_path = Path(temp_dir)
            bin_path = temp_path / 'bin'
            state_path = temp_path / 'state'
            work_path = temp_path / 'work'
            bin_path.mkdir()
            state_path.mkdir()
            work_path.mkdir()
            for name, content in (
                    ('pkg', PKG_SCRIPT),
                    ('pkginfo', PKGINFO_SCRIPT),
                    ('pkgrm', PKGRM_SCRIPT)):
                command_path = bin_path / name
                command_path.write_text(content)
                command_path.chmod(
                    command_path.stat().st_mode | stat.S_IXUSR
                )
            for entry in plan:
                initial_state = {
                    'svr4': 'legacy',
                    'ips': 'ips',
                    'absent': 'absent',
                }[entry['owner']]
                (state_path / entry['package']).write_text(
                    '{}\n'.format(initial_state)
                )
                (state_path / '{}.version'.format(entry['package'])).write_text(
                    '{}\n'.format(entry['installed_version'])
                )
            log_path = temp_path / 'operations.log'
            environment = dict(os.environ)
            environment.update({
                'ANSIBLE_NOCOLOR': '1',
                'ANSIBLE_ROLES_PATH': str(ROOT / 'roles'),
                'PATH': '{}:{}'.format(bin_path, environment['PATH']),
                'SAS_LEGACY_OPERATION_LOG': str(log_path),
                'SAS_LEGACY_STATE_DIR': str(state_path),
                'SAS_FAKE_PKGRM_RC': str(pkgrm_rc),
                'SAS_FAKE_INSTALL_RC': str(install_rc),
            })
            package_state = {
                entry['package']: entry['state'] for entry in plan
            }
            packages = {
                entry['package']: {
                    'path': entry['source_path'],
                    'file': entry['source_file'],
                    'vers': entry['target_version'],
                    'publisher': entry['source_publisher'],
                }
                for entry in plan if entry['state'] == 'present'
            }
            command = [
                PLAYBOOK,
                '-i', 'localhost,',
                '-c', 'local',
                str(FIXTURES / 'legacy_svr4_migration.yml'),
                '-e', json.dumps({
                    'test_package_plan': plan,
                    'test_temp_dir': str(work_path),
                    'test_package_state': package_state,
                    'test_packages': packages,
                    'test_staged_sources': staged_sources or [],
                    'expected_processed_packages': expected_processed,
                    'expected_final_owners': expected_owners or {},
                    'expected_final_versions': expected_versions or {},
                    'test_reports': expected_actions is not None,
                    'expected_action_facts': expected_actions or {},
                    'expected_request_facts': package_state,
                    'expected_rebuilt_plan': expected_rebuilt_plan,
                    'expected_plan_actions': expected_plan_actions or {},
                    'expected_operation_failure': expected_failure,
                }),
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
            log = log_path.read_text() if log_path.exists() else ''
            admin_files = list(work_path.rglob('*.admin'))
            operation_dirs = list(
                work_path.glob('ansible-as-client-sw-legacy-*')
            )
            self.assertEqual(operation_dirs, [], completed.stdout)
        return completed, log, admin_files

    def test_legacy_absent_request_uses_interactive_pkgrm(self):
        completed, log, admin_files = self.run_case(
            [removal_entry('vasclnts')],
            ['vasclnts'],
            expected_owners={'vasclnts': 'absent'},
            expected_actions={'vasclnts': 'removed'},
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('pkgrm\tvasclnts\ty', log)
        self.assertIn('pkgrm-argv\t-a\t', log)
        self.assertNotIn('\t-n\t', log)
        self.assertNotIn('\tall\n', log)
        self.assertIn('instance=overwrite', log)
        self.assertNotIn('pkgadd', log)
        self.assertEqual(admin_files, [])

    def test_completed_legacy_pkgrm_return_codes_are_accepted(self):
        for return_code in (2, 10, 20):
            with self.subTest(return_code=return_code):
                completed, log, admin_files = self.run_case(
                    [removal_entry('vasclnts')],
                    ['vasclnts'],
                    expected_owners={'vasclnts': 'absent'},
                    expected_actions={'vasclnts': 'removed'},
                    pkgrm_rc=return_code,
                )
                self.assertEqual(completed.returncode, 0, completed.stdout)
                self.assertEqual(log.count('pkgrm\tvasclnts\ty'), 1, log)
                self.assertEqual(admin_files, [])
                if return_code == 2:
                    self.assertIn('warning', completed.stdout)
                else:
                    self.assertIn('reboot required', completed.stdout)

    def test_lower_version_legacy_package_migrates_to_exact_ips_fmri(self):
        entry = migration_entry('vasclnts')
        completed, log, admin_files = self.run_case(
            [entry],
            ['vasclnts'],
            expected_owners={'vasclnts': 'ips'},
            expected_versions={'vasclnts': '7.0.0.8900'},
            expected_actions={'vasclnts': 'upgraded'},
            staged_sources=[{
                'source_path': entry['source_path'],
                'source_file': entry['source_file'],
                'staged_path': '/var/tmp/ips-stage/000-sas_site.p5p',
            }],
            expected_rebuilt_plan=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log.count('pkgrm\tvasclnts\ty'), 1, log)
        self.assertIn(
            'pkg\tinstall\t--accept\t-g\t'
            '/var/tmp/ips-stage/000-sas_site.p5p\t'
            'pkg://OneIdentity/vasclnts@7.0.0.8900',
            log,
        )
        self.assertLess(log.index('pkgrm'), log.index('pkg\tinstall'))
        self.assertEqual(admin_files, [])

    def test_equal_version_legacy_package_is_still_migrated(self):
        entry = migration_entry(
            'vasclnts',
            installed_version='7.0.0.8900',
            target_version='7.0.0.8900',
            action='none',
        )
        completed, log, admin_files = self.run_case(
            [entry],
            ['vasclnts'],
            expected_owners={'vasclnts': 'ips'},
            expected_versions={'vasclnts': '7.0.0.8900'},
            expected_actions={'vasclnts': 'upgraded'},
            staged_sources=[{
                'source_path': entry['source_path'],
                'source_file': entry['source_file'],
                'staged_path': '/var/tmp/ips-stage/000-sas_site.p5p',
            }],
            expected_rebuilt_plan=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log.count('pkgrm\tvasclnts\ty'), 1, log)
        self.assertIn('pkg://OneIdentity/vasclnts@7.0.0.8900', log)
        self.assertEqual(admin_files, [])

    def test_higher_version_legacy_package_reports_downgrade(self):
        entry = migration_entry(
            'vasclnts',
            installed_version='8.0.0.100',
            target_version='7.0.0.8900',
            action='downgrade',
        )
        completed, log, admin_files = self.run_case(
            [entry],
            ['vasclnts'],
            expected_owners={'vasclnts': 'ips'},
            expected_versions={'vasclnts': '7.0.0.8900'},
            expected_actions={'vasclnts': 'downgraded'},
            staged_sources=[{
                'source_path': entry['source_path'],
                'source_file': entry['source_file'],
                'staged_path': '/var/tmp/ips-stage/000-sas_site.p5p',
            }],
            expected_rebuilt_plan=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log.count('pkgrm\tvasclnts\ty'), 1, log)
        self.assertIn('pkg://OneIdentity/vasclnts@7.0.0.8900', log)
        self.assertEqual(admin_files, [])

    def test_shared_archive_migration_removes_client_last_and_installs_once(self):
        client = migration_entry('vasclnts')
        group_policy = migration_entry('vasgps')
        completed, log, admin_files = self.run_case(
            [client, group_policy],
            ['vasclnts', 'vasgps'],
            expected_owners={'vasclnts': 'ips', 'vasgps': 'ips'},
            expected_versions={
                'vasclnts': '7.0.0.8900',
                'vasgps': '7.0.0.8900',
            },
            expected_actions={
                'vasclnts': 'upgraded',
                'vasgps': 'upgraded',
            },
            staged_sources=[{
                'source_path': client['source_path'],
                'source_file': client['source_file'],
                'staged_path': '/var/tmp/ips-stage/000-sas_site.p5p',
            }],
            expected_rebuilt_plan=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertLess(
            log.index('pkgrm\tvasgps\ty'),
            log.index('pkgrm\tvasclnts\ty'),
        )
        self.assertEqual(log.count('pkg\tinstall'), 1, log)
        self.assertIn('pkg://OneIdentity/vasclnts@7.0.0.8900', log)
        self.assertIn('pkg://OneIdentity/vasgps@7.0.0.8900', log)
        self.assertEqual(admin_files, [])

    def test_multi_archive_migration_uses_matching_staged_sources(self):
        standard = migration_entry(
            'vassc', source_path='/media/solaris11-sparc/sas.p5p'
        )
        qa = migration_entry(
            'vasqa', source_path='/media/solaris11-sparc/sas_qa.p5p'
        )
        completed, log, admin_files = self.run_case(
            [standard, qa],
            ['vassc', 'vasqa'],
            expected_owners={'vassc': 'ips', 'vasqa': 'ips'},
            expected_versions={
                'vassc': '7.0.0.8900',
                'vasqa': '7.0.0.8900',
            },
            staged_sources=[
                {
                    'source_path': standard['source_path'],
                    'source_file': standard['source_file'],
                    'staged_path': '/var/tmp/ips-stage/000-sas.p5p',
                },
                {
                    'source_path': qa['source_path'],
                    'source_file': qa['source_file'],
                    'staged_path': '/var/tmp/ips-stage/001-sas_qa.p5p',
                },
            ],
            expected_rebuilt_plan=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        install_lines = [
            line for line in log.splitlines() if line.startswith('pkg\tinstall')
        ]
        self.assertEqual(len(install_lines), 2, log)
        self.assertIn(
            '-g\t/var/tmp/ips-stage/000-sas.p5p\t'
            'pkg://OneIdentity/vassc@7.0.0.8900',
            install_lines[0],
        )
        self.assertIn(
            '-g\t/var/tmp/ips-stage/001-sas_qa.p5p\t'
            'pkg://OneIdentity/vasqa@7.0.0.8900',
            install_lines[1],
        )
        self.assertEqual(admin_files, [])

    def test_missing_migration_archive_stops_before_any_pkgrm(self):
        entry = migration_entry('vasclnts')
        completed, log, admin_files = self.run_case(
            [entry],
            ['vasclnts'],
            expected_failure=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('was not staged exactly once', completed.stdout)
        self.assertEqual(log, '')
        self.assertEqual(admin_files, [])

    def test_mixed_removal_and_migration_use_one_ordered_legacy_phase(self):
        client = migration_entry('vasclnts')
        group_policy = removal_entry('vasgps')
        completed, log, admin_files = self.run_case(
            [client, group_policy],
            ['vasgps', 'vasclnts'],
            expected_owners={'vasclnts': 'ips', 'vasgps': 'absent'},
            expected_versions={
                'vasclnts': '7.0.0.8900',
                'vasgps': '',
            },
            expected_actions={
                'vasclnts': 'upgraded',
                'vasgps': 'removed',
            },
            staged_sources=[{
                'source_path': client['source_path'],
                'source_file': client['source_file'],
                'staged_path': '/var/tmp/ips-stage/000-sas_site.p5p',
            }],
            expected_rebuilt_plan=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertLess(
            log.index('pkgrm\tvasgps\ty'),
            log.index('pkgrm\tvasclnts\ty'),
        )
        self.assertEqual(log.count('pkgrm\tvasgps\ty'), 1, log)
        self.assertEqual(log.count('pkgrm\tvasclnts\ty'), 1, log)
        install_line = next(
            line for line in log.splitlines() if line.startswith('pkg\tinstall')
        )
        self.assertIn('pkg://OneIdentity/vasclnts@7.0.0.8900', install_line)
        self.assertNotIn('vasgps@', install_line)
        self.assertEqual(admin_files, [])

    def test_check_mode_reports_intent_without_package_commands(self):
        migration = migration_entry('vasclnts')
        removal = removal_entry('vasgps')
        completed, log, admin_files = self.run_case(
            [migration, removal],
            ['vasgps', 'vasclnts'],
            expected_actions={
                'vasclnts': 'upgraded',
                'vasgps': 'removed',
            },
            check_mode=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, '')
        self.assertEqual(admin_files, [])
        self.assertIn('changed=0', completed.stdout)

    def test_settled_packages_are_not_processed_again(self):
        migrated = migration_entry('vasclnts')
        migrated.update({
            'installed_version': migrated['target_version'],
            'owner': 'ips',
            'migration_required': False,
            'action': 'none',
            'requires_source': False,
            'may_remove_installed': False,
        })
        already_absent = removal_entry('vasgps', owner='absent')
        completed, log, admin_files = self.run_case(
            [migrated, already_absent],
            [],
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, '')
        self.assertEqual(admin_files, [])

    def test_failed_pkgrm_stops_before_ips_install_and_reports_failure(self):
        entry = migration_entry('vasclnts')
        completed, log, admin_files = self.run_case(
            [entry],
            ['vasclnts'],
            expected_actions={'vasclnts': 'failed'},
            pkgrm_rc=1,
            staged_sources=[{
                'source_path': entry['source_path'],
                'source_file': entry['source_file'],
                'staged_path': '/var/tmp/ips-stage/000-sas_site.p5p',
            }],
            expected_failure=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log.count('pkgrm\tvasclnts\ty'), 1, log)
        self.assertNotIn('pkg\tinstall', log)
        self.assertEqual(admin_files, [])

    def test_failed_ips_install_reports_failure_without_second_removal(self):
        entry = migration_entry('vasclnts')
        completed, log, admin_files = self.run_case(
            [entry],
            ['vasclnts'],
            expected_actions={'vasclnts': 'failed'},
            install_rc=1,
            staged_sources=[{
                'source_path': entry['source_path'],
                'source_file': entry['source_file'],
                'staged_path': '/var/tmp/ips-stage/000-sas_site.p5p',
            }],
            expected_failure=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log.count('pkgrm\tvasclnts\ty'), 1, log)
        self.assertEqual(log.count('pkg\tinstall'), 1, log)
        self.assertEqual(admin_files, [])

    def test_rebuilt_plan_preserves_unrelated_native_install(self):
        legacy = migration_entry('vasclnts')
        native = migration_entry(
            'vasqa', source_path='/media/solaris11-sparc/sas_qa.p5p'
        )
        native.update({
            'installed_version': '',
            'owner': 'absent',
            'migration_required': False,
            'action': 'install',
            'may_remove_installed': False,
        })
        completed, log, admin_files = self.run_case(
            [legacy, native],
            ['vasclnts'],
            expected_owners={'vasclnts': 'ips'},
            expected_versions={'vasclnts': '7.0.0.8900'},
            expected_actions={'vasclnts': 'upgraded'},
            staged_sources=[
                {
                    'source_path': legacy['source_path'],
                    'source_file': legacy['source_file'],
                    'staged_path': '/var/tmp/ips-stage/000-sas_site.p5p',
                },
                {
                    'source_path': native['source_path'],
                    'source_file': native['source_file'],
                    'staged_path': '/var/tmp/ips-stage/001-sas_qa.p5p',
                },
            ],
            expected_plan_actions={
                'vasclnts': 'none',
                'vasqa': 'install',
            },
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('pkg://OneIdentity/vasclnts@7.0.0.8900', log)
        self.assertNotIn('pkg://OneIdentity/vasqa@7.0.0.8900', log)
        self.assertEqual(admin_files, [])


if __name__ == '__main__':
    unittest.main()
