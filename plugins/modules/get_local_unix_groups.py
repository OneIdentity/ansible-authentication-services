#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright (c) 2021, One Identity LLC
# File: get_local_unix_groups.py
# Desc: Ansible module for local_unix_groups role that reads, filters and
#       returns data from /etc/group.
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
module: get_local_unix_groups.py

short_description: Returns all groups or specific user groups.

version_added: '2.9'

description: >
    Returns either all groups or some specific groups from
    /etc/group.

options:
    group_name:
        description:
            - Group name.
        type: str
        required: false
        default: ''
    gid_number:
        description:
            - Group ID.
        type: str
        required: false
        default: ''
    member:
        description:
            - Comma separated user names.
        type: str
        required: false
        default: ''
    include_all_group_members:
        description:
            - Include all of the group members in the report?
        type: bool
        required: false
        default: true
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
        default: 'local_unix_groups'

author:
    - Laszlo Nagy (laszlo.nagy@oneidentity.com)
"""

EXAMPLES = """
- name: Normal usage
  get_local_unix_groups:
    group_name: ''
    gid_number: ''
    member: ''
    include_all_group_members: true
  register: get_local_unix_groups_result
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
        local_unix_groups:
            description: All fields of each group
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
GROUP_FIELD_DEFAULT = ''
INCLUDE_ALL_GROUP_MEMBERS_DEFAULT = True
FACTS_DEFAULT = True
FACTS_KEY_DEFAULT = 'local_unix_groups'


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
            'group_name': {
                'type': 'str',
                'required': False,
                'default': GROUP_FIELD_DEFAULT
            },
            'gid_number': {
                'type': 'str',
                'required': False,
                'default': GROUP_FIELD_DEFAULT
            },
            'member': {
                'type': 'str',
                'required': False,
                'default': GROUP_FIELD_DEFAULT
            },
            'include_all_group_members': {
                'type': 'bool',
                'required': False,
                'default': INCLUDE_ALL_GROUP_MEMBERS_DEFAULT
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
    local_unix_groups = []

    # Parameters
    group_name = params['group_name']
    gid_number = params['gid_number']
    member = params['member']
    include_all_group_members = params['include_all_group_members']
    facts = params['facts']
    facts_key = params['facts_key'] if params['facts_key'] else FACTS_KEY_DEFAULT

    try:
        if platform.system() == 'Darwin':
            rc, rval_str = run_dscl('. -list /Groups')
            if rc == 0:
                list_of_groups = rval_str.splitlines()
                for group in list_of_groups:
                    gid = get_group_property(group, 'PrimaryGroupID')
                    members = get_group_property(group, 'GroupMembership')
                    local_unix_groups.append([group, '*', gid, members])
            else:
                err = 'Failed to get list of groups. ' + rval_str
        else :
            with open('/etc/group', 'rb') as group_file:
                group_bytes = group_file.read()
                group_str = to_text(group_bytes, errors='surrogate_or_strict')

                local_unix_groups = group_str.split('\n')
                local_unix_groups = [group.strip() for group in local_unix_groups]
                local_unix_groups = [group for group in local_unix_groups if len(group) > 0]
                local_unix_groups = [group for group in local_unix_groups if group[0] != '#']
                local_unix_groups = [group.split(':') for group in local_unix_groups]
                local_unix_groups = [group for group in local_unix_groups if len(group) == 4]

        if group_name:
            local_unix_groups = [group for group in local_unix_groups if group_name in group[0]]
        if gid_number:
            local_unix_groups = [group for group in local_unix_groups if gid_number == group[2]]
        if member:
            local_unix_group_having_member_users = []
            member_users = member.split(',')
            for group in local_unix_groups:
                for member_user in member_users:
                    if member_user in group[3]:
                        local_unix_group_having_member_users.append(group)
                        break
            local_unix_groups = local_unix_group_having_member_users

        if not include_all_group_members:
            local_unix_groups = [group[ : -1] for group in local_unix_groups]

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
        result_facts['local_unix_groups'] = local_unix_groups
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
def get_group_property(group, prop):

    rc, rval_str = run_dscl('. -read /Groups/' + enclose_shell_arg(group) + ' ' + prop)
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
