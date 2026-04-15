#! /usr/bin/env python3

# Sysdiagnose Jupyter integration
# Author: EC-DIGIT-CSIRC

"""
Sysdiagnose Jupyter integration.

Usage in a Jupyter notebook::

    %load_ext sysdiagnose.jupyter

Then use magic commands::

    %sd cases
    %sd use <case_id>
    %sd parse <parser_name>
    %sd analyse <analyser_name>
    %sd info

Or use the Python API directly::

    from sysdiagnose.jupyter import get_sd
    sd = get_sd()
"""


def get_sd():
    """Return the shared Sysdiagnose instance used by the Jupyter extension."""
    from sysdiagnose.jupyter.magic import SysdiagnoseMagic  # noqa: PLC0415
    magic = SysdiagnoseMagic.instance()
    if magic:
        return magic.sd
    from sysdiagnose import Sysdiagnose  # noqa: PLC0415
    return Sysdiagnose()


def load_ipython_extension(ipython):
    """Called by %load_ext sysdiagnose.jupyter"""
    from sysdiagnose.jupyter.magic import SysdiagnoseMagic  # noqa: PLC0415
    ipython.register_magics(SysdiagnoseMagic)
    print("Sysdiagnose Jupyter extension loaded. Use %sd help for usage.")
