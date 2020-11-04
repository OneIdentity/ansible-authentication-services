#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright (c) 2020, One Identity LLC
# File: vastool.py
# Desc: Shared code for the various vastool_* modules
# Auth: Mark Stillings
# Note:
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

import sys
import subprocess
import re


# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------

# Vastool
VASTOOL_DIR = '/opt/quest/bin'
VASTOOL_FILE = 'vastool'
VASTOOL_PATH = VASTOOL_DIR + '/' + VASTOOL_FILE


# ------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
def vastool_status():
    """
    Call vastool status
    """

    # Return values
    domain = None

    # Build vastool command
    cmd = []
    cmd += [VASTOOL_PATH]
    cmd += ['status']
    cmd += ['-q']

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
    domain = vastool_status_parse(rval_str)

    # Return
    return domain


# ------------------------------------------------------------------------------
def vastool_status_parse(rval_str):

    # Return values
    domain = None

    # Find domain
    domain_re_str = r'^Domain: <(\S+)>$'
    domain_re = re.compile(domain_re_str, re.MULTILINE)
    domain_re_match = domain_re.split(rval_str)
    if len(domain_re_match) > 1 and domain_re_match[1] != 'N/A':
        domain = domain_re_match[1]

    # Return
    return domain
