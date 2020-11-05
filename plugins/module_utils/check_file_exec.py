#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright (c) 2020, One Identity LLC
# File: check_file_exec.py
# Desc: Ansible utils module to check executable file permissions and get
#       its version.
# Auth: Mark Stillings
# Note:
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

import sys
import os
import subprocess
import re


# ------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
def check_file_exec(file_path, version_cmd):
    """
    Check if executable exists, can be executed, and get its version
    """

    # Return values
    err = None
    version = ''

    # Check if file is present
    exists = os.path.isfile(file_path)
    if not exists:
        err = file_path + ' was not found'

    # Check if we have permission to execute file
    if not err:
        x_ok = os.access(file_path, os.X_OK)
        if not x_ok:
            err = 'Insufficient permissions to execute ' + file_path

    # Get version
    if not err:
        err, version = get_file_version(file_path, version_cmd)

    # Return
    return err, version


# ------------------------------------------------------------------------------
def get_file_version(file_path, version_cmd):
    """
    Get executable file version
    """

    # Return values
    err = None
    version = None

    # Build vastool command
    cmd = []
    cmd += [file_path]
    cmd += [version_cmd]

    # Exec file to get version
    try:
        p = subprocess.Popen(' '.join(cmd), stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        rval_bytes, rval_err = p.communicate()
        rval_bytes += rval_err
    except subprocess.CalledProcessError as e:
        rval_bytes = e.output
    # Popen returns list of bytes so we have to decode to get a string
    rval_str = rval_bytes.decode(sys.stdout.encoding)

    # Compile regex
    vers_re_str = r'(?=.*)[\d]+\.[\d]+\.[\d]+[\.-][\d]+'
    vers_re = re.compile(vers_re_str)

    # Parse version from response
    version_match = vers_re.search(rval_str)
    if version_match:
        version_str = version_match.group()
        version_str = version_str.replace('-', '.')
        version = version_str

    # Check for error
    if not version:
        err = 'Could not get version of ' + file_path
        version = ''

    # Return
    return err, version
