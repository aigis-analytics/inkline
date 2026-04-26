"""Inkline authoring — markdown-based deck authoring with directive grammar.

This package provides:
- ``directives`` — grammar, scopes, and plugin registry
- ``preprocessor`` — markdown → (deck_meta, sections[])
- ``asset_shorthand`` — ``![bg ...]`` parser
- ``notes_writer`` — ``<basename>.notes.txt`` emitter
- ``backend_coverage`` — slide-type × backend matrix + downgrade chains
- ``classes`` — class registry for Typst show-rule fragments
"""

from inkline.authoring.preprocessor import preprocess
from inkline.authoring.directives import register, DirectiveError

__all__ = ["preprocess", "register", "DirectiveError"]
