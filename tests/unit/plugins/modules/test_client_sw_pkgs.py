import io
import importlib.util
import os
import shutil
import tarfile
import tempfile
import unittest

import yaml


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
MODULE_PATH = os.path.join(ROOT, 'plugins', 'modules', 'client_sw_pkgs.py')
SPEC = importlib.util.spec_from_file_location('client_sw_pkgs', MODULE_PATH)
client_sw_pkgs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(client_sw_pkgs)


def write_p5p(path, records=None, other_members=None):
    records = records or []
    other_members = other_members or []
    with tarfile.open(path, 'w', format=tarfile.USTAR_FORMAT) as archive:
        for publisher, package, version in records:
            member_name = 'publisher/{}/pkg/{}/{}'.format(
                publisher,
                package,
                version.replace(',', '%2C').replace(':', '%3A'),
            )
            member = tarfile.TarInfo(member_name)
            member.size = 0
            archive.addfile(member, io.BytesIO(b''))
        for member_name in other_members:
            member = tarfile.TarInfo(member_name)
            member.size = 0
            archive.addfile(member, io.BytesIO(b''))


class SolarisPathTests(unittest.TestCase):

    def test_solaris_major_version_parser(self):
        self.assertEqual(client_sw_pkgs.solaris_major_version('10'), 10)
        self.assertEqual(client_sw_pkgs.solaris_major_version('11.4'), 11)
        self.assertEqual(client_sw_pkgs.solaris_major_version(''), 0)
        self.assertEqual(client_sw_pkgs.solaris_major_version(None), 0)
        self.assertEqual(client_sw_pkgs.solaris_major_version('unknown'), 0)

    def test_missing_solaris_major_version_fails_closed(self):
        for version in ('', None, 'unknown'):
            error, path = client_sw_pkgs.find_packages_path(
                'sunos', 'sparc', version)
            self.assertEqual(
                error,
                'Solaris major version is required for package discovery')
            self.assertEqual(path, '')

    def test_solaris_10_architecture_aliases_use_svr4_directories(self):
        for architecture in ('sparc', 'sparc64', 'sun4u', 'sun4v'):
            error, path = client_sw_pkgs.find_packages_path(
                'sunos', architecture, '10')
            self.assertIsNone(error)
            self.assertEqual(path, 'solaris10-sparc')

        for architecture in ('i386', 'i86pc', 'x86_64', 'amd64'):
            error, path = client_sw_pkgs.find_packages_path(
                'sunos', architecture, '10')
            self.assertIsNone(error)
            self.assertEqual(path, 'solaris10-x64')

    def test_solaris_11_architecture_aliases_use_ips_directories(self):
        for architecture in ('sparc', 'sparc64', 'sun4u', 'sun4v'):
            error, path = client_sw_pkgs.find_packages_path(
                'sunos', architecture, '11.4')
            self.assertIsNone(error)
            self.assertEqual(path, 'solaris11-sparc')

        for architecture in ('i386', 'i86pc', 'x86_64', 'amd64'):
            error, path = client_sw_pkgs.find_packages_path(
                'sunos', architecture, '11')
            self.assertIsNone(error)
            self.assertEqual(path, 'solaris11-x64')


class SolarisIpsDiscoveryTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.media_dir = os.path.join(self.temp_dir, 'solaris11-sparc')
        os.makedirs(self.media_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_discovers_standard_site_and_qa_packages_with_component_versions(self):
        standard = os.path.join(self.media_dir, 'sas-7.0.0.8900.p5p')
        site = os.path.join(self.media_dir, 'sas_site-7.0.0.8900.p5p')
        qa = os.path.join(self.media_dir, 'sas_qa.p5p')
        write_p5p(standard, [
            ('OneIdentity', 'vasclnt', '7.0.0.8900,5.11-0:20260101T000000Z'),
            ('OneIdentity', 'vasgp', '7.0.0.8900,5.11-0:20260101T000000Z'),
            ('OneIdentity', 'vassc', '7.0.0.8900,5.11-0:20260101T000000Z'),
            ('OneIdentity', 'vascert', '1.4.0.70,5.11-0:20260101T000000Z'),
            ('OneIdentity', 'dnsupdate', '7.0.0.8900,5.11-0:20260101T000000Z'),
            ('OneIdentity', 'pamdefender', '7.0.0.8900,5.11-0:20260101T000000Z'),
            ('OneIdentity', 'vasyp', '7.0.0.8900,5.11-0:20260101T000000Z'),
            ('OneIdentity', 'vasproxy', '7.0.0.8900,5.11-0:20260101T000000Z'),
            ('OneIdentity', 'vasdev', '7.0.0.8900,5.11-0:20260101T000000Z'),
        ])
        write_p5p(site, [
            ('OneIdentity', 'vasclnts', '7.0.0.8900,5.11-0:20260101T000000Z'),
            ('OneIdentity', 'vasgps', '7.0.0.8900,5.11-0:20260101T000000Z'),
            ('OneIdentity', 'vassc', '7.0.0.8900,5.11-0:20260101T000000Z'),
        ])
        write_p5p(qa, [
            ('OneIdentity', 'vasqa', '7.0.0.8900,5.11-0:20260101T000000Z'),
        ])

        error, packages = client_sw_pkgs.find_packages(
            self.temp_dir, 'sunos', 'solaris', 'sun4v', '11.4')

        self.assertIsNone(error)
        expected_packages = {
            'vasclnt', 'vasclnts', 'vasgp', 'vasgps', 'vassc', 'vascert',
            'dnsupdate', 'pamdefender', 'vasyp', 'vasqa', 'vasproxy', 'vasdev',
        }
        self.assertEqual(expected_packages, set(packages) - {'preflight'})
        self.assertEqual(packages['vascert']['vers'], '1.4.0.70')
        self.assertEqual(packages['vasqa']['file'], 'sas_qa.p5p')
        self.assertEqual(packages['vasclnt']['publisher'], 'OneIdentity')
        self.assertEqual(packages['vassc']['path'], standard)

    def test_identical_duplicate_uses_deterministic_archive(self):
        first = os.path.join(self.media_dir, 'a.p5p')
        second = os.path.join(self.media_dir, 'b.p5p')
        record = [
            ('OneIdentity', 'vassc', '7.0.0.8900,5.11-0:20260101T000000Z'),
        ]
        write_p5p(second, record)
        write_p5p(first, record)

        error, packages = client_sw_pkgs.find_packages(
            self.temp_dir, 'sunos', 'solaris', 'sparc', '11')

        self.assertIsNone(error)
        self.assertEqual(packages['vassc']['path'], first)

    def test_url_encoded_package_stem_is_decoded(self):
        write_p5p(os.path.join(self.media_dir, 'sas.p5p'), [
            ('OneIdentity', 'vas%63lnt',
             '7.0.0.8900,5.11-0:20260101T000000Z'),
        ])

        error, packages = client_sw_pkgs.find_packages(
            self.temp_dir, 'sunos', 'solaris', 'sparc', '11')

        self.assertIsNone(error)
        self.assertIn('vasclnt', packages)
        self.assertNotIn('vas%63lnt', packages)

    def test_conflicting_duplicate_versions_fail(self):
        write_p5p(os.path.join(self.media_dir, 'a.p5p'), [
            ('OneIdentity', 'vassc', '7.0.0.8900,5.11-0:20260101T000000Z'),
        ])
        write_p5p(os.path.join(self.media_dir, 'b.p5p'), [
            ('OneIdentity', 'vassc', '7.1.0.1000,5.11-0:20260201T000000Z'),
        ])

        error, packages = client_sw_pkgs.find_packages(
            self.temp_dir, 'sunos', 'solaris', 'sparc', '11')

        self.assertIn('conflicting versions', error)
        self.assertIn('vassc', error)
        self.assertEqual(packages, {})

    def test_conflicting_publishers_fail(self):
        write_p5p(os.path.join(self.media_dir, 'a.p5p'), [
            ('OneIdentity', 'vassc', '7.0.0.8900,5.11-0:20260101T000000Z'),
        ])
        write_p5p(os.path.join(self.media_dir, 'b.p5p'), [
            ('OtherPublisher', 'vassc', '7.0.0.8900,5.11-0:20260101T000000Z'),
        ])

        error, packages = client_sw_pkgs.find_packages(
            self.temp_dir, 'sunos', 'solaris', 'sparc', '11')

        self.assertIn('conflicting publishers', error)
        self.assertIn('vassc', error)
        self.assertEqual(packages, {})

    def test_corrupt_archive_fails_discovery(self):
        archive = os.path.join(self.media_dir, 'sas.p5p')
        with open(archive, 'wb') as output:
            output.write(b'not a package archive')

        error, packages = client_sw_pkgs.find_packages(
            self.temp_dir, 'sunos', 'solaris', 'sparc', '11')

        self.assertIn('sas.p5p', error)
        self.assertIn('Unable to read', error)
        self.assertEqual(packages, {})

    def test_package_empty_archive_fails_discovery(self):
        archive = os.path.join(self.media_dir, 'sas.p5p')
        write_p5p(archive, other_members=['pkg5.repository'])

        error, packages = client_sw_pkgs.find_packages(
            self.temp_dir, 'sunos', 'solaris', 'sparc', '11')

        self.assertIn('contains no package manifests', error)
        self.assertEqual(packages, {})

    def test_missing_archive_fails_discovery(self):
        error, packages = client_sw_pkgs.find_packages(
            self.temp_dir, 'sunos', 'solaris', 'sparc', '11')

        self.assertIn('No Solaris IPS package archives', error)
        self.assertEqual(packages, {})


class CompatibilityTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_solaris_10_keeps_svr4_discovery(self):
        package_dir = os.path.join(self.temp_dir, 'solaris10-sparc')
        os.makedirs(package_dir)
        package_file = 'vasclnt_SunOS_5.10_sparc-7.0.0.8900.pkg'
        open(os.path.join(package_dir, package_file), 'wb').close()

        error, packages = client_sw_pkgs.find_packages(
            self.temp_dir, 'sunos', 'solaris', 'sun4u', '10')

        self.assertIsNone(error)
        self.assertEqual(packages['vasclnt']['file'], package_file)
        self.assertEqual(packages['vasclnt']['vers'], '7.0.0.8900')

    def test_non_solaris_discovery_is_unchanged(self):
        package_dir = os.path.join(self.temp_dir, 'linux-x86_64')
        os.makedirs(package_dir)
        package_file = 'vasgp-7.0.0-8900.x86_64.rpm'
        open(os.path.join(package_dir, package_file), 'wb').close()

        error, packages = client_sw_pkgs.find_packages(
            self.temp_dir, 'linux', 'redhat', 'x86_64', '43')

        self.assertIsNone(error)
        self.assertEqual(packages['vasgp']['file'], package_file)
        self.assertEqual(packages['vasgp']['vers'], '7.0.0.8900')

    def test_run_normal_preserves_version_parameter(self):
        package_dir = os.path.join(self.temp_dir, 'linux-x86_64')
        os.makedirs(package_dir)
        open(os.path.join(package_dir, 'vasgp-7.0.0-8900.x86_64.rpm'), 'wb').close()
        params = {
            'sys': 'Linux',
            'dist': 'RedHat',
            'arch': 'x86_64',
            'ver': '43',
            'path': self.temp_dir,
            'facts': False,
            'facts_key': 'client_sw_pkgs',
        }
        result = {
            'changed': False,
            'failed': False,
            'msg': '',
            'params': {},
            'packages': {},
        }

        error, result = client_sw_pkgs.run_normal(params, result)

        self.assertIsNone(error)
        self.assertEqual(result['params']['ver'], '43')


class CallerContractTests(unittest.TestCase):

    def test_delegated_callers_pass_managed_host_major_version(self):
        relative_paths = (
            'roles/client_sw/tasks/check_package_directory.yml',
            'roles/client_preflight/tasks/utils/check_package_directory.yml',
        )
        expected = "{{ ansible_facts['distribution_major_version'] | default('') }}"

        for relative_path in relative_paths:
            with self.subTest(path=relative_path):
                with open(os.path.join(ROOT, relative_path)) as source:
                    tasks = yaml.safe_load(source)
                module_args = tasks[0]['client_sw_pkgs']
                self.assertEqual(module_args['ver'], expected)
                self.assertIn('delegate_to', tasks[0])


if __name__ == '__main__':
    unittest.main()
