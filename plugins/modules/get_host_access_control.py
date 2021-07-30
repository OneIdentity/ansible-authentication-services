#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright (c) 2021, One Identity LLC
# File: get_host_access_control.py
# Desc: Ansible module for host_access_control role that reads and returns data
#       from users.allow and users.deny.
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
module: get_host_access_control.py

short_description: Returns entries from users.allow and users.deny.

version_added: '2.9'

description: >
    Returns list of Active Directory users, groups, organizational units and
    domain names from users.allow and users.deny.

options:
    facts:
        description:
            - Generate Ansible facts?
        type: bool
        required: false
        default: true
    facts_key:
        description:
            - Ansible facts key
        type: str
        required: false
        default: 'host_access_control'

author:
    - Laszlo Nagy (laszlo.nagy@oneidentity.com)
"""

EXAMPLES = """
- name: Normal usage
  get_host_access_control:
    facts: true
    facts_key: host_access_control_facts_key
  register: get_host_access_control_result
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
        users_allow:
            description: All entries of users.allow
            type: list of strs
            returned: always
        users_deny:
            description: All entries of users.deny
            type: list of strs
            returned: always
"""


# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_text
import os
import sys
import subprocess
import traceback
import ansible_collections.oneidentity.authentication_services.plugins.module_utils.vastool as vt
import ansible_collections.oneidentity.authentication_services.plugins.module_utils.check_file_exec as cfe


# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------

# Arg defaults
FACTS_DEFAULT = True
FACTS_VERBOSE_DEFAULT = True
FACTS_KEY_DEFAULT = 'host_access_control'


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
        supports_check_mode=True
    )

    # Run logic
    # NOTE: This module makes no changes so check mode doesn't need to be handled
    #       specially
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
    users_allow = []
    users_deny = []

    # Parameters
    facts = params['facts']
    facts_key = params['facts_key'] if params['facts_key'] else FACTS_KEY_DEFAULT

    try:

        # Check vastool
        err, version = cfe.check_file_exec(vt.VASTOOL_PATH, '-v')

        # Run vastool
        if err is None:
            err, users_allow_file = run_vastool_inspect('vas_auth users-allow-file')

        if err is None:
            err, users_deny_file = run_vastool_inspect('vas_auth users-deny-file')

        if err is None:
            if not users_allow_file:
                users_allow_file = '/etc/opt/quest/vas/users.allow'
            if not users_deny_file:
                users_deny_file = '/etc/opt/quest/vas/users.deny'

        if err is None:
            err, users_allow = get_entries(users_allow_file)

        if err is None:
            err, users_deny = get_entries(users_deny_file)

    except Exception:
        tb = traceback.format_exc()
        err = str(tb)

    # Build result
    result['changed'] = False   # this module never makes any changes to the host
    result['failed'] = err is not None
    result['msg'] = err if err is not None else ''

    # Create ansible_facts data
    if facts:
        result_facts = result.copy()
        result_facts['params'] = params
        result_facts['version'] = version
        result_facts['users_allow'] = users_allow
        result_facts['users_deny'] = users_deny
        result['ansible_facts'] = {facts_key: result_facts}

    # Return
    return err, result



# ------------------------------------------------------------------------------
def run_vastool_inspect(setting):
    """
    Run vastool inspect
    """

    # Return values
    err = None
    value = ''
    non_zero_ret_code = False

    # Build vastool command
    cmd = []
    cmd += [vt.VASTOOL_PATH]
    cmd += ['inspect']
    cmd += [setting]

    # Call vastool
    try:
        p = subprocess.Popen(' '.join(cmd), stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        rval_bytes, rval_err = p.communicate()
        rval_bytes += rval_err
    # This exception happens when the process exits with a non-zero return code
    except subprocess.CalledProcessError as e:
        # Just grab output bytes likes a normal exit
        rval_bytes = e.output
    # Popen returns list of bytes so we have to decode to get a string
    rval_str = rval_bytes.decode(sys.stdout.encoding)

    if p.returncode:
        err = rval_str
    else:
        value = rval_str.strip()

    # Return
    return err, value


# ------------------------------------------------------------------------------
def get_entries(file_name):
    """
    Get non-empty, non-comment lines
    """

    err = None
    entries = []

    # check whether the file exists
    if os.path.isfile(file_name):
        try:
            with open(file_name, 'rb') as users_file:
                users_bytes = users_file.read()
                users_str = to_text(users_bytes, errors='surrogate_or_strict')

                entries = users_str.split('\n')
                entries = [entry.strip() for entry in entries]
                entries = [entry for entry in entries if len(entry) > 0]
                entries = [entry for entry in entries if entry[0] != '#']

        except Exception:
            tb = traceback.format_exc()
            err = str(tb)
    else:
        entries.append(file_name + ' does not exist.')

    # Return
    return err, entries


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
