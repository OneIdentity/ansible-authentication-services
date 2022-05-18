#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright (c) 2020, One Identity LLC
# File: vastool_join.py
# Desc: Ansible module that wraps vastool join/unjoin commands.
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
module: vastool_join

short_description: Active Directory join

version_added: '2.9'

description: >
    Performs Active Directory join/unjoin using the Authentication Services vastool binary.

options:
    state:
        description:
            - Active Directory join state
        type: str
        required: false
        default: joined
        choices: ['joined', 'unjoined']
    domain:
        description:
            - Active Directory domain to join
        type: str
        required: true
    username:
        description:
            - Active Directory user or principal to perform join
        type: str
        required: true
    password:
        description:
            - Active Directory password to authenticate
        type: str
        required: true
    servers:
        description:
            - Servers to use for join
        type: list
        elements: str
        required: false
        default: []
    account_name:
        description:
            - Name of host computer account
        type: str
        required: false
        default: fully-qualified DNS name of host
    account_container:
        description:
            - Name of container for host computer account
        type: str
        required: false
        default: default computers container
    extra_args:
        description:
            - Other arguments to be passed on to vastool
        type: str
        required: false
        default: ''
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
        default: 'vastool_join'

author:
    - Mark Stillings (mark.stillings@oneidentity.com)
"""

EXAMPLES = """
- name: Simple join
  vastool_join:
    state: joined
    domain: oneidentity.com
    username: user
    password: pass
  register: vastool_join_result
- name: Simple unjoin
  vastool_join:
    state: unjoined
    domain: oneidentity.com
    username: user
    password: pass
  register: vastool_join_result
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
        steps:
            description: Vastool join/unjoin steps and results of those steps
            type: list of dicts
            returned: when facts_verbose true
"""


# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

from ansible.module_utils.basic import AnsibleModule
import sys
import subprocess
import traceback
import re
import ansible_collections.oneidentity.authentication_services.plugins.module_utils.vastool as vt
import ansible_collections.oneidentity.authentication_services.plugins.module_utils.check_file_exec as cfe
from ansible_collections.oneidentity.authentication_services.plugins.module_utils.misc_utils import enclose_shell_arg


# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------

# Arg choices and defaults
STATE_DEFAULT = 'joined'
STATE_CHOICES = ['joined', 'unjoined']
SERVERS_DEFAULT = []
ACCOUNT_NAME_DEFAULT = None
ACCOUNT_CONTAINER_DEFAULT = None
EXTRA_ARGS_DEFAULT = ''
FACTS_DEFAULT = True
FACTS_VERBOSE_DEFAULT = True
FACTS_KEY_DEFAULT = 'vastool_join'


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
            'state': {
                'type': 'str',
                'required': False,
                'choices': STATE_CHOICES,
                'default': STATE_DEFAULT
            },
            'domain': {
                'type': 'str',
                'required': True
            },
            'username': {
                'type': 'str',
                'required': True,
                'no_log': True
            },
            'password': {
                'type': 'str',
                'required': True,
                'no_log': True
            },
            'servers': {
                'type': 'list',
                'elements': 'str',
                'required': False,
                'default': SERVERS_DEFAULT
            },
            'account_name': {
                'type': 'str',
                'required': False,
                'default': ACCOUNT_NAME_DEFAULT
            },
            'account_container': {
                'type': 'str',
                'required': False,
                'default': ACCOUNT_CONTAINER_DEFAULT
            },
            'extra_args': {
                'type': 'str',
                'required': False,
                'default': EXTRA_ARGS_DEFAULT
            },
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
    changed = False
    steps = []

    # Parameters
    state = params['state']
    domain = params['domain']
    username = params['username']
    password = params['password']
    servers = params['servers']
    account_name = params['account_name']
    account_container = params['account_container']
    extra_args = params['extra_args']
    facts = params['facts']
    facts_verbose = params['facts_verbose']
    facts_key = params['facts_key'] if params['facts_key'] else FACTS_KEY_DEFAULT

    try:

        # Check vastool
        err, version = cfe.check_file_exec(vt.VASTOOL_PATH, '-v')

        # Run vastool
        if err is None:
            err, changed, steps = run_vastool(
                state,
                domain,
                username,
                password,
                servers,
                account_name,
                account_container,
                extra_args)

    except Exception:
        tb = traceback.format_exc()
        err = str(tb)

    # Build result
    result['changed'] = changed
    result['failed'] = err is not None
    result['msg'] = err if err is not None else ''

    # Create ansible_facts data
    if facts:
        result_facts = result.copy()
        result_facts['params'] = params
        result_facts['version'] = version
        if facts_verbose:
            result_facts['steps'] = steps
        result['ansible_facts'] = {facts_key: result_facts}

    # Return
    return err, result


# ------------------------------------------------------------------------------
def run_vastool(
        state,
        domain,
        username,
        password,
        servers,
        account_name,
        account_container,
        extra_args):
    """
    Run vastool
    """

    # Return values
    err = None
    changed = False
    steps = []

    # Check status to decide what to do
    status_domain = vt.vastool_status()

    # Joined
    if state == 'joined':

        # If not already joined to a domain then join
        if status_domain is None:
            err, changed, steps = run_vastool_join(
                domain,
                username,
                password,
                servers,
                account_name,
                account_container,
                extra_args
            )

        # If already joined to requested domain then do nothing
        elif status_domain == domain:
            pass

        # If joined to a different domain then we need to complain
        else:
            err = 'Cannot join domain ' + domain + ' because already joined to domain ' + status_domain

    # Unjoined
    elif state == 'unjoined':

        # If joined to a domain then unjoin
        if status_domain is not None:
            err, changed, steps = run_vastool_unjoin(
                username,
                password,
                account_name,
                extra_args
            )

        # If already unjoined then do nothing
        else:
            pass

    # Unknown state
    else:
        err = 'Unexpected state requested: ' + state

    # Return
    return err, changed, steps


# ------------------------------------------------------------------------------
def run_vastool_join(
        domain,
        username,
        password,
        servers,
        account_name,
        account_container,
        extra_args):

    # Return values
    err = None
    changed = False
    steps = []

    # Build vastool command
    cmd = []
    cmd += [vt.VASTOOL_PATH]
    cmd += ['-u ' + enclose_shell_arg(username)]
    cmd += ['-w ' + enclose_shell_arg(password)]
    cmd += ['join']
    cmd += ['-f']
    cmd += ['-n ' + account_name] if account_name else []
    cmd += ['-c ' + enclose_shell_arg(account_container)] if account_container else []
    cmd += [extra_args] if extra_args else []
    cmd += [domain]
    cmd += servers if servers else []

    # Call vastool
    try:
        p = subprocess.Popen(' '.join(cmd), stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        rval_bytes, rval_err = p.communicate()
        rval_bytes += rval_err
    # This exception happens when the process exits with a non-zero return code
    except subprocess.CalledProcessError as e:
        # Just grab output bytes likes a normal exit, we'll parse it for errors anyway
        rval_bytes = e.output
    # Popen returns list of bytes so we have to decode to get a string
    rval_str = rval_bytes.decode(sys.stdout.encoding)

    # Parse vastool return
    err, changed, steps = parse_vastool_steps(domain, rval_str)

    # Return
    return err, changed, steps


# ------------------------------------------------------------------------------
def run_vastool_unjoin(
        username,
        password,
        account_name,
        extra_args):

    # Return values
    err = None
    changed = False
    steps = []

    # Build vastool command
    cmd = []
    cmd += [vt.VASTOOL_PATH]
    cmd += ['-u ' + enclose_shell_arg(username)]
    cmd += ['-w ' + enclose_shell_arg(password)]
    cmd += ['unjoin']
    cmd += ['-f']
    cmd += ['-n ' + account_name] if account_name else []
    cmd += [extra_args] if extra_args else []

    # Call vastool
    try:
        p = subprocess.Popen(' '.join(cmd), stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        rval_bytes, rval_err = p.communicate()
        rval_bytes += rval_err
    # This exception happens when the process exits with a non-zero return code
    except subprocess.CalledProcessError as e:
        # Just grab output bytes likes a normal exit, we'll parse it for errors anyway
        rval_bytes = e.output
    # Popen returns list of bytes so we have to decode to get a string
    rval_str = rval_bytes.decode(sys.stdout.encoding)

    # Parse vastool return
    err, changed, steps = parse_vastool_steps('', rval_str)

    # Return
    return err, changed, steps


# ------------------------------------------------------------------------------
def parse_vastool_steps(domain, steps_str):

    # Return values
    err = None
    changed = False
    steps = []

    # Find steps
    steps_re_str = r'^(.+)\s\.\.\.\s(.+)'
    steps_re = re.compile(steps_re_str, re.MULTILINE)
    steps_re_match = steps_re.findall(steps_str)

    # Format into list of dicts
    for steps_match in steps_re_match:
        if len(steps_match) > 1:
            steps += [
                {
                    'message': steps_match[0],
                    'result': steps_match[1].capitalize()
                }
            ]

    # Find errors
    error_re_str = r'^(error): (.*)$'
    error_re = re.compile(error_re_str, re.MULTILINE | re.IGNORECASE)
    error_re_match = error_re.findall(steps_str)

    # Format into list of dicts
    for error_match in error_re_match:
        if len(error_match) > 1:
            steps += [
                {
                    'message': error_match[1],
                    'result': error_match[0].capitalize()
                }
            ]

    # Build list of errors
    err_list = []

    # Check each step for result
    error_results = ['Failure', 'Failed', 'Error']
    for step in steps:
        if step['result'] in error_results:
            err_list += [step['result'] + ': ' + step['message']]

    # If no errors then we succeeded, mark changed
    if not err_list:
        changed = True

    # Check for error
    if err_list:
        err = '\n'.join(err_list)

    # Return
    return err, changed, steps


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
