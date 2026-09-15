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
printf 'pkg' >> "$SAS_IPS_OPERATION_LOG"
for argument in "$@"; do
    printf '\\t%s' "$argument" >> "$SAS_IPS_OPERATION_LOG"
done
printf '\\n' >> "$SAS_IPS_OPERATION_LOG"
case "$1" in
    install) exit "$SAS_FAKE_INSTALL_RC" ;;
    uninstall) exit "$SAS_FAKE_UNINSTALL_RC" ;;
    *) exit 97 ;;
esac
'''


def plan_entry(package, source_path, action='install', owner='absent'):
    return {
        'package': package,
        'state': 'present',
        'installed_version': '' if owner == 'absent' else '6.1.0.4900',
        'owner': owner,
        'migration_required': False,
        'target_version': '7.0.0.8900',
        'source_path': source_path,
        'source_file': os.path.basename(source_path),
        'source_publisher': 'OneIdentity',
        'action': action,
        'requires_source': True,
        'may_remove_installed': False,
    }


def removal_entry(package, owner='ips'):
    return {
        'package': package,
        'state': 'absent',
        'installed_version': '7.0.0.8900' if owner != 'absent' else '',
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


@unittest.skipUnless(PLAYBOOK, 'ansible-playbook is required')
class SolarisIpsPackageOperationTests(unittest.TestCase):

    def run_case(self, plan, staged_sources, expected_processed,
                 install_rc=0, uninstall_rc=0, check_mode=False,
                 expected_actions=None):
        with tempfile.TemporaryDirectory(prefix='sas ips operation ') as temp_dir:
            temp_path = Path(temp_dir)
            bin_path = temp_path / 'bin'
            bin_path.mkdir()
            pkg_path = bin_path / 'pkg'
            pkg_path.write_text(PKG_SCRIPT)
            pkg_path.chmod(pkg_path.stat().st_mode | stat.S_IXUSR)
            log_path = temp_path / 'operations.log'
            environment = dict(os.environ)
            environment.update({
                'ANSIBLE_NOCOLOR': '1',
                'ANSIBLE_ROLES_PATH': str(ROOT / 'roles'),
                'PATH': '{}:{}'.format(bin_path, environment['PATH']),
                'SAS_IPS_OPERATION_LOG': str(log_path),
                'SAS_FAKE_INSTALL_RC': str(install_rc),
                'SAS_FAKE_UNINSTALL_RC': str(uninstall_rc),
            })
            command = [
                PLAYBOOK,
                '-i', 'localhost,',
                '-c', 'local',
                str(FIXTURES / 'ips_package_operations.yml'),
                '-e', json.dumps({
                    'test_package_plan': plan,
                    'test_staged_sources': staged_sources,
                    'expected_processed_packages': expected_processed,
                    'test_reports': expected_actions is not None,
                    'expected_action_facts': expected_actions or {},
                    'expected_request_facts': {
                        entry['package']: entry['state'] for entry in plan
                    },
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
        return completed, log

    def test_fresh_install_uses_staged_archive_and_exact_fmri(self):
        source = '/media/solaris11-sparc/sas.p5p'
        staged = '/var/tmp/ips-stage/000-sas.p5p'
        completed, log = self.run_case(
            [plan_entry('vasclnt', source)],
            [{
                'source_path': source,
                'source_file': 'sas.p5p',
                'staged_path': staged,
            }],
            ['vasclnt'],
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(
            log,
            'pkg\tinstall\t--accept\t-g\t{}\t{}\n'.format(
                staged,
                'pkg://OneIdentity/vasclnt@7.0.0.8900',
            ),
        )
        self.assertNotIn('set-publisher', log)

    def test_packages_sharing_archive_use_one_transaction(self):
        source = '/media/solaris11-sparc/sas.p5p'
        staged = '/var/tmp/ips-stage/000-sas.p5p'
        completed, log = self.run_case(
            [
                plan_entry('vasclnt', source),
                plan_entry('vassc', source),
            ],
            [{
                'source_path': source,
                'source_file': 'sas.p5p',
                'staged_path': staged,
            }],
            ['vasclnt', 'vassc'],
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(len(log.splitlines()), 1, log)
        self.assertIn('\t-g\t{}\t'.format(staged), log)
        self.assertIn('pkg://OneIdentity/vasclnt@7.0.0.8900', log)
        self.assertIn('pkg://OneIdentity/vassc@7.0.0.8900', log)

    def test_same_archive_preserves_independent_component_versions(self):
        source = '/media/solaris11-sparc/sas.p5p'
        staged = '/var/tmp/ips-stage/000-sas.p5p'
        client = plan_entry('vasclnt', source)
        certificate = plan_entry('vascert', source)
        certificate['target_version'] = '1.4.0.70'
        completed, log = self.run_case(
            [client, certificate],
            [{
                'source_path': source,
                'source_file': 'sas.p5p',
                'staged_path': staged,
            }],
            ['vasclnt', 'vascert'],
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('pkg://OneIdentity/vasclnt@7.0.0.8900', log)
        self.assertIn('pkg://OneIdentity/vascert@1.4.0.70', log)

    def test_packages_from_different_archives_use_matching_transactions(self):
        standard = '/media/solaris11-sparc/sas.p5p'
        qa = '/media/solaris11-sparc/sas_qa.p5p'
        standard_stage = '/var/tmp/ips-stage/000-sas.p5p'
        qa_stage = '/var/tmp/ips-stage/001-sas_qa.p5p'
        completed, log = self.run_case(
            [
                plan_entry('vasclnt', standard),
                plan_entry('vasqa', qa),
            ],
            [
                {
                    'source_path': standard,
                    'source_file': 'sas.p5p',
                    'staged_path': standard_stage,
                },
                {
                    'source_path': qa,
                    'source_file': 'sas_qa.p5p',
                    'staged_path': qa_stage,
                },
            ],
            ['vasclnt', 'vasqa'],
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(
            log.splitlines(),
            [
                'pkg\tinstall\t--accept\t-g\t{}\t{}'.format(
                    standard_stage,
                    'pkg://OneIdentity/vasclnt@7.0.0.8900',
                ),
                'pkg\tinstall\t--accept\t-g\t{}\t{}'.format(
                    qa_stage,
                    'pkg://OneIdentity/vasqa@7.0.0.8900',
                ),
            ],
        )

    def test_missing_transition_archive_stops_before_removal(self):
        source = '/media/solaris11-sparc/sas.p5p'
        completed, log = self.run_case(
            [removal_entry('vasgp'), plan_entry('vasclnt', source)],
            [],
            ['vasgp', 'vasclnt'],
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('staged exactly once', completed.stdout)
        self.assertEqual(log, '')

    def test_upgrade_and_downgrade_are_one_in_place_transaction(self):
        source = '/media/solaris11-sparc/sas.p5p'
        staged = '/var/tmp/ips-stage/000-sas.p5p'
        upgrade = plan_entry('vasclnt', source, 'upgrade', 'ips')
        downgrade = plan_entry('vasgp', source, 'downgrade', 'ips')
        downgrade['installed_version'] = '8.0.0.100'
        completed, log = self.run_case(
            [upgrade, downgrade],
            [{
                'source_path': source,
                'source_file': 'sas.p5p',
                'staged_path': staged,
            }],
            ['vasclnt', 'vasgp'],
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(len(log.splitlines()), 1, log)
        self.assertIn('\tinstall\t', log)
        self.assertNotIn('\tuninstall\t', log)

    def test_nothing_to_do_return_code_is_unchanged_success(self):
        source = '/media/solaris11-sparc/sas.p5p'
        completed, log = self.run_case(
            [plan_entry('vasclnt', source)],
            [{
                'source_path': source,
                'source_file': 'sas.p5p',
                'staged_path': '/var/tmp/ips-stage/000-sas.p5p',
            }],
            ['vasclnt'],
            install_rc=4,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('pkg\tinstall', log)
        self.assertIn('changed=0', completed.stdout)

    def test_native_packages_are_removed_in_one_ips_transaction(self):
        completed, log = self.run_case(
            [removal_entry('vasgp'), removal_entry('vasclnt')],
            [],
            ['vasgp', 'vasclnt'],
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(
            log,
            'pkg\tuninstall\tvasgp\tvasclnt\n',
        )

    def test_uninstall_nothing_to_do_return_code_is_unchanged_success(self):
        completed, log = self.run_case(
            [removal_entry('vasclnt')],
            [],
            ['vasclnt'],
            uninstall_rc=4,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, 'pkg\tuninstall\tvasclnt\n')
        self.assertIn('changed=0', completed.stdout)

    def test_failed_uninstall_stops_before_archive_transaction(self):
        source = '/media/solaris11-sparc/sas.p5p'
        completed, log = self.run_case(
            [removal_entry('vasgp'), plan_entry('vasclnt', source)],
            [{
                'source_path': source,
                'source_file': 'sas.p5p',
                'staged_path': '/var/tmp/ips-stage/000-sas.p5p',
            }],
            ['vasgp', 'vasclnt'],
            uninstall_rc=1,
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, 'pkg\tuninstall\tvasgp\n')

    def test_equal_version_and_already_absent_are_no_ops(self):
        equal = plan_entry('vasclnt', '/media/solaris11-sparc/sas.p5p',
                           action='none', owner='ips')
        equal['installed_version'] = equal['target_version']
        equal['requires_source'] = False
        completed, log = self.run_case(
            [equal, removal_entry('vasgp', owner='absent')],
            [],
            [],
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, '')

    def test_native_operations_use_existing_report_actions(self):
        source = '/media/solaris11-sparc/sas.p5p'
        install = plan_entry('vasclnt', source)
        upgrade = plan_entry('vasgp', source, 'upgrade', 'ips')
        downgrade = plan_entry('vassc', source, 'downgrade', 'ips')
        downgrade['installed_version'] = '8.0.0.100'
        remove = removal_entry('vasqa')
        completed, log = self.run_case(
            [install, upgrade, downgrade, remove],
            [{
                'source_path': source,
                'source_file': 'sas.p5p',
                'staged_path': '/var/tmp/ips-stage/000-sas.p5p',
            }],
            ['vasqa', 'vasclnt', 'vasgp', 'vassc'],
            expected_actions={
                'vasclnt': 'installed',
                'vasgp': 'upgraded',
                'vassc': 'downgraded',
                'vasqa': 'removed',
            },
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(
            log.splitlines()[0],
            'pkg\tuninstall\tvasqa',
        )

    def test_failed_transition_never_uninstalls_existing_package(self):
        source = '/media/solaris11-sparc/sas.p5p'
        completed, log = self.run_case(
            [plan_entry('vasclnt', source, 'upgrade', 'ips')],
            [{
                'source_path': source,
                'source_file': 'sas.p5p',
                'staged_path': '/var/tmp/ips-stage/000-sas.p5p',
            }],
            ['vasclnt'],
            install_rc=1,
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('pkg\tinstall', log)
        self.assertNotIn('uninstall', log)

    def test_check_mode_marks_transition_owned_without_running_pkg(self):
        source = '/media/solaris11-sparc/sas.p5p'
        completed, log = self.run_case(
            [plan_entry('vasclnt', source)],
            [{
                'source_path': source,
                'source_file': 'sas.p5p',
                'staged_path': '/var/tmp/ips-stage/000-sas.p5p',
            }],
            ['vasclnt'],
            check_mode=True,
            expected_actions={'vasclnt': 'installed'},
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, '')
        self.assertIn('changed=0', completed.stdout)

    def test_legacy_migration_is_left_for_migration_phase(self):
        source = '/media/solaris11-sparc/sas_site.p5p'
        migration = plan_entry('vasclnts', source, 'upgrade', 'svr4')
        migration['migration_required'] = True
        migration['may_remove_installed'] = True
        completed, log = self.run_case(
            [migration],
            [{
                'source_path': source,
                'source_file': 'sas_site.p5p',
                'staged_path': '/var/tmp/ips-stage/000-sas_site.p5p',
            }],
            [],
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, '')


if __name__ == '__main__':
    unittest.main()
