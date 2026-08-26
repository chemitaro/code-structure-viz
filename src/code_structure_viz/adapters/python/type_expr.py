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
class _RenderTask:
    node: ast.expr
    role: TypeReferenceRole
    range_override: SourceRangeWithColumns | None
    allow_forward: bool


@dataclass(frozen=True, slots=True)
class _CombineForward:
    pass


@dataclass(frozen=True, slots=True)
class _CombineAnnotated:
    canonical_base: str


@dataclass(frozen=True, slots=True)
class _CombineSubscript:
    canonical_base: str
    base_spelling: tuple[str, ...]
    base_node: ast.expr
    range_override: SourceRangeWithColumns | None
    argument_count: int


@dataclass(frozen=True, slots=True)
class _CombineTuple:
    item_count: int


@dataclass(frozen=True, slots=True)
class _CombineUnion:
    leaf_count: int


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
        pending: list[
            _RenderTask
            | _CombineForward
            | _CombineAnnotated
            | _CombineSubscript
            | _CombineTuple
            | _CombineUnion
        ] = [_RenderTask(node, role, range_override, allow_forward)]
        results: list[_RenderedNode] = []
        while pending:
            operation = pending.pop()
            if isinstance(operation, _RenderTask):
                symbol = _symbol(operation.node)
                if symbol is not None:
                    results.append(
                        _RenderedNode(
                            self._candidate(symbol).rendered_name,
                            (
                                _OccurrenceDraft(
                                    symbol,
                                    operation.role,
                                    operation.range_override or _range(operation.node),
                                ),
                            ),
                            True,
                            0 if operation.role is TypeReferenceRole.HEAD else None,
                        )
                    )
                    continue
                if isinstance(operation.node, ast.Subscript):
                    base = _symbol(operation.node.value)
                    if base is None:
                        results.append(_unsupported())
                        continue
                    base_candidate = self._candidate(base)
                    canonical_base = base_candidate.rendered_name
                    arguments = (
                        operation.node.slice.elts
                        if isinstance(operation.node.slice, ast.Tuple)
                        else [operation.node.slice]
                    )
                    if (
                        base_candidate.internal_class is None
                        and base_candidate.candidate_name in _LITERAL_NAMES
                    ):
                        results.append(
                            _unsupported()
                            if not arguments
                            else _RenderedNode(
                                f"{canonical_base}[{', '.join('?' for _ in arguments)}]", (), True
                            )
                        )
                        continue
                    if (
                        base_candidate.internal_class is None
                        and base_candidate.candidate_name in _ANNOTATED_NAMES
                    ):
                        if len(arguments) < 2:
                            results.append(_unsupported())
                            continue
                        pending.append(_CombineAnnotated(canonical_base))
                        pending.append(
                            _RenderTask(
                                arguments[0],
                                operation.role,
                                operation.range_override,
                                operation.allow_forward,
                            )
                        )
                        continue
                    if not arguments:
                        results.append(_unsupported())
                        continue
                    pending.append(
                        _CombineSubscript(
                            canonical_base,
                            base,
                            operation.node.value,
                            operation.range_override,
                            len(arguments),
                        )
                    )
                    for argument in reversed(arguments):
                        pending.append(
                            _RenderTask(
                                argument,
                                TypeReferenceRole.ARGUMENT,
                                operation.range_override,
                                operation.allow_forward,
                            )
                        )
                    continue
                if isinstance(operation.node, ast.Tuple):
                    pending.append(_CombineTuple(len(operation.node.elts)))
                    for item in reversed(operation.node.elts):
                        pending.append(
                            _RenderTask(
                                item,
                                operation.role,
                                operation.range_override,
                                operation.allow_forward,
                            )
                        )
                    continue
                if isinstance(operation.node, ast.BinOp) and isinstance(
                    operation.node.op, ast.BitOr
                ):
                    leaves = _union_leaves(operation.node)
                    pending.append(_CombineUnion(len(leaves)))
                    for leaf in reversed(leaves):
                        pending.append(
                            _RenderTask(
                                leaf,
                                operation.role,
                                operation.range_override,
                                operation.allow_forward,
                            )
                        )
                    continue
                if isinstance(operation.node, ast.Constant):
                    if operation.node.value is None:
                        results.append(_RenderedNode("None", (), True))
                    elif operation.node.value is Ellipsis:
                        results.append(_RenderedNode("...", (), True))
                    elif isinstance(operation.node.value, str):
                        if not operation.allow_forward:
                            results.append(_RenderedNode("?", (), True))
                            continue
                        try:
                            parsed = ast.parse(
                                operation.node.value,
                                filename="<forward-annotation>",
                                mode="eval",
                                feature_version=(3, 12),
                            ).body
                        except (SyntaxError, ValueError, RecursionError):
                            results.append(_unsupported())
                            continue
                        pending.append(_CombineForward())
                        pending.append(
                            _RenderTask(
                                parsed,
                                operation.role,
                                operation.range_override or _range(operation.node),
                                False,
                            )
                        )
                    else:
                        results.append(_RenderedNode("?", (), True))
                    continue
                results.append(_unsupported())
                continue
            if isinstance(operation, _CombineForward):
                continue
            if isinstance(operation, _CombineAnnotated):
                first = results.pop()
                results.append(
                    _unsupported()
                    if not first.supported
                    else _RenderedNode(
                        f"{operation.canonical_base}[{first.text}, ?]",
                        first.occurrences,
                        True,
                        first.outer_head_index,
                    )
                )
                continue
            if isinstance(operation, _CombineSubscript):
                rendered_arguments = results[-operation.argument_count :]
                del results[-operation.argument_count :]
                if any(not item.supported for item in rendered_arguments):
                    results.append(_unsupported())
                    continue
                results.append(
                    _RenderedNode(
                        (
                            f"{operation.canonical_base}["
                            f"{', '.join(item.text for item in rendered_arguments)}]"
                        ),
                        (
                            _OccurrenceDraft(
                                operation.base_spelling,
                                TypeReferenceRole.HEAD,
                                operation.range_override or _range(operation.base_node),
                            ),
                            *(
                                occurrence
                                for item in rendered_arguments
                                for occurrence in item.occurrences
                            ),
                        ),
                        True,
                        0,
                    )
                )
                continue
            if isinstance(operation, _CombineTuple):
                items = results[-operation.item_count :] if operation.item_count else []
                if operation.item_count:
                    del results[-operation.item_count :]
                if any(not item.supported for item in items):
                    results.append(_unsupported())
                    continue
                if not items:
                    text = "()"
                elif len(items) == 1:
                    text = f"({items[0].text},)"
                else:
                    text = f"({', '.join(item.text for item in items)})"
                results.append(
                    _RenderedNode(
                        text,
                        tuple(occurrence for item in items for occurrence in item.occurrences),
                        True,
                    )
                )
                continue
            if isinstance(operation, _CombineUnion):
                rendered_leaves = results[-operation.leaf_count :]
                del results[-operation.leaf_count :]
                if any(not item.supported for item in rendered_leaves):
                    results.append(_unsupported())
                    continue
                results.append(
                    _RenderedNode(
                        " | ".join(item.text for item in rendered_leaves),
                        tuple(
                            occurrence
                            for item in rendered_leaves
                            for occurrence in item.occurrences
                        ),
                        True,
                    )
                )
                continue
            raise RuntimeError(f"unknown render operation: {type(operation).__name__}")
        return results.pop()

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
    attributes: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        attributes.append(unicodedata.normalize("NFC", current.attr))
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    return (
        unicodedata.normalize("NFC", current.id),
        *reversed(attributes),
    )


def _union_leaves(node: ast.expr) -> tuple[ast.expr, ...]:
    leaves: list[ast.expr] = []
    pending = [node]
    while pending:
        current = pending.pop()
        if isinstance(current, ast.BinOp) and isinstance(current.op, ast.BitOr):
            pending.extend((current.right, current.left))
        else:
            leaves.append(current)
    return tuple(leaves)


def _range(node: ast.expr) -> SourceRangeWithColumns:
    start_line = max(1, getattr(node, "lineno", 1))
    start_col = max(0, getattr(node, "col_offset", 0))
    end_line = max(start_line, getattr(node, "end_lineno", start_line) or start_line)
    end_col = max(0, getattr(node, "end_col_offset", start_col) or start_col)
    return SourceRangeWithColumns(start_line, start_col, end_line, end_col)
