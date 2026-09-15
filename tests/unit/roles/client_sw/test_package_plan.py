import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[4]
FIXTURES = Path(__file__).resolve().parent / 'fixtures'
PLAYBOOK = shutil.which('ansible-playbook')

# Representative test vectors only. Production reads both versions at runtime:
# the installed version from host facts and the target from discovered media.
SAS_5 = '5.0.0.100'
SAS_6 = '6.0.0.200'
SAS_7 = '7.0.0.300'


def package(path, version, publisher=''):
    result = {
        'path': path,
        'file': os.path.basename(path),
        'vers': version,
    }
    if publisher:
        result['publisher'] = publisher
    return result


def plan_entry(name, state, installed, target, source, action,
               requires_source, may_remove, publisher='', owner=None,
               migration_required=False):
    if owner is None:
        owner = 'svr4' if installed else 'absent'
    return {
        'package': name,
        'state': state,
        'installed_version': installed,
        'owner': owner,
        'migration_required': migration_required,
        'target_version': target,
        'source_path': source,
        'source_file': os.path.basename(source) if source else '',
        'source_publisher': publisher,
        'action': action,
        'requires_source': requires_source,
        'may_remove_installed': may_remove,
    }


@unittest.skipUnless(PLAYBOOK, 'ansible-playbook is required')
class PackagePlanBehaviorTests(unittest.TestCase):

    def run_case(self, variables, expected_success=True, check_mode=False):
        environment = dict(os.environ)
        environment.update({
            'ANSIBLE_NOCOLOR': '1',
            'ANSIBLE_ROLES_PATH': str(ROOT / 'roles'),
        })
        command = [
            PLAYBOOK,
            '-i', 'localhost,',
            '-c', 'local',
            str(FIXTURES / 'package_plan.yml'),
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
        if expected_success:
            self.assertEqual(completed.returncode, 0, completed.stdout)
        else:
            self.assertNotEqual(completed.returncode, 0, completed.stdout)
        return completed

    def test_plans_numeric_upgrade_downgrade_equal_and_install(self):
        source = '/media/solaris11-sparc/sas.p5p'
        variables = {
            'client_sw_pkg_state': {
                'vascert': 'present',
                'vasclnt': 'present',
                'vasgp': 'present',
                'vassc': 'present',
            },
            'client_sw_pkgs': {
                'packages': {
                    'vascert': package(source, '1.4.0.70'),
                    'vasclnt': package(source, '7.1.0.1000'),
                    'vasgp': package(source, '7.1.0.900'),
                    'vassc': package(source, '7.1.0.1000'),
                },
            },
            'sas_client_sw_vascert_vers_beg': '',
            'sas_client_sw_vasclnt_vers_beg': '7.1.0.900',
            'sas_client_sw_vasgp_vers_beg': '7.1.0.1000',
            'sas_client_sw_vassc_vers_beg': '7.1.0.1000',
            'test_ownership': {
                'vascert': {'owner': 'absent'},
                'vasclnt': {'owner': 'ips'},
                'vasgp': {'owner': 'ips'},
                'vassc': {'owner': 'ips'},
            },
            'expected_plan': [
                plan_entry('vascert', 'present', '', '1.4.0.70', source,
                           'install', True, False),
                plan_entry('vasclnt', 'present', '7.1.0.900', '7.1.0.1000',
                           source, 'upgrade', True, False, owner='ips'),
                plan_entry('vasgp', 'present', '7.1.0.1000', '7.1.0.900',
                           source, 'downgrade', True, False, owner='ips'),
                plan_entry('vassc', 'present', '7.1.0.1000', '7.1.0.1000',
                           source, 'none', False, False, owner='ips'),
            ],
            'expected_sources': [
                {'path': source, 'file': 'sas.p5p'},
            ],
        }
        self.run_case(variables)

    def test_plans_upgrades_across_major_sas_versions(self):
        source = '/media/solaris11-sparc/sas.p5p'
        variables = {
            'client_sw_pkg_state': {
                'dnsupdate': 'present',
                'pamdefender': 'present',
                'vasclnt': 'present',
            },
            'client_sw_pkgs': {
                'packages': {
                    'dnsupdate': package(source, SAS_6),
                    'pamdefender': package(source, SAS_7),
                    'vasclnt': package(source, SAS_7),
                },
            },
            'sas_client_sw_dnsupdate_vers_beg': SAS_5,
            'sas_client_sw_pamdefender_vers_beg': SAS_5,
            'sas_client_sw_vasclnt_vers_beg': SAS_6,
            'test_ownership': {
                'dnsupdate': {'owner': 'svr4'},
                'pamdefender': {'owner': 'svr4'},
                'vasclnt': {'owner': 'svr4'},
            },
            'expected_plan': [
                plan_entry('dnsupdate', 'present', SAS_5, SAS_6, source,
                           'upgrade', True, True),
                plan_entry('pamdefender', 'present', SAS_5, SAS_7, source,
                           'upgrade', True, True),
                plan_entry('vasclnt', 'present', SAS_6, SAS_7, source,
                           'upgrade', True, True),
            ],
            'expected_sources': [
                {'path': source, 'file': 'sas.p5p'},
            ],
        }
        self.run_case(variables)

    def test_plans_remove_check_and_absent_noop(self):
        variables = {
            'client_sw_pkg_state': {
                'vascert': 'check',
                'vasclnt': 'absent',
                'vasgp': 'absent',
            },
            'client_sw_pkgs': {'packages': {}},
            'sas_client_sw_vascert_vers_beg': '1.4.0.70',
            'sas_client_sw_vasclnt_vers_beg': '7.0.0.8900',
            'sas_client_sw_vasgp_vers_beg': '',
            'test_ownership': {
                'vascert': {'owner': 'ips'},
                'vasclnt': {'owner': 'ips'},
                'vasgp': {'owner': 'absent'},
            },
            'expected_plan': [
                plan_entry('vascert', 'check', '1.4.0.70', '', '',
                           'check', False, False, owner='ips'),
                plan_entry('vasclnt', 'absent', '7.0.0.8900', '', '',
                           'remove', False, True, owner='ips'),
                plan_entry('vasgp', 'absent', '', '', '',
                           'none', False, False),
            ],
            'expected_sources': [],
        }
        self.run_case(variables)

    def test_collects_each_required_source_once(self):
        standard = '/media/solaris11-sparc/sas.p5p'
        qa = '/media/solaris11-sparc/sas_qa.p5p'
        variables = {
            'client_sw_pkg_state': {
                'vasclnt': 'present',
                'vasgp': 'present',
                'vasqa': 'present',
            },
            'client_sw_pkgs': {
                'packages': {
                    'vasclnt': package(standard, '7.0.0.8900', 'OneIdentity'),
                    'vasgp': package(standard, '7.0.0.8900', 'OneIdentity'),
                    'vasqa': package(qa, '7.0.0.8900', 'OneIdentity'),
                },
            },
            'sas_client_sw_vasclnt_vers_beg': '6.1.0.4900',
            'sas_client_sw_vasgp_vers_beg': '',
            'sas_client_sw_vasqa_vers_beg': '',
            'test_ownership': {
                'vasclnt': {'owner': 'ips'},
                'vasgp': {'owner': 'absent'},
                'vasqa': {'owner': 'absent'},
            },
            'expected_plan': [
                plan_entry('vasclnt', 'present', '6.1.0.4900', '7.0.0.8900',
                           standard, 'upgrade', True, False, 'OneIdentity',
                           'ips'),
                plan_entry('vasgp', 'present', '', '7.0.0.8900', standard,
                           'install', True, False, 'OneIdentity'),
                plan_entry('vasqa', 'present', '', '7.0.0.8900', qa,
                           'install', True, False, 'OneIdentity'),
            ],
            'expected_sources': [
                {'path': standard, 'file': 'sas.p5p'},
                {'path': qa, 'file': 'sas_qa.p5p'},
            ],
        }
        self.run_case(variables)

    def test_missing_present_package_fails_before_planning(self):
        variables = {
            'client_sw_pkg_state': {'vasclnt': 'present'},
            'client_sw_pkgs': {'packages': {}},
            'sas_client_sw_vasclnt_vers_beg': '6.1.0.4900',
            'expected_plan': [],
            'expected_sources': [],
        }
        completed = self.run_case(variables, expected_success=False)
        self.assertIn('was not found in the selected platform media',
                      completed.stdout)

    def test_incomplete_present_package_metadata_fails(self):
        variables = {
            'client_sw_pkg_state': {'vasclnt': 'present'},
            'client_sw_pkgs': {'packages': {
                'vasclnt': package('/media/sas.p5p', ''),
            }},
            'sas_client_sw_vasclnt_vers_beg': '6.1.0.4900',
            'expected_plan': [],
            'expected_sources': [],
        }
        completed = self.run_case(variables, expected_success=False)
        self.assertIn('does not have complete version and source metadata',
                      completed.stdout)

    def test_missing_ownership_facts_fail_before_planning(self):
        source = '/media/sas.p5p'
        variables = {
            'client_sw_pkg_state': {'vasclnt': 'present'},
            'client_sw_pkgs': {'packages': {
                'vasclnt': package(source, '7.0.0.8900'),
            }},
            'sas_client_sw_vasclnt_vers_beg': '6.1.0.4900',
            'expected_plan': [],
            'expected_sources': [],
        }
        completed = self.run_case(variables, expected_success=False)
        self.assertIn('ownership facts', completed.stdout)

    def test_unexpected_state_does_not_plan_a_version_transition(self):
        source = '/media/sas.p5p'
        variables = {
            'client_sw_pkg_state': {'vasclnt': 'unexpected'},
            'client_sw_pkgs': {'packages': {
                'vasclnt': package(source, '7.0.0.8900'),
            }},
            'sas_client_sw_vasclnt_vers_beg': '6.1.0.4900',
            'test_ownership': {
                'vasclnt': {'owner': 'svr4'},
            },
            'expected_plan': [
                plan_entry('vasclnt', 'unexpected', '6.1.0.4900',
                           '7.0.0.8900', source, 'none', False, False),
            ],
            'expected_sources': [],
        }
        self.run_case(variables)

    def test_plan_executes_in_check_mode_without_reporting_changes(self):
        source = '/media/sas.p5p'
        variables = {
            'client_sw_pkg_state': {'vasclnt': 'present'},
            'client_sw_pkgs': {'packages': {
                'vasclnt': package(source, '7.0.0.8900'),
            }},
            'sas_client_sw_vasclnt_vers_beg': '6.1.0.4900',
            'test_ownership': {
                'vasclnt': {'owner': 'ips'},
            },
            'expected_plan': [
                plan_entry('vasclnt', 'present', '6.1.0.4900',
                           '7.0.0.8900', source, 'upgrade', True, False,
                           owner='ips'),
            ],
            'expected_sources': [
                {'path': source, 'file': 'sas.p5p'},
            ],
        }
        completed = self.run_case(variables, check_mode=True)
        self.assertIn('changed=0', completed.stdout)

    def test_equal_version_legacy_package_requires_migration_source(self):
        source = '/media/solaris11-sparc/sas_site.p5p'
        variables = {
            'client_sw_pkg_state': {'vasclnts': 'present'},
            'client_sw_pkgs': {'packages': {
                'vasclnts': package(source, '6.1.0.4900', 'OneIdentity'),
            }},
            'sas_client_sw_vasclnts_vers_beg': '6.1.0.4900',
            'test_ownership': {
                'vasclnts': {
                    'owner': 'svr4',
                    'migration_required': True,
                },
            },
            'expected_plan': [
                plan_entry('vasclnts', 'present', '6.1.0.4900',
                           '6.1.0.4900', source, 'none', True, True,
                           'OneIdentity', 'svr4', True),
            ],
            'expected_sources': [
                {'path': source, 'file': 'sas_site.p5p'},
            ],
        }
        self.run_case(variables)

    def test_mutually_exclusive_standard_and_site_packages_fail(self):
        for states, message in (
                ({'vasclnt': 'present', 'vasclnts': 'present'},
                 'vasclnt and vasclnts cannot both be requested present'),
                ({'vasgp': 'present', 'vasgps': 'present'},
                 'vasgp and vasgps cannot both be requested present')):
            with self.subTest(states=states):
                variables = {
                    'client_sw_pkg_state': states,
                    'client_sw_pkgs': {'packages': {
                        name: package('/media/sas.p5p', '7.0.0.8900')
                        for name in states
                    }},
                    'expected_plan': [],
                    'expected_sources': [],
                }
                for name in states:
                    variables['sas_client_sw_{}_vers_beg'.format(name)] = ''
                completed = self.run_case(variables, expected_success=False)
                self.assertIn(message, completed.stdout)


class PackagePlanTaskContractTests(unittest.TestCase):

    def test_plan_is_inserted_once_before_staging_and_mutation(self):
        path = ROOT / 'roles/client_sw/tasks/run_package_tasks.yml'
        tasks = yaml.safe_load(path.read_text())
        includes = [task.get('include_tasks') for task in tasks]
        plan_index = includes.index('build_package_plan.yml')
        plan_task = tasks[plan_index]
        operation_index = next(
            index for index, task in enumerate(tasks)
            if task.get('name') == 'preflight and perform package operations'
        )
        operation_includes = [
            task.get('include_tasks')
            for task in tasks[operation_index]['block']
        ]
        self.assertEqual(includes.count('build_package_plan.yml'), 1)
        self.assertLess(plan_index, includes.index('temp_dir_create.yml'))
        self.assertLess(plan_index, operation_index)
        self.assertEqual(operation_includes.count('run_package_task.yml'), 1)
        self.assertEqual(
            plan_task['when'],
            "ansible_facts['os_family'] | lower == 'solaris'",
        )

    def test_execution_routing_uses_ansible_version_test(self):
        path = ROOT / 'roles/client_sw/tasks/run_package_task.yml'
        tasks = yaml.safe_load(path.read_text())
        by_name = {task.get('name'): task for task in tasks if task.get('name')}
        upgrade_conditions = by_name['upgrade {{ package }}']['when']
        downgrade_conditions = by_name['downgrade {{ package }}']['when']
        self.assertTrue(any(' is version(' in condition and "'<'" in condition
                            for condition in upgrade_conditions))
        self.assertTrue(any(' is version(' in condition and "'>'" in condition
                            for condition in downgrade_conditions))
        self.assertFalse(any(' < ' in condition for condition in upgrade_conditions))
        self.assertFalse(any(' > ' in condition for condition in downgrade_conditions))


if __name__ == '__main__':
    unittest.main()
