#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright (c) 2021, One Identity LLC
# File: get_local_unix_user_conflicts.py
# Desc: Ansible module for local_unix_user_conflicts role that reads, filters
#       and returns data from /etc/passwd.
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
module: get_local_unix_user_conflicts.py

short_description: >
    Returns local user accounts that would conflict with a
    specified user name and UID on other hosts.

version_added: '2.9'

description: >
    Returns local user accounts that would conflict with a
    specified user name and UID on other hosts.

options:
    user_name:
        description:
            - User name.
        type: str
        required: true
    uid_number:
        description:
            - User ID.
        type: str
        required: true
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
        default: 'local_unix_user_conflicts'

author:
    - Laszlo Nagy (laszlo.nagy@oneidentity.com)
"""

EXAMPLES = """
- name: Normal usage
  get_local_unix_user_conflicts:
    user_name: 'bob'
    uid_number: '1001'
  register: get_local_unix_user_conflicts_result
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
        local_unix_user_conflicts:
            description: All fields of each conflicting user account
            type: list of lists
            returned: always
"""


# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_text
import platform
import subprocess
import sys
import traceback
from ansible_collections.oneidentity.authentication_services.plugins.module_utils.misc_utils import enclose_shell_arg


# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------

# Arg defaults
FACTS_DEFAULT = True
FACTS_KEY_DEFAULT = 'local_unix_user_conflicts'


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
            'user_name': {
                'type': 'str',
                'required': True,
            },
            'uid_number': {
                'type': 'str',
                'required': True,
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
    local_unix_users = []

    # Parameters
    user_name = params['user_name']
    uid_number = params['uid_number']
    facts = params['facts']
    facts_key = params['facts_key'] if params['facts_key'] else FACTS_KEY_DEFAULT

    try:
        if platform.system() == 'Darwin':
            rc, rval_str = run_dscl('. -list /Users')
            if rc == 0:
                list_of_users = rval_str.splitlines()
                for user in list_of_users:
                    uid = get_user_property(user, 'UniqueID')
                    gid = get_user_property(user, 'PrimaryGroupID')
                    gecos = get_user_property(user, 'RealName')
                    home_dir = get_user_property(user, 'NFSHomeDirectory')
                    shell = get_user_property(user, 'UserShell')
                    local_unix_users.append([user, '*', uid, gid, gecos, home_dir, shell])
            else:
                err = 'Failed to get list of users. ' + rval_str
        else:
            with open('/etc/passwd', 'rb') as passwd_file:
                passwd_bytes = passwd_file.read()
                passwd_str = to_text(passwd_bytes, errors='surrogate_or_strict')

                local_unix_users = passwd_str.split('\n')
                local_unix_users = [user.strip() for user in local_unix_users]
                local_unix_users = [user for user in local_unix_users if len(user) > 0]
                local_unix_users = [user for user in local_unix_users if user[0] != '#']
                local_unix_users = [user.split(':') for user in local_unix_users]
                local_unix_users = [user for user in local_unix_users if len(user) == 7]

        local_unix_users = [user for user in local_unix_users if
            (user_name == user[0] and uid_number != user[2]) or
            (user_name != user[0] and uid_number == user[2])]

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
        result_facts['local_unix_user_conflicts'] = local_unix_users
        result['ansible_facts'] = {facts_key: result_facts}

    # Return
    return err, result


# ------------------------------------------------------------------------------
def run_dscl(args):
    """
    macOS manages users and groups by directory services instead of /etc/passwd
    and /etc/group.
    macOS uses the dscl command to interact with directory services.
    """

    try:
        p = subprocess.Popen('dscl ' + args, stdin = None, stdout = subprocess.PIPE,
            stderr = subprocess.PIPE, shell = True)
        rval_bytes, rval_err = p.communicate()
        rval_bytes += rval_err
    # This exception happens when the process exits with a non-zero return code
    except subprocess.CalledProcessError as e:
        # Just grab output bytes likes a normal exit, we'll parse it for errors anyway
        rval_bytes = e.output

    # Popen returns list of bytes so we have to decode to get a string
    rval_str = rval_bytes.decode(sys.stdout.encoding)

    return p.returncode, rval_str


# ------------------------------------------------------------------------------
def get_user_property(user, prop):

    rc, rval_str = run_dscl('. -read /Users/' + enclose_shell_arg(user) + ' ' + prop)
    if rc == 0:
        # -read: Prints a directory. The property key is followed by colon, then a
        # space-separated list of the values for that property. If any value contains
        # embedded spaces, the list will instead be displayed one entry per line,
        # starting on the line after the key.
        lines = rval_str.splitlines()
        if len(lines) == 1:
            if lines[0].startswith(prop):
                return lines[0].split(': ')[1]
        elif len(lines) == 2:
            return lines[1].strip()

    return ''


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
