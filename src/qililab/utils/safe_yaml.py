# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Registry-isolated, data-only YAML loader for safe deserialization.

The serialization backbone of qililab is ``from qilisdk.yaml import yaml`` where the
imported object is ``QiliYAML(typ="unsafe")``. The ``unsafe`` flavour makes ruamel use
``ruamel.yaml.constructor.Constructor``, whose class-level registries carry the
``tag:yaml.org,2002:python/{name,module,object,object/apply,object/new}`` multi
constructors (arbitrary code execution), and qilisdk additionally registers code-exec
gadget constructors on that same shared class: ``!function`` / ``!lambda`` (``dill.loads``
on base64) and ``!type`` / ``!PydanticModel`` / ``!defaultdict`` (``__import__`` of an
attacker-supplied string). Calling ``yaml.load`` on untrusted input therefore executes
arbitrary code before any type check can run.

This module builds a loader that is byte-compatible with the qilisdk tag scheme (so every
legitimate qililab round-trip keeps working) but cannot execute code:

* It gives its constructor brand-new, per-instance ``yaml_constructors`` /
  ``yaml_multi_constructors`` dicts. ruamel resolves a node's constructor via the instance
  attribute first, so editing these never mutates (and is never affected by) the shared
  class registry that the unsafe loader depends on.
* It seeds those dicts with the canonical YAML core tags and the side-effect-free data /
  class tags qililab actually round-trips (``!ndarray``, ``!complex``, ``!tuple``,
  ``!Square``, ``!QProgram``, ``!UUID``, ...), and copies no ``python/*`` constructor.
* It installs rejecting constructors for ``!function`` / ``!lambda``, allow-list-gated
  constructors for ``!type`` / ``!PydanticModel`` / ``!defaultdict``, and an
  unknown-tag fallback that raises (without the explicit fallback ruamel would silently
  treat an unknown ``!!python/object/apply`` as benign undefined data instead of raising).

The loader is built lazily and cached on first use: qililab populates the shared class
registry through ``@yaml.register_class`` decorators at import time, and some of those
imports run after this module, so snapshotting at import time would miss class tags.

Delegation note: once qilisdk ships a safe-by-default loader (QSDK-01 / ``safe_yaml``) and
the qililab dependency pin is bumped to that tagged release, this module should collapse to
delegating to qilisdk's safe ``deserialize`` and the hand-built registry copy below can be
deleted.
"""

from typing import Any

from qilisdk.yaml import QiliYAML

# Gadget tags that decode/execute arbitrary code via dill.loads. Rejected outright.
_REJECT_TAGS: frozenset[str] = frozenset({"!function", "!lambda"})

# Gadget tags that import an attacker-supplied fully-qualified name via __import__.
# Allowed only for fully-qualified names in the allow-list below.
_GATED_TAGS: frozenset[str] = frozenset({"!type", "!PydanticModel", "!defaultdict"})

# Fully-qualified names permitted through the gated tags. Empirically empty for qililab:
# a grep of src + tests emits none of the gated tags, so every legitimate round-trip works
# with an empty allow-list. Add a concrete FQN here only if a feature genuinely needs it.
_ALLOWED_FQNS: frozenset[str] = frozenset()

_safe_loader: QiliYAML | None = None


class _RejectingConstructorError(Exception):
    """Internal marker raised while constructing a rejected/unknown tag.

    Re-wrapped by the public ``deserialize`` into a ``DeserializationError`` together with
    every other load failure, so callers see a single error type.
    """


def _reject(tag: str):
    """Build a constructor that always refuses, used for code-execution gadget tags.

    Args:
        tag (str): The YAML tag the rejecting constructor stands in for.

    Returns:
        Callable: A ruamel constructor that raises instead of constructing.
    """

    def _constructor(constructor: Any, node: Any) -> Any:
        raise _RejectingConstructorError(f"Refusing to deserialize tag {tag!r}: possible arbitrary code execution.")

    return _constructor


def _reject_unknown(constructor: Any, node: Any) -> Any:
    """Fallback for any tag without a registered safe constructor.

    Args:
        constructor (Any): The ruamel constructor instance (unused).
        node (Any): The YAML node whose tag is unknown.

    Returns:
        Any: Never returns; always raises.
    """
    raise _RejectingConstructorError(f"Refusing to deserialize unknown tag {node.tag!r}.")


def _gate(tag: str, original: Any):
    """Wrap a gated qilisdk constructor behind the fully-qualified-name allow-list.

    Args:
        tag (str): The gated YAML tag (``!type`` / ``!PydanticModel`` / ``!defaultdict``).
        original (Any): The original qilisdk constructor to delegate to when allowed.

    Returns:
        Callable: A ruamel constructor that imports only allow-listed names.
    """

    def _constructor(constructor: Any, node: Any) -> Any:
        # Extract the fully-qualified name the gadget would import.
        if tag == "!type":
            fqn = node.value
        else:
            mapping = constructor.construct_mapping(node, deep=True)
            fqn = mapping.get("type") if tag == "!PydanticModel" else mapping.get("default_factory")
        if fqn not in _ALLOWED_FQNS:
            raise _RejectingConstructorError(
                f"Refusing to deserialize tag {tag!r} importing {fqn!r}: not in allow-list."
            )
        # Reachable only once an FQN is added to the (currently empty) allow-list, so it
        # is unreachable in the shipped config.
        return original(constructor, node)  # pragma: no cover

    return _constructor


def _build_safe_loader() -> QiliYAML:
    """Build the registry-isolated, data-only loader.

    Returns:
        QiliYAML: A loader that constructs only side-effect-free data and class tags and
        raises on every code-execution gadget tag or unknown tag.
    """
    loader = QiliYAML(typ="unsafe")  # same subclass so register_class tagging matches
    sc = loader.constructor
    source = type(loader.constructor)

    # Shadow the shared class registries with fresh per-instance dicts. ruamel looks up the
    # instance attribute first, so from here on edits never touch the shared class registry.
    sc.yaml_constructors = {}
    sc.yaml_multi_constructors = {}

    # Seed the safe core YAML tags and the side-effect-free data / class tags. Skip the
    # None default, the rejected tags, the gated tags, and every python/* constructor.
    for tag, ctor in source.yaml_constructors.items():
        if tag is None:
            continue
        if tag in _REJECT_TAGS or tag in _GATED_TAGS:
            continue
        if isinstance(tag, str) and tag.startswith("tag:yaml.org,2002:python/"):
            continue
        sc.yaml_constructors[tag] = ctor

    # Reject the dill gadget tags outright.
    for tag in _REJECT_TAGS:
        sc.yaml_constructors[tag] = _reject(tag)

    # Gate the __import__ gadget tags behind the allow-list.
    for tag in _GATED_TAGS:
        original = source.yaml_constructors.get(tag)
        if original is not None:
            sc.yaml_constructors[tag] = _gate(tag, original)

    # Raise on any unknown tag (including the python/* multi-constructor tags, which are not
    # copied above). Without this, ruamel silently returns benign undefined data instead.
    sc.yaml_constructors[None] = _reject_unknown

    # Leave yaml_multi_constructors empty: the python/object[/apply|/new] / name / module
    # multi-constructors are the primary RCE vectors and are intentionally not registered.
    return loader


def get_safe_loader() -> QiliYAML:
    """Return the cached registry-isolated safe loader, building it on first use.

    Returns:
        QiliYAML: The shared safe loader instance.
    """
    global _safe_loader
    if _safe_loader is None:
        _safe_loader = _build_safe_loader()
    return _safe_loader
