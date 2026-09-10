#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright (c) 2020, One Identity LLC
# File: client_sw_pkgs.py
# Desc: Ansible module for client_sw role that checks package install directory
#       for packages for the specified system, distribution, and architecture.
# Auth: Mark Stillings
# Note:
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# Required Ansible documentation
# ------------------------------------------------------------------------------

ANSIBLE_METADATA = {
    'metadata_version': '0.2',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
---
module: client_sw_pkgs

short_description: Checks and parses Authentication Services client software install directory

version_added: '2.9'

description: >
    Checks and parses Authentication Services client software install directory to find list
    of client software packages per the provided system (sys), distribution (dist),
    architecture (arch), at the specified path (path)

options:
    sys:
        description:
            - System (Linux, FreeBSD, Solaris, etc.)
        required: true
    dist:
        description:
            - Distribution (Redhat, Debian, etc.)
        required: true
    arch:
        description:
            - Architecture (x86, amd64, etc.)
        required: true
    ver:
        description:
            - Operating system major version used for version-specific package formats
            - Required when sys is SunOS
        type: str
        required: false
        default: ''
    path:
        description:
            - Client software directory
        required: true
    facts:
        description:
            - Generate Ansible facts?
        type: bool
        required: false
        default: false
    facts_key:
        description:
            - Ansible facts key
        type: str
        required: false
        default: 'client_sw_pkgs'

author:
    - Mark Stillings (mark.stillings@oneidentity.com)
"""

EXAMPLES = """
- name: Normal usage
  client_sw_pkgs:
    sys: linux
    dist: debian
    arch: amd64
    path: /var/tmp/authentication_services/client
  register: client_sw_pkgs_result
"""

RETURN = """
params:
    description: Parameters passed in
    type: dict
    returned: always
packages:
    description: The discovered packages and versions in supplied path
    type: dict
    returned: always
ansible_facts:
    description: All return data is placed in Ansible facts
    type: dict
    returned: when facts parameter is true
    keys:
        changed:
            description: Did the state of the host change?
            type: bool
            returned: always
        failed:
            description: Did the module fail?
            type: bool
            returned: always
        msg:
            description: Additional information if failed
            type: str
            returned: always
        params:
            description: Parameters passed in
            type: dict
            returned: always
        packages:
            description: The discovered packages and versions in supplied path
            type: dict
            returned: always
"""


# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

from ansible.module_utils.basic import AnsibleModule
import os
import traceback
import glob
import re
import tarfile

try:
    from urllib.parse import unquote
except ImportError:
    from urllib import unquote


# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------

# Arg choices and defaults
FACTS_DEFAULT = False
FACTS_KEY_DEFAULT = 'client_sw_pkgs'

# Package paths for all supported systems and architectures
PKG_PATHS = {
    'linux': {
        'i386': 'linux-x86',
        'x86_64': 'linux-x86_64',
        'amd64': 'linux-x86_64',
        'ppc64': 'linux-ppc64',
        'ppc64le': 'linux-ppc64le',
        'aarch64': 'linux-aarch64',
        'ia64': 'linux-ia64',
        's390': 'linux-s390',
        's390x': 'linux-s390x'
    },
    'freebsd': {
        'x86_64': 'freebsd-x86_64',
        'amd64': 'freebsd-x86_64'
    },
    'sunos': {
        'i386': 'solaris10-x64',
        'x86_64': 'solaris10-x64',
        'amd64': 'solaris10-x64',
        'sparc': 'solaris10-sparc',
        'sparc64': 'solaris10-sparc',
        'sun4u': 'solaris10-sparc',
        'sun4v': 'solaris10-sparc'
    },
    'darwin': {
        'x86_64': 'macos'
    },
    'hp-ux': {
        '9000/800': 'hpux-pa-11v3',
        'ia64': 'hpux-ia64'
    },
    'aix': {
        'chrp': 'aix-71'
    },
}

# Package file extensions for all supported distributions
PKG_EXTENSIONS = {
    'debian': 'deb',
    'ubuntu': 'deb',
    'redhat': 'rpm',
    'centos': 'rpm',
    'suse': 'rpm',
    'freebsd': 'txz',
    'solaris': 'pkg',
    'darwin': 'dmg',
    'hp-ux': 'depot',
    'aix': 'bff'
}


# ------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
def run_module():
    """
    Main Ansible module function
    """

    # Module argument info
    module_args = {
            'sys': {
                'type': 'str',
                'required': True
            },
            'dist': {
                'type': 'str',
                'required': True
            },
            'arch': {
                'type': 'str',
                'required': True
            },
            'ver': {
                'type': 'str',
                'required': False,
                'default': ''
            },
            'path': {
                'type': 'str',
                'required': True
            },
            'facts': {
                'type': 'bool',
                'required': False,
                'default': FACTS_DEFAULT
            },
            'facts_key': {
                'type': 'str',
                'required': False,
                'default': FACTS_KEY_DEFAULT
            }
        }

    # Seed result value
    result = {
            'changed': False,
            'failed': False,
            'msg': '',
            'params': {},
            'packages': {}
        }

    # Lean on boilerplate code in AnsibleModule class
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Run logic
    # NOTE: This module makes no changes so check mode doesn't need to be handled
    #       specially
    err, result = run_normal(module.params, result)

    # Exit - success
    module.exit_json(**result)


# ------------------------------------------------------------------------------
def run_normal(params, result):
    """
    Normal mode logic.

    params contains input parameters.

    result contains run results skeleton, will modify/add to and then return
    this value along with an err value that contains None if no error or a string
    describing the error.
    """

    # Return data
    err = None
    packages = {}

    # Parameters
    path = params['path']
    sys = params['sys'].lower()
    dist = params['dist'].lower()
    arch = params['arch'].lower()
    ver = params.get('ver', '') or ''
    facts = params['facts']
    facts_key = params['facts_key'] if params['facts_key'] else FACTS_KEY_DEFAULT

    try:

        # Check directory
        err = check_dir(path)

        # Find packages
        if err is None:
            err, packages = find_packages(path, sys, dist, arch, ver)

    except Exception:
        tb = traceback.format_exc()
        err = str(tb)

    # Build result
    result['changed'] = False   # Never makes any changes to the host
    result['failed'] = err is not None
    result['msg'] = err if err is not None else ''
    result['params'] = params
    result['packages'] = packages

    # Create ansible_facts data
    if facts:
        result_facts = result.copy()
        result['ansible_facts'] = {facts_key: result_facts}

    # Return
    return err, result


# ------------------------------------------------------------------------------
def check_dir(path):
    """
    Check if software source directory exists
    """

    # Return value
    err = None

    # Check directory
    exists = os.path.exists(path)
    isdir = os.path.isdir(path)

    # Path does not exist
    if not exists:
        err = path + ' does not exist'

    # Path is a file
    elif not isdir:
        err = path + ' is a file not a directory'

    # Return
    return err


# ------------------------------------------------------------------------------
def find_packages(sw_path, sys, dist, arch, ver=''):
    """
    Find packages
    """

    # Return values
    err = None
    packages = {}

    # Find package path for specified sys and arch
    err, pkgs_dir = find_packages_path(sys, arch, ver)

    # Find packages using the native Solaris 11 IPS archive format or the
    # existing per-distribution package format.
    if not err:
        pkgs_path = os.path.join(sw_path, pkgs_dir)
        if sys == 'sunos' and solaris_major_version(ver) >= 11:
            err, packages = find_packages_solaris_ips(pkgs_path)
        else:
            err, pkgs_ext = find_packages_ext(dist)
            if not err:
                err, packages = parse_packages(pkgs_path, pkgs_ext)

    # NOTE: Authentication Services macOS packages are grouped into dmg files,
    #       so need to do some post-processing
    if not err and sys == 'darwin':
        err, packages = process_macos_packages(packages)

    # Find preflight
    if not err:
        packages['preflight'] = find_preflight(pkgs_path)

    # Check for no packages found
    if not err and not packages:
        err = 'No packages found at ' + sw_path + ' for sys=' + sys + ', dist=' + dist + ', arch=' + arch

    # Return
    return err, packages


# ------------------------------------------------------------------------------
def find_packages_path(sys, arch, ver=''):
    """
    Find package path for specified sys and arch
    """

    # Return values
    err = None
    path = ''

    if sys == 'sunos' and solaris_major_version(ver) == 0:
        return 'Solaris major version is required for package discovery', path

    # Find path info
    if sys in PKG_PATHS:
        sys_archs = PKG_PATHS[sys]

        if arch in sys_archs:
            path = sys_archs[arch]
            if sys == 'sunos' and solaris_major_version(ver) >= 11:
                path = path.replace('solaris10-', 'solaris11-', 1)

        else:
            err = 'Unsupported architecture ' + arch

    else:
        err = 'Unsupported system ' + sys

    return err, path


# ------------------------------------------------------------------------------
def solaris_major_version(ver):
    """
    Return the integer Solaris major version, or 0 when it is unavailable.
    """

    try:
        return int(str(ver).split('.')[0])
    except (AttributeError, TypeError, ValueError):
        return 0


# ------------------------------------------------------------------------------
def read_p5p_packages(archive_path):
    """
    Read package publisher, name, and component version from a .p5p archive.
    """

    packages = {}
    try:
        with tarfile.open(archive_path, mode='r:*') as archive:
            for member in archive:
                parts = member.name.rstrip('/').split('/')
                if (len(parts) != 5 or parts[0] != 'publisher'
                        or parts[2] != 'pkg' or not parts[1]
                        or not parts[3] or not parts[4]):
                    continue

                publisher = unquote(parts[1])
                package = unquote(parts[3])
                version = unquote(parts[4]).split(',', 1)[0]
                if not version:
                    continue

                existing = packages.get(package)
                if existing and existing['publisher'] != publisher:
                    return ('Package {} has conflicting publishers in {}'
                            .format(package, archive_path)), {}
                if existing and existing['vers'] != version:
                    return ('Package {} has conflicting versions in {}'
                            .format(package, archive_path)), {}

                packages[package] = {
                    'publisher': publisher,
                    'vers': version
                }
    except (IOError, OSError, tarfile.TarError) as error:
        return ('Unable to read Solaris IPS package archive {}: {}'
                .format(archive_path, error)), {}

    if not packages:
        return ('Solaris IPS package archive {} contains no package manifests'
                .format(archive_path)), {}

    return None, packages


# ------------------------------------------------------------------------------
def find_packages_solaris_ips(pkgs_path):
    """
    Discover packages and component versions in Solaris IPS archives.
    """

    packages = {}
    archives = sorted(glob.glob(os.path.join(pkgs_path, '*.p5p')))
    if not archives:
        return ('No Solaris IPS package archives (*.p5p) found at {}'
                .format(pkgs_path)), {}

    for archive_path in archives:
        err, archive_packages = read_p5p_packages(archive_path)
        if err:
            return err, {}

        for package, package_data in archive_packages.items():
            existing = packages.get(package)
            if (existing
                    and existing['publisher'] != package_data['publisher']):
                return ('Package {} has conflicting publishers in {} and {}'
                        .format(package, existing['path'], archive_path)), {}
            if existing and existing['vers'] != package_data['vers']:
                return ('Package {} has conflicting versions in {} and {}'
                        .format(package, existing['path'], archive_path)), {}
            if existing:
                continue

            packages[package] = {
                'path': archive_path,
                'file': os.path.basename(archive_path),
                'vers': package_data['vers'],
                'publisher': package_data['publisher']
            }

    return None, packages


# ------------------------------------------------------------------------------
def find_packages_ext(dist):
    """
    find package file extension for specified OS distribution
    """

    # Return values
    err = None
    ext = ''

    # Find extension info
    if dist in PKG_EXTENSIONS:
        ext = PKG_EXTENSIONS[dist]

    else:
        err = 'Unsupported distribution ' + dist

    return err, ext


# ------------------------------------------------------------------------------
def parse_packages(path, ext):
    """
    Parse packages
    """

    # Return values
    err = None
    packages = {}

    # regex strings
    pkg_name_re_str = r'^[a-z]+'
    pkg_vers_re_str = r'(?=.*)[\d]+\.[\d]+\.[\d]+[\.-][\d]+(?=\D\D)'

    # Compile regex's
    pkg_name_re = re.compile(pkg_name_re_str, re.I)
    pkg_vers_re = re.compile(pkg_vers_re_str)

    # Glob the package directory to find packages with correct file extension
    pkgs_str = path + '*/*.' + ext
    pkgs = glob.glob(pkgs_str)

    # Parse each package
    for pkg in pkgs:

        pkg_path = pkg
        pkg_file = os.path.basename(pkg_path)

        pkg_name = None
        pkg_name_match = pkg_name_re.search(pkg_file)
        if pkg_name_match:
            pkg_name = pkg_name_match.group().lower()

        pkg_vers = ''
        pkg_vers_match = pkg_vers_re.search(pkg_file)
        if pkg_vers_match:
            pkg_vers = pkg_vers_match.group()
            pkg_vers = pkg_vers.replace('-', '.')

        if pkg_name:
            packages[pkg_name] = {
                    'path': pkg_path,
                    'file': pkg_file,
                    'vers': pkg_vers
                }

    return err, packages


# ------------------------------------------------------------------------------
def process_macos_packages(dmg_pkgs):
    """
    Process macOS packages
    """

    # Return values
    err = None
    packages = {}

    # macOS dmg prefixes
    vas_dmg_pkg = 'vas'
    vassite_dmg_pkg = 'vassite'
    ddns_dmg_pkg = 'dnsupdate'

    # macOS packages
    vas_pkgs = ['vasclnt', 'vasgp']
    vassite_pkgs = ['vasclnts', 'vasgps']
    common_pkgs = ['vassc', 'vascert', 'vasdev']
    ddns_pkgs = ['dnsupdate']

    # Check for VAS-*.dmg package
    vas_packages = process_dmg_package(dmg_pkgs, vas_dmg_pkg, vas_pkgs + common_pkgs + ddns_pkgs)

    # Check for VASsite*.dmg package
    vassite_packages = process_dmg_package(dmg_pkgs, vassite_dmg_pkg, vassite_pkgs + common_pkgs + ddns_pkgs)

    # Check for dnsupdate*.dmg package
    ddns_packages = process_dmg_package(dmg_pkgs, ddns_dmg_pkg, ddns_pkgs)

    # Merge found packages (order matters here, lowest priority first, highest priority last)
    packages.update(ddns_packages)
    packages.update(vassite_packages)
    packages.update(vas_packages)

    # Check for no packages found
    if not packages:
        err = 'No packages found in ' + ' '.join(dmg_pkgs)

    return err, packages


# ------------------------------------------------------------------------------
def process_dmg_package(dmg_pkgs, dmg_pkg, pkg_names):
    """
    Process macOS dmg package
    """

    packages = {}

    dmg_name = None
    dmg_data = None

    for key, val in dmg_pkgs.items():
        if key == dmg_pkg:
            dmg_name = key
            dmg_data = val

    if dmg_name:
        for pkg_name in pkg_names:

            # vascert has a version different from the other software packages
            if pkg_name == 'vascert':
                packages[pkg_name] = {
                        'path': dmg_data['path'],
                        'file': dmg_data['file'],
                        'vers': get_vascert_version(dmg_data['vers'])
                    }

            # All other packages share the same version as the installer
            else:
                packages[pkg_name] = {
                        'path': dmg_data['path'],
                        'file': dmg_data['file'],
                        'vers': dmg_data['vers']
                    }

    return packages


# ------------------------------------------------------------------------------
def get_vascert_version(dmg_version):

    # For now, there is only one version of vascert in the wild in SAS 4.2.0 and later
    # so we can return a constant.  Later we may need to add a lookup table to map
    # vascert version to major/minor SAS version.
    return '1.1.0.750'


# ------------------------------------------------------------------------------
def find_preflight(path):
    """
    Find preflight
    """

    # Return values
    preflight = None

    # Glob the package directory to find preflight
    pkgs_str = path + '/preflight'
    pkgs = glob.glob(pkgs_str)
    if pkgs:
        preflight = {
                'path': pkgs[0],
                'file': 'preflight',
                'vers': ''
            }

    return preflight


# ------------------------------------------------------------------------------
def main():
    """
    Main
    """

    run_module()


# When run from command line
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
