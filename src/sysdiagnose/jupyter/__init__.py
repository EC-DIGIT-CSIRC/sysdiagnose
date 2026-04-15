"""
Sysdiagnose Jupyter integration.

Usage in a Jupyter notebook:
    %load_ext sysdiagnose.jupyter

Then use magic commands:
    %sd cases
    %sd use <case_id>
    %sd parse <parser_name>
    %sd analyse <analyser_name>
    %sd info

Or use the Python API directly:
    from sysdiagnose.jupyter import get_sd
    sd = get_sd()
"""

_sd_instance = None


def get_sd():
    """Return the shared Sysdiagnose instance used by the Jupyter extension."""
    from sysdiagnose.jupyter.magic import SysdiagnoseMagic
    magic = SysdiagnoseMagic.instance()
    if magic:
        return magic.sd
    # fallback: create a new instance
    from sysdiagnose import Sysdiagnose
    return Sysdiagnose()


def load_ipython_extension(ipython):
    """Called by %load_ext sysdiagnose.jupyter"""
    from sysdiagnose.jupyter.magic import SysdiagnoseMagic
    ipython.register_magics(SysdiagnoseMagic)
    print("Sysdiagnose Jupyter extension loaded. Use %sd help for usage.")
