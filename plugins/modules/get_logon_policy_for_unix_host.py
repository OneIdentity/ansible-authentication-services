#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright (c) 2022, One Identity LLC
# File: get_logon_policy_for_unix_host.py
# Desc: Ansible module that returns users that are allowed access to the Unix
#       host using the vastool list users-allowed command.
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
module: get_logon_policy_for_unix_host

short_description: Returns users that are allowed access to the Unix host

version_added: '2.9'

description: >
    Returns users that are allowed access to the Unix host using the
    vastool list users-allowed command.

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
        default: 'get_logon_policy_for_unix_host_facts_key'

author:
    - Laszlo Nagy (laszlo.nagy@oneidentity.com)
"""

EXAMPLES = """
- name: Get logon policy for unix host
  get_logon_policy_for_unix_host:
    facts: true
    facts_key: get_logon_policy_for_unix_host_facts_key
  register: get_logon_policy_for_unix_host_result
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
        users_allowed:
            description: All fields of each user account
            type: list of lists
            returned: always
"""


# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------


from ansible.module_utils.basic import AnsibleModule
import sys
import subprocess
import traceback
import ansible_collections.oneidentity.authentication_services.plugins.module_utils.vastool as vt
import ansible_collections.oneidentity.authentication_services.plugins.module_utils.check_file_exec as cfe


# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------

# Arg choices and defaults
FACTS_DEFAULT = True
FACTS_VERBOSE_DEFAULT = True
FACTS_KEY_DEFAULT = 'get_logon_policy_for_unix_host_facts_key'


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
    users_allowed = []

    # Parameters
    facts = params['facts']
    facts_key = params['facts_key'] if params['facts_key'] else FACTS_KEY_DEFAULT

    try:

        # Check vastool
        err, version = cfe.check_file_exec(vt.VASTOOL_PATH, '-v')

        # Run vastool
        if err is None:
            err, users_allowed = run_vastool_list_users_allowed()

    except Exception:
        tb = traceback.format_exc()
        err = str(tb)

    # Build result
    result['changed'] = False   # vastool list users-allowed never makes any changes to the host
    result['failed'] = err is not None
    result['msg'] = err if err is not None else ''

    # Create ansible_facts data
    if facts:
        result_facts = result.copy()
        result_facts['params'] = params
        result_facts['version'] = version
        result_facts['users_allowed'] = users_allowed
        result['ansible_facts'] = {facts_key: result_facts}

    # Return
    return err, result


# ------------------------------------------------------------------------------
def run_vastool_list_users_allowed():
    """
    Run vastool list users-allowed
    """

    # Return values
    err = None
    users_allowed = []
    non_zero_ret_code = False

    # Build vastool command
    cmd = []
    cmd += [vt.VASTOOL_PATH]
    cmd += ['list']
    cmd += ['users-allowed']

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
    err, users_allowed = parse_vastool_stdout(non_zero_ret_code, rval_str)

    # Return
    return err, users_allowed


# ------------------------------------------------------------------------------
def parse_vastool_stdout(non_zero_ret_code, stdout_str):

    # Return values
    err = None
    users_allowed = []

    if non_zero_ret_code:
        err = stdout_str
    else:
        users_allowed = stdout_str.split('\n')
        users_allowed = [user.strip() for user in users_allowed]
        users_allowed = [user for user in users_allowed if len(user) > 0]
        users_allowed = [user.split(':') for user in users_allowed]
        users_allowed = [user for user in users_allowed if len(user) == 7]

    # Return
    return err, users_allowed


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
