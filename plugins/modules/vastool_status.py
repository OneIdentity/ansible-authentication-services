#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright (c) 2021, One Identity LLC
# File: vastool_status.py
# Desc: Ansible module that wraps vastool status command.
# Auth: Laszlo Nagy
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
module: vastool_status

short_description: Check the health status of Authentication Services agents

version_added: '2.9'

description: >
    Check the health status of Authentication Services agents. Tests the
    machine's join against Active Directory and local configuration for
    various issues using the Authentication Services vastool binary.

options:
    facts:
        description:
            - Generate Ansible facts?
        type: bool
        required: false
        default: true
    facts_verbose:
        description:
            - Verbose Ansible facts?
        type: bool
        required: false
        default: true
    facts_key:
        description:
            - Ansible facts key
        type: str
        required: false
        default: 'vastool_status_facts_key'

author:
    - Laszlo Nagy (laszlo.nagy@oneidentity.com)
"""

EXAMPLES = """
- name: Simple agent status check
  vastool_status:
    facts: true
    facts_verbose: true
    facts_key: vastool_status_facts_key
  register: vastool_status_result
"""

RETURN = """
ansible_facts:
    description: All non-standard return values are placed in Ansible facts
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
        version:
            description: Version of vastool
            type: str
            returned: always
        issues:
            description: Issues found
            type: list of dicts
            returned: when facts_verbose true
"""


# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------


from ansible.module_utils.basic import AnsibleModule
from io import StringIO
import csv
import sys
import subprocess
import traceback
import re
import ansible_collections.oneidentity.authentication_services.plugins.module_utils.vastool as vt
import ansible_collections.oneidentity.authentication_services.plugins.module_utils.check_file_exec as cfe


# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------

# Arg choices and defaults
FACTS_DEFAULT = True
FACTS_VERBOSE_DEFAULT = True
FACTS_KEY_DEFAULT = 'vastool_status_facts_key'


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
            'facts': {
                'type': 'bool',
                'required': False,
                'default': FACTS_DEFAULT
            },
            'facts_verbose': {
                'type': 'bool',
                'required': False,
                'default': FACTS_VERBOSE_DEFAULT
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
            'msg': ''
        }

    # Lean on boilerplate code in AnsibleModule class
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    # Run logic
    # NOTE: This module does not support check mode right now so no special check handling
    err, result = run_normal(module.params, result)

    # Exit
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
    version = ''
    issues = []

    # Parameters
    facts = params['facts']
    facts_verbose = params['facts_verbose']
    facts_key = params['facts_key'] if params['facts_key'] else FACTS_KEY_DEFAULT

    try:

        # Check vastool
        err, version = cfe.check_file_exec(vt.VASTOOL_PATH, '-v')

        # Run vastool
        if err is None:
            err, issues = run_vastool_status()

    except Exception:
        tb = traceback.format_exc()
        err = str(tb)

    # Build result
    result['changed'] = False   # vastool status never makes any changes to the host
    result['failed'] = err is not None
    result['msg'] = err if err is not None else ''

    # Create ansible_facts data
    if facts:
        result_facts = result.copy()
        result_facts['params'] = params
        result_facts['version'] = version
        if facts_verbose:
            result_facts['issues'] = issues
        result['ansible_facts'] = {facts_key: result_facts}

    # Return
    return err, result


# ------------------------------------------------------------------------------
def run_vastool_status():
    """
    Run vastool status
    """

    # Return values
    err = None
    issues = []
    non_zero_ret_code = False

    # Build vastool command
    cmd = []
    cmd += [vt.VASTOOL_PATH]
    cmd += ['status']
    cmd += ['-c']

    # Call vastool
    try:
        p = subprocess.Popen(' '.join(cmd), stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        rval_bytes, rval_err = p.communicate()
        rval_bytes += rval_err
    # This exception happens when the process exits with a non-zero return code
    except subprocess.CalledProcessError as e:
        # Just grab output bytes likes a normal exit, we'll parse it for errors anyway
        rval_bytes = e.output
    if p.returncode > 0:
        non_zero_ret_code = True
    # Popen returns list of bytes so we have to decode to get a string
    rval_str = rval_bytes.decode(sys.stdout.encoding)

    # Parse vastool return
    err, issues = parse_vastool_stdout(non_zero_ret_code, rval_str)

    # Return
    return err, issues


# ------------------------------------------------------------------------------
def parse_vastool_stdout(non_zero_ret_code, stdout_str):

    # Return values
    err = None
    issues = []

    failure = False

    severities = {
        '1': 'Warning',
        '2': 'Failure',
        '3': 'Critical Failure'
    }

    text_stream = StringIO(stdout_str)
    csv_reader = csv.reader(text_stream)
    for row in csv_reader:
        if row[0] != 'STATUS':
            continue
        if row[3] not in severities:
            continue
        if row[3] in ('2', '3'):
            failure = True
        issues += [
            {
                'test_id': row[1],
                'description': row[2].replace("`", ""),
                'severity': severities[row[3]],
                'result': row[4].replace("`", "")
            }
        ]

    if failure:
        err = 'One or more QAS Status checks failed.'

    if not issues and non_zero_ret_code:
        err = stdout_str

    # Return
    return err, issues


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
