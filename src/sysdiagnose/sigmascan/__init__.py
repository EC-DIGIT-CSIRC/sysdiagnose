"""
Support package for the `sigmascan` analyser.

This package holds the engine internals that are pure, stateless, and unit-testable
independently of the SAF analyser wiring:

- `loader`    : discover rule files, parse/validate via pySigma, enforce the operator
                allow-list, extract `logsource.modules`; invalid rules are logged and skipped.
- `matcher`   : leaf matcher over SAF's nested `data.*` events.
- `condition` : walk pySigma's parsed condition tree.
- `logsource` : module discovery / inverted index.
- `emit`      : build alert records.
"""
