"""
sigmascan module discovery + inverted rule index.

A sigmascan "module" is any SAF output ``parsed_data/<name>.*`` produced by a parser or an
analyser. Name→class resolution is delegated to ``SysdiagnoseConfig.get_module_class()``
(parser-first, then analyser), so new/renamed modules are picked up automatically. Scanner
modules (``sigmascan``, ``yarascan``, …) are excluded via the ``scannable`` class flag so
scanners never scan each other's or their own output.

The inverted index ``module -> [rules]`` maps each module to its module-scoped rules plus
every all-modules rule, so each source is scanned once by all rules that target it.
"""

from sysdiagnose.sigmascan.loader import LoadedRule
from sysdiagnose.utils.base import SysdiagnoseConfig
from sysdiagnose.utils.logger import logger

# Module output formats that are a scannable event stream.
SCANNABLE_FORMATS = ("jsonl", "json")


def discover_modules(config: SysdiagnoseConfig) -> set[str]:
    """Return the set of scannable module names SAF can produce.

    A module is scannable only if its output is an event stream (``format`` in
    ``jsonl``/``json`` — text/custom/binary outputs are excluded) and it is not a scanner
    itself (``scannable`` is ``True``). This is both the ``known_modules`` set the loader
    validates ``logsource.modules`` against and the universe an all-modules rule expands
    over.
    """
    names = set(config.get_parsers()) | set(config.get_analysers())
    scannable = set()
    for name in names:
        cls = config.get_module_class(name)
        if cls is None:
            continue
        if getattr(cls, "format", None) not in SCANNABLE_FORMATS:
            continue
        if not getattr(cls, "scannable", True):
            continue
        scannable.add(name)
    return scannable


def build_module_index(rules: list[LoadedRule], modules: set[str]) -> dict[str, list[LoadedRule]]:
    """Build the inverted index ``module -> [rules targeting it]``.

    Each module's list is its module-scoped rules plus every all-modules rule. Modules with
    no targeting rule are omitted.

    Args:
        rules: the validated rules to index.
        modules: the set of known module names (from ``discover_modules``).

    Returns:
        A dict mapping each targeted module name to the rules to run against it.
    """
    index: dict[str, list[LoadedRule]] = {}

    all_module_rules = [r for r in rules if r.is_all_modules]
    scoped_rules = [r for r in rules if not r.is_all_modules]

    # all-modules rules apply to every module
    if all_module_rules:
        for module in modules:
            index.setdefault(module, []).extend(all_module_rules)

    # module-scoped rules apply only to the modules they name
    for rule in scoped_rules:
        for module in rule.modules or ():
            if module not in modules:
                # should already be filtered by the loader; skip defensively
                logger.debug(f"sigmascan rule {rule.source_path}: skipping unknown module {module!r}")
                continue
            index.setdefault(module, []).append(rule)

    return index
