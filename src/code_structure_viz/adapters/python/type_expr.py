from __future__ import annotations

import ast
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath

from code_structure_viz.adapters.python.model import SourceRangeWithColumns


class BindingKind(StrEnum):
    MODULE = "module"
    SYMBOL = "symbol"


class TypeReferenceRole(StrEnum):
    HEAD = "head"
    ARGUMENT = "argument"


class TypeReferenceSiteKind(StrEnum):
    INHERITANCE_BASE = "inheritance_base"
    FIELD_ANNOTATION = "field_annotation"
    PARAMETER_ANNOTATION = "parameter_annotation"
    RETURN_ANNOTATION = "return_annotation"


@dataclass(frozen=True, slots=True)
class ImportBinding:
    local_name: str
    canonical_name: str
    kind: BindingKind

    def __post_init__(self) -> None:
        local = unicodedata.normalize("NFC", self.local_name)
        canonical = unicodedata.normalize("NFC", self.canonical_name)
        if not local or not canonical:
            raise ValueError("import binding is empty")
        object.__setattr__(self, "local_name", local)
        object.__setattr__(self, "canonical_name", canonical)


@dataclass(frozen=True, slots=True)
class TypeReferenceSite:
    kind: TypeReferenceSiteKind
    owner_class_id: str
    member_id: str | None
    site_index: int
    path: PurePosixPath

    def __post_init__(self) -> None:
        if type(self.site_index) is not int or self.site_index < 0:
            raise ValueError("type reference site index is invalid")
        if self.kind is TypeReferenceSiteKind.INHERITANCE_BASE:
            if self.member_id is not None:
                raise ValueError("inheritance site cannot have a member")
        elif self.member_id is None:
            raise ValueError("member annotation site requires a member")


@dataclass(frozen=True, slots=True)
class TypeReferenceOccurrence:
    spelling: tuple[str, ...]
    role: TypeReferenceRole
    site_kind: TypeReferenceSiteKind
    owner_class_id: str
    member_id: str | None
    site_index: int
    path: PurePosixPath
    range: SourceRangeWithColumns
    preorder_ordinal: int


@dataclass(frozen=True, slots=True)
class RenderedType:
    text: str
    occurrences: tuple[TypeReferenceOccurrence, ...]
    supported: bool
    outer_head: TypeReferenceOccurrence | None


@dataclass(frozen=True, slots=True)
class _OccurrenceDraft:
    spelling: tuple[str, ...]
    role: TypeReferenceRole
    range: SourceRangeWithColumns


@dataclass(frozen=True, slots=True)
class _RenderedNode:
    text: str
    occurrences: tuple[_OccurrenceDraft, ...]
    supported: bool
    outer_head_index: int | None = None


@dataclass(frozen=True, slots=True)
class _TypeReferenceCandidate:
    original_name: str
    candidate_name: str
    rendered_name: str
    explicit_import: bool
    binding_kind: BindingKind | None
    binding_exact: bool
    internal_class: tuple[str, str] | None


_LITERAL_NAMES = frozenset({"typing.Literal", "typing_extensions.Literal"})
_ANNOTATED_NAMES = frozenset({"typing.Annotated", "typing_extensions.Annotated"})


class SafeTypeExpressionRenderer:
    def __init__(
        self,
        bindings: tuple[ImportBinding, ...],
        *,
        current_module: str | None = None,
        owner_qualified_name: str | None = None,
        class_identities: frozenset[tuple[str, str]] = frozenset(),
        modules: frozenset[str] = frozenset(),
    ) -> None:
        grouped: dict[str, set[tuple[str, BindingKind]]] = {}
        for binding in bindings:
            grouped.setdefault(binding.local_name, set()).add(
                (binding.canonical_name, binding.kind)
            )
        self._bindings = {
            local: ImportBinding(local, next(iter(values))[0], next(iter(values))[1])
            for local, values in grouped.items()
            if len(values) == 1
        }
        self._current_module = current_module
        self._owner_qualified_name = owner_qualified_name
        self._class_identities = class_identities
        self._modules = modules

    def render(self, node: ast.expr, site: TypeReferenceSite) -> RenderedType:
        rendered = self._render_node(
            node,
            TypeReferenceRole.HEAD,
            range_override=None,
            allow_forward=True,
        )
        if not rendered.supported:
            return RenderedType("?", (), False, None)
        occurrences = tuple(
            TypeReferenceOccurrence(
                spelling=draft.spelling,
                role=draft.role,
                site_kind=site.kind,
                owner_class_id=site.owner_class_id,
                member_id=site.member_id,
                site_index=site.site_index,
                path=site.path,
                range=draft.range,
                preorder_ordinal=ordinal,
            )
            for ordinal, draft in enumerate(rendered.occurrences)
        )
        outer_head = (
            occurrences[rendered.outer_head_index]
            if rendered.outer_head_index is not None
            else None
        )
        return RenderedType(rendered.text, occurrences, True, outer_head)

    def _render_node(
        self,
        node: ast.expr,
        role: TypeReferenceRole,
        *,
        range_override: SourceRangeWithColumns | None,
        allow_forward: bool,
    ) -> _RenderedNode:
        symbol = _symbol(node)
        if symbol is not None:
            return _RenderedNode(
                self._candidate(symbol).rendered_name,
                (_OccurrenceDraft(symbol, role, range_override or _range(node)),),
                True,
                0 if role is TypeReferenceRole.HEAD else None,
            )

        if isinstance(node, ast.Subscript):
            base = _symbol(node.value)
            if base is None:
                return _unsupported()
            base_candidate = self._candidate(base)
            canonical_base = base_candidate.rendered_name
            arguments = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
            if (
                base_candidate.internal_class is None
                and base_candidate.candidate_name in _LITERAL_NAMES
            ):
                if not arguments:
                    return _unsupported()
                return _RenderedNode(
                    f"{canonical_base}[{', '.join('?' for _ in arguments)}]", (), True
                )
            if (
                base_candidate.internal_class is None
                and base_candidate.candidate_name in _ANNOTATED_NAMES
            ):
                if len(arguments) < 2:
                    return _unsupported()
                first = self._render_node(
                    arguments[0],
                    role,
                    range_override=range_override,
                    allow_forward=allow_forward,
                )
                if not first.supported:
                    return _unsupported()
                return _RenderedNode(f"{canonical_base}[{first.text}, ?]", first.occurrences, True)

            base_occurrence = _OccurrenceDraft(
                base,
                TypeReferenceRole.HEAD,
                range_override or _range(node.value),
            )
            rendered_arguments = tuple(
                self._render_node(
                    argument,
                    TypeReferenceRole.ARGUMENT,
                    range_override=range_override,
                    allow_forward=allow_forward,
                )
                for argument in arguments
            )
            if not arguments or any(not item.supported for item in rendered_arguments):
                return _unsupported()
            return _RenderedNode(
                f"{canonical_base}[{', '.join(item.text for item in rendered_arguments)}]",
                (
                    base_occurrence,
                    *(occurrence for item in rendered_arguments for occurrence in item.occurrences),
                ),
                True,
                0,
            )

        if isinstance(node, ast.Tuple):
            items = tuple(
                self._render_node(
                    item,
                    role,
                    range_override=range_override,
                    allow_forward=allow_forward,
                )
                for item in node.elts
            )
            if any(not item.supported for item in items):
                return _unsupported()
            if not items:
                text = "()"
            elif len(items) == 1:
                text = f"({items[0].text},)"
            else:
                text = f"({', '.join(item.text for item in items)})"
            return _RenderedNode(
                text,
                tuple(occurrence for item in items for occurrence in item.occurrences),
                True,
            )

        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            leaves = _union_leaves(node)
            rendered_leaves = tuple(
                self._render_node(
                    leaf,
                    role,
                    range_override=range_override,
                    allow_forward=allow_forward,
                )
                for leaf in leaves
            )
            if any(not item.supported for item in rendered_leaves):
                return _unsupported()
            return _RenderedNode(
                " | ".join(item.text for item in rendered_leaves),
                tuple(occurrence for item in rendered_leaves for occurrence in item.occurrences),
                True,
            )

        if isinstance(node, ast.Constant):
            if node.value is None:
                return _RenderedNode("None", (), True)
            if node.value is Ellipsis:
                return _RenderedNode("...", (), True)
            if isinstance(node.value, str):
                if not allow_forward:
                    return _RenderedNode("?", (), True)
                try:
                    parsed = ast.parse(
                        node.value,
                        filename="<forward-annotation>",
                        mode="eval",
                        feature_version=(3, 12),
                    ).body
                except (SyntaxError, ValueError):
                    return _unsupported()
                return self._render_node(
                    parsed,
                    role,
                    range_override=range_override or _range(node),
                    allow_forward=False,
                )
            return _RenderedNode("?", (), True)

        return _unsupported()

    def _candidate(self, spelling: tuple[str, ...]) -> _TypeReferenceCandidate:
        return _construct_type_reference_candidate(
            spelling,
            self._bindings,
            current_module=self._current_module,
            owner_qualified_name=self._owner_qualified_name,
            class_identities=self._class_identities,
            modules=self._modules,
        )


def _construct_type_reference_candidate(
    spelling: tuple[str, ...],
    bindings: Mapping[str, ImportBinding],
    *,
    current_module: str | None,
    owner_qualified_name: str | None,
    class_identities: frozenset[tuple[str, str]],
    modules: frozenset[str],
) -> _TypeReferenceCandidate:
    original_name = ".".join(spelling)
    if current_module is not None and owner_qualified_name is not None:
        owner_parts = owner_qualified_name.split(".")
        for length in range(len(owner_parts), -1, -1):
            qualified_name = ".".join((*owner_parts[:length], *spelling))
            identity = (current_module, qualified_name)
            if identity in class_identities:
                return _TypeReferenceCandidate(
                    original_name,
                    f"{current_module}.{qualified_name}",
                    original_name,
                    False,
                    None,
                    False,
                    identity,
                )

    binding = bindings.get(spelling[0])
    if binding is not None:
        suffix = ".".join(spelling[1:])
        candidate_name = (
            binding.canonical_name if not suffix else f"{binding.canonical_name}.{suffix}"
        )
        return _TypeReferenceCandidate(
            original_name,
            candidate_name,
            candidate_name,
            True,
            binding.kind,
            len(spelling) == 1,
            _find_exact_class(candidate_name, class_identities, modules),
        )

    return _TypeReferenceCandidate(
        original_name,
        original_name,
        original_name,
        False,
        None,
        False,
        _find_exact_class(original_name, class_identities, modules),
    )


def _find_exact_class(
    candidate_name: str,
    class_identities: frozenset[tuple[str, str]],
    modules: frozenset[str],
) -> tuple[str, str] | None:
    parts = candidate_name.split(".")
    for split_at in range(len(parts) - 1, 0, -1):
        module = ".".join(parts[:split_at])
        qualified_name = ".".join(parts[split_at:])
        identity = (module, qualified_name)
        if module in modules and identity in class_identities:
            return identity
    return None


def _unsupported() -> _RenderedNode:
    return _RenderedNode("?", (), False)


def _symbol(node: ast.expr) -> tuple[str, ...] | None:
    if isinstance(node, ast.Name):
        return (unicodedata.normalize("NFC", node.id),)
    if not isinstance(node, ast.Attribute):
        return None
    prefix = _symbol(node.value)
    if prefix is None:
        return None
    return (*prefix, unicodedata.normalize("NFC", node.attr))


def _union_leaves(node: ast.expr) -> tuple[ast.expr, ...]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return (*_union_leaves(node.left), *_union_leaves(node.right))
    return (node,)


def _range(node: ast.expr) -> SourceRangeWithColumns:
    start_line = max(1, getattr(node, "lineno", 1))
    start_col = max(0, getattr(node, "col_offset", 0))
    end_line = max(start_line, getattr(node, "end_lineno", start_line) or start_line)
    end_col = max(0, getattr(node, "end_col_offset", start_col) or start_col)
    return SourceRangeWithColumns(start_line, start_col, end_line, end_col)
