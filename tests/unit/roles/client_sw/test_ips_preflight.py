import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[4]
FIXTURES = Path(__file__).resolve().parent / 'fixtures'
PLAYBOOK = shutil.which('ansible-playbook')


PKG_SCRIPT = '''#!/bin/sh
printf 'pkg %s\\n' "$*" >> "$SAS_IPS_LOG"
if [ "$1" = version ]; then
    printf 'test-version\\n'
    exit 0
fi
if [ "$1" = list-linked ] && [ "$2" = -H ]; then
    printf '%s\\n' "$SAS_FAKE_LINKED_OUTPUT"
    exit "$SAS_FAKE_LINKED_RC"
fi
printf 'unexpected pkg command: %s\\n' "$*" >&2
exit 97
'''


PKGREPO_SCRIPT = '''#!/bin/sh
printf 'pkgrepo %s\\n' "$*" >> "$SAS_IPS_LOG"
if [ "$1" = version ]; then
    printf 'test-version\\n'
    exit "$SAS_FAKE_PKGREPO_VERSION_RC"
fi
if [ "$1" = -s ] && [ "$3" = list ]; then
    if [ "$4" = "$SAS_FAKE_PKGREPO_ERROR_FMRI" ]; then
        printf 'pkgrepo: archive query failed\n' >&2
        exit 2
    fi
    case ";$SAS_FAKE_FMRIS;" in
        *";$4;"*)
            printf 'PUBLISHER NAME O VERSION\\n'
            exit 0
            ;;
        *)
            printf 'pkgrepo list: pattern did not match: %s\\n' "$4" >&2
            exit 1
            ;;
    esac
fi
exit 97
'''


MUTATION_SCRIPT = '''#!/bin/sh
printf '%s %s\n' "$(basename "$0")" "$*" >> "$SAS_IPS_LOG"
exit 0
'''


@unittest.skipUnless(PLAYBOOK, 'ansible-playbook is required')
class SolarisIpsPreflightTests(unittest.TestCase):

    def run_case(self, variables, linked_output='', linked_rc=0,
                 source_files=None, fmris=None, query_error_fmri='',
                 pkgrepo_version_rc=0, check_mode=False):
        stages_before = set(Path('/var/tmp').glob(
            'ansible-as-client-sw-ips-*'
        ))
        with tempfile.TemporaryDirectory(prefix='sas ips ') as temp_dir:
            temp_path = Path(temp_dir)
            bin_path = temp_path / 'bin'
            media_path = temp_path / 'media directory'
            bin_path.mkdir()
            media_path.mkdir()
            for name, content in (
                    ('pkg', PKG_SCRIPT),
                    ('pkgrepo', PKGREPO_SCRIPT),
                    ('pkgrm', MUTATION_SCRIPT)):
                script = bin_path / name
                script.write_text(content)
                script.chmod(script.stat().st_mode | stat.S_IXUSR)

            for name in source_files or []:
                (media_path / name).write_text('test archive')

            serialized_variables = json.dumps(variables).replace(
                '__MEDIA__', str(media_path)
            )

            log_path = temp_path / 'ips.log'
            environment = dict(os.environ)
            environment.update({
                'ANSIBLE_NOCOLOR': '1',
                'ANSIBLE_ROLES_PATH': str(ROOT / 'roles'),
                'PATH': '{}:{}'.format(bin_path, environment['PATH']),
                'SAS_IPS_LOG': str(log_path),
                'SAS_FAKE_LINKED_OUTPUT': linked_output,
                'SAS_FAKE_LINKED_RC': str(linked_rc),
                'SAS_FAKE_FMRIS': ';'.join(fmris or []),
                'SAS_FAKE_PKGREPO_ERROR_FMRI': query_error_fmri,
                'SAS_FAKE_PKGREPO_VERSION_RC': str(pkgrepo_version_rc),
            })
            command = [
                PLAYBOOK,
                '-i', 'localhost,',
                '-c', 'local',
                str(FIXTURES / 'ips_preflight.yml'),
                '-e', serialized_variables,
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
        leaked_stages = set(Path('/var/tmp').glob(
            'ansible-as-client-sw-ips-*'
        )) - stages_before
        for path in leaked_stages:
            shutil.rmtree(str(path), ignore_errors=True)
        return completed, log, leaked_stages

    def test_linked_child_is_rejected_before_archive_or_mutation_commands(self):
        source = '/media/solaris11-sparc/sas.p5p'
        variables = {
            'test_package_plan': [{
                'package': 'vasclnt',
                'state': 'present',
                'installed_version': '6.1.0.4900',
                'owner': 'ips',
                'migration_required': False,
                'target_version': '7.0.0.8900',
                'source_path': source,
                'source_file': 'sas.p5p',
                'source_publisher': 'OneIdentity',
                'action': 'upgrade',
                'requires_source': True,
                'may_remove_installed': False,
            }],
            'test_required_sources': [{
                'path': source,
                'file': 'sas.p5p',
            }],
        }
        completed, log, leaked_stages = self.run_case(
            variables,
            linked_output='zone1 child /zones/zone1',
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('linked images are not supported', completed.stdout)
        self.assertEqual(log, 'pkg list-linked -H\n')
        self.assertEqual(leaked_stages, set())

    def test_linked_parent_is_rejected_before_archive_or_mutation_commands(self):
        variables = {
            'test_package_plan': [],
            'test_required_sources': [],
            'test_mutation_package': 'vasclnt',
        }
        completed, log, leaked_stages = self.run_case(
            variables,
            linked_output='global parent /',
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('linked images are not supported', completed.stdout)
        self.assertIn('themselves linked children', completed.stdout)
        self.assertEqual(log, 'pkg list-linked -H\n')
        self.assertEqual(leaked_stages, set())

    def test_topology_query_error_fails_before_archive_or_mutation_commands(self):
        variables = {
            'test_package_plan': [],
            'test_required_sources': [],
            'test_mutation_package': 'vasclnt',
        }
        completed, log, leaked_stages = self.run_case(
            variables,
            linked_rc=2,
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, 'pkg list-linked -H\n')
        self.assertEqual(leaked_stages, set())

    def test_absent_request_checks_tools_without_staging(self):
        variables = {
            'test_package_plan': [{
                'package': 'vasclnt',
                'state': 'absent',
                'installed_version': '7.0.0.8900',
                'owner': 'ips',
                'migration_required': False,
                'target_version': '',
                'source_path': '',
                'source_file': '',
                'source_publisher': '',
                'action': 'remove',
                'requires_source': False,
                'may_remove_installed': True,
            }],
            'test_required_sources': [],
            'test_mutation_package': 'vasclnt',
            'expected_staged_source_count': 0,
        }
        completed, log, leaked_stages = self.run_case(variables)
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(
            log,
            'pkg list-linked -H\npkgrepo version\npkgrm vasclnt\n',
        )
        self.assertEqual(leaked_stages, set())

    def test_unlinked_preflight_stages_all_archives_and_exact_fmris(self):
        standard = '__MEDIA__/sas.p5p'
        qa = '__MEDIA__/sas_qa.p5p'
        variables = {
            'test_package_plan': [
                {
                    'package': 'vasclnt',
                    'state': 'present',
                    'installed_version': '6.1.0.4900',
                    'owner': 'ips',
                    'migration_required': False,
                    'target_version': '7.0.0.8900',
                    'source_path': standard,
                    'source_file': 'sas.p5p',
                    'source_publisher': 'OneIdentity',
                    'action': 'upgrade',
                    'requires_source': True,
                    'may_remove_installed': False,
                },
                {
                    'package': 'vasqa',
                    'state': 'present',
                    'installed_version': '',
                    'owner': 'absent',
                    'migration_required': False,
                    'target_version': '7.0.0.8900',
                    'source_path': qa,
                    'source_file': 'sas_qa.p5p',
                    'source_publisher': 'OneIdentity',
                    'action': 'install',
                    'requires_source': True,
                    'may_remove_installed': False,
                },
            ],
            'test_required_sources': [
                {'path': standard, 'file': 'sas.p5p'},
                {'path': qa, 'file': 'sas_qa.p5p'},
            ],
            'expected_staged_source_count': 2,
        }
        expected_fmris = [
            'pkg://OneIdentity/vasclnt@7.0.0.8900',
            'pkg://OneIdentity/vasqa@7.0.0.8900',
        ]
        completed, log, leaked_stages = self.run_case(
            variables,
            source_files=['sas.p5p', 'sas_qa.p5p'],
            fmris=expected_fmris,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('pkg list-linked -H', log)
        self.assertIn('pkgrepo version', log)
        for fmri in expected_fmris:
            self.assertIn(' list {}\n'.format(fmri), log)
        self.assertEqual(leaked_stages, set())

    def test_missing_final_archive_stops_before_mutation_or_staging(self):
        first = '__MEDIA__/sas.p5p'
        missing = '__MEDIA__/missing-qa.p5p'
        variables = {
            'test_package_plan': [
                self.plan_entry('vasclnt', first, 'sas.p5p'),
                self.plan_entry('vasqa', missing, 'missing-qa.p5p'),
            ],
            'test_required_sources': [
                {'path': first, 'file': 'sas.p5p'},
                {'path': missing, 'file': 'missing-qa.p5p'},
            ],
            'test_mutation_package': 'vasclnt',
        }
        completed, log, leaked_stages = self.run_case(
            variables,
            source_files=['sas.p5p'],
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('missing-qa.p5p', completed.stdout)
        self.assertNotIn('pkgrm ', log)
        self.assertNotIn('set-publisher', log)
        self.assertNotIn('pkgrepo -s', log)
        self.assertEqual(leaked_stages, set())

    def test_wrong_final_fmri_stops_before_mutation_and_cleans_stage(self):
        standard = '__MEDIA__/sas.p5p'
        qa = '__MEDIA__/sas_qa.p5p'
        vasclnt_fmri = 'pkg://OneIdentity/vasclnt@7.0.0.8900'
        vasqa_fmri = 'pkg://OneIdentity/vasqa@7.0.0.8900'
        variables = {
            'test_package_plan': [
                self.plan_entry('vasclnt', standard, 'sas.p5p'),
                self.plan_entry('vasqa', qa, 'sas_qa.p5p'),
            ],
            'test_required_sources': [
                {'path': standard, 'file': 'sas.p5p'},
                {'path': qa, 'file': 'sas_qa.p5p'},
            ],
            'test_mutation_package': 'vasclnt',
        }
        completed, log, leaked_stages = self.run_case(
            variables,
            source_files=['sas.p5p', 'sas_qa.p5p'],
            fmris=[vasclnt_fmri],
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('Required exact FMRI', completed.stdout)
        self.assertIn(' list {}\n'.format(vasclnt_fmri), log)
        self.assertIn(' list {}\n'.format(vasqa_fmri), log)
        self.assertNotIn('pkgrm ', log)
        self.assertNotIn('set-publisher', log)
        self.assertEqual(leaked_stages, set())

    def test_archive_query_error_stops_before_mutation_and_cleans_stage(self):
        source = '__MEDIA__/sas.p5p'
        fmri = 'pkg://OneIdentity/vasclnt@7.0.0.8900'
        variables = {
            'test_package_plan': [
                self.plan_entry('vasclnt', source, 'sas.p5p'),
            ],
            'test_required_sources': [
                {'path': source, 'file': 'sas.p5p'},
            ],
            'test_mutation_package': 'vasclnt',
        }
        completed, log, leaked_stages = self.run_case(
            variables,
            source_files=['sas.p5p'],
            fmris=[fmri],
            query_error_fmri=fmri,
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('archive query failed', completed.stdout)
        self.assertNotIn('pkgrm ', log)
        self.assertNotIn('set-publisher', log)
        self.assertEqual(leaked_stages, set())

    def test_missing_pkgrepo_fails_before_staging_or_mutation(self):
        source = '__MEDIA__/sas.p5p'
        variables = {
            'test_package_plan': [
                self.plan_entry('vasclnt', source, 'sas.p5p'),
            ],
            'test_required_sources': [
                {'path': source, 'file': 'sas.p5p'},
            ],
            'test_mutation_package': 'vasclnt',
        }
        completed, log, leaked_stages = self.run_case(
            variables,
            source_files=['sas.p5p'],
            pkgrepo_version_rc=127,
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(
            log,
            'pkg list-linked -H\npkgrepo version\n',
        )
        self.assertEqual(leaked_stages, set())

    def test_staging_allocation_failure_stops_before_mutation(self):
        source = '__MEDIA__/sas.p5p'
        variables = {
            'test_package_plan': [
                self.plan_entry('vasclnt', source, 'sas.p5p'),
            ],
            'test_required_sources': [
                {'path': source, 'file': 'sas.p5p'},
            ],
            'test_mutation_package': 'vasclnt',
            'sas_client_sw_ips_stage_root': '__MEDIA__/not-a-directory',
        }
        completed, log, leaked_stages = self.run_case(
            variables,
            source_files=['sas.p5p', 'not-a-directory'],
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertNotIn('pkgrm ', log)
        self.assertNotIn('set-publisher', log)
        self.assertNotIn('pkgrepo -s', log)
        self.assertEqual(leaked_stages, set())

    def test_check_mode_runs_queries_without_staging_or_mutation(self):
        source = '__MEDIA__/sas.p5p'
        variables = {
            'test_package_plan': [
                self.plan_entry('vasclnt', source, 'sas.p5p'),
            ],
            'test_required_sources': [
                {'path': source, 'file': 'sas.p5p'},
            ],
            'test_mutation_package': 'vasclnt',
        }
        completed, log, leaked_stages = self.run_case(
            variables,
            source_files=['sas.p5p'],
            check_mode=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(
            log,
            'pkg list-linked -H\npkgrepo version\n',
        )
        self.assertIn('changed=0', completed.stdout)
        self.assertEqual(leaked_stages, set())

    @staticmethod
    def plan_entry(package, source_path, source_file):
        return {
            'package': package,
            'state': 'present',
            'installed_version': '',
            'owner': 'absent',
            'migration_required': False,
            'target_version': '7.0.0.8900',
            'source_path': source_path,
            'source_file': source_file,
            'source_publisher': 'OneIdentity',
            'action': 'install',
            'requires_source': True,
            'may_remove_installed': False,
        }


class SolarisIpsPreflightTaskContractTests(unittest.TestCase):

    def test_preflight_wraps_mutation_and_cleanup_runs_in_always(self):
        path = ROOT / 'roles/client_sw/tasks/run_package_tasks.yml'
        tasks = yaml.safe_load(path.read_text())
        operation_task = next(
            task for task in tasks
            if task.get('name') == 'preflight and perform package operations'
        )
        block_includes = [
            task.get('include_tasks') for task in operation_task['block']
        ]
        always_includes = [
            task.get('include_tasks') for task in operation_task['always']
        ]
        self.assertEqual(block_includes.count('preflight_ips.yml'), 1)
        self.assertLess(
            block_includes.index('preflight_ips.yml'),
            block_includes.index('migrate_legacy_svr4.yml'),
        )
        self.assertLess(
            block_includes.index('migrate_legacy_svr4.yml'),
            block_includes.index('run_ips_operations.yml'),
        )
        self.assertLess(
            block_includes.index('run_ips_operations.yml'),
            block_includes.index('run_package_task.yml'),
        )
        self.assertEqual(always_includes, ['cleanup_ips.yml'])
        ips_task = operation_task['block'][
            block_includes.index('preflight_ips.yml')
        ]
        self.assertEqual(
            ips_task['when'],
            [
                "ansible_facts['os_family'] | lower == 'solaris'",
                "ansible_facts['distribution_major_version'] | int >= 11",
            ],
        )
        ips_operation_task = operation_task['block'][
            block_includes.index('run_ips_operations.yml')
        ]
        migration_task = operation_task['block'][
            block_includes.index('migrate_legacy_svr4.yml')
        ]
        self.assertEqual(migration_task['when'], ips_task['when'])
        self.assertEqual(
            ips_operation_task['when'],
            [
                "ansible_facts['os_family'] | lower == 'solaris'",
                "ansible_facts['distribution_major_version'] | int >= 11",
            ],
        )
        ordinary_task = operation_task['block'][
            block_includes.index('run_package_task.yml')
        ]
        self.assertEqual(
            ordinary_task['when'],
            [
                "item.key not in (sas_client_sw_ips_processed_packages "
                "| default([]))",
                "item.key not in (sas_client_sw_legacy_processed_packages "
                "| default([]))",
            ],
        )

    def test_step5_tasks_do_not_mutate_packages_or_publishers(self):
        task_dir = ROOT / 'roles/client_sw/tasks'
        task_text = '\n'.join(
            (task_dir / name).read_text()
            for name in ('preflight_ips.yml', 'cleanup_ips.yml')
        )
        for command in (
                'pkg install',
                'pkg uninstall',
                'pkg set-publisher',
                'pkg unset-publisher',
                'pkgadd',
                'pkgrm'):
            with self.subTest(command=command):
                self.assertNotIn(command, task_text)

    def test_native_ips_tasks_do_not_mutate_publishers_or_use_svr4(self):
        task_dir = ROOT / 'roles/client_sw/tasks'
        task_text = '\n'.join(
            (task_dir / name).read_text()
            for name in (
                'run_ips_operations.yml',
                'run_ips_archive_transaction.yml',
            )
        )
        for command in ('set-publisher', 'unset-publisher', 'pkgadd', 'pkgrm'):
            with self.subTest(command=command):
                self.assertNotIn(command, task_text)

    def test_legacy_migration_does_not_mutate_publishers_or_use_pkgadd(self):
        task_dir = ROOT / 'roles/client_sw/tasks'
        task_text = '\n'.join(
            (task_dir / name).read_text()
            for name in (
                'migrate_legacy_svr4.yml',
                'remove_legacy_svr4_package.yml',
                'run_legacy_ips_archive_transaction.yml',
            )
        )
        for command in (
                'set-publisher',
                'unset-publisher',
                'pkg uninstall',
                'pkgadd',
                'pkgrm -n'):
            with self.subTest(command=command):
                self.assertNotIn(command, task_text)


if __name__ == '__main__':
    unittest.main()
