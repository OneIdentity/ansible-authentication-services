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


SVCS_SCRIPT = '''#!/bin/sh
printf 'svcs' >> "$SAS_FINAL_STATE_LOG"
for argument in "$@"; do
    printf '\\t%s' "$argument" >> "$SAS_FINAL_STATE_LOG"
done
printf '\\n' >> "$SAS_FINAL_STATE_LOG"
if [ "$SAS_FAKE_SVCS_RC" -ne 0 ]; then
    exit "$SAS_FAKE_SVCS_RC"
fi
printf '%s' "$SAS_FAKE_SMF_OUTPUT"
'''


@unittest.skipUnless(PLAYBOOK, 'ansible-playbook is required')
class SolarisFinalStateTests(unittest.TestCase):

    def run_case(self, package_state, packages, final_packages,
                 solaris_major='11', vasd_registered=True,
                 vasd_state='online', vgp_services=None, svcs_rc=0,
                 ips_stage=None, ips_staged_sources=None,
                 leak_ips_stage=False, leak_legacy_stage=False,
                 check_mode=False):
        final_packages = dict(final_packages)
        for service_package in ('vasclnt', 'vasclnts', 'vasgp', 'vasgps'):
            final_packages.setdefault(
                service_package,
                {'owner': 'absent', 'version': ''},
            )
        with tempfile.TemporaryDirectory(prefix='sas final state ') as temp_dir:
            temp_path = Path(temp_dir)
            bin_path = temp_path / 'bin'
            bin_path.mkdir()
            svcs_path = bin_path / 'svcs'
            svcs_path.write_text(SVCS_SCRIPT)
            svcs_path.chmod(svcs_path.stat().st_mode | stat.S_IXUSR)
            legacy_stage_path = temp_path / 'legacy-stage'
            ips_stage_path = temp_path / 'ips-stage'
            if leak_ips_stage:
                ips_stage_path.mkdir()
            if leak_legacy_stage:
                legacy_stage_path.mkdir()
            log_path = temp_path / 'commands.log'
            environment = dict(os.environ)
            smf_lines = []
            if vasd_registered:
                smf_lines.append(
                    'svc:/quest/vas/vasd:default {}'.format(vasd_state)
                )
            for fmri, state in (vgp_services or {}).items():
                smf_lines.append('{} {}'.format(fmri, state))
            environment.update({
                'ANSIBLE_NOCOLOR': '1',
                'ANSIBLE_ROLES_PATH': str(ROOT / 'roles'),
                'PATH': '{}:{}'.format(bin_path, environment['PATH']),
                'SAS_FINAL_STATE_LOG': str(log_path),
                'SAS_FAKE_SVCS_RC': str(svcs_rc),
                'SAS_FAKE_SMF_OUTPUT': (
                    '\n'.join(smf_lines) + ('\n' if smf_lines else '')
                ),
            })
            command = [
                PLAYBOOK,
                '-i', 'localhost,',
                '-c', 'local',
                str(FIXTURES / 'solaris_final_state.yml'),
                '-e', json.dumps({
                    'test_solaris_major': solaris_major,
                    'test_package_state': package_state,
                    'test_packages': packages,
                    'test_final_packages': final_packages,
                    'test_ips_stage': ips_stage or {},
                    'test_ips_staged_sources': ips_staged_sources or [],
                    'test_ips_cleaned_stage_path': (
                        str(ips_stage_path) if leak_ips_stage else ''
                    ),
                    'test_legacy_stage': (
                        {'path': str(legacy_stage_path)}
                        if leak_legacy_stage else {}
                    ),
                }),
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
        return completed, log

    def test_success_or_noop_with_wrong_final_version_fails(self):
        completed, log = self.run_case(
            {'vasclnts': 'present'},
            {'vasclnts': {'vers': '7.0.0.8900'}},
            {'vasclnts': {'owner': 'ips', 'version': '6.1.0.4900'}},
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('does not match requested version', completed.stdout)
        self.assertEqual(log, '')

    def test_present_solaris11_package_requires_ips_ownership(self):
        completed, log = self.run_case(
            {'vassc': 'present'},
            {'vassc': {'vers': '7.0.0.8900'}},
            {'vassc': {'owner': 'svr4', 'version': '7.0.0.8900'}},
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('native ips ownership', completed.stdout)
        self.assertEqual(log, '')

    def test_present_solaris10_package_requires_exact_svr4_state(self):
        completed, log = self.run_case(
            {'vassc': 'present'},
            {'vassc': {'vers': '7.0.0.8900'}},
            {'vassc': {'owner': 'svr4', 'version': '7.0.0.8900'}},
            solaris_major='10',
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, '')

    def test_absent_package_rejects_remaining_legacy_registration(self):
        completed, log = self.run_case(
            {'vasgps': 'absent'},
            {},
            {'vasgps': {'owner': 'svr4', 'version': '6.1.0.4900'}},
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('remains registered', completed.stdout)
        self.assertEqual(log, '')

    def test_absent_package_rejects_remaining_ips_registration(self):
        completed, log = self.run_case(
            {'vasgps': 'absent'},
            {},
            {'vasgps': {'owner': 'ips', 'version': '7.0.0.8900'}},
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('remains registered', completed.stdout)
        self.assertEqual(log, '')

    def test_absent_non_client_package_succeeds_without_service_query(self):
        completed, log = self.run_case(
            {'vassc': 'absent'},
            {},
            {'vassc': {'owner': 'absent', 'version': ''}},
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, '')

    def test_present_client_requires_vasd_registration(self):
        completed, log = self.run_case(
            {'vasclnt': 'check', 'vasclnts': 'present'},
            {'vasclnts': {'vers': '7.0.0.8900'}},
            {
                'vasclnt': {'owner': 'absent', 'version': ''},
                'vasclnts': {'owner': 'ips', 'version': '7.0.0.8900'},
            },
            vasd_registered=False,
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('vasd:default is not registered', completed.stdout)
        self.assertEqual(log, 'svcs\t-aH\t-o\tFMRI,STATE\n')

    def test_present_client_with_vasd_registration_succeeds(self):
        completed, log = self.run_case(
            {'vasclnt': 'check', 'vasclnts': 'present'},
            {'vasclnts': {'vers': '7.0.0.8900'}},
            {
                'vasclnt': {'owner': 'absent', 'version': ''},
                'vasclnts': {'owner': 'ips', 'version': '7.0.0.8900'},
            },
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, 'svcs\t-aH\t-o\tFMRI,STATE\n')

    def test_present_client_requires_vasd_running(self):
        completed, log = self.run_case(
            {'vasclnt': 'check', 'vasclnts': 'present'},
            {'vasclnts': {'vers': '7.0.0.8900'}},
            {
                'vasclnt': {'owner': 'absent', 'version': ''},
                'vasclnts': {'owner': 'ips', 'version': '7.0.0.8900'},
            },
            vasd_state='offline',
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('vasd:default is not online', completed.stdout)
        self.assertEqual(log, 'svcs\t-aH\t-o\tFMRI,STATE\n')

    def test_solaris10_client_requires_vasd_registration(self):
        completed, log = self.run_case(
            {'vasclnt': 'present', 'vasclnts': 'check'},
            {'vasclnt': {'vers': '7.0.0.8900'}},
            {
                'vasclnt': {'owner': 'svr4', 'version': '7.0.0.8900'},
                'vasclnts': {'owner': 'absent', 'version': ''},
            },
            solaris_major='10',
            vasd_registered=False,
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('vasd:default is not registered', completed.stdout)
        self.assertEqual(log, 'svcs\t-aH\t-o\tFMRI,STATE\n')

    def test_complete_client_removal_rejects_remaining_vasd_registration(self):
        completed, log = self.run_case(
            {'vasclnt': 'check', 'vasclnts': 'absent'},
            {},
            {
                'vasclnt': {'owner': 'absent', 'version': ''},
                'vasclnts': {'owner': 'absent', 'version': ''},
                'vasgp': {'owner': 'absent', 'version': ''},
                'vasgps': {'owner': 'absent', 'version': ''},
            },
            vasd_registered=True,
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('vasd:default remains registered', completed.stdout)
        self.assertEqual(log, 'svcs\t-aH\t-o\tFMRI,STATE\n')

    def test_complete_client_removal_without_vasd_succeeds(self):
        completed, log = self.run_case(
            {'vasclnt': 'check', 'vasclnts': 'absent'},
            {},
            {
                'vasclnt': {'owner': 'absent', 'version': ''},
                'vasclnts': {'owner': 'absent', 'version': ''},
                'vasgp': {'owner': 'absent', 'version': ''},
                'vasgps': {'owner': 'absent', 'version': ''},
            },
            vasd_registered=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, 'svcs\t-aH\t-o\tFMRI,STATE\n')

    def test_removing_one_client_allows_service_for_installed_alternative(self):
        completed, log = self.run_case(
            {'vasclnt': 'check', 'vasclnts': 'absent'},
            {},
            {
                'vasclnt': {'owner': 'ips', 'version': '7.0.0.8900'},
                'vasclnts': {'owner': 'absent', 'version': ''},
            },
            vasd_registered=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, 'svcs\t-aH\t-o\tFMRI,STATE\n')

    def test_partial_client_removal_checks_complete_service_ownership(self):
        completed, log = self.run_case(
            {'vasclnts': 'absent'},
            {},
            {
                'vasclnt': {'owner': 'absent', 'version': ''},
                'vasclnts': {'owner': 'absent', 'version': ''},
                'vasgp': {'owner': 'absent', 'version': ''},
                'vasgps': {'owner': 'absent', 'version': ''},
            },
            vasd_registered=True,
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('vasd:default remains registered', completed.stdout)
        self.assertEqual(log, 'svcs\t-aH\t-o\tFMRI,STATE\n')

    def test_vasd_query_error_fails_closed(self):
        completed, log = self.run_case(
            {'vasclnt': 'check', 'vasclnts': 'present'},
            {'vasclnts': {'vers': '7.0.0.8900'}},
            {
                'vasclnt': {'owner': 'absent', 'version': ''},
                'vasclnts': {'owner': 'ips', 'version': '7.0.0.8900'},
            },
            svcs_rc=2,
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('Could not query final Solaris SMF state', completed.stdout)
        self.assertEqual(log, 'svcs\t-aH\t-o\tFMRI,STATE\n')

    def test_present_solaris11_group_policy_requires_config_service_online(self):
        completed, log = self.run_case(
            {'vasgps': 'present'},
            {'vasgps': {'vers': '7.0.0.8900'}},
            {'vasgps': {'owner': 'ips', 'version': '7.0.0.8900'}},
            vgp_services={
                'svc:/site/vasgps-config:default': 'offline',
            },
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('vasgps-config:default is not online', completed.stdout)
        self.assertEqual(log, 'svcs\t-aH\t-o\tFMRI,STATE\n')

    def test_present_solaris11_group_policy_service_online_succeeds(self):
        completed, log = self.run_case(
            {'vasgps': 'present'},
            {'vasgps': {'vers': '7.0.0.8900'}},
            {'vasgps': {'owner': 'ips', 'version': '7.0.0.8900'}},
            vgp_services={
                'svc:/site/vasgps-config:default': 'online',
            },
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, 'svcs\t-aH\t-o\tFMRI,STATE\n')

    def test_present_standard_group_policy_uses_matching_config_service(self):
        completed, log = self.run_case(
            {'vasgp': 'present'},
            {'vasgp': {'vers': '7.0.0.8900'}},
            {'vasgp': {'owner': 'ips', 'version': '7.0.0.8900'}},
            vgp_services={
                'svc:/site/vasgp-config:default': 'online',
            },
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, 'svcs\t-aH\t-o\tFMRI,STATE\n')

    def test_present_group_policy_requires_shared_vasd_online(self):
        completed, log = self.run_case(
            {'vasgps': 'present'},
            {'vasgps': {'vers': '7.0.0.8900'}},
            {'vasgps': {'owner': 'ips', 'version': '7.0.0.8900'}},
            vasd_state='offline',
            vgp_services={
                'svc:/site/vasgps-config:default': 'online',
            },
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('vasd:default is not online', completed.stdout)
        self.assertEqual(log, 'svcs\t-aH\t-o\tFMRI,STATE\n')

    def test_present_solaris10_group_policy_uses_shared_vasd(self):
        completed, log = self.run_case(
            {'vasgps': 'present'},
            {'vasgps': {'vers': '7.0.0.8900'}},
            {'vasgps': {'owner': 'svr4', 'version': '7.0.0.8900'}},
            solaris_major='10',
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, 'svcs\t-aH\t-o\tFMRI,STATE\n')

    def test_removed_solaris11_group_policy_rejects_online_service(self):
        completed, log = self.run_case(
            {'vasgps': 'absent'},
            {},
            {'vasgps': {'owner': 'absent', 'version': ''}},
            vasd_registered=False,
            vgp_services={
                'svc:/site/vasgps-config:default': 'online',
            },
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('vasgps-config:default is not stopped', completed.stdout)
        self.assertEqual(log, 'svcs\t-aH\t-o\tFMRI,STATE\n')

    def test_removed_solaris11_group_policy_rejects_maintenance_service(self):
        completed, log = self.run_case(
            {'vasgps': 'absent'},
            {},
            {'vasgps': {'owner': 'absent', 'version': ''}},
            vasd_registered=False,
            vgp_services={
                'svc:/site/vasgps-config:default': 'maintenance',
            },
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('vasgps-config:default is not stopped', completed.stdout)
        self.assertEqual(log, 'svcs\t-aH\t-o\tFMRI,STATE\n')

    def test_removed_solaris11_group_policy_service_stopped_succeeds(self):
        completed, log = self.run_case(
            {'vasgps': 'absent'},
            {},
            {'vasgps': {'owner': 'absent', 'version': ''}},
            vasd_registered=False,
            vgp_services={
                'svc:/site/vasgps-config:default': 'disabled',
            },
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, 'svcs\t-aH\t-o\tFMRI,STATE\n')

    def test_removed_solaris11_group_policy_service_offline_succeeds(self):
        completed, log = self.run_case(
            {'vasgps': 'absent'},
            {},
            {'vasgps': {'owner': 'absent', 'version': ''}},
            vasd_registered=False,
            vgp_services={
                'svc:/site/vasgps-config:default': 'offline',
            },
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, 'svcs\t-aH\t-o\tFMRI,STATE\n')

    def test_removed_solaris11_group_policy_service_absence_succeeds(self):
        completed, log = self.run_case(
            {'vasgps': 'absent'},
            {},
            {'vasgps': {'owner': 'absent', 'version': ''}},
            vasd_registered=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, 'svcs\t-aH\t-o\tFMRI,STATE\n')

    def test_complete_group_policy_removal_requires_vasd_absence(self):
        completed, log = self.run_case(
            {'vasgps': 'absent'},
            {},
            {
                'vasclnt': {'owner': 'absent', 'version': ''},
                'vasclnts': {'owner': 'absent', 'version': ''},
                'vasgp': {'owner': 'absent', 'version': ''},
                'vasgps': {'owner': 'absent', 'version': ''},
            },
            vasd_registered=True,
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('vasd:default remains registered', completed.stdout)
        self.assertEqual(log, 'svcs\t-aH\t-o\tFMRI,STATE\n')

    def test_group_policy_removal_allows_vasd_for_installed_client(self):
        completed, log = self.run_case(
            {'vasgps': 'absent'},
            {},
            {
                'vasclnt': {'owner': 'ips', 'version': '7.0.0.8900'},
                'vasclnts': {'owner': 'absent', 'version': ''},
                'vasgp': {'owner': 'absent', 'version': ''},
                'vasgps': {'owner': 'absent', 'version': ''},
            },
            vasd_registered=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, 'svcs\t-aH\t-o\tFMRI,STATE\n')

    def test_removal_verifies_omitted_installed_vgp_service(self):
        completed, log = self.run_case(
            {'vasgps': 'absent'},
            {},
            {
                'vasclnt': {'owner': 'absent', 'version': ''},
                'vasclnts': {'owner': 'absent', 'version': ''},
                'vasgp': {'owner': 'ips', 'version': '7.0.0.8900'},
                'vasgps': {'owner': 'absent', 'version': ''},
            },
            vgp_services={
                'svc:/site/vasgp-config:default': 'offline',
            },
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('vasgp-config:default is not online', completed.stdout)
        self.assertEqual(log, 'svcs\t-aH\t-o\tFMRI,STATE\n')

    def test_check_only_packages_do_not_assert_service_state(self):
        completed, log = self.run_case(
            {'vasclnt': 'check', 'vasclnts': 'check'},
            {},
            {
                'vasclnt': {'owner': 'absent', 'version': ''},
                'vasclnts': {'owner': 'absent', 'version': ''},
            },
            vasd_registered=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, '')

    def test_ansible_check_mode_does_not_assert_skipped_postconditions(self):
        completed, log = self.run_case(
            {'vasclnt': 'check', 'vasclnts': 'present'},
            {'vasclnts': {'vers': '7.0.0.8900'}},
            {
                'vasclnt': {'owner': 'absent', 'version': ''},
                'vasclnts': {'owner': 'absent', 'version': ''},
            },
            vasd_registered=False,
            check_mode=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(log, '')
        self.assertIn('changed=0', completed.stdout)

    def test_uncleared_ips_operation_state_fails(self):
        completed, log = self.run_case(
            {'vassc': 'check'},
            {},
            {'vassc': {'owner': 'absent', 'version': ''}},
            ips_stage={'path': '/var/tmp/ansible-as-client-sw-ips-test'},
            ips_staged_sources=[{
                'source_path': '/media/sas.p5p',
                'source_file': 'sas.p5p',
                'staged_path': '/var/tmp/ansible-as-client-sw-ips-test/sas.p5p',
            }],
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('IPS operation state was not cleared', completed.stdout)
        self.assertEqual(log, '')

    def test_leaked_ips_operation_directory_fails(self):
        completed, log = self.run_case(
            {'vassc': 'check'},
            {},
            {'vassc': {'owner': 'absent', 'version': ''}},
            leak_ips_stage=True,
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('IPS operation directory was not removed', completed.stdout)
        self.assertEqual(log, '')

    def test_leaked_legacy_operation_directory_fails(self):
        completed, log = self.run_case(
            {'vassc': 'check'},
            {},
            {'vassc': {'owner': 'absent', 'version': ''}},
            leak_legacy_stage=True,
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('legacy operation directory was not removed', completed.stdout)
        self.assertEqual(log, '')


class SolarisFinalStateTaskContractTests(unittest.TestCase):

    def test_final_verification_runs_after_all_package_probes(self):
        path = ROOT / 'roles/client_sw/tasks/run_package_tasks.yml'
        tasks = yaml.safe_load(path.read_text())
        includes = [task.get('include_tasks') for task in tasks]
        self.assertEqual(includes.count('verify_solaris_state.yml'), 1)
        verification_index = includes.index('verify_solaris_state.yml')
        final_probe_index = max(
            index for index, include in enumerate(includes)
            if include == 'read_package_version.yml'
        )
        self.assertGreater(verification_index, final_probe_index)
        self.assertEqual(
            tasks[verification_index]['when'],
            "ansible_facts['os_family'] | lower == 'solaris'",
        )

    def test_missing_service_package_facts_are_probed_before_verification(self):
        path = ROOT / 'roles/client_sw/tasks/run_package_tasks.yml'
        tasks = yaml.safe_load(path.read_text())
        probe = next(
            task for task in tasks
            if task.get('name') == 'read final Solaris service package state'
        )
        verification = next(
            task for task in tasks
            if task.get('include_tasks') == 'verify_solaris_state.yml'
        )
        self.assertLess(tasks.index(probe), tasks.index(verification))
        self.assertEqual(
            probe['loop'],
            ['vasclnt', 'vasclnts', 'vasgp', 'vasgps'],
        )
        self.assertIn('item not in client_sw_pkg_state', probe['when'])


if __name__ == '__main__':
    unittest.main()