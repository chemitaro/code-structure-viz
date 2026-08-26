from __future__ import annotations

import ast
import io
import tokenize
import unicodedata
from dataclasses import dataclass
from pathlib import PurePosixPath

from code_structure_viz.adapters.python.model import (
    CoverageFrontier,
    DecoratorRef,
    FailedSourceFile,
    FailedStage,
    FrontierDirection,
    FrontierKind,
    FrontierReason,
    MemberKind,
    MemberScope,
    MethodKind,
    MethodSignature,
    Parameter,
    ParameterKind,
    PropertyRole,
    PythonClassEntity,
    PythonMember,
    PythonRelation,
    RelationKind,
    RelationTarget,
    SourceRange,
    SourceRangeWithColumns,
    TargetKind,
    TargetResolution,
    entity_sort_key,
    failed_source_sort_key,
    frontier_sort_key,
    member_sort_key,
    relation_sort_key,
)
from code_structure_viz.adapters.python.module_index import (
    IndexedModule,
    ModuleCollision,
    PythonModuleIndex,
)
from code_structure_viz.adapters.python.type_expr import (
    BindingKind,
    ImportBinding,
    RenderedType,
    SafeTypeExpressionRenderer,
    TypeReferenceOccurrence,
    TypeReferenceSite,
    TypeReferenceSiteKind,
    _construct_type_reference_candidate,
)
from code_structure_viz.core.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    canonical_diagnostics,
    diagnostic,
)


@dataclass(frozen=True, slots=True)
class AnalyzedModule:
    module: str
    path: PurePosixPath
    bindings: tuple[ImportBinding, ...]

    @property
    def id(self) -> str:
        return f"python:module:{self.module}"


@dataclass(frozen=True, slots=True)
class ClassCollision:
    entity_id: str
    path: PurePosixPath


@dataclass(frozen=True, slots=True)
class PythonAnalysisResult:
    modules: tuple[AnalyzedModule, ...]
    entities: tuple[PythonClassEntity, ...]
    members: tuple[PythonMember, ...]
    relations: tuple[PythonRelation, ...]
    failures: tuple[FailedSourceFile, ...]
    diagnostics: tuple[Diagnostic, ...]
    frontier: tuple[CoverageFrontier, ...]
    parsed_file_count: int
    candidate_file_count: int
    class_collisions: tuple[ClassCollision, ...]
    indexed_modules: tuple[IndexedModule, ...]
    module_collisions: tuple[ModuleCollision, ...]


@dataclass(frozen=True, slots=True)
class _ParsedModule:
    indexed: IndexedModule
    tree: ast.Module
    bindings: tuple[ImportBinding, ...]
    module_type_parameters: frozenset[str]


@dataclass(frozen=True, slots=True)
class _ClassCandidate:
    parsed: _ParsedModule
    node: ast.ClassDef
    qualified_name: str
    type_parameters: frozenset[str]

    @property
    def entity_id(self) -> str:
        return f"python:class:{self.parsed.indexed.module}:{self.qualified_name}"


@dataclass(frozen=True, slots=True)
class _FieldDeclaration:
    node: ast.stmt
    name: str
    scope: MemberScope
    annotation_node: ast.expr | None
    origin_rank: int
    type_parameters: frozenset[str]


@dataclass(frozen=True, slots=True)
class _CallableDeclaration:
    node: ast.FunctionDef | ast.AsyncFunctionDef
    kind: MemberKind
    property_role: PropertyRole | None
    method_kind: MethodKind | None
    type_parameters: frozenset[str]


@dataclass(frozen=True, slots=True)
class _RelationEvidence:
    kind: RelationKind
    source_id: str
    target: RelationTarget
    via_member_id: str | None
    annotation: str | None
    path: PurePosixPath
    range: SourceRangeWithColumns
    origin_rank: int


@dataclass(frozen=True, slots=True)
class _TypeEvidence:
    occurrence: TypeReferenceOccurrence
    module: str
    owner_qualified_name: str
    type_parameters: frozenset[str]
    relation_kind: RelationKind
    annotation: str


@dataclass(frozen=True, slots=True)
class _ImportEvidence:
    module: str | None
    node: ast.Import | ast.ImportFrom
    star: bool


_BUILTIN_TYPES = frozenset(
    {
        "BaseException",
        "Exception",
        "bool",
        "bytearray",
        "bytes",
        "complex",
        "dict",
        "float",
        "frozenset",
        "int",
        "list",
        "memoryview",
        "object",
        "range",
        "set",
        "slice",
        "str",
        "tuple",
        "type",
    }
)
_TYPE_PARAMETER_FACTORIES = frozenset(
    {
        "typing.TypeVar",
        "typing.ParamSpec",
        "typing.TypeVarTuple",
        "typing_extensions.TypeVar",
        "typing_extensions.ParamSpec",
        "typing_extensions.TypeVarTuple",
    }
)


class PythonSnapshotAnalyzer:
    def analyze(self, index: PythonModuleIndex) -> PythonAnalysisResult:
        failures = list(index.failures)
        diagnostics = list(index.diagnostics)
        parsed_modules: list[_ParsedModule] = []

        for indexed in index.modules:
            parsed = self._parse_module(indexed, failures, diagnostics)
            if parsed is not None:
                parsed_modules.append(parsed)

        class_candidates: list[_ClassCandidate] = []
        frontier: list[CoverageFrontier] = []
        for parsed in parsed_modules:
            candidates = _direct_class_candidates(parsed)
            class_candidates.extend(candidates)
            _collect_skipped_classes(parsed, candidates, diagnostics, frontier)

        grouped_classes: dict[str, list[_ClassCandidate]] = {}
        for candidate in class_candidates:
            grouped_classes.setdefault(candidate.entity_id, []).append(candidate)

        safe_candidates: list[_ClassCandidate] = []
        class_collisions: list[ClassCollision] = []
        for entity_id, collision_group in grouped_classes.items():
            if len(collision_group) == 1:
                safe_candidates.append(collision_group[0])
                continue
            representative_path = min(
                (item.parsed.indexed.path for item in collision_group), key=_path_key
            )
            class_collisions.append(ClassCollision(entity_id, representative_path))
            diagnostics.append(
                diagnostic(
                    DiagnosticCode.PY_CLASS_COLLISION,
                    domain="python",
                    symbol=entity_id,
                )
            )
            frontier.append(
                CoverageFrontier(
                    FrontierDirection.FAILURE,
                    FrontierKind.CLASS,
                    entity_id,
                    FrontierReason.IDENTITY_COLLISION,
                )
            )

        entities = tuple(
            sorted((_entity(candidate) for candidate in safe_candidates), key=entity_sort_key)
        )
        entity_by_id = {entity.id: entity for entity in entities}
        parsed_by_module = {item.indexed.module: item for item in parsed_modules}
        module_names = frozenset(parsed_by_module)
        class_identities = frozenset((entity.module, entity.qualified_name) for entity in entities)

        members: list[PythonMember] = []
        type_evidence: list[_TypeEvidence] = []
        for candidate in safe_candidates:
            class_members, class_types = _analyze_class_members(
                candidate,
                diagnostics,
                class_identities,
                module_names,
            )
            members.extend(class_members)
            type_evidence.extend(class_types)
            type_evidence.extend(
                _analyze_inheritance(
                    candidate,
                    diagnostics,
                    class_identities,
                    module_names,
                )
            )

        relation_evidence: list[_RelationEvidence] = []
        for evidence in type_evidence:
            target = _resolve_type_reference(
                evidence,
                parsed_by_module,
                module_names,
                class_identities,
                entity_by_id,
            )
            if target is None:
                continue
            if target.resolution is TargetResolution.UNKNOWN:
                diagnostics.append(
                    diagnostic(
                        DiagnosticCode.PY_REFERENCE_UNKNOWN,
                        domain="python",
                        path=evidence.occurrence.path.as_posix(),
                        symbol=target.name,
                        line=evidence.occurrence.range.start_line,
                    )
                )
                frontier.append(
                    CoverageFrontier(
                        FrontierDirection.FAILURE,
                        FrontierKind.SYMBOL,
                        target.name,
                        FrontierReason.UNRESOLVED_REFERENCE,
                    )
                )
            relation_evidence.append(
                _RelationEvidence(
                    kind=evidence.relation_kind,
                    source_id=evidence.occurrence.owner_class_id,
                    target=target,
                    via_member_id=evidence.occurrence.member_id,
                    annotation=evidence.annotation,
                    path=evidence.occurrence.path,
                    range=evidence.occurrence.range,
                    origin_rank=_type_origin_rank(evidence.occurrence.site_kind),
                )
            )

        for parsed in parsed_modules:
            import_items, import_frontier = _import_relation_evidence(parsed, module_names)
            relation_evidence.extend(import_items)
            frontier.extend(import_frontier)

        relations = _canonical_relations(relation_evidence)
        return PythonAnalysisResult(
            modules=tuple(
                sorted(
                    (
                        AnalyzedModule(item.indexed.module, item.indexed.path, item.bindings)
                        for item in parsed_modules
                    ),
                    key=lambda item: _utf8(item.module),
                )
            ),
            entities=entities,
            members=tuple(sorted(members, key=member_sort_key)),
            relations=relations,
            failures=tuple(sorted(failures, key=failed_source_sort_key)),
            diagnostics=canonical_diagnostics(tuple(diagnostics)),
            frontier=tuple(sorted(set(frontier), key=frontier_sort_key)),
            parsed_file_count=len(parsed_modules),
            candidate_file_count=index.candidate_file_count,
            class_collisions=tuple(
                sorted(class_collisions, key=lambda item: _utf8(item.entity_id))
            ),
            indexed_modules=index.modules,
            module_collisions=index.collisions,
        )

    def _parse_module(
        self,
        indexed: IndexedModule,
        failures: list[FailedSourceFile],
        diagnostics: list[Diagnostic],
    ) -> _ParsedModule | None:
        try:
            encoding, _ = tokenize.detect_encoding(io.BytesIO(indexed.source.content).readline)
            text = indexed.source.content.decode(encoding, errors="strict")
        except (SyntaxError, UnicodeDecodeError, LookupError):
            failures.append(
                FailedSourceFile(indexed.path, FailedStage.ENCODING, DiagnosticCode.PY_ENCODING)
            )
            diagnostics.append(
                diagnostic(
                    DiagnosticCode.PY_ENCODING,
                    domain="python",
                    path=indexed.path.as_posix(),
                )
            )
            return None
        try:
            tree = ast.parse(
                text,
                filename=indexed.path.as_posix(),
                mode="exec",
                type_comments=False,
                feature_version=(3, 12),
            )
        except (SyntaxError, ValueError, RecursionError) as error:
            line = (
                error.lineno
                if isinstance(error, SyntaxError) and error.lineno is not None and error.lineno > 0
                else None
            )
            failures.append(
                FailedSourceFile(indexed.path, FailedStage.PARSE, DiagnosticCode.PY_PARSE)
            )
            diagnostics.append(
                diagnostic(
                    DiagnosticCode.PY_PARSE,
                    domain="python",
                    path=indexed.path.as_posix(),
                    line=line,
                )
            )
            return None
        bindings = _collect_import_bindings(indexed.module, indexed.path, tree)
        return _ParsedModule(
            indexed=indexed,
            tree=tree,
            bindings=bindings,
            module_type_parameters=_legacy_type_parameters(tree.body, bindings),
        )


def _utf8(value: str) -> bytes:
    return value.encode("utf-8")


def _path_key(value: PurePosixPath) -> bytes:
    return _utf8(value.as_posix())


def _range(node: ast.AST) -> SourceRange:
    start = max(1, getattr(node, "lineno", 1))
    end = max(start, getattr(node, "end_lineno", start) or start)
    return SourceRange(start, end)


def _internal_range(node: ast.AST) -> SourceRangeWithColumns:
    start = max(1, getattr(node, "lineno", 1))
    start_col = max(0, getattr(node, "col_offset", 0))
    end = max(start, getattr(node, "end_lineno", start) or start)
    end_col = max(0, getattr(node, "end_col_offset", start_col) or start_col)
    return SourceRangeWithColumns(start, start_col, end, end_col)


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


def _binding_map(bindings: tuple[ImportBinding, ...]) -> dict[str, ImportBinding]:
    return {item.local_name: item for item in bindings}


def _canonical_symbol(spelling: tuple[str, ...], bindings: tuple[ImportBinding, ...]) -> str:
    binding = _binding_map(bindings).get(spelling[0])
    if binding is None:
        return ".".join(spelling)
    suffix = ".".join(spelling[1:])
    return binding.canonical_name if not suffix else f"{binding.canonical_name}.{suffix}"


def _module_package(module: str, path: PurePosixPath) -> tuple[str, ...]:
    parts = module.split(".")
    return tuple(parts if path.name == "__init__.py" else parts[:-1])


def _relative_module(
    current_module: str,
    path: PurePosixPath,
    level: int,
    imported_module: str | None,
) -> str | None:
    if level == 0:
        return imported_module or ""
    package = _module_package(current_module, path)
    remove_count = level - 1
    if remove_count > len(package):
        return None
    base = package[: len(package) - remove_count] if remove_count else package
    suffix = tuple(imported_module.split(".")) if imported_module else ()
    parts = (*base, *suffix)
    return ".".join(parts) if parts else None


def _import_records(
    module: str,
    path: PurePosixPath,
    tree: ast.Module,
) -> tuple[tuple[ImportBinding, ...], tuple[_ImportEvidence, ...]]:
    binding_candidates: dict[str, set[tuple[str, BindingKind]]] = {}
    evidence: list[_ImportEvidence] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported = unicodedata.normalize("NFC", alias.name)
                evidence.append(_ImportEvidence(imported, node, False))
                if alias.asname:
                    local = unicodedata.normalize("NFC", alias.asname)
                    canonical = imported
                else:
                    local = imported.split(".", 1)[0]
                    canonical = local
                binding_candidates.setdefault(local, set()).add((canonical, BindingKind.MODULE))
        elif isinstance(node, ast.ImportFrom):
            resolved_import = _relative_module(module, path, node.level, node.module)
            evidence.append(
                _ImportEvidence(
                    resolved_import,
                    node,
                    any(alias.name == "*" for alias in node.names),
                )
            )
            if resolved_import is None:
                continue
            for alias in node.names:
                if alias.name == "*":
                    continue
                source_name = unicodedata.normalize("NFC", alias.name)
                local = unicodedata.normalize("NFC", alias.asname or alias.name)
                canonical = f"{resolved_import}.{source_name}" if resolved_import else source_name
                binding_candidates.setdefault(local, set()).add((canonical, BindingKind.SYMBOL))
    bindings: list[ImportBinding] = []
    for local, values in binding_candidates.items():
        if len(values) != 1:
            continue
        canonical, kind = next(iter(values))
        bindings.append(ImportBinding(local, canonical, kind))
    return (
        tuple(sorted(bindings, key=lambda item: _utf8(item.local_name))),
        tuple(evidence),
    )


def _collect_import_bindings(
    module: str, path: PurePosixPath, tree: ast.Module
) -> tuple[ImportBinding, ...]:
    bindings, _ = _import_records(module, path, tree)
    return bindings


def _type_param_names(node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    result: set[str] = set()
    for item in getattr(node, "type_params", ()):
        name = getattr(item, "name", None)
        if isinstance(name, str):
            result.add(unicodedata.normalize("NFC", name))
    return result


def _legacy_type_parameters(
    statements: list[ast.stmt], bindings: tuple[ImportBinding, ...]
) -> frozenset[str]:
    result: set[str] = set()
    for statement in statements:
        if (
            not isinstance(statement, ast.Assign)
            or len(statement.targets) != 1
            or not isinstance(statement.targets[0], ast.Name)
            or not isinstance(statement.value, ast.Call)
        ):
            continue
        callee = _symbol(statement.value.func)
        if callee is None or _canonical_symbol(callee, bindings) not in _TYPE_PARAMETER_FACTORIES:
            continue
        result.add(unicodedata.normalize("NFC", statement.targets[0].id))
    return frozenset(result)


def _direct_class_candidates(parsed: _ParsedModule) -> tuple[_ClassCandidate, ...]:
    result: list[_ClassCandidate] = []

    def collect(
        statements: list[ast.stmt],
        prefix: tuple[str, ...],
        inherited_type_parameters: frozenset[str],
    ) -> None:
        for statement in statements:
            if not isinstance(statement, ast.ClassDef):
                continue
            name = unicodedata.normalize("NFC", statement.name)
            qualified = ".".join((*prefix, name))
            active = frozenset(
                {
                    *inherited_type_parameters,
                    *_type_param_names(statement),
                    *_legacy_type_parameters(statement.body, parsed.bindings),
                }
            )
            result.append(_ClassCandidate(parsed, statement, qualified, active))
            collect(statement.body, (*prefix, name), active)

    collect(parsed.tree.body, (), parsed.module_type_parameters)
    return tuple(result)


def _collect_skipped_classes(
    parsed: _ParsedModule,
    candidates: tuple[_ClassCandidate, ...],
    diagnostics: list[Diagnostic],
    frontier: list[CoverageFrontier],
) -> None:
    accepted = {id(item.node) for item in candidates}

    def scan(statements: list[ast.stmt], lexical: tuple[str, ...]) -> None:
        for statement in statements:
            if isinstance(statement, ast.ClassDef):
                qualified = (*lexical, unicodedata.normalize("NFC", statement.name))
                if id(statement) not in accepted:
                    symbol = f"class:{'.'.join(qualified)}"
                    diagnostics.append(
                        diagnostic(
                            DiagnosticCode.PY_CLASS_SCOPE,
                            domain="python",
                            path=parsed.indexed.path.as_posix(),
                            symbol=symbol,
                            line=max(1, statement.lineno),
                        )
                    )
                    frontier.append(
                        CoverageFrontier(
                            FrontierDirection.FAILURE,
                            FrontierKind.CLASS,
                            f"python:class:{parsed.indexed.module}:{'.'.join(qualified)}",
                            FrontierReason.UNSUPPORTED_SCOPE,
                        )
                    )
                scan(statement.body, qualified)
                continue
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                scan(
                    statement.body,
                    (*lexical, unicodedata.normalize("NFC", statement.name)),
                )
                continue
            for block in _control_flow_blocks(statement):
                scan(block, lexical)

    scan(parsed.tree.body, ())


def _decorators(
    nodes: list[ast.expr], bindings: tuple[ImportBinding, ...], path: PurePosixPath
) -> tuple[DecoratorRef, ...]:
    decorated: list[tuple[DecoratorRef, SourceRangeWithColumns]] = []
    for node in nodes:
        called = isinstance(node, ast.Call)
        target = node.func if isinstance(node, ast.Call) else node
        spelling = _symbol(target)
        name = _canonical_symbol(spelling, bindings) if spelling is not None else "?"
        decorated.append((DecoratorRef(name, called), _internal_range(node)))
    decorated.sort(
        key=lambda item: (
            _utf8(item[0].name),
            item[0].called,
            _path_key(path),
            item[1].start_line,
            item[1].start_col,
            item[1].end_line,
            item[1].end_col,
        )
    )
    unique: list[tuple[DecoratorRef, SourceRangeWithColumns]] = []
    for item in decorated:
        if item not in unique:
            unique.append(item)
    return tuple(item[0] for item in unique)


def _entity(candidate: _ClassCandidate) -> PythonClassEntity:
    return PythonClassEntity.create(
        module=candidate.parsed.indexed.module,
        qualified_name=candidate.qualified_name,
        path=candidate.parsed.indexed.path,
        source_range=_range(candidate.node),
        decorators=_decorators(
            candidate.node.decorator_list,
            candidate.parsed.bindings,
            candidate.parsed.indexed.path,
        ),
    )


def _simple_names(target: ast.expr) -> tuple[str, ...]:
    if isinstance(target, ast.Name):
        return (unicodedata.normalize("NFC", target.id),)
    if isinstance(target, (ast.Tuple, ast.List)):
        return tuple(name for item in target.elts for name in _simple_names(item))
    return ()


def _receiver_fields(target: ast.expr) -> tuple[tuple[str, MemberScope], ...]:
    if (
        isinstance(target, ast.Attribute)
        and isinstance(target.value, ast.Name)
        and target.value.id in {"self", "cls"}
    ):
        scope = MemberScope.INSTANCE if target.value.id == "self" else MemberScope.CLASS
        return ((unicodedata.normalize("NFC", target.attr), scope),)
    if isinstance(target, (ast.Tuple, ast.List)):
        return tuple(item for child in target.elts for item in _receiver_fields(child))
    return ()


def _control_flow_blocks(statement: ast.stmt) -> tuple[list[ast.stmt], ...]:
    if isinstance(statement, ast.If):
        return statement.body, statement.orelse
    if isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
        return statement.body, statement.orelse
    if isinstance(statement, (ast.With, ast.AsyncWith)):
        return (statement.body,)
    if isinstance(statement, (ast.Try, ast.TryStar)):
        return (
            statement.body,
            *(handler.body for handler in statement.handlers),
            statement.orelse,
            statement.finalbody,
        )
    if isinstance(statement, ast.Match):
        return tuple(case.body for case in statement.cases)
    return ()


def _method_field_declarations(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    type_parameters: frozenset[str],
) -> tuple[_FieldDeclaration, ...]:
    result: list[_FieldDeclaration] = []

    def scan(statements: list[ast.stmt]) -> None:
        for statement in statements:
            targets: tuple[ast.expr, ...] = ()
            annotation: ast.expr | None = None
            if isinstance(statement, ast.Assign):
                targets = tuple(statement.targets)
            elif isinstance(statement, ast.AnnAssign):
                targets = (statement.target,)
                annotation = statement.annotation
            elif isinstance(statement, ast.AugAssign):
                targets = (statement.target,)
            if targets:
                for target in targets:
                    for name, scope in _receiver_fields(target):
                        result.append(
                            _FieldDeclaration(
                                statement,
                                name,
                                scope,
                                annotation,
                                1 if scope is MemberScope.INSTANCE else 2,
                                type_parameters,
                            )
                        )
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            for block in _control_flow_blocks(statement):
                scan(block)

    scan(function.body)
    return tuple(result)


def _callable_kind(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    bindings: tuple[ImportBinding, ...],
) -> tuple[MemberKind, PropertyRole | None, MethodKind | None]:
    normalized_name = unicodedata.normalize("NFC", node.name)
    symbolic_decorators = tuple(
        (decorator, symbol, _canonical_symbol(symbol, bindings))
        for decorator in node.decorator_list
        if (symbol := _symbol(decorator.func if isinstance(decorator, ast.Call) else decorator))
        is not None
    )
    if any(
        not isinstance(decorator, ast.Call) and symbol == ("property",) and canonical == "property"
        for decorator, symbol, canonical in symbolic_decorators
    ):
        return MemberKind.PROPERTY, PropertyRole.GETTER, None
    if any(
        not isinstance(decorator, ast.Call) and symbol == (normalized_name, "setter")
        for decorator, symbol, _canonical in symbolic_decorators
    ):
        return MemberKind.PROPERTY, PropertyRole.SETTER, None
    if any(
        not isinstance(decorator, ast.Call) and symbol == (normalized_name, "deleter")
        for decorator, symbol, _canonical in symbolic_decorators
    ):
        return MemberKind.PROPERTY, PropertyRole.DELETER, None
    names = [canonical for _decorator, _symbol_value, canonical in symbolic_decorators]
    if "staticmethod" in names or "builtins.staticmethod" in names:
        return MemberKind.METHOD, None, MethodKind.STATIC
    if "classmethod" in names or "builtins.classmethod" in names:
        return MemberKind.METHOD, None, MethodKind.CLASS
    return MemberKind.METHOD, None, MethodKind.INSTANCE


def _class_declarations(
    candidate: _ClassCandidate,
) -> tuple[tuple[_FieldDeclaration, ...], tuple[_CallableDeclaration, ...]]:
    fields: list[_FieldDeclaration] = []
    callables: list[_CallableDeclaration] = []
    for statement in candidate.node.body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                fields.extend(
                    _FieldDeclaration(
                        statement,
                        name,
                        MemberScope.CLASS,
                        None,
                        0,
                        candidate.type_parameters,
                    )
                    for name in _simple_names(target)
                )
        elif isinstance(statement, ast.AnnAssign):
            fields.extend(
                _FieldDeclaration(
                    statement,
                    name,
                    MemberScope.CLASS,
                    statement.annotation,
                    0,
                    candidate.type_parameters,
                )
                for name in _simple_names(statement.target)
            )
        elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            kind, role, method_kind = _callable_kind(statement, candidate.parsed.bindings)
            active = frozenset({*candidate.type_parameters, *_type_param_names(statement)})
            callables.append(_CallableDeclaration(statement, kind, role, method_kind, active))
            fields.extend(_method_field_declarations(statement, active))
    return tuple(fields), tuple(callables)


def _location_key(path: PurePosixPath, node: ast.AST, origin_rank: int) -> tuple[object, ...]:
    location = _internal_range(node)
    return (
        _path_key(path),
        location.start_line,
        location.start_col,
        location.end_line,
        location.end_col,
        origin_rank,
    )


def _render_type(
    renderer: SafeTypeExpressionRenderer,
    node: ast.expr,
    site: TypeReferenceSite,
    diagnostics: list[Diagnostic],
    site_token: str,
) -> RenderedType:
    rendered = renderer.render(node, site)
    if not rendered.supported:
        diagnostics.append(
            diagnostic(
                DiagnosticCode.PY_TYPE_UNSUPPORTED,
                domain="python",
                path=site.path.as_posix(),
                symbol=site_token,
                line=max(1, getattr(node, "lineno", 1)),
            )
        )
    return rendered


def _analyze_class_members(
    candidate: _ClassCandidate,
    diagnostics: list[Diagnostic],
    class_identities: frozenset[tuple[str, str]],
    modules: frozenset[str],
) -> tuple[tuple[PythonMember, ...], tuple[_TypeEvidence, ...]]:
    path = candidate.parsed.indexed.path
    entity_id = candidate.entity_id
    renderer = SafeTypeExpressionRenderer(
        candidate.parsed.bindings,
        current_module=candidate.parsed.indexed.module,
        owner_qualified_name=candidate.qualified_name,
        class_identities=class_identities,
        modules=modules,
    )
    field_declarations, callables = _class_declarations(candidate)
    members: list[PythonMember] = []
    type_evidence: list[_TypeEvidence] = []

    field_groups: dict[tuple[str, MemberScope], list[_FieldDeclaration]] = {}
    for declaration in field_declarations:
        field_groups.setdefault((declaration.name, declaration.scope), []).append(declaration)
    for (name, scope), declarations in field_groups.items():
        ordered = sorted(
            declarations,
            key=lambda item: _location_key(path, item.node, item.origin_rank),
        )
        provisional = PythonMember.create_field(
            owner_id=entity_id,
            name=name,
            scope=scope,
            annotation=None,
            source_range=_range(ordered[0].node),
        )
        rendered_items: list[tuple[RenderedType, _FieldDeclaration]] = []
        for declaration in ordered:
            if declaration.annotation_node is None:
                continue
            site = TypeReferenceSite(
                TypeReferenceSiteKind.FIELD_ANNOTATION,
                entity_id,
                provisional.id,
                0,
                path,
            )
            rendered_items.append(
                (
                    _render_type(
                        renderer,
                        declaration.annotation_node,
                        site,
                        diagnostics,
                        f"{provisional.id}#annotation",
                    ),
                    declaration,
                )
            )
        annotations = {item.text for item, _ in rendered_items}
        annotation = next(iter(annotations)) if len(annotations) == 1 else None
        if len(annotations) > 1:
            annotation = "?"
        member = PythonMember.create_field(
            owner_id=entity_id,
            name=name,
            scope=scope,
            annotation=annotation,
            source_range=_range(ordered[0].node),
        )
        members.append(member)
        if len(annotations) > 1:
            diagnostics.append(
                diagnostic(
                    DiagnosticCode.PY_FIELD_CONFLICT,
                    domain="python",
                    path=path.as_posix(),
                    symbol=member.id,
                    line=member.range.start_line,
                )
            )
        for rendered, declaration in rendered_items:
            type_evidence.extend(
                _type_evidence(
                    rendered,
                    candidate,
                    declaration.type_parameters,
                    RelationKind.COMPOSITION,
                )
            )
    callable_groups: dict[
        tuple[MemberKind, str, PropertyRole | None, MethodKind | None],
        list[_CallableDeclaration],
    ] = {}
    for callable_decl in callables:
        callable_groups.setdefault(
            (
                callable_decl.kind,
                unicodedata.normalize("NFC", callable_decl.node.name),
                callable_decl.property_role,
                callable_decl.method_kind,
            ),
            [],
        ).append(callable_decl)
    for (kind, name, property_role, method_kind), callable_declarations in callable_groups.items():
        for ordinal, callable_decl in enumerate(
            sorted(
                callable_declarations,
                key=lambda item: _location_key(
                    path, item.node, 3 if kind is MemberKind.PROPERTY else 4
                ),
            )
        ):
            empty_signature = MethodSignature(
                isinstance(callable_decl.node, ast.AsyncFunctionDef), (), None
            )
            if kind is MemberKind.PROPERTY:
                assert property_role is not None
                provisional = PythonMember.create_property(
                    owner_id=entity_id,
                    name=name,
                    role=property_role,
                    annotation=None,
                    signature=empty_signature,
                    decorators=(),
                    source_range=_range(callable_decl.node),
                    declaration_ordinal=ordinal,
                )
            else:
                assert method_kind is not None
                provisional = PythonMember.create_method(
                    owner_id=entity_id,
                    name=name,
                    method_kind=method_kind,
                    signature=empty_signature,
                    decorators=(),
                    source_range=_range(callable_decl.node),
                    declaration_ordinal=ordinal,
                )
            signature, rendered_parameters, rendered_return = _signature(
                callable_decl,
                candidate,
                provisional.id,
                renderer,
                diagnostics,
            )
            decorators = _decorators(
                callable_decl.node.decorator_list, candidate.parsed.bindings, path
            )
            if kind is MemberKind.PROPERTY:
                assert property_role is not None
                if property_role is PropertyRole.GETTER:
                    annotation = signature.returns
                elif property_role is PropertyRole.SETTER:
                    annotation = next(
                        (
                            parameter.annotation
                            for parameter in signature.parameters
                            if parameter.name not in {"self", "cls"}
                        ),
                        None,
                    )
                else:
                    annotation = None
                member = PythonMember.create_property(
                    owner_id=entity_id,
                    name=name,
                    role=property_role,
                    annotation=annotation,
                    signature=signature,
                    decorators=decorators,
                    source_range=_range(callable_decl.node),
                    declaration_ordinal=ordinal,
                )
            else:
                assert method_kind is not None
                member = PythonMember.create_method(
                    owner_id=entity_id,
                    name=name,
                    method_kind=method_kind,
                    signature=signature,
                    decorators=decorators,
                    source_range=_range(callable_decl.node),
                    declaration_ordinal=ordinal,
                )
            members.append(member)
            adopted_types: tuple[RenderedType | None, ...]
            if kind is MemberKind.PROPERTY:
                assert property_role is not None
                if property_role is PropertyRole.GETTER:
                    adopted_types = (rendered_return,)
                elif property_role is PropertyRole.SETTER:
                    value_index = next(
                        (
                            index
                            for index, parameter in enumerate(signature.parameters)
                            if parameter.name not in {"self", "cls"}
                        ),
                        None,
                    )
                    adopted_types = (
                        rendered_parameters[value_index] if value_index is not None else None,
                    )
                else:
                    adopted_types = ()
            else:
                adopted_types = (*rendered_parameters, rendered_return)
            for rendered_type in adopted_types:
                if rendered_type is not None:
                    type_evidence.extend(
                        _type_evidence(
                            rendered_type,
                            candidate,
                            callable_decl.type_parameters,
                            RelationKind.TYPED_DEPENDENCY,
                        )
                    )

    return tuple(members), tuple(type_evidence)


def _parameter_records(
    arguments: ast.arguments,
) -> tuple[tuple[ast.arg, ParameterKind, bool], ...]:
    positional = [*arguments.posonlyargs, *arguments.args]
    default_start = len(positional) - len(arguments.defaults)
    result: list[tuple[ast.arg, ParameterKind, bool]] = []
    for index, argument in enumerate(arguments.posonlyargs):
        result.append((argument, ParameterKind.POSITIONAL_ONLY, index >= default_start))
    for offset, argument in enumerate(arguments.args, start=len(arguments.posonlyargs)):
        result.append((argument, ParameterKind.POSITIONAL_OR_KEYWORD, offset >= default_start))
    if arguments.vararg is not None:
        result.append((arguments.vararg, ParameterKind.VAR_POSITIONAL, False))
    for argument, default in zip(arguments.kwonlyargs, arguments.kw_defaults, strict=True):
        result.append((argument, ParameterKind.KEYWORD_ONLY, default is not None))
    if arguments.kwarg is not None:
        result.append((arguments.kwarg, ParameterKind.VAR_KEYWORD, False))
    return tuple(result)


def _signature(
    declaration: _CallableDeclaration,
    candidate: _ClassCandidate,
    member_id: str,
    renderer: SafeTypeExpressionRenderer,
    diagnostics: list[Diagnostic],
) -> tuple[MethodSignature, tuple[RenderedType | None, ...], RenderedType | None]:
    parameters: list[Parameter] = []
    rendered_parameters: list[RenderedType | None] = []
    path = candidate.parsed.indexed.path
    for index, (argument, kind, has_default) in enumerate(
        _parameter_records(declaration.node.args)
    ):
        rendered: RenderedType | None = None
        if argument.annotation is not None:
            site = TypeReferenceSite(
                TypeReferenceSiteKind.PARAMETER_ANNOTATION,
                candidate.entity_id,
                member_id,
                index,
                path,
            )
            rendered = _render_type(
                renderer,
                argument.annotation,
                site,
                diagnostics,
                f"{member_id}#parameter:{argument.arg}",
            )
        rendered_parameters.append(rendered)
        parameters.append(
            Parameter(
                unicodedata.normalize("NFC", argument.arg),
                kind,
                rendered.text if rendered is not None else None,
                has_default,
            )
        )
    rendered_return: RenderedType | None = None
    if declaration.node.returns is not None:
        site = TypeReferenceSite(
            TypeReferenceSiteKind.RETURN_ANNOTATION,
            candidate.entity_id,
            member_id,
            0,
            path,
        )
        rendered_return = _render_type(
            renderer,
            declaration.node.returns,
            site,
            diagnostics,
            f"{member_id}#return",
        )
    return (
        MethodSignature(
            isinstance(declaration.node, ast.AsyncFunctionDef),
            tuple(parameters),
            rendered_return.text if rendered_return is not None else None,
        ),
        tuple(rendered_parameters),
        rendered_return,
    )


def _type_evidence(
    rendered: RenderedType,
    candidate: _ClassCandidate,
    type_parameters: frozenset[str],
    relation_kind: RelationKind,
) -> tuple[_TypeEvidence, ...]:
    if not rendered.supported:
        return ()
    occurrences = rendered.occurrences
    if relation_kind is RelationKind.INHERITANCE:
        occurrences = (rendered.outer_head,) if rendered.outer_head is not None else ()
    return tuple(
        _TypeEvidence(
            occurrence,
            candidate.parsed.indexed.module,
            candidate.qualified_name,
            type_parameters,
            relation_kind,
            rendered.text,
        )
        for occurrence in occurrences
    )


def _analyze_inheritance(
    candidate: _ClassCandidate,
    diagnostics: list[Diagnostic],
    class_identities: frozenset[tuple[str, str]],
    modules: frozenset[str],
) -> tuple[_TypeEvidence, ...]:
    renderer = SafeTypeExpressionRenderer(
        candidate.parsed.bindings,
        current_module=candidate.parsed.indexed.module,
        owner_qualified_name=candidate.qualified_name,
        class_identities=class_identities,
        modules=modules,
    )
    evidence: list[_TypeEvidence] = []
    for index, base in enumerate(candidate.node.bases):
        site = TypeReferenceSite(
            TypeReferenceSiteKind.INHERITANCE_BASE,
            candidate.entity_id,
            None,
            index,
            candidate.parsed.indexed.path,
        )
        rendered = _render_type(
            renderer,
            base,
            site,
            diagnostics,
            f"{candidate.entity_id}#base:{index}",
        )
        evidence.extend(
            _type_evidence(
                rendered,
                candidate,
                candidate.type_parameters,
                RelationKind.INHERITANCE,
            )
        )
    return tuple(evidence)


def _resolve_type_reference(
    evidence: _TypeEvidence,
    parsed_by_module: dict[str, _ParsedModule],
    modules: frozenset[str],
    class_identities: frozenset[tuple[str, str]],
    entity_by_id: dict[str, PythonClassEntity],
) -> RelationTarget | None:
    occurrence = evidence.occurrence
    spelling = occurrence.spelling
    if len(spelling) == 1 and spelling[0] in evidence.type_parameters:
        return None

    owner = entity_by_id[occurrence.owner_class_id]
    candidate = _construct_type_reference_candidate(
        spelling,
        _binding_map(parsed_by_module[evidence.module].bindings),
        current_module=evidence.module,
        owner_qualified_name=owner.qualified_name,
        class_identities=class_identities,
        modules=modules,
    )
    if candidate.internal_class is not None:
        module, qualified_name = candidate.internal_class
        internal_class = entity_by_id[f"python:class:{module}:{qualified_name}"]
        return RelationTarget(
            TargetResolution.INTERNAL,
            TargetKind.CLASS,
            internal_class.id,
            f"{internal_class.module}.{internal_class.qualified_name}",
        )
    if (
        candidate.binding_kind is BindingKind.MODULE
        and candidate.binding_exact
        and candidate.candidate_name in modules
    ):
        return RelationTarget(
            TargetResolution.INTERNAL,
            TargetKind.MODULE,
            f"python:module:{candidate.candidate_name}",
            candidate.candidate_name,
        )
    if (
        (not candidate.explicit_import and len(spelling) == 1 and spelling[0] in _BUILTIN_TYPES)
        or candidate.candidate_name.startswith("builtins.")
        or candidate.candidate_name.startswith("typing.")
        or candidate.candidate_name.startswith("typing_extensions.")
    ):
        return None
    if candidate.explicit_import:
        target_kind = (
            TargetKind.MODULE
            if candidate.binding_kind is BindingKind.MODULE and candidate.binding_exact
            else TargetKind.SYMBOL
        )
        return RelationTarget(
            TargetResolution.EXTERNAL,
            target_kind,
            None,
            candidate.candidate_name,
        )
    return RelationTarget(
        TargetResolution.UNKNOWN,
        TargetKind.SYMBOL,
        None,
        candidate.original_name,
    )


def _type_origin_rank(kind: TypeReferenceSiteKind) -> int:
    return {
        TypeReferenceSiteKind.INHERITANCE_BASE: 0,
        TypeReferenceSiteKind.FIELD_ANNOTATION: 1,
        TypeReferenceSiteKind.PARAMETER_ANNOTATION: 2,
        TypeReferenceSiteKind.RETURN_ANNOTATION: 3,
    }[kind]


def _import_relation_evidence(
    parsed: _ParsedModule, modules: frozenset[str]
) -> tuple[tuple[_RelationEvidence, ...], tuple[CoverageFrontier, ...]]:
    _, imports = _import_records(parsed.indexed.module, parsed.indexed.path, parsed.tree)
    evidence: list[_RelationEvidence] = []
    frontier: list[CoverageFrontier] = []
    for item in imports:
        if item.module is None:
            target = RelationTarget(
                TargetResolution.UNKNOWN, TargetKind.MODULE, None, "relative-import"
            )
        elif item.module in modules:
            target = RelationTarget(
                TargetResolution.INTERNAL,
                TargetKind.MODULE,
                f"python:module:{item.module}",
                item.module,
            )
        else:
            target = RelationTarget(
                TargetResolution.EXTERNAL,
                TargetKind.MODULE,
                None,
                item.module or "relative-import",
            )
        evidence.append(
            _RelationEvidence(
                RelationKind.IMPORT_DEPENDENCY,
                f"python:module:{parsed.indexed.module}",
                target,
                None,
                None,
                parsed.indexed.path,
                _internal_range(item.node),
                4,
            )
        )
        if item.star:
            frontier.append(
                CoverageFrontier(
                    FrontierDirection.FAILURE,
                    FrontierKind.MODULE,
                    target.id or target.name,
                    FrontierReason.STAR_IMPORT,
                )
            )
    return tuple(evidence), tuple(frontier)


def _canonical_relations(
    evidence: list[_RelationEvidence],
) -> tuple[PythonRelation, ...]:
    winners: dict[str, tuple[PythonRelation, tuple[object, ...]]] = {}
    for item in evidence:
        relation = PythonRelation.create(
            kind=item.kind,
            source_id=item.source_id,
            target=item.target,
            via_member_id=item.via_member_id,
            annotation=item.annotation,
            source_range=item.range.public(),
        )
        key = (
            _path_key(item.path),
            item.range.start_line,
            item.range.start_col,
            item.range.end_line,
            item.range.end_col,
            item.origin_rank,
        )
        current = winners.get(relation.id)
        if current is None or key < current[1]:
            winners[relation.id] = (relation, key)
    return tuple(sorted((item[0] for item in winners.values()), key=relation_sort_key))
