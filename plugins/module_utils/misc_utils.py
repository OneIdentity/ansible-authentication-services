#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright (c) 2022, One Identity LLC
# File: misc_utils.py
# Desc: Ansible utils module that contains miscellaneous functions.
# Auth: Laszlo Nagy
# Note:
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
def enclose_shell_arg(arg):
    """
    Encloses shell argument in quotation marks because it may contain space(s).
    If the string contains a single quotation mark then it must be replaced
    by '"'"'. See https://stackoverflow.com/q/1250079/26449
    """

    return "'" + arg.replace("'", "'\"'\"'") + "'"
