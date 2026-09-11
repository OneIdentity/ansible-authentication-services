import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest

import yaml


from plugins.filter.client_sw_filters import pkg_dict_2_items


ROOT = Path(__file__).resolve().parents[4]
FIXTURES = Path(__file__).resolve().parent / 'fixtures'
PLAYBOOK = shutil.which('ansible-playbook')


SVR4_COMMAND_SCRIPT = '''#!/bin/sh
{
    printf 'command=%s\\n' "$(basename "$0")"
    for argument in "$@"; do
        printf 'argument=%s\\n' "$argument"
    done
    admin_file=
    previous=
    for argument in "$@"; do
        if [ "$previous" = '-a' ]; then
            admin_file=$argument
            break
        fi
        previous=$argument
    done
    printf '%s\\n' 'admin-begin'
    cat "$admin_file"
    printf '%s\\n' 'admin-end'
    IFS= read -r answer || true
    printf 'stdin=%s\\n' "$answer"
} >> "$SAS_SVR4_LOG"
exit "$SAS_SVR4_RC"
'''


@unittest.skipUnless(PLAYBOOK, 'ansible-playbook is required')
class SolarisSvr4PackageOperationTests(unittest.TestCase):

    def run_operation(self, operation, return_code=0, check_mode=False,
                      solaris_major='10'):
        with tempfile.TemporaryDirectory(prefix='sas svr4 ') as temp_dir:
            temp_path = Path(temp_dir)
            bin_path = temp_path / 'bin'
            media_path = temp_path / 'media directory'
            target_path = temp_path / 'target directory'
            bin_path.mkdir()
            media_path.mkdir()
            target_path.mkdir()

            for command_name in ('pkgadd', 'pkgrm'):
                command_path = bin_path / command_name
                command_path.write_text(SVR4_COMMAND_SCRIPT)
                command_path.chmod(
                    command_path.stat().st_mode | stat.S_IXUSR
                )

            package_name = 'vasclnts'
            package_file = '{}.pkg'.format(package_name)
            source_path = media_path / package_file
            source_path.write_text('test package')
            log_path = temp_path / 'svr4.log'
            variables = {
                'test_operation': operation,
                'test_package': package_name,
                'test_solaris_major': solaris_major,
                'test_temp_dir': str(target_path),
                'test_packages': {
                    package_name: {
                        'path': str(source_path),
                        'file': package_file,
                        'vers': '7.0.0.8900',
                    },
                },
            }
            environment = dict(os.environ)
            environment.update({
                'ANSIBLE_NOCOLOR': '1',
                'ANSIBLE_ROLES_PATH': str(ROOT / 'roles'),
                'PATH': '{}:{}'.format(bin_path, environment['PATH']),
                'SAS_SVR4_LOG': str(log_path),
                'SAS_SVR4_RC': str(return_code),
            })
            command = [
                PLAYBOOK,
                '-i', 'localhost,',
                '-c', 'local',
                str(FIXTURES / 'svr4_package_operation.yml'),
                '-e', json.dumps(variables),
            ]
            if check_mode:
                command.append('--check')
            completed = subprocess.run(
                command,
                cwd=str(ROOT),
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=30,
            )
            log = log_path.read_text() if log_path.exists() else ''
            admin_files = list(target_path.rglob('*.admin'))
            staged_path = target_path / 'ansible-as-client_sw' / package_file
        return completed, log, admin_files, str(staged_path)

    def run_playbook(self, fixture, variables, environment=None):
        test_environment = dict(os.environ)
        test_environment.update({
            'ANSIBLE_NOCOLOR': '1',
            'ANSIBLE_ROLES_PATH': str(ROOT / 'roles'),
        })
        if environment:
            test_environment.update(environment)
        return subprocess.run(
            [
                PLAYBOOK,
                '-i', 'localhost,',
                '-c', 'local',
                str(FIXTURES / fixture),
                '-e', json.dumps(variables),
            ],
            cwd=str(ROOT),
            env=test_environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
        )

    def test_install_runs_interactive_pkgadd_for_requested_package(self):
        completed, log, admin_files, staged_path = self.run_operation('install')
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('command=pkgadd', log)
        self.assertIn('argument={}'.format(staged_path), log)
        self.assertIn('argument=vasclnts', log)
        self.assertNotIn('argument=all', log)
        self.assertNotIn('argument=-n', log)
        self.assertNotIn('argument=-G', log)
        self.assertIn('stdin=y', log)
        self.assertIn('instance=overwrite', log)
        self.assertEqual(admin_files, [])

    def test_absent_only_remove_runs_interactive_pkgrm(self):
        completed, log, admin_files, unused_staged_path = self.run_operation(
            'remove'
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('command=pkgrm', log)
        self.assertIn('argument=vasclnts', log)
        self.assertNotIn('argument=all', log)
        self.assertNotIn('argument=-n', log)
        self.assertIn('stdin=y', log)
        self.assertIn('instance=overwrite', log)
        self.assertEqual(admin_files, [])

    def test_completed_svr4_return_codes_are_accepted(self):
        for operation in ('install', 'remove'):
            for return_code in (0, 2, 10, 20):
                with self.subTest(operation=operation, return_code=return_code):
                    completed, unused_log, admin_files, unused_path = (
                        self.run_operation(operation, return_code)
                    )
                    self.assertEqual(
                        completed.returncode, 0, completed.stdout
                    )
                    self.assertEqual(admin_files, [])
                    if return_code == 2:
                        self.assertIn('warning', completed.stdout)
                    if return_code in (10, 20):
                        self.assertIn('reboot required', completed.stdout)

    def test_unexpected_svr4_return_codes_fail_and_clean_admin_file(self):
        for operation in ('install', 'remove'):
            with self.subTest(operation=operation):
                completed, unused_log, admin_files, unused_path = (
                    self.run_operation(operation, 1)
                )
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertEqual(admin_files, [])

    def test_package_commands_are_skipped_in_check_mode(self):
        for operation in ('install', 'remove'):
            with self.subTest(operation=operation):
                completed, log, admin_files, unused_path = self.run_operation(
                    operation, check_mode=True
                )
                self.assertEqual(completed.returncode, 0, completed.stdout)
                self.assertEqual(log, '')
                self.assertEqual(admin_files, [])
                self.assertIn('changed=0', completed.stdout)

    def test_solaris11_rejects_svr4_commands_before_execution(self):
        for operation in ('install', 'remove'):
            with self.subTest(operation=operation):
                completed, log, admin_files, unused_path = self.run_operation(
                    operation, solaris_major='11'
                )
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertIn('native IPS handling', completed.stdout)
                self.assertEqual(log, '')
                self.assertEqual(admin_files, [])

    def test_preflight_stages_every_required_package(self):
        with tempfile.TemporaryDirectory(prefix='sas svr4 ') as temp_dir:
            temp_path = Path(temp_dir)
            media_path = temp_path / 'media directory'
            target_path = temp_path / 'target directory'
            media_path.mkdir()
            target_path.mkdir()
            sources = []
            for package_file in ('vasclnts.pkg', 'vasgps.pkg'):
                source_path = media_path / package_file
                source_path.write_text('test package')
                sources.append({
                    'path': str(source_path),
                    'file': package_file,
                })

            variables = {
                'test_temp_dir': str(target_path),
                'test_required_sources': sources,
                'expected_staged_sources': [
                    source['path'] for source in sources
                ],
            }
            environment = dict(os.environ)
            environment.update({
                'ANSIBLE_NOCOLOR': '1',
                'ANSIBLE_ROLES_PATH': str(ROOT / 'roles'),
            })
            completed = subprocess.run(
                [
                    PLAYBOOK,
                    '-i', 'localhost,',
                    '-c', 'local',
                    str(FIXTURES / 'svr4_preflight.yml'),
                    '-e', json.dumps(variables),
                ],
                cwd=str(ROOT),
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=30,
            )
            staged_files = sorted(
                path.name
                for path in (target_path / 'ansible-as-client_sw').glob('*.pkg')
            )

        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(staged_files, ['vasclnts.pkg', 'vasgps.pkg'])

    def test_missing_late_source_prevents_any_package_removal(self):
        with tempfile.TemporaryDirectory(prefix='sas svr4 ') as temp_dir:
            temp_path = Path(temp_dir)
            bin_path = temp_path / 'bin'
            media_path = temp_path / 'media'
            target_path = temp_path / 'target'
            bin_path.mkdir()
            media_path.mkdir()
            target_path.mkdir()
            command_path = bin_path / 'pkgrm'
            command_path.write_text(SVR4_COMMAND_SCRIPT)
            command_path.chmod(command_path.stat().st_mode | stat.S_IXUSR)
            first_source = media_path / 'vasclnts.pkg'
            first_source.write_text('test package')
            log_path = temp_path / 'svr4.log'
            sources = [
                {'path': str(first_source), 'file': first_source.name},
                {
                    'path': str(media_path / 'missing-vasgps.pkg'),
                    'file': 'missing-vasgps.pkg',
                },
            ]
            completed = self.run_playbook(
                'svr4_preflight.yml',
                {
                    'test_temp_dir': str(target_path),
                    'test_required_sources': sources,
                    'expected_staged_sources': [],
                    'test_remove_package': 'vasclnts',
                },
                {
                    'PATH': '{}:{}'.format(bin_path, os.environ['PATH']),
                    'SAS_SVR4_LOG': str(log_path),
                    'SAS_SVR4_RC': '0',
                },
            )
            log = log_path.read_text() if log_path.exists() else ''
            staged_files = list(
                (target_path / 'ansible-as-client_sw').glob('*.pkg')
            )

        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('missing-vasgps.pkg', completed.stdout)
        self.assertNotIn('command=pkgrm', log)
        self.assertEqual(staged_files, [])

    def test_equal_version_does_not_run_an_svr4_command(self):
        with tempfile.TemporaryDirectory(prefix='sas svr4 ') as temp_dir:
            temp_path = Path(temp_dir)
            bin_path = temp_path / 'bin'
            media_path = temp_path / 'media'
            bin_path.mkdir()
            media_path.mkdir()
            for command_name in ('pkgadd', 'pkgrm'):
                command_path = bin_path / command_name
                command_path.write_text(SVR4_COMMAND_SCRIPT)
                command_path.chmod(
                    command_path.stat().st_mode | stat.S_IXUSR
                )
            source_path = media_path / 'vasclnts.pkg'
            source_path.write_text('test package')
            log_path = temp_path / 'svr4.log'
            variables = {
                'test_package': 'vasclnts',
                'test_temp_dir': str(temp_path / 'target'),
                'test_packages': {
                    'vasclnts': {
                        'path': str(source_path),
                        'file': source_path.name,
                        'vers': '7.0.0.8900',
                    },
                },
                'sas_client_sw_vasclnts_vers_beg': '7.0.0.8900',
            }
            completed = self.run_playbook(
                'svr4_equal_version.yml',
                variables,
                {
                    'PATH': '{}:{}'.format(bin_path, os.environ['PATH']),
                    'SAS_SVR4_LOG': str(log_path),
                    'SAS_SVR4_RC': '0',
                },
            )
            log = log_path.read_text() if log_path.exists() else ''

        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, '')
        self.assertIn('changed=0', completed.stdout)


class SolarisSvr4TaskContractTests(unittest.TestCase):

    def test_preflight_runs_before_package_mutation(self):
        path = ROOT / 'roles/client_sw/tasks/run_package_tasks.yml'
        tasks = yaml.safe_load(path.read_text())
        includes = [task.get('include_tasks') for task in tasks]
        plan_index = includes.index('build_package_plan.yml')
        temp_dir_index = includes.index('temp_dir_create.yml')
        preflight_index = includes.index('preflight_svr4.yml')
        mutation_index = includes.index('run_package_task.yml')
        self.assertEqual(includes.count('preflight_svr4.yml'), 1)
        self.assertLess(plan_index, temp_dir_index)
        self.assertLess(temp_dir_index, preflight_index)
        self.assertLess(preflight_index, mutation_index)
        self.assertEqual(
            tasks[preflight_index]['when'],
            [
                "ansible_facts['os_family'] | lower == 'solaris'",
                "ansible_facts['distribution_major_version'] | int < 11",
            ],
        )

    def test_direct_commands_do_not_use_svr4pkg_or_noninteractive_flag(self):
        task_dir = ROOT / 'roles/client_sw/tasks/os/solaris'
        operation_text = '\n'.join(
            (task_dir / name).read_text()
            for name in ('install.yml', 'remove.yml')
        )
        self.assertNotIn('svr4pkg:', operation_text)
        self.assertNotRegex(operation_text, r'(^|\s)-n(?:\s|$)')
        self.assertNotRegex(operation_text, r'(^|\s)-G(?:\s|$)')
        self.assertIn('yes | pkgadd', operation_text)
        self.assertIn('yes | pkgrm', operation_text)

    def test_existing_filter_preserves_client_operation_order(self):
        package_states = {
            'vassc': 'present',
            'vasclnt': 'present',
            'vasgp': 'absent',
            'vasclnts': 'absent',
        }
        ordered = pkg_dict_2_items(dict(package_states))
        self.assertEqual(
            [item['key'] for item in ordered],
            ['vasgp', 'vasclnts', 'vasclnt', 'vassc'],
        )


if __name__ == '__main__':
    unittest.main()