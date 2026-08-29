from __future__ import annotations

import ast
import io
import tokenize
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final

from code_structure_viz.adapters.sqlalchemy.model import (
    RedactedExpression,
    RedactedExpressionCategory,
    SqlAlchemyAssociationTableRow,
    SqlAlchemyCardinality,
    SqlAlchemyCheckRow,
    SqlAlchemyColumnRow,
    SqlAlchemyCoverage,
    SqlAlchemyCoverageFrontier,
    SqlAlchemyFailedSource,
    SqlAlchemyFailedStage,
    SqlAlchemyForeignKeyRow,
    SqlAlchemyFrontierDirection,
    SqlAlchemyFrontierKind,
    SqlAlchemyFrontierReason,
    SqlAlchemyIndexRow,
    SqlAlchemyIndexTerm,
    SqlAlchemyInheritanceRow,
    SqlAlchemyInternalDeclarationSpan,
    SqlAlchemyMappingSource,
    SqlAlchemyMappingSourceKind,
    SqlAlchemyPrimaryKeyRow,
    SqlAlchemyRedactionSummary,
    SqlAlchemyRelation,
    SqlAlchemyRelationKind,
    SqlAlchemyRelationshipRow,
    SqlAlchemyRelationTarget,
    SqlAlchemyRow,
    SqlAlchemyRowEvidence,
    SqlAlchemyRowKind,
    SqlAlchemySnapshot,
    SqlAlchemySourceLocation,
    SqlAlchemySourceRange,
    SqlAlchemyTable,
    SqlAlchemyTargetResolution,
    SqlAlchemyTypeCategory,
    SqlAlchemyTypeDescriptor,
    SqlAlchemyUniqueRow,
    canonicalize_relations,
    canonicalize_row_evidence,
    failed_source_sort_key,
    frontier_sort_key,
    redacted_value_count,
    row_sort_key,
    safe_dotted_symbol,
    safe_structural_string,
    sqlalchemy_occurrence_diagnostic_symbol,
    sqlalchemy_table_id,
    table_sort_key,
)
from code_structure_viz.core.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    canonical_diagnostics,
    diagnostic,
)
from code_structure_viz.source.python_modules import (
    PythonSourceFailure,
    PythonSourceIndex,
    PythonSourceModule,
    PythonSourceStage,
)


class SqlAlchemyApplicability(StrEnum):
    ABSENT = "absent"
    PRESENT = "present"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class SqlAlchemyAnalysisResult:
    snapshot: SqlAlchemySnapshot
    applicability: SqlAlchemyApplicability


@dataclass(slots=True)
class _ParsedModule:
    module: str
    path: str
    tree: ast.Module
    bindings: dict[str, str | None]
    ambiguous_bindings: dict[str, set[str]]
    star_import: bool
    is_package: bool
    attribute_mutations: set[str] = field(default_factory=set)
    imported_module_aliases: dict[str, set[str]] = field(default_factory=dict)
    imported_module_alias_candidates: dict[str, set[str]] = field(default_factory=dict)
    import_alias_definite_positions: dict[str, tuple[int, int]] = field(default_factory=dict)
    import_alias_events: dict[str, list[tuple[tuple[int, int], str | None]]] = field(
        default_factory=dict
    )
    star_import_origins: set[str] = field(default_factory=set)
    repository_bindings: dict[str, str | None] = field(default_factory=dict)
    repository_ambiguous_bindings: dict[str, frozenset[str]] = field(default_factory=dict)
    repository_modules: frozenset[str] = frozenset()
    repository_module_origins: frozenset[str] = frozenset()
    repository_module_aliases: dict[str, frozenset[str]] = field(default_factory=dict)
    repository_star_imports: dict[str, frozenset[str]] = field(default_factory=dict)


@dataclass(slots=True)
class _ClassDeclaration:
    module: _ParsedModule
    node: ast.ClassDef
    symbol: str
    duplicate: bool = False
    shadowed_names: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class _ClassSpecialBinding:
    value: ast.expr | None
    module: _ParsedModule
    supported: bool


@dataclass(slots=True)
class _TableCandidate:
    origin: str
    schema_name: str | None
    table_name: str
    mapping_sources: list[SqlAlchemyMappingSource] = field(default_factory=list)
    table_calls: list[tuple[_ParsedModule, ast.Call]] = field(default_factory=list)
    classes: list[_ClassDeclaration] = field(default_factory=list)
    class_constraints: list[tuple[_ParsedModule, ast.Call]] = field(default_factory=list)


@dataclass(slots=True)
class _State:
    diagnostics: list[Diagnostic] = field(default_factory=list)
    failed_files: list[SqlAlchemyFailedSource] = field(default_factory=list)
    frontier: list[SqlAlchemyCoverageFrontier] = field(default_factory=list)
    evidence_files: set[str] = field(default_factory=set)
    consumed_calls: set[int] = field(default_factory=set)
    supported_declarations: int = 0
    unknown_declarations: int = 0

    def supported(self, module: _ParsedModule, call: ast.Call | None = None) -> None:
        self.supported_declarations += 1
        self.evidence_files.add(module.path)
        if call is not None:
            self.consumed_calls.add(id(call))

    def unknown(
        self,
        *,
        module: _ParsedModule,
        code: DiagnosticCode,
        symbol: str,
        line: int,
        kind: SqlAlchemyFrontierKind,
        reference: str | None = None,
    ) -> None:
        self.unknown_declarations += 1
        self.evidence_files.add(module.path)
        self.diagnostics.append(
            diagnostic(
                code,
                domain="sqlalchemy",
                path=module.path,
                symbol=symbol,
                line=line,
            )
        )
        self.frontier.append(
            SqlAlchemyCoverageFrontier(
                SqlAlchemyFrontierDirection.FAILURE,
                kind,
                reference or symbol,
                (
                    SqlAlchemyFrontierReason.UNRESOLVED_REFERENCE
                    if code
                    in {DiagnosticCode.SA_DECLARATIVE_BINDING, DiagnosticCode.SA_RELATION_TARGET}
                    else SqlAlchemyFrontierReason.UNSUPPORTED_PATTERN
                ),
            )
        )


_CONSTRUCTION_SYMBOLS: Final = frozenset(
    {
        "sqlalchemy.Table",
        "sqlalchemy.Column",
        "sqlalchemy.ForeignKey",
        "sqlalchemy.ForeignKeyConstraint",
        "sqlalchemy.PrimaryKeyConstraint",
        "sqlalchemy.UniqueConstraint",
        "sqlalchemy.CheckConstraint",
        "sqlalchemy.Index",
        "sqlalchemy.Computed",
        "sqlalchemy.Identity",
        "sqlalchemy.orm.declarative_base",
        "sqlalchemy.orm.mapped_column",
        "sqlalchemy.orm.relationship",
    }
)
_CONSTRUCTION_TERMINALS: Final = frozenset(
    value.rsplit(".", 1)[-1] for value in _CONSTRUCTION_SYMBOLS
)
_SQLALCHEMY_MODULE_SYMBOLS: Final = frozenset(
    {
        "sqlalchemy",
        "sqlalchemy.ext",
        "sqlalchemy.ext.declarative",
        "sqlalchemy.orm",
        "sqlalchemy.schema",
        "sqlalchemy.sql",
        "sqlalchemy.sql.schema",
        "sqlalchemy.types",
    }
)
_SQLALCHEMY_BINDING_SYMBOLS: Final = _CONSTRUCTION_SYMBOLS | {
    "sqlalchemy",
    "sqlalchemy.orm",
    "sqlalchemy.schema",
    "sqlalchemy.sql",
    "sqlalchemy.sql.schema",
    "sqlalchemy.types",
    "sqlalchemy.orm.DeclarativeBase",
    "sqlalchemy.orm.Mapped",
}
_SQLALCHEMY_EVIDENCE_TERMINALS: Final = _CONSTRUCTION_TERMINALS | {"Mapped"}
_COLUMN_SYMBOLS: Final = {"sqlalchemy.Column", "sqlalchemy.orm.mapped_column"}
_COLUMN_SPECIALS: Final = {
    "sqlalchemy.ForeignKey",
    "sqlalchemy.Computed",
    "sqlalchemy.Identity",
}
_CONSTRAINT_SYMBOLS: Final = {
    "sqlalchemy.PrimaryKeyConstraint",
    "sqlalchemy.UniqueConstraint",
    "sqlalchemy.CheckConstraint",
    "sqlalchemy.Index",
    "sqlalchemy.ForeignKeyConstraint",
}
_TYPE_CATEGORIES: Final[dict[str, SqlAlchemyTypeCategory]] = {
    "sqlalchemy.Integer": SqlAlchemyTypeCategory.INTEGER,
    "sqlalchemy.BigInteger": SqlAlchemyTypeCategory.INTEGER,
    "sqlalchemy.SmallInteger": SqlAlchemyTypeCategory.INTEGER,
    "builtins.int": SqlAlchemyTypeCategory.INTEGER,
    "sqlalchemy.String": SqlAlchemyTypeCategory.STRING,
    "sqlalchemy.Unicode": SqlAlchemyTypeCategory.STRING,
    "sqlalchemy.CHAR": SqlAlchemyTypeCategory.STRING,
    "sqlalchemy.VARCHAR": SqlAlchemyTypeCategory.STRING,
    "sqlalchemy.NCHAR": SqlAlchemyTypeCategory.STRING,
    "sqlalchemy.NVARCHAR": SqlAlchemyTypeCategory.STRING,
    "builtins.str": SqlAlchemyTypeCategory.STRING,
    "sqlalchemy.Text": SqlAlchemyTypeCategory.TEXT,
    "sqlalchemy.UnicodeText": SqlAlchemyTypeCategory.TEXT,
    "sqlalchemy.Boolean": SqlAlchemyTypeCategory.BOOLEAN,
    "builtins.bool": SqlAlchemyTypeCategory.BOOLEAN,
    "sqlalchemy.Date": SqlAlchemyTypeCategory.DATE,
    "datetime.date": SqlAlchemyTypeCategory.DATE,
    "sqlalchemy.DateTime": SqlAlchemyTypeCategory.DATETIME,
    "datetime.datetime": SqlAlchemyTypeCategory.DATETIME,
    "sqlalchemy.Time": SqlAlchemyTypeCategory.TIME,
    "datetime.time": SqlAlchemyTypeCategory.TIME,
    "sqlalchemy.Numeric": SqlAlchemyTypeCategory.DECIMAL,
    "sqlalchemy.DECIMAL": SqlAlchemyTypeCategory.DECIMAL,
    "decimal.Decimal": SqlAlchemyTypeCategory.DECIMAL,
    "sqlalchemy.Float": SqlAlchemyTypeCategory.FLOAT,
    "sqlalchemy.REAL": SqlAlchemyTypeCategory.FLOAT,
    "sqlalchemy.DOUBLE": SqlAlchemyTypeCategory.FLOAT,
    "builtins.float": SqlAlchemyTypeCategory.FLOAT,
    "sqlalchemy.JSON": SqlAlchemyTypeCategory.JSON,
    "sqlalchemy.LargeBinary": SqlAlchemyTypeCategory.BINARY,
    "sqlalchemy.BINARY": SqlAlchemyTypeCategory.BINARY,
    "sqlalchemy.VARBINARY": SqlAlchemyTypeCategory.BINARY,
    "builtins.bytes": SqlAlchemyTypeCategory.BINARY,
    "sqlalchemy.Uuid": SqlAlchemyTypeCategory.UUID,
    "sqlalchemy.UUID": SqlAlchemyTypeCategory.UUID,
    "uuid.UUID": SqlAlchemyTypeCategory.UUID,
    "sqlalchemy.Enum": SqlAlchemyTypeCategory.ENUM,
    "sqlalchemy.ARRAY": SqlAlchemyTypeCategory.ARRAY,
}
_BUILTIN_TYPES: Final = frozenset({"int", "str", "bool", "float", "bytes"})
_CLASS_TABLE_SPECIALS: Final = frozenset({"__tablename__", "__table__", "__table_args__"})


class SqlAlchemySnapshotAnalyzer:
    def analyze(self, index: PythonSourceIndex) -> SqlAlchemyAnalysisResult:
        state = _State()
        self._adopt_source_failures(index, state)
        modules = self._parse_modules(index.modules, state)
        self._index_bindings(modules)
        classes = self._classes(modules, state)
        declarative_classes, classic_bases = self._declarative_classes(classes, modules, state)
        candidates, table_bindings = self._table_candidates(
            modules,
            declarative_classes,
            state,
        )
        tables, surviving, class_tables, collided_ids = self._canonical_tables(
            candidates,
            state,
        )
        row_evidence = self._extract_rows(
            surviving,
            tables,
            table_bindings,
            class_tables,
            collided_ids,
            frozenset(module.module for module in modules),
            frozenset(declaration.symbol for declaration in declarative_classes),
            state,
        )
        rows, row_diagnostics = canonicalize_row_evidence(tuple(row_evidence))
        state.diagnostics.extend(row_diagnostics)
        state.unknown_declarations += len(row_diagnostics)
        for item in row_diagnostics:
            assert item.symbol is not None
            state.frontier.append(
                SqlAlchemyCoverageFrontier(
                    SqlAlchemyFrontierDirection.FAILURE,
                    SqlAlchemyFrontierKind.ROW,
                    item.symbol,
                    SqlAlchemyFrontierReason.UNSUPPORTED_PATTERN,
                )
            )
        module_table_ids = frozenset(
            surviving[origin][1].id for origin in table_bindings.values() if origin in surviving
        )
        association_rows = self._association_rows(rows, tables, module_table_ids)
        rows = tuple(sorted((*rows, *association_rows), key=row_sort_key))
        relations = self._relations(rows, tables)
        canonical_relations, relation_conflicts = canonicalize_relations(relations)
        if relation_conflicts:
            raise ValueError("SQLAlchemy relation identity conflict escaped row canonicalization")
        diagnostics = canonical_diagnostics(tuple(state.diagnostics))
        failed_files = tuple(sorted(state.failed_files, key=failed_source_sort_key))
        frontier = tuple(sorted(set(state.frontier), key=frontier_sort_key))
        partial_safe = bool(failed_files or state.unknown_declarations or diagnostics)
        selected_modules = tuple(
            sorted(
                {source.module for table in tables for source in table.mapping_sources},
                key=_utf8,
            )
        )
        coverage = SqlAlchemyCoverage(
            candidate_files=index.candidate_file_count,
            parsed_files=len(modules),
            failed_files=failed_files,
            evidence_files=tuple(sorted(state.evidence_files, key=_utf8)),
            selected_modules=selected_modules,
            mapped_classes=len(class_tables),
            association_tables=len(
                {row.owner_id for row in rows if isinstance(row, SqlAlchemyAssociationTableRow)}
            ),
            selected_entities=len(tables),
            unknown_declarations=state.unknown_declarations,
            frontier=frontier,
            redaction=SqlAlchemyRedactionSummary.create(redacted_value_count(rows)),
        )
        snapshot = SqlAlchemySnapshot(
            tuple(sorted(tables, key=table_sort_key)),
            rows,
            canonical_relations,
            coverage,
            diagnostics,
            partial_safe,
        )
        applicability = (
            SqlAlchemyApplicability.PRESENT
            if state.supported_declarations
            else SqlAlchemyApplicability.INDETERMINATE
            if failed_files or state.unknown_declarations
            else SqlAlchemyApplicability.ABSENT
        )
        del classic_bases
        return SqlAlchemyAnalysisResult(snapshot, applicability)

    def _adopt_source_failures(self, index: PythonSourceIndex, state: _State) -> None:
        for failure in index.failures:
            failed = _failed_source(failure)
            state.failed_files.append(failed)
            if failure.stage is PythonSourceStage.MODULE_COLLISION:
                continue
            state.diagnostics.append(
                diagnostic(
                    failed.diagnostic_code,
                    domain="sqlalchemy",
                    path=failed.path,
                )
            )
            state.frontier.append(
                SqlAlchemyCoverageFrontier(
                    SqlAlchemyFrontierDirection.FAILURE,
                    SqlAlchemyFrontierKind.FILE,
                    failed.path,
                    SqlAlchemyFrontierReason.FAILED_SOURCE,
                )
            )
        for collision in index.collisions:
            state.diagnostics.append(
                diagnostic(
                    DiagnosticCode.SA_MODULE_COLLISION,
                    domain="sqlalchemy",
                    symbol=f"sqlalchemy:module:{collision.module}",
                )
            )

    def _parse_modules(
        self,
        modules: tuple[PythonSourceModule, ...],
        state: _State,
    ) -> list[_ParsedModule]:
        parsed: list[_ParsedModule] = []
        for indexed in modules:
            path = indexed.source.path.as_posix()
            try:
                encoding, _ = tokenize.detect_encoding(io.BytesIO(indexed.source.content).readline)
                text = indexed.source.content.decode(encoding, errors="strict")
            except (SyntaxError, UnicodeDecodeError, LookupError):
                failed = SqlAlchemyFailedSource(
                    path,
                    SqlAlchemyFailedStage.ENCODING,
                    DiagnosticCode.SA_ENCODING,
                )
                state.failed_files.append(failed)
                state.diagnostics.append(
                    diagnostic(DiagnosticCode.SA_ENCODING, domain="sqlalchemy", path=path)
                )
                state.frontier.append(
                    SqlAlchemyCoverageFrontier(
                        SqlAlchemyFrontierDirection.FAILURE,
                        SqlAlchemyFrontierKind.FILE,
                        path,
                        SqlAlchemyFrontierReason.FAILED_SOURCE,
                    )
                )
                continue
            try:
                tree = ast.parse(
                    text,
                    filename=path,
                    mode="exec",
                    type_comments=False,
                    feature_version=(3, 12),
                )
            except (SyntaxError, ValueError, RecursionError) as error:
                line = error.lineno if isinstance(error, SyntaxError) else None
                if line is not None and (type(line) is not int or line <= 0):
                    line = None
                failed = SqlAlchemyFailedSource(
                    path,
                    SqlAlchemyFailedStage.PARSE,
                    DiagnosticCode.SA_PARSE,
                )
                state.failed_files.append(failed)
                state.diagnostics.append(
                    diagnostic(
                        DiagnosticCode.SA_PARSE,
                        domain="sqlalchemy",
                        path=path,
                        line=line,
                    )
                )
                state.frontier.append(
                    SqlAlchemyCoverageFrontier(
                        SqlAlchemyFrontierDirection.FAILURE,
                        SqlAlchemyFrontierKind.FILE,
                        path,
                        SqlAlchemyFrontierReason.FAILED_SOURCE,
                    )
                )
                continue
            finally:
                # Decoded source is deliberately not retained by the analysis graph.
                del text
            parsed.append(
                _ParsedModule(
                    indexed.module,
                    path,
                    tree,
                    {},
                    {},
                    False,
                    indexed.source.path.name == "__init__.py",
                )
            )
        return sorted(parsed, key=lambda item: (_utf8(item.module), _utf8(item.path)))

    def _index_bindings(self, modules: list[_ParsedModule]) -> None:
        repository_modules = frozenset(module.module for module in modules)
        repository_module_origins = _preview_repository_module_origins(modules, repository_modules)
        for module in modules:
            module.repository_modules = repository_modules
            module.repository_module_origins = repository_module_origins
        for module in modules:
            for statement in module.tree.body:
                _bind_module_statement(module, statement)
                if isinstance(statement, ast.ClassDef):
                    _invalidate_executed_class_body_mutations(
                        module,
                        statement,
                        f"{module.module}.{statement.name}",
                    )
                for write in _nested_module_scope_writes(statement):
                    _bind_module_statement(module, write, ambiguous=True)
                    if isinstance(write, ast.ClassDef):
                        _invalidate_executed_class_body_mutations(
                            module,
                            write,
                            f"{module.module}.{write.name}",
                            ambiguous_execution=True,
                        )
            for statement in module.tree.body:
                for candidate in (statement, *_nested_module_scope_writes(statement)):
                    if isinstance(candidate, ast.ClassDef):
                        _invalidate_executed_class_body_mutations(
                            module,
                            candidate,
                            f"{module.module}.{candidate.name}",
                            ambiguous_execution=candidate is not statement,
                            apply_global_bindings=False,
                        )
        attribute_mutations = _expand_imported_module_alias_mutations(modules)
        for module in modules:
            module.attribute_mutations.update(attribute_mutations)
        raw_bindings = {module.module: dict(module.bindings) for module in modules}
        raw_ambiguous_bindings = {
            module.module: {
                name: set(origins) for name, origins in module.ambiguous_bindings.items()
            }
            for module in modules
        }
        _resolve_repository_bindings(modules)
        _refresh_resolved_module_alias_provenance(modules)
        for module in modules:
            for statement in module.tree.body:
                for candidate in (statement, *_nested_module_scope_writes(statement)):
                    if isinstance(candidate, ast.ClassDef):
                        _invalidate_executed_class_body_mutations(
                            module,
                            candidate,
                            f"{module.module}.{candidate.name}",
                            ambiguous_execution=candidate is not statement,
                            apply_global_bindings=False,
                        )
        attribute_mutations = _expand_imported_module_alias_mutations(modules)
        for module in modules:
            module.attribute_mutations.update(attribute_mutations)
            module.bindings = raw_bindings[module.module]
            module.ambiguous_bindings = raw_ambiguous_bindings[module.module]
        _resolve_repository_bindings(modules)

    def _classes(
        self,
        modules: list[_ParsedModule],
        state: _State,
    ) -> list[_ClassDeclaration]:
        values: list[_ClassDeclaration] = []
        for module in modules:
            counts: dict[str, int] = {}
            for statement in module.tree.body:
                if isinstance(statement, ast.ClassDef):
                    counts[statement.name] = counts.get(statement.name, 0) + 1
            for statement in module.tree.body:
                if not isinstance(statement, ast.ClassDef):
                    continue
                symbol = f"{module.module}.{statement.name}"
                values.append(
                    _ClassDeclaration(
                        module,
                        statement,
                        symbol,
                        duplicate=counts[statement.name] != 1,
                        shadowed_names=_class_shadowed_names(module, statement),
                    )
                )
        return values

    def _declarative_classes(
        self,
        classes: list[_ClassDeclaration],
        modules: list[_ParsedModule],
        state: _State,
    ) -> tuple[list[_ClassDeclaration], set[str]]:
        classic_bases: set[str] = set()
        for module in modules:
            for statement in module.tree.body:
                if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
                    continue
                target = statement.targets[0]
                if not isinstance(target, ast.Name) or not isinstance(statement.value, ast.Call):
                    continue
                resolved_call = _resolve_call(statement.value, module)
                if resolved_call != "sqlalchemy.orm.declarative_base":
                    if _unresolved_terminal(
                        statement.value.func,
                        module,
                        {"declarative_base"},
                    ):
                        _consume_construction_calls(module, statement.value, state)
                        state.unknown(
                            module=module,
                            code=DiagnosticCode.SA_DECLARATIVE_BINDING,
                            symbol=f"{module.module}.{target.id}",
                            line=_line(statement.value),
                            kind=SqlAlchemyFrontierKind.CLASS,
                            reference=f"module:{module.module}",
                        )
                    continue
                symbol = f"{module.module}.{target.id}"
                if module.bindings.get(target.id) != symbol:
                    self._unknown_declarative_base_expression(
                        module,
                        statement.value,
                        symbol,
                        state,
                    )
                    continue
                classic_bases.add(symbol)
                state.supported(module, statement.value)

        proven: list[_ClassDeclaration] = []
        proven_nodes: set[int] = set()
        proven_symbols: set[str] = set()
        bound = set(classic_bases)
        for _ in range(len(classes) + 1):
            changed = False
            for declaration in classes:
                if id(declaration.node) in proven_nodes:
                    continue
                bases = tuple(
                    _resolve_symbol(base, declaration.module) for base in declaration.node.bases
                )
                if "sqlalchemy.orm.DeclarativeBase" in bases or any(
                    base in bound or base in proven_symbols for base in bases if base is not None
                ):
                    proven.append(declaration)
                    proven_nodes.add(id(declaration.node))
                    proven_symbols.add(declaration.symbol)
                    state.supported(declaration.module)
                    if declaration.duplicate:
                        state.unknown(
                            module=declaration.module,
                            code=DiagnosticCode.SA_DECLARATIVE_BINDING,
                            symbol=declaration.symbol,
                            line=_line(declaration.node),
                            kind=SqlAlchemyFrontierKind.CLASS,
                        )
                    changed = True
                elif any(
                    _unresolved_terminal(base, declaration.module, {"DeclarativeBase"})
                    or _ambiguous_binding_matches(
                        base,
                        declaration.module,
                        proven_symbols | classic_bases,
                    )
                    or _declarative_base_expression_evidence(
                        base,
                        declaration.module,
                        proven_symbols | classic_bases,
                    )
                    for base in declaration.node.bases
                ):
                    state.unknown(
                        module=declaration.module,
                        code=DiagnosticCode.SA_DECLARATIVE_BINDING,
                        symbol=declaration.symbol,
                        line=_line(declaration.node),
                        kind=SqlAlchemyFrontierKind.CLASS,
                    )
            if not changed:
                break
        base_symbols = proven_symbols | classic_bases
        base_candidate_bindings: set[str] = set()
        for declaration in classes:
            for base in declaration.node.bases:
                for node in ast.walk(base):
                    if not isinstance(node, (ast.Name, ast.Attribute)):
                        continue
                    resolved = _resolve_symbol(node, declaration.module)
                    if resolved is not None:
                        base_candidate_bindings.add(resolved)
                    base_candidate_bindings.update(_ambiguous_symbols(node, declaration.module))
        for module in modules:
            for statement in module.tree.body:
                self._unsupported_declarative_base_assignment(
                    module,
                    statement,
                    nested=False,
                    base_symbols=base_symbols,
                    base_candidate_bindings=base_candidate_bindings,
                    state=state,
                )
                for write in _nested_module_scope_writes(statement):
                    self._unsupported_declarative_base_assignment(
                        module,
                        write,
                        nested=True,
                        base_symbols=base_symbols,
                        base_candidate_bindings=base_candidate_bindings,
                        state=state,
                    )
        return sorted(
            proven,
            key=lambda item: (
                _utf8(item.symbol),
                _utf8(item.module.path),
                _line(item.node),
            ),
        ), classic_bases

    def _unsupported_declarative_base_assignment(
        self,
        module: _ParsedModule,
        statement: ast.AST,
        *,
        nested: bool,
        base_symbols: set[str],
        base_candidate_bindings: set[str],
        state: _State,
    ) -> None:
        assigned_bindings = {f"{module.module}.{name}" for name in _assignment_names(statement)}
        targets: tuple[ast.expr, ...]
        if isinstance(statement, ast.Assign):
            targets = tuple(statement.targets)
        elif isinstance(statement, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            targets = (statement.target,)
        else:
            targets = ()
        for target in targets:
            for node in ast.walk(target):
                if not isinstance(node, ast.Attribute):
                    continue
                resolved = _resolve_symbol(node, module)
                if resolved is not None:
                    assigned_bindings.add(resolved)
                assigned_bindings.update(_ambiguous_symbols(node, module))
        if not assigned_bindings & base_candidate_bindings:
            return
        value = _assignment_value(statement)
        if value is None or not _declarative_base_expression_evidence(
            value,
            module,
            base_symbols,
        ):
            return
        if (
            not nested
            and isinstance(value, ast.Call)
            and _is_supported_module_single_name_assignment(statement)
            and (
                _resolve_call(value, module) == "sqlalchemy.orm.declarative_base"
                or _unresolved_terminal(value.func, module, {"declarative_base"})
            )
        ):
            return
        span = _span(statement)
        symbol = (
            f"{module.module}.declarative_base_occurrence_"
            f"{span.start_line}_{span.start_utf8_byte_column}_"
            f"{span.end_line}_{span.end_utf8_byte_column}"
        )
        self._unknown_declarative_base_expression(module, value, symbol, state)

    def _unknown_declarative_base_expression(
        self,
        module: _ParsedModule,
        value: ast.expr,
        symbol: str,
        state: _State,
    ) -> None:
        _consume_construction_calls(module, value, state)
        state.unknown(
            module=module,
            code=DiagnosticCode.SA_DECLARATIVE_BINDING,
            symbol=symbol,
            line=_line(value),
            kind=SqlAlchemyFrontierKind.CLASS,
            reference=f"module:{module.module}",
        )

    def _table_candidates(
        self,
        modules: list[_ParsedModule],
        declarative_classes: list[_ClassDeclaration],
        state: _State,
    ) -> tuple[dict[str, _TableCandidate], dict[str, str]]:
        candidates: dict[str, _TableCandidate] = {}
        table_bindings: dict[str, str] = {}
        for module in modules:
            for statement in module.tree.body:
                if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
                    continue
                target = statement.targets[0]
                if not isinstance(target, ast.Name) or not isinstance(statement.value, ast.Call):
                    continue
                resolved_call = _resolve_call(statement.value, module)
                if resolved_call != "sqlalchemy.Table":
                    if _unresolved_terminal(
                        statement.value.func,
                        module,
                        {"Table"},
                    ):
                        self._unknown_table_call(
                            module,
                            statement.value,
                            f"{module.module}.{target.id}",
                            state,
                        )
                    continue
                if module.bindings.get(target.id) != f"{module.module}.{target.id}":
                    self._unknown_table_call(
                        module,
                        statement.value,
                        f"{module.module}.{target.id}",
                        state,
                    )
                    continue
                origin = f"table:{module.module}.{target.id}"
                candidate = self._candidate_from_table_call(
                    module,
                    statement.value,
                    origin,
                    f"{module.module}.{target.id}",
                    state,
                )
                if candidate is not None:
                    candidates[origin] = candidate
                    table_bindings[f"{module.module}.{target.id}"] = origin
            for statement in module.tree.body:
                self._unsupported_module_table_assignment(
                    module,
                    statement,
                    nested=False,
                    state=state,
                )
                for write in _nested_module_scope_writes(statement):
                    self._unsupported_module_table_assignment(
                        module,
                        write,
                        nested=True,
                        state=state,
                    )

        for declaration in declarative_classes:
            scope_modules, global_names = _class_scope_modules(declaration)
            special = _special_assignments(declaration, scope_modules, global_names)
            if any(
                len(special.get(name, ())) > 1
                or any(not binding.supported for binding in special.get(name, ()))
                for name in _CLASS_TABLE_SPECIALS
            ):
                self._unknown_table(declaration, state)
                continue
            table_args = special.get("__table_args__", ())
            schema_from_args: str | None = None
            class_constraints: tuple[ast.Call, ...] = ()
            table_args_module = declaration.module
            if table_args:
                table_args_binding = table_args[0]
                assert table_args_binding.value is not None
                table_args_module = table_args_binding.module
                parsed_args = _parse_table_args(
                    table_args_binding.value,
                    table_args_module,
                )
                if parsed_args is None:
                    self._unknown_table(declaration, state)
                    continue
                schema_from_args, class_constraints = parsed_args

            tablename: str | None = None
            if special.get("__tablename__"):
                tablename_binding = special["__tablename__"][0]
                assert tablename_binding.value is not None
                tablename = _static_structural_string(tablename_binding.value)
                if tablename is None:
                    self._unknown_table(declaration, state)
                    continue

            linked_origin: str | None = None
            direct_candidate: _TableCandidate | None = None
            table_values = special.get("__table__", ())
            if table_values:
                table_binding = table_values[0]
                assert table_binding.value is not None
                table_value = table_binding.value
                table_module = table_binding.module
                if (
                    isinstance(table_value, ast.Call)
                    and _resolve_call(table_value, table_module) == "sqlalchemy.Table"
                ):
                    origin = _class_candidate_origin("class-table", declaration)
                    direct_candidate = self._candidate_from_table_call(
                        table_module,
                        table_value,
                        origin,
                        f"{declaration.symbol}.__table__",
                        state,
                    )
                    if direct_candidate is None:
                        continue
                    candidates[origin] = direct_candidate
                    linked_origin = origin
                else:
                    symbol = _resolve_symbol(table_value, table_module)
                    linked_origin = table_bindings.get(symbol or "")
                    if linked_origin is None:
                        self._unknown_table(declaration, state)
                        continue

            if linked_origin is not None:
                candidate = candidates[linked_origin]
                if tablename is not None and tablename != candidate.table_name:
                    self._unknown_table(declaration, state)
                    continue
                if schema_from_args is not None and schema_from_args != candidate.schema_name:
                    self._unknown_table(declaration, state)
                    continue
            elif tablename is not None:
                origin = _class_candidate_origin("class", declaration)
                candidate = _TableCandidate(origin, schema_from_args, tablename)
                candidates[origin] = candidate
                linked_origin = origin
            else:
                continue

            assert linked_origin is not None
            candidate = candidates[linked_origin]
            candidate.classes.append(declaration)
            candidate.mapping_sources.append(
                SqlAlchemyMappingSource(
                    SqlAlchemyMappingSourceKind.DECLARATIVE_CLASS,
                    declaration.module.module,
                    declaration.symbol,
                    _location(declaration.module, declaration.node),
                )
            )
            candidate.class_constraints.extend(
                (table_args_module, call) for call in class_constraints
            )
        return candidates, table_bindings

    def _unsupported_module_table_assignment(
        self,
        module: _ParsedModule,
        statement: ast.AST,
        *,
        nested: bool,
        state: _State,
    ) -> None:
        value = _assignment_value(statement)
        if not isinstance(value, ast.Call):
            return
        if _resolve_call(value, module) != "sqlalchemy.Table" and not _unresolved_terminal(
            value.func,
            module,
            {"Table"},
        ):
            return
        if not nested and _is_supported_module_single_name_assignment(statement):
            return
        span = _span(statement)
        symbol = (
            f"{module.module}.table_occurrence_"
            f"{span.start_line}_{span.start_utf8_byte_column}_"
            f"{span.end_line}_{span.end_utf8_byte_column}"
        )
        self._unknown_table_call(module, value, symbol, state)

    def _candidate_from_table_call(
        self,
        module: _ParsedModule,
        call: ast.Call,
        origin: str,
        symbol: str,
        state: _State,
    ) -> _TableCandidate | None:
        state.supported(module, call)
        if len(call.args) < 2 or any(isinstance(argument, ast.Starred) for argument in call.args):
            self._unknown_table_call(module, call, symbol, state)
            return None
        table_name = _static_structural_string(call.args[0])
        if table_name is None:
            self._unknown_table_call(module, call, symbol, state)
            return None
        schema_name: str | None = None
        seen_schema = False
        for keyword in call.keywords:
            if keyword.arg != "schema" or seen_schema:
                self._unknown_table_call(module, call, symbol, state)
                return None
            seen_schema = True
            schema_name = _static_structural_string(keyword.value)
            if schema_name is None:
                self._unknown_table_call(module, call, symbol, state)
                return None
        candidate = _TableCandidate(origin, schema_name, table_name)
        candidate.table_calls.append((module, call))
        candidate.mapping_sources.append(
            SqlAlchemyMappingSource(
                SqlAlchemyMappingSourceKind.TABLE,
                module.module,
                symbol,
                _location(module, call),
            )
        )
        return candidate

    def _canonical_tables(
        self,
        candidates: dict[str, _TableCandidate],
        state: _State,
    ) -> tuple[
        list[SqlAlchemyTable],
        dict[str, tuple[_TableCandidate, SqlAlchemyTable]],
        dict[str, SqlAlchemyTable],
        set[str],
    ]:
        identity_groups: dict[str, list[_TableCandidate]] = {}
        for candidate in candidates.values():
            identity_groups.setdefault(
                sqlalchemy_table_id(candidate.schema_name, candidate.table_name), []
            ).append(candidate)
        tables: list[SqlAlchemyTable] = []
        surviving: dict[str, tuple[_TableCandidate, SqlAlchemyTable]] = {}
        class_table_candidates: dict[str, list[SqlAlchemyTable]] = {}
        collided: set[str] = set()
        for table_id in sorted(identity_groups, key=_utf8):
            group = identity_groups[table_id]
            if len(group) != 1:
                collided.add(table_id)
                state.unknown_declarations += len(group)
                state.diagnostics.append(
                    diagnostic(
                        DiagnosticCode.SA_TABLE_COLLISION,
                        domain="sqlalchemy",
                        symbol=table_id,
                    )
                )
                state.frontier.append(
                    SqlAlchemyCoverageFrontier(
                        SqlAlchemyFrontierDirection.FAILURE,
                        SqlAlchemyFrontierKind.TABLE,
                        table_id,
                        SqlAlchemyFrontierReason.IDENTITY_COLLISION,
                    )
                )
                continue
            candidate = group[0]
            table = SqlAlchemyTable.create(
                schema_name=candidate.schema_name,
                name=candidate.table_name,
                mapping_sources=tuple(candidate.mapping_sources),
            )
            tables.append(table)
            surviving[candidate.origin] = (candidate, table)
            for declaration in candidate.classes:
                class_table_candidates.setdefault(declaration.symbol, []).append(table)
        class_tables = {
            symbol: values[0]
            for symbol, values in class_table_candidates.items()
            if len(values) == 1
        }
        return tables, surviving, class_tables, collided

    def _extract_rows(
        self,
        surviving: dict[str, tuple[_TableCandidate, SqlAlchemyTable]],
        tables: list[SqlAlchemyTable],
        table_bindings: dict[str, str],
        class_tables: dict[str, SqlAlchemyTable],
        collided_ids: set[str],
        source_modules: frozenset[str],
        declarative_symbols: frozenset[str],
        state: _State,
    ) -> list[SqlAlchemyRowEvidence]:
        tables_by_id = {table.id: table for table in tables}
        bound_tables = {
            symbol: surviving[origin][1]
            for symbol, origin in table_bindings.items()
            if origin in surviving
        }
        rows: list[SqlAlchemyRowEvidence] = []
        for candidate, table in surviving.values():
            known_columns: dict[str, str | None] = {}
            deferred_constraints: list[tuple[_ParsedModule, ast.Call]] = []
            for module, call in candidate.table_calls:
                for argument in call.args[2:]:
                    if not isinstance(argument, ast.Call):
                        self._unknown_row(module, table, SqlAlchemyRowKind.COLUMN, argument, state)
                        continue
                    symbol = _resolve_call(argument, module)
                    if symbol in _COLUMN_SYMBOLS:
                        parsed = self._column_rows(
                            module,
                            table,
                            argument,
                            attribute_name=None,
                            annotation=None,
                            table_column=True,
                            tables_by_id=tables_by_id,
                            state=state,
                        )
                        rows.extend(parsed)
                        for parsed_row in parsed:
                            if (
                                isinstance(parsed_row.row, SqlAlchemyColumnRow)
                                and parsed_row.row.name is not None
                            ):
                                _remember_column(
                                    known_columns, parsed_row.row.name, parsed_row.row.name
                                )
                    elif symbol in _CONSTRAINT_SYMBOLS:
                        deferred_constraints.append((module, argument))
                    else:
                        self._unknown_row(module, table, SqlAlchemyRowKind.COLUMN, argument, state)

            for declaration in candidate.classes:
                scope_modules, global_names = _class_scope_modules(declaration)
                for statement in declaration.node.body:
                    module = scope_modules[id(statement)]
                    for write in _nested_module_scope_writes(statement):
                        if not _only_global_bindings(write, global_names[id(write)]):
                            self._unsupported_row_assignment(
                                scope_modules[id(write)],
                                table,
                                write,
                                state,
                            )
                    assignment = _row_assignment(statement)
                    if assignment is None:
                        self._unsupported_row_assignment(
                            module,
                            table,
                            statement,
                            state,
                        )
                        continue
                    name, annotation, value = assignment
                    if name in global_names[id(statement)]:
                        continue
                    if name.startswith("__"):
                        continue
                    if value is not None and _expression_uses_shadowed(
                        value, declaration.shadowed_names
                    ):
                        self._unknown_row(
                            module,
                            table,
                            _shadowed_row_kind(value, module, declaration.shadowed_names),
                            value,
                            state,
                        )
                        continue
                    if annotation is not None and _expression_uses_shadowed(
                        annotation, declaration.shadowed_names
                    ):
                        self._unknown_row(
                            module,
                            table,
                            SqlAlchemyRowKind.COLUMN,
                            statement,
                            state,
                        )
                        continue
                    if (
                        isinstance(value, ast.Call)
                        and _resolve_call(value, module) in _COLUMN_SYMBOLS
                    ):
                        parsed = self._column_rows(
                            module,
                            table,
                            value,
                            attribute_name=name,
                            annotation=annotation,
                            table_column=False,
                            tables_by_id=tables_by_id,
                            state=state,
                        )
                        rows.extend(parsed)
                        for parsed_row in parsed:
                            if (
                                isinstance(parsed_row.row, SqlAlchemyColumnRow)
                                and parsed_row.row.name is not None
                            ):
                                _remember_column(known_columns, name, parsed_row.row.name)
                    elif (
                        isinstance(value, ast.Call)
                        and _resolve_call(value, module) == "sqlalchemy.orm.relationship"
                    ):
                        relationship = self._relationship_row(
                            declaration,
                            module,
                            table,
                            name,
                            annotation,
                            value,
                            class_tables,
                            bound_tables,
                            tables_by_id,
                            collided_ids,
                            source_modules,
                            declarative_symbols,
                            state,
                        )
                        if relationship is not None:
                            rows.append(relationship)
                    elif (
                        value is None
                        and annotation is not None
                        and _mapped_inner(annotation, module) is not None
                    ):
                        source = _location(module, statement)
                        row = SqlAlchemyColumnRow.create(
                            owner_id=table.id,
                            name=name,
                            source=source,
                            type=_type_descriptor(
                                _mapped_inner(annotation, module),
                                module,
                                state,
                            ),
                        )
                        if row.type.category is SqlAlchemyTypeCategory.UNKNOWN:
                            self._unknown_row(
                                module,
                                table,
                                SqlAlchemyRowKind.COLUMN,
                                statement,
                                state,
                            )
                        rows.append(SqlAlchemyRowEvidence(row, _span(statement)))
                        _remember_column(known_columns, name, name)
                        state.supported(module)
                    elif isinstance(value, ast.Call) and _unresolved_terminal(
                        value.func,
                        module,
                        _SQLALCHEMY_EVIDENCE_TERMINALS,
                    ):
                        kind = (
                            SqlAlchemyRowKind.RELATIONSHIP
                            if _terminal_name(value.func) == "relationship"
                            else SqlAlchemyRowKind.COLUMN
                        )
                        self._unknown_row(module, table, kind, value, state)
                    elif (
                        value is None
                        and annotation is not None
                        and _unresolved_mapped_annotation(annotation, module)
                    ):
                        self._unknown_row(
                            module,
                            table,
                            SqlAlchemyRowKind.COLUMN,
                            statement,
                            state,
                        )
                rows.extend(
                    self._inheritance_rows(
                        declaration,
                        table,
                        class_tables,
                    )
                )
            deferred_constraints.extend(candidate.class_constraints)
            for module, call in deferred_constraints:
                rows.extend(
                    self._constraint_rows(module, table, call, known_columns, tables_by_id, state)
                )
        return rows

    def _unsupported_row_assignment(
        self,
        module: _ParsedModule,
        table: SqlAlchemyTable,
        statement: ast.AST,
        state: _State,
    ) -> None:
        value = _assignment_value(statement)
        names = _assignment_names(statement)
        if any(name.startswith("__") for name in names):
            return
        if isinstance(value, ast.Call):
            symbol = _resolve_call(value, module)
            if symbol in _COLUMN_SYMBOLS:
                kind = SqlAlchemyRowKind.COLUMN
            elif symbol == "sqlalchemy.orm.relationship":
                kind = SqlAlchemyRowKind.RELATIONSHIP
            elif _unresolved_terminal(
                value.func,
                module,
                _SQLALCHEMY_EVIDENCE_TERMINALS,
            ):
                kind = (
                    SqlAlchemyRowKind.RELATIONSHIP
                    if _terminal_name(value.func) == "relationship"
                    else SqlAlchemyRowKind.COLUMN
                )
            else:
                return
            self._unknown_row(module, table, kind, value, state)
            return
        annotation = statement.annotation if isinstance(statement, ast.AnnAssign) else None
        if annotation is not None and (
            _mapped_inner(annotation, module) is not None
            or _unresolved_mapped_annotation(annotation, module)
        ):
            self._unknown_row(
                module,
                table,
                SqlAlchemyRowKind.COLUMN,
                statement,
                state,
            )

    def _relationship_row(
        self,
        declaration: _ClassDeclaration,
        module: _ParsedModule,
        table: SqlAlchemyTable,
        name: str,
        annotation: ast.expr | None,
        call: ast.Call,
        class_tables: dict[str, SqlAlchemyTable],
        bound_tables: dict[str, SqlAlchemyTable],
        tables_by_id: dict[str, SqlAlchemyTable],
        collided_ids: set[str],
        source_modules: frozenset[str],
        declarative_symbols: frozenset[str],
        state: _State,
    ) -> SqlAlchemyRowEvidence | None:
        state.supported(module, call)
        keywords = _keyword_map(call)
        allowed_keywords = {
            "argument",
            "uselist",
            "back_populates",
            "secondary",
            "primaryjoin",
            "secondaryjoin",
            "order_by",
            "foreign_keys",
        }
        if (
            keywords is None
            or len(call.args) > 1
            or any(isinstance(argument, ast.Starred) for argument in call.args)
            or set(keywords) - allowed_keywords
            or (call.args and "argument" in keywords)
        ):
            self._unknown_row(module, table, SqlAlchemyRowKind.RELATIONSHIP, call, state)
            return None

        annotation_target, annotation_cardinality = _relationship_annotation(annotation, module)
        target_node = (
            call.args[0]
            if call.args
            else keywords.get("argument")
            if "argument" in keywords
            else annotation_target
        )
        target = _relationship_target(
            target_node,
            module,
            class_tables,
            source_modules,
            declarative_symbols,
        )
        unresolved_target = target.resolution is SqlAlchemyTargetResolution.UNKNOWN

        row_unrepresentable = False
        uselist: bool | None = None
        if "uselist" in keywords:
            uselist = _static_bool(keywords["uselist"])
            if uselist is None:
                cardinality = SqlAlchemyCardinality.UNKNOWN
                row_unrepresentable = True
            else:
                cardinality = (
                    SqlAlchemyCardinality.MANY if uselist else SqlAlchemyCardinality.SCALAR
                )
        else:
            cardinality = annotation_cardinality
            if cardinality is SqlAlchemyCardinality.UNKNOWN:
                row_unrepresentable = True

        back_populates: str | None = None
        if "back_populates" in keywords:
            back_populates = _static_structural_string(keywords["back_populates"])
            if back_populates is None:
                row_unrepresentable = True

        secondary: SqlAlchemyRelationTarget | None = None
        if "secondary" in keywords:
            secondary = _secondary_target(
                keywords["secondary"],
                module,
                bound_tables,
                tables_by_id,
                collided_ids,
            )
            if secondary.resolution is SqlAlchemyTargetResolution.UNKNOWN:
                unresolved_target = True

        relationship = SqlAlchemyRelationshipRow.create(
            owner_id=table.id,
            name=name,
            source=_location(module, call),
            target=target,
            cardinality=cardinality,
            uselist=uselist,
            back_populates=back_populates,
            secondary=secondary,
            primaryjoin=_redacted(keywords.get("primaryjoin"), module, state),
            secondaryjoin=_redacted(keywords.get("secondaryjoin"), module, state),
            order_by=_redacted(keywords.get("order_by"), module, state),
            foreign_keys=_redacted(keywords.get("foreign_keys"), module, state),
        )
        if any(
            value.category is RedactedExpressionCategory.UNKNOWN
            for value in (
                relationship.primaryjoin,
                relationship.secondaryjoin,
                relationship.order_by,
                relationship.foreign_keys,
            )
        ):
            row_unrepresentable = True
        if row_unrepresentable or unresolved_target:
            self._unknown_row(module, table, SqlAlchemyRowKind.RELATIONSHIP, call, state)
        if unresolved_target:
            symbol = f"{declaration.symbol}.{name}"
            state.diagnostics.append(
                diagnostic(
                    DiagnosticCode.SA_RELATION_TARGET,
                    domain="sqlalchemy",
                    path=module.path,
                    symbol=symbol,
                    line=_line(call),
                )
            )
            state.frontier.append(
                SqlAlchemyCoverageFrontier(
                    SqlAlchemyFrontierDirection.FAILURE,
                    SqlAlchemyFrontierKind.RELATION,
                    relationship.id,
                    SqlAlchemyFrontierReason.UNRESOLVED_REFERENCE,
                )
            )
        return SqlAlchemyRowEvidence(relationship, _span(call))

    def _inheritance_rows(
        self,
        declaration: _ClassDeclaration,
        table: SqlAlchemyTable,
        class_tables: dict[str, SqlAlchemyTable],
    ) -> list[SqlAlchemyRowEvidence]:
        rows: list[SqlAlchemyRowEvidence] = []
        for base in declaration.node.bases:
            parent = class_tables.get(_resolve_symbol(base, declaration.module) or "")
            if parent is None or parent.id == table.id:
                continue
            rows.append(
                SqlAlchemyRowEvidence(
                    SqlAlchemyInheritanceRow.create(
                        owner_id=table.id,
                        source=_location(declaration.module, declaration.node),
                        target=SqlAlchemyRelationTarget.internal_table(parent),
                    ),
                    _span(declaration.node),
                )
            )
        return rows

    def _association_rows(
        self,
        rows: tuple[SqlAlchemyRow, ...],
        tables: list[SqlAlchemyTable],
        module_table_ids: frozenset[str],
    ) -> tuple[SqlAlchemyAssociationTableRow, ...]:
        tables_by_id = {table.id: table for table in tables}
        values: list[SqlAlchemyAssociationTableRow] = []
        for row in rows:
            if (
                not isinstance(row, SqlAlchemyRelationshipRow)
                or row.secondary is None
                or row.secondary.id not in tables_by_id
                or row.secondary.id not in module_table_ids
                or row.secondary.id == row.owner_id
            ):
                continue
            source_table = tables_by_id[row.owner_id]
            secondary_table = tables_by_id[row.secondary.id]
            assert row.name is not None
            values.append(
                SqlAlchemyAssociationTableRow.create(
                    owner_id=secondary_table.id,
                    name=row.name,
                    source=row.source,
                    source_table=SqlAlchemyRelationTarget.internal_table(source_table),
                    relationship_target=row.target,
                    relationship_member_id=row.id,
                )
            )
        return tuple(values)

    def _column_rows(
        self,
        module: _ParsedModule,
        table: SqlAlchemyTable,
        call: ast.Call,
        *,
        attribute_name: str | None,
        annotation: ast.expr | None,
        table_column: bool,
        tables_by_id: dict[str, SqlAlchemyTable],
        state: _State,
    ) -> list[SqlAlchemyRowEvidence]:
        state.supported(module, call)
        allowed_keywords = {
            "nullable",
            "primary_key",
            "unique",
            "index",
            "default",
            "server_default",
            "onupdate",
            "server_onupdate",
        }
        keywords = _keyword_map(call)
        if (
            keywords is None
            or any(isinstance(argument, ast.Starred) for argument in call.args)
            or any(name not in allowed_keywords for name in keywords)
        ):
            self._unknown_row(module, table, SqlAlchemyRowKind.COLUMN, call, state)
            return []
        arguments = list(call.args)
        name = attribute_name
        if (
            arguments
            and isinstance(arguments[0], ast.Constant)
            and isinstance(arguments[0].value, str)
        ):
            explicit_name = _static_structural_string(arguments.pop(0))
            if explicit_name is None:
                self._unknown_row(module, table, SqlAlchemyRowKind.COLUMN, call, state)
                return []
            name = explicit_name
        if table_column and name is None:
            self._unknown_row(module, table, SqlAlchemyRowKind.COLUMN, call, state)
            return []
        if name is None:
            self._unknown_row(module, table, SqlAlchemyRowKind.COLUMN, call, state)
            return []

        type_node: ast.expr | None = None
        special_calls: list[tuple[str, ast.Call]] = []
        seen_special = False
        for argument in arguments:
            if isinstance(argument, ast.Call):
                symbol = _resolve_call(argument, module)
                if symbol in _COLUMN_SPECIALS:
                    special_calls.append((symbol, argument))
                    seen_special = True
                    continue
            if seen_special or type_node is not None:
                self._unknown_row(module, table, SqlAlchemyRowKind.COLUMN, call, state)
                return []
            type_node = argument
        if any(
            sum(candidate == symbol for candidate, _ in special_calls) > 1
            for symbol in ("sqlalchemy.Computed", "sqlalchemy.Identity")
        ):
            self._unknown_row(module, table, SqlAlchemyRowKind.COLUMN, call, state)
            return []
        if type_node is None and annotation is not None:
            type_node = _mapped_inner(annotation, module)
        type_descriptor = _type_descriptor(type_node, module, state)
        flags: dict[str, bool | None] = {}
        for flag in ("nullable", "primary_key", "unique", "index"):
            flags[flag] = _static_bool(keywords[flag]) if flag in keywords else None
            if flag in keywords and flags[flag] is None:
                self._unknown_row(module, table, SqlAlchemyRowKind.COLUMN, call, state)
                return []
        source = _location(module, call)
        column = SqlAlchemyColumnRow.create(
            owner_id=table.id,
            name=name,
            source=source,
            type=type_descriptor,
            nullable=flags["nullable"],
            primary_key=flags["primary_key"],
            unique=flags["unique"],
            index=flags["index"],
            default=_redacted(keywords.get("default"), module, state),
            server_default=_redacted(keywords.get("server_default"), module, state),
            onupdate=_redacted(keywords.get("onupdate"), module, state),
            server_onupdate=_redacted(keywords.get("server_onupdate"), module, state),
            computed=_special_redaction(special_calls, "sqlalchemy.Computed", module, state),
            identity=_special_redaction(special_calls, "sqlalchemy.Identity", module, state),
        )
        if column.type.category is SqlAlchemyTypeCategory.UNKNOWN or any(
            value.category is RedactedExpressionCategory.UNKNOWN
            for value in (
                column.type.parameters,
                column.default,
                column.server_default,
                column.onupdate,
                column.server_onupdate,
                column.computed,
                column.identity,
            )
        ):
            self._unknown_row(module, table, SqlAlchemyRowKind.COLUMN, call, state)
        span = _span(call)
        rows: list[SqlAlchemyRowEvidence] = [SqlAlchemyRowEvidence(column, span)]
        if flags["primary_key"] is True:
            rows.append(
                SqlAlchemyRowEvidence(
                    SqlAlchemyPrimaryKeyRow.create(
                        owner_id=table.id,
                        name=None,
                        source=source,
                        columns=(name,),
                    ),
                    span,
                )
            )
        if flags["unique"] is True:
            rows.append(
                SqlAlchemyRowEvidence(
                    SqlAlchemyUniqueRow.create(
                        owner_id=table.id,
                        name=None,
                        source=source,
                        columns=(name,),
                    ),
                    span,
                )
            )
        if flags["index"] is True:
            rows.append(
                SqlAlchemyRowEvidence(
                    SqlAlchemyIndexRow.create(
                        owner_id=table.id,
                        name=None,
                        source=source,
                        unique=None,
                        terms=(SqlAlchemyIndexTerm.column(name),),
                    ),
                    span,
                )
            )
        for symbol, special in special_calls:
            state.consumed_calls.add(id(special))
            if symbol != "sqlalchemy.ForeignKey":
                continue
            foreign_key = self._inline_foreign_key(
                module,
                table,
                special,
                name,
                source,
                tables_by_id,
                state,
            )
            if foreign_key is not None:
                rows.append(SqlAlchemyRowEvidence(foreign_key, span))
        return rows

    def _constraint_rows(
        self,
        module: _ParsedModule,
        table: SqlAlchemyTable,
        call: ast.Call,
        known_columns: dict[str, str | None],
        tables_by_id: dict[str, SqlAlchemyTable],
        state: _State,
    ) -> list[SqlAlchemyRowEvidence]:
        symbol = _resolve_call(call, module)
        constraint_kind = {
            "sqlalchemy.PrimaryKeyConstraint": SqlAlchemyRowKind.PRIMARY_KEY,
            "sqlalchemy.UniqueConstraint": SqlAlchemyRowKind.UNIQUE,
            "sqlalchemy.CheckConstraint": SqlAlchemyRowKind.CHECK,
            "sqlalchemy.Index": SqlAlchemyRowKind.INDEX,
            "sqlalchemy.ForeignKeyConstraint": SqlAlchemyRowKind.FOREIGN_KEY,
        }.get(symbol or "", SqlAlchemyRowKind.CHECK)
        state.supported(module, call)
        keywords = _keyword_map(call)
        if keywords is None or any(isinstance(argument, ast.Starred) for argument in call.args):
            self._unknown_row(module, table, constraint_kind, call, state)
            return []
        source = _location(module, call)
        span = _span(call)
        if symbol in {"sqlalchemy.PrimaryKeyConstraint", "sqlalchemy.UniqueConstraint"}:
            if set(keywords) - {"name"}:
                self._unknown_row(module, table, constraint_kind, call, state)
                return []
            name = _optional_static_name(keywords.get("name"))
            if "name" in keywords and name is _INVALID:
                self._unknown_row(module, table, constraint_kind, call, state)
                return []
            columns = tuple(_column_reference(argument, known_columns) for argument in call.args)
            if not columns or any(column is None for column in columns):
                self._unknown_row(module, table, constraint_kind, call, state)
                return []
            row: SqlAlchemyRow = (
                SqlAlchemyPrimaryKeyRow.create(
                    owner_id=table.id,
                    name=name if isinstance(name, str) else None,
                    source=source,
                    columns=tuple(column for column in columns if column is not None),
                )
                if symbol == "sqlalchemy.PrimaryKeyConstraint"
                else SqlAlchemyUniqueRow.create(
                    owner_id=table.id,
                    name=name if isinstance(name, str) else None,
                    source=source,
                    columns=tuple(column for column in columns if column is not None),
                )
            )
            return [SqlAlchemyRowEvidence(row, span)]
        if symbol == "sqlalchemy.CheckConstraint":
            if len(call.args) != 1 or set(keywords) - {"name"}:
                self._unknown_row(module, table, SqlAlchemyRowKind.CHECK, call, state)
                return []
            name = _optional_static_name(keywords.get("name"))
            if "name" in keywords and name is _INVALID:
                self._unknown_row(module, table, SqlAlchemyRowKind.CHECK, call, state)
                return []
            expression = _redacted(call.args[0], module, state)
            if expression.category not in {
                RedactedExpressionCategory.SQL_EXPRESSION,
                RedactedExpressionCategory.LITERAL,
                RedactedExpressionCategory.UNKNOWN,
            }:
                self._unknown_row(module, table, SqlAlchemyRowKind.CHECK, call, state)
                return []
            return [
                SqlAlchemyRowEvidence(
                    SqlAlchemyCheckRow.create(
                        owner_id=table.id,
                        name=name if isinstance(name, str) else None,
                        source=source,
                        expression=expression,
                    ),
                    span,
                )
            ]
        if symbol == "sqlalchemy.Index":
            if len(call.args) < 2 or set(keywords) - {"unique"}:
                self._unknown_row(module, table, SqlAlchemyRowKind.INDEX, call, state)
                return []
            name = _optional_static_name(call.args[0])
            if name is _INVALID:
                self._unknown_row(module, table, SqlAlchemyRowKind.INDEX, call, state)
                return []
            unique = _static_bool(keywords["unique"]) if "unique" in keywords else None
            if "unique" in keywords and unique is None:
                self._unknown_row(module, table, SqlAlchemyRowKind.INDEX, call, state)
                return []
            terms: list[SqlAlchemyIndexTerm] = []
            for argument in call.args[1:]:
                column = _column_reference(argument, known_columns)
                if (
                    column is None
                    and isinstance(argument, ast.Name)
                    and argument.id in known_columns
                ):
                    self._unknown_row(module, table, SqlAlchemyRowKind.INDEX, call, state)
                    return []
                terms.append(
                    SqlAlchemyIndexTerm.column(column)
                    if column is not None
                    else SqlAlchemyIndexTerm.redacted_expression(
                        _redacted(argument, module, state).category
                    )
                )
            return [
                SqlAlchemyRowEvidence(
                    SqlAlchemyIndexRow.create(
                        owner_id=table.id,
                        name=name if isinstance(name, str) else None,
                        source=source,
                        unique=unique,
                        terms=tuple(terms),
                    ),
                    span,
                )
            ]
        if symbol == "sqlalchemy.ForeignKeyConstraint":
            if len(call.args) != 2 or set(keywords) - {"name", "ondelete", "onupdate"}:
                self._unknown_row(module, table, SqlAlchemyRowKind.FOREIGN_KEY, call, state)
                return []
            local_values = _static_string_sequence(call.args[0])
            target_values = _static_string_sequence(call.args[1])
            if (
                local_values is None
                or target_values is None
                or len(local_values) != len(target_values)
            ):
                self._unknown_row(module, table, SqlAlchemyRowKind.FOREIGN_KEY, call, state)
                return []
            parsed_targets = [_foreign_key_target(value, tables_by_id) for value in target_values]
            if any(value is None for value in parsed_targets):
                self._unknown_row(module, table, SqlAlchemyRowKind.FOREIGN_KEY, call, state)
                return []
            targets = [value for value in parsed_targets if value is not None]
            first_target = targets[0][0]
            if any(target != first_target for target, _ in targets):
                self._unknown_row(module, table, SqlAlchemyRowKind.FOREIGN_KEY, call, state)
                return []
            name = _optional_static_name(keywords.get("name"))
            if "name" in keywords and name is _INVALID:
                self._unknown_row(module, table, SqlAlchemyRowKind.FOREIGN_KEY, call, state)
                return []
            return [
                SqlAlchemyRowEvidence(
                    SqlAlchemyForeignKeyRow.create(
                        owner_id=table.id,
                        name=name if isinstance(name, str) else None,
                        source=source,
                        local_columns=local_values,
                        target=first_target,
                        target_columns=tuple(column for _, column in targets),
                        ondelete=_redacted(keywords.get("ondelete"), module, state),
                        onupdate=_redacted(keywords.get("onupdate"), module, state),
                    ),
                    span,
                )
            ]
        self._unknown_row(module, table, constraint_kind, call, state)
        return []

    def _inline_foreign_key(
        self,
        module: _ParsedModule,
        table: SqlAlchemyTable,
        call: ast.Call,
        column_name: str,
        source: SqlAlchemySourceLocation,
        tables_by_id: dict[str, SqlAlchemyTable],
        state: _State,
    ) -> SqlAlchemyForeignKeyRow | None:
        keywords = _keyword_map(call)
        if (
            keywords is None
            or any(isinstance(argument, ast.Starred) for argument in call.args)
            or len(call.args) != 1
            or set(keywords) - {"name", "ondelete", "onupdate"}
            or not isinstance(call.args[0], ast.Constant)
            or not isinstance(call.args[0].value, str)
        ):
            self._unknown_row(module, table, SqlAlchemyRowKind.FOREIGN_KEY, call, state)
            return None
        target_value = _foreign_key_target(call.args[0].value, tables_by_id)
        if target_value is None:
            self._unknown_row(module, table, SqlAlchemyRowKind.FOREIGN_KEY, call, state)
            return None
        target, target_column = target_value
        name = _optional_static_name(keywords.get("name"))
        if "name" in keywords and name is _INVALID:
            self._unknown_row(module, table, SqlAlchemyRowKind.FOREIGN_KEY, call, state)
            return None
        return SqlAlchemyForeignKeyRow.create(
            owner_id=table.id,
            name=name if isinstance(name, str) else None,
            source=source,
            local_columns=(column_name,),
            target=target,
            target_columns=(target_column,),
            ondelete=_redacted(keywords.get("ondelete"), module, state),
            onupdate=_redacted(keywords.get("onupdate"), module, state),
        )

    def _relations(
        self,
        rows: tuple[SqlAlchemyRow, ...],
        tables: list[SqlAlchemyTable],
    ) -> tuple[SqlAlchemyRelation, ...]:
        tables_by_id = {table.id: table for table in tables}
        relations: list[SqlAlchemyRelation] = []
        for row in rows:
            kind: SqlAlchemyRelationKind
            source_id = row.owner_id
            target: SqlAlchemyRelationTarget
            via_member_id: str | None
            role: str | None
            if isinstance(row, SqlAlchemyForeignKeyRow):
                kind = SqlAlchemyRelationKind.FOREIGN_KEY
                target = row.target
                via_member_id = row.id
                role = None
            elif isinstance(row, SqlAlchemyRelationshipRow):
                kind = SqlAlchemyRelationKind.RELATIONSHIP
                target = row.target
                via_member_id = row.id
                role = row.name
            elif isinstance(row, SqlAlchemyInheritanceRow):
                kind = SqlAlchemyRelationKind.INHERITANCE
                target = row.target
                via_member_id = None
                role = None
            elif isinstance(row, SqlAlchemyAssociationTableRow):
                kind = SqlAlchemyRelationKind.ASSOCIATION
                assert row.source_table.id is not None
                source_id = row.source_table.id
                target = SqlAlchemyRelationTarget.internal_table(tables_by_id[row.owner_id])
                via_member_id = row.id
                role = row.name
            else:
                continue
            if target.resolution is not SqlAlchemyTargetResolution.INTERNAL:
                continue
            relations.append(
                SqlAlchemyRelation.create(
                    kind=kind,
                    source_id=source_id,
                    target=target,
                    via_member_id=via_member_id,
                    role=role,
                    source=row.source,
                )
            )
        return tuple(relations)

    def _unknown_table(self, declaration: _ClassDeclaration, state: _State) -> None:
        _consume_construction_calls(declaration.module, declaration.node, state)
        state.unknown(
            module=declaration.module,
            code=DiagnosticCode.SA_TABLE_IDENTITY,
            symbol=declaration.symbol,
            line=_line(declaration.node),
            kind=SqlAlchemyFrontierKind.TABLE,
        )

    def _unknown_table_call(
        self,
        module: _ParsedModule,
        call: ast.Call,
        symbol: str,
        state: _State,
    ) -> None:
        _consume_construction_calls(module, call, state)
        state.unknown(
            module=module,
            code=DiagnosticCode.SA_TABLE_IDENTITY,
            symbol=symbol,
            line=_line(call),
            kind=SqlAlchemyFrontierKind.TABLE,
        )

    def _unknown_row(
        self,
        module: _ParsedModule,
        table: SqlAlchemyTable,
        kind: SqlAlchemyRowKind,
        node: ast.AST,
        state: _State,
    ) -> None:
        _consume_construction_calls(module, node, state)
        span = _span(node)
        occurrence = sqlalchemy_occurrence_diagnostic_symbol(
            table.id,
            kind,
            module.path,
            span,
        )
        state.unknown_declarations += 1
        state.evidence_files.add(module.path)
        state.diagnostics.append(
            diagnostic(
                DiagnosticCode.SA_ROW_UNREPRESENTABLE,
                domain="sqlalchemy",
                path=module.path,
                symbol=occurrence,
                line=span.start_line,
            )
        )
        state.frontier.append(
            SqlAlchemyCoverageFrontier(
                SqlAlchemyFrontierDirection.FAILURE,
                SqlAlchemyFrontierKind.ROW,
                occurrence,
                SqlAlchemyFrontierReason.UNSUPPORTED_PATTERN,
            )
        )


def _failed_source(value: PythonSourceFailure) -> SqlAlchemyFailedSource:
    stage = {
        PythonSourceStage.READ: SqlAlchemyFailedStage.READ,
        PythonSourceStage.PATH_SAFETY: SqlAlchemyFailedStage.PATH_SAFETY,
        PythonSourceStage.MODULE_IDENTITY: SqlAlchemyFailedStage.MODULE_IDENTITY,
        PythonSourceStage.MODULE_COLLISION: SqlAlchemyFailedStage.MODULE_COLLISION,
    }[value.stage]
    code = {
        PythonSourceStage.READ: DiagnosticCode.SA_READ,
        PythonSourceStage.PATH_SAFETY: DiagnosticCode.SA_READ,
        PythonSourceStage.MODULE_IDENTITY: DiagnosticCode.SA_MODULE_IDENTITY,
        PythonSourceStage.MODULE_COLLISION: DiagnosticCode.SA_MODULE_COLLISION,
    }[value.stage]
    return SqlAlchemyFailedSource(value.path.as_posix(), stage, code)


def _bind_module_statement(
    module: _ParsedModule,
    statement: ast.AST,
    *,
    ambiguous: bool = False,
    binding_owner: str | None = None,
) -> None:
    owner = binding_owner or module.module
    if isinstance(statement, ast.Import):
        for alias in statement.names:
            local = alias.asname or alias.name.split(".", 1)[0]
            origin = alias.name if alias.asname else alias.name.split(".", 1)[0]
            normalized_origin = _normalize_symbol(origin)
            _bind(
                module.bindings,
                module.ambiguous_bindings,
                local,
                normalized_origin,
                ambiguous=ambiguous,
            )
            if binding_owner is None:
                _record_import_alias_provenance(
                    module,
                    local,
                    normalized_origin,
                    candidate=False,
                    ambiguous=ambiguous,
                    statement=statement,
                )
    elif isinstance(statement, ast.ImportFrom):
        if any(alias.name == "*" for alias in statement.names):
            module.star_import = True
            import_origin = _import_from_origin(module, statement)
            if import_origin is not None:
                module.star_import_origins.add(_normalize_symbol(import_origin))
            _invalidate_star_import(module)
            return
        import_origin = _import_from_origin(module, statement)
        if import_origin is None:
            return
        for alias in statement.names:
            local = alias.asname or alias.name
            normalized_origin = _normalize_symbol(f"{import_origin}.{alias.name}")
            _bind(
                module.bindings,
                module.ambiguous_bindings,
                local,
                normalized_origin,
                ambiguous=ambiguous,
            )
            if binding_owner is None:
                _record_import_alias_provenance(
                    module,
                    local,
                    normalized_origin,
                    candidate=True,
                    ambiguous=ambiguous,
                    statement=statement,
                )
    elif isinstance(statement, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        if binding_owner is None and not ambiguous:
            _clear_import_alias_provenance(module, statement.name, statement)
        _bind(
            module.bindings,
            module.ambiguous_bindings,
            statement.name,
            f"{owner}.{statement.name}",
            ambiguous=ambiguous,
        )
    elif isinstance(statement, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
        if isinstance(statement, ast.AnnAssign) and statement.value is None:
            return
        targets = statement.targets if isinstance(statement, ast.Assign) else (statement.target,)
        if binding_owner is None:
            for target in targets:
                _invalidate_attribute_target(module, target)
        names = _assignment_names(statement)
        if binding_owner is None:
            preserved = _alias_preserving_assignment_provenance(module, statement)
            if not ambiguous:
                for name in names:
                    _clear_import_alias_provenance(module, name, statement)
            if preserved is not None and not ambiguous:
                local, aliases, candidates = preserved
                symbol = f"{module.module}.{local}"
                if aliases:
                    module.imported_module_aliases[symbol] = aliases
                if candidates:
                    module.imported_module_alias_candidates[symbol] = candidates
                events = module.import_alias_events.setdefault(symbol, [])
                position = _node_position(statement)
                events.extend(
                    (position, origin) for origin in sorted((*aliases, *candidates), key=_utf8)
                )
            elif preserved is not None:
                local, aliases, candidates = preserved
                for origin in aliases:
                    _record_import_alias_provenance(
                        module,
                        local,
                        origin,
                        candidate=False,
                        ambiguous=True,
                        statement=statement,
                    )
                for origin in candidates:
                    _record_import_alias_provenance(
                        module,
                        local,
                        origin,
                        candidate=True,
                        ambiguous=True,
                        statement=statement,
                    )
        for name in names:
            _bind(
                module.bindings,
                module.ambiguous_bindings,
                name,
                f"{owner}.{name}",
                ambiguous=ambiguous,
            )
    elif isinstance(statement, ast.TypeAlias):
        for name in _target_names(statement.name):
            if binding_owner is None and not ambiguous:
                _clear_import_alias_provenance(module, name, statement)
            _bind(
                module.bindings,
                module.ambiguous_bindings,
                name,
                f"{owner}.{name}",
                ambiguous=ambiguous,
            )
    elif isinstance(statement, (ast.For, ast.AsyncFor)):
        if binding_owner is None:
            _invalidate_attribute_target(module, statement.target)
        _bind_target(module, statement.target, ambiguous=True, binding_owner=owner)
    elif isinstance(statement, (ast.With, ast.AsyncWith)):
        for item in statement.items:
            if item.optional_vars is not None:
                if binding_owner is None:
                    _invalidate_attribute_target(module, item.optional_vars)
                _bind_target(module, item.optional_vars, ambiguous=True, binding_owner=owner)
    elif isinstance(statement, ast.ExceptHandler):
        if statement.name is not None:
            _bind_name(module, statement.name, ambiguous=True, binding_owner=owner)
    elif isinstance(statement, ast.Match):
        for case in statement.cases:
            for name in _pattern_binding_names(case.pattern):
                _bind_name(module, name, ambiguous=True, binding_owner=owner)
    elif isinstance(statement, ast.Delete):
        for target in statement.targets:
            if binding_owner is None:
                _invalidate_attribute_target(module, target)
                if not ambiguous:
                    for name in _target_names(target):
                        _clear_import_alias_provenance(module, name, statement)
            _bind_target(module, target, ambiguous=True, binding_owner=owner)


def _record_import_alias_provenance(
    module: _ParsedModule,
    local: str,
    origin: str,
    *,
    candidate: bool,
    ambiguous: bool,
    statement: ast.AST,
) -> None:
    symbol = f"{module.module}.{local}"
    position = _node_position(statement)
    definite_position = module.import_alias_definite_positions.get(symbol)
    if ambiguous and definite_position is not None and position < definite_position:
        return
    if not ambiguous:
        module.imported_module_aliases.pop(symbol, None)
        module.imported_module_alias_candidates.pop(symbol, None)
        module.import_alias_definite_positions[symbol] = position
        module.import_alias_events.setdefault(symbol, []).append((position, None))
    target = (
        module.imported_module_alias_candidates if candidate else module.imported_module_aliases
    )
    target.setdefault(symbol, set()).add(origin)
    module.import_alias_events.setdefault(symbol, []).append((position, origin))


def _clear_import_alias_provenance(
    module: _ParsedModule,
    local: str,
    statement: ast.AST,
) -> None:
    symbol = f"{module.module}.{local}"
    module.imported_module_aliases.pop(symbol, None)
    module.imported_module_alias_candidates.pop(symbol, None)
    position = _node_position(statement)
    module.import_alias_definite_positions[symbol] = position
    module.import_alias_events.setdefault(symbol, []).append((position, None))


def _alias_preserving_assignment_provenance(
    module: _ParsedModule,
    statement: ast.Assign | ast.AnnAssign | ast.AugAssign | ast.NamedExpr,
) -> tuple[str, set[str], set[str]] | None:
    if isinstance(statement, ast.Assign):
        if len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
            return None
        target = statement.targets[0]
    elif isinstance(statement, (ast.AnnAssign, ast.NamedExpr)):
        if not isinstance(statement.target, ast.Name):
            return None
        target = statement.target
    else:
        return None
    if isinstance(statement.value, ast.Attribute):
        origin = _resolve_symbol(statement.value, module)
        if not _proven_module_origin(module, origin):
            return None
        assert origin is not None
        if origin in module.repository_modules and _module_import_precedes(
            module, origin, statement
        ):
            return target.id, {origin}, set()
        return target.id, set(), {origin}
    if not isinstance(statement.value, ast.Name):
        return None

    source = f"{module.module}.{statement.value.id}"
    aliases = set(module.imported_module_aliases.get(source, ()))
    candidates = set(module.imported_module_alias_candidates.get(source, ()))
    if not aliases and not candidates:
        return None
    return target.id, aliases, candidates


def _node_position(value: ast.AST) -> tuple[int, int]:
    return (
        getattr(value, "lineno", -1),
        getattr(value, "col_offset", -1),
    )


def _module_import_precedes(
    module: _ParsedModule,
    origin: str,
    statement: ast.AST,
) -> bool:
    position = _node_position(statement)
    return any(
        _normalize_symbol(alias.name) == origin and _node_position(candidate) < position
        for top_level in module.tree.body
        for candidate in (top_level, *_nested_module_scope_writes(top_level))
        if isinstance(candidate, ast.Import)
        for alias in candidate.names
    )


def _module_alias_origins_before(
    module: _ParsedModule,
    name: str,
    statement: ast.AST,
) -> set[str]:
    symbol = f"{module.module}.{name}"
    events = module.import_alias_events.get(symbol)
    if not events:
        fallback_origins = set(module.ambiguous_bindings.get(name, ()))
        current = module.bindings.get(name)
        if current is not None:
            fallback_origins.add(current)
        return fallback_origins
    origins: set[str] = set()
    statement_position = _node_position(statement)
    ordered_events = sorted(
        enumerate(events),
        key=lambda item: (item[1][0], item[0]),
    )
    for _, (position, origin) in ordered_events:
        if position >= statement_position:
            break
        if origin is None:
            origins.clear()
        else:
            origins.add(origin)
    return origins


def _attribute_root_and_suffix(value: ast.expr) -> tuple[str, tuple[str, ...]] | None:
    suffix: list[str] = []
    current = value
    while isinstance(current, ast.Attribute):
        suffix.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    return current.id, tuple(reversed(suffix))


def _module_object_origins_before(
    module: _ParsedModule,
    value: ast.expr,
    statement: ast.AST,
) -> set[str]:
    root = _attribute_root_and_suffix(value)
    if root is None:
        return set()
    name, suffix = root
    result: set[str] = set()
    for candidate in _module_alias_origins_before(module, name, statement):
        if suffix:
            candidate = _normalize_symbol(f"{candidate}.{'.'.join(suffix)}")
        result.update(
            origin
            for origin in _module_object_path_candidates(module, candidate)
            if _external_sqlalchemy_module_origin(module, origin)
            or origin in module.repository_module_origins
        )
    return result


def _module_object_path_candidates(module: _ParsedModule, origin: str) -> set[str]:
    candidates = {origin}
    step_limit = max(
        1,
        len(module.repository_bindings) + len(module.repository_module_aliases) + 1,
    )
    for _ in range(step_limit):
        additions: set[str] = set()
        for candidate in candidates:
            resolved = module.repository_bindings.get(candidate)
            if resolved is not None:
                additions.add(resolved)
            aliases = module.repository_module_aliases.get(candidate, ())
            additions.update(aliases)
            additions.update(
                possible
                for possible in module.repository_ambiguous_bindings.get(candidate, ())
                if possible in aliases
            )
            for prefix, prefix_origins in module.repository_module_aliases.items():
                if not candidate.startswith(f"{prefix}."):
                    continue
                remainder = candidate[len(prefix) :]
                additions.update(
                    _normalize_symbol(f"{prefix_origin}{remainder}")
                    for prefix_origin in prefix_origins
                )
        if additions.issubset(candidates):
            break
        candidates.update(additions)
    return candidates


def _refresh_resolved_module_alias_provenance(modules: list[_ParsedModule]) -> None:
    statements_by_module = [
        (
            module,
            tuple(
                sorted(
                    (
                        candidate
                        for statement in module.tree.body
                        for candidate in (statement, *_nested_module_scope_writes(statement))
                    ),
                    key=_node_position,
                )
            ),
        )
        for module in modules
    ]
    assignment_count = sum(
        _static_module_alias_assignment(statement) is not None
        for _, statements in statements_by_module
        for statement in statements
    )
    for _ in range(max(1, assignment_count + 1)):
        changed = False
        for module, statements in statements_by_module:
            for statement in statements:
                assignment = _static_module_alias_assignment(statement)
                if assignment is None:
                    continue
                names, value = assignment
                origins = _module_object_origins_before(module, value, statement)
                if not origins:
                    continue
                position = _node_position(statement)
                for name in names:
                    symbol = f"{module.module}.{name}"
                    events = module.import_alias_events.setdefault(symbol, [])
                    additions = [
                        (position, origin)
                        for origin in sorted(origins, key=_utf8)
                        if (position, origin) not in events
                    ]
                    if additions:
                        events.extend(additions)
                        changed = True
                    definite_position = module.import_alias_definite_positions.get(symbol)
                    if definite_position is None or definite_position <= position:
                        candidates = module.imported_module_alias_candidates.setdefault(
                            symbol, set()
                        )
                        new_origins = origins - candidates
                        if new_origins:
                            candidates.update(new_origins)
                            changed = True
        repository_module_aliases = {
            symbol: frozenset(origins)
            for symbol, origins in _resolved_imported_module_aliases(modules).items()
        }
        aliases_changed = any(
            module.repository_module_aliases != repository_module_aliases for module in modules
        )
        for module in modules:
            module.repository_module_aliases = repository_module_aliases
        if not changed and not aliases_changed:
            break

    for module, statements in statements_by_module:
        for statement in statements:
            for target in _attribute_write_targets(statement):
                _record_resolved_attribute_mutation(module, target, statement)


def _record_resolved_attribute_mutation(
    module: _ParsedModule,
    target: ast.expr,
    statement: ast.AST,
) -> None:
    if isinstance(target, ast.Attribute):
        module.attribute_mutations.update(
            _normalize_symbol(f"{origin}.{target.attr}")
            for origin in _module_object_origins_before(module, target.value, statement)
        )
    elif isinstance(target, (ast.Tuple, ast.List)):
        for element in target.elts:
            _record_resolved_attribute_mutation(module, element, statement)
    elif isinstance(target, ast.Starred):
        _record_resolved_attribute_mutation(module, target.value, statement)


def _invalidate_attribute_target(
    module: _ParsedModule,
    target: ast.expr,
    *,
    resolution_scope: _ParsedModule | None = None,
) -> None:
    scope = resolution_scope or module
    if isinstance(target, ast.Attribute):
        resolved_base = _resolve_symbol(target.value, scope)
        resolved: str | None
        if _proven_module_origin(scope, resolved_base):
            assert resolved_base is not None
            resolved = _normalize_symbol(f"{resolved_base}.{target.attr}")
        else:
            resolved = _resolve_symbol(target, scope)
        if resolved is not None:
            module.attribute_mutations.add(resolved)
        ambiguous_bases = {
            origin
            for origin in _ambiguous_symbols(target.value, scope)
            if _proven_module_origin(scope, origin)
        }
        if ambiguous_bases:
            module.attribute_mutations.update(
                _normalize_symbol(f"{origin}.{target.attr}") for origin in ambiguous_bases
            )
        else:
            module.attribute_mutations.update(_ambiguous_symbols(target, scope))
    elif isinstance(target, (ast.Tuple, ast.List)):
        for element in target.elts:
            _invalidate_attribute_target(module, element, resolution_scope=scope)
    elif isinstance(target, ast.Starred):
        _invalidate_attribute_target(module, target.value, resolution_scope=scope)


def _invalidate_executed_class_body_mutations(
    module: _ParsedModule,
    node: ast.ClassDef,
    symbol: str,
    *,
    ambiguous_execution: bool = False,
    apply_global_bindings: bool = True,
) -> None:
    scopes = _class_mutation_scope_modules(
        _ClassDeclaration(module, node, symbol),
        ambiguous_execution=ambiguous_execution,
        apply_global_bindings=apply_global_bindings,
    )
    for statement in node.body:
        for write in (statement, *_nested_module_scope_writes(statement)):
            scope = scopes[id(write)]
            for target in _attribute_write_targets(write):
                _invalidate_attribute_target(module, target, resolution_scope=scope)
            if isinstance(write, ast.ClassDef):
                _invalidate_executed_class_body_mutations(
                    module,
                    write,
                    f"{symbol}.{write.name}",
                    ambiguous_execution=(ambiguous_execution or write is not statement),
                    apply_global_bindings=apply_global_bindings,
                )


def _attribute_write_targets(value: ast.AST) -> tuple[ast.expr, ...]:
    if isinstance(value, ast.Assign):
        return tuple(value.targets)
    if isinstance(value, ast.AnnAssign):
        return (value.target,) if value.value is not None else ()
    if isinstance(value, (ast.AugAssign, ast.NamedExpr)):
        return (value.target,)
    if isinstance(value, (ast.For, ast.AsyncFor)):
        return (value.target,)
    if isinstance(value, (ast.With, ast.AsyncWith)):
        return tuple(item.optional_vars for item in value.items if item.optional_vars is not None)
    if isinstance(value, ast.Delete):
        return tuple(value.targets)
    return ()


def _class_mutation_scope_modules(
    declaration: _ClassDeclaration,
    *,
    ambiguous_execution: bool = False,
    apply_global_bindings: bool = True,
) -> dict[int, _ParsedModule]:
    scope = _copy_parsed_module(declaration.module)
    result: dict[int, _ParsedModule] = {}
    global_names: set[str] = set()
    for statement in declaration.node.body:
        for write, nested in (
            (statement, False),
            *((candidate, True) for candidate in _nested_module_scope_writes(statement)),
        ):
            result[id(write)] = _copy_parsed_module(scope)
            if isinstance(write, ast.Global):
                global_names.update(write.names)
                continue
            ambiguous = ambiguous_execution or nested
            before = _copy_parsed_module(scope)
            if not ambiguous:
                for name in _definite_class_binding_names(write):
                    if name not in global_names:
                        scope.bindings.pop(name, None)
                        scope.ambiguous_bindings.pop(name, None)
            _bind_module_statement(
                scope,
                write,
                ambiguous=ambiguous,
                binding_owner=declaration.symbol,
            )
            bound_globals = set(_statement_binding_names(write)) & global_names
            if bound_globals:
                _apply_class_global_write(
                    declaration.module,
                    scope,
                    before,
                    write,
                    bound_globals,
                    ambiguous=ambiguous,
                    apply_outer=apply_global_bindings,
                )
            proven_module = _proven_sqlalchemy_module_assignment(before, write)
            if proven_module is not None:
                names, origin = proven_module
                for name in names:
                    if ambiguous:
                        scope.bindings[name] = None
                        scope.ambiguous_bindings.setdefault(name, set()).add(origin)
                    else:
                        scope.bindings[name] = origin
                        scope.ambiguous_bindings.pop(name, None)
                continue
            possible_module = _possible_sqlalchemy_module_assignment(before, write)
            if possible_module is not None:
                names, origins = possible_module
                for name in names:
                    scope.bindings[name] = None
                    scope.ambiguous_bindings.setdefault(name, set()).update(origins)
    return result


def _apply_class_global_write(
    module: _ParsedModule,
    scope: _ParsedModule,
    before: _ParsedModule,
    statement: ast.AST,
    names: set[str],
    *,
    ambiguous: bool,
    apply_outer: bool,
) -> None:
    assignment = _static_module_alias_assignment(statement)
    module_names: tuple[str, ...] = ()
    module_origins: set[str] = set()
    if assignment is not None:
        assignment_names, value = assignment
        module_names = tuple(name for name in assignment_names if name in names)
        module_origins = _module_object_origins_before(before, value, statement)

    if apply_outer:
        outer_result = _copy_parsed_module(module)
        _bind_module_statement(outer_result, statement, ambiguous=ambiguous)
        _materialize_global_module_aliases(
            outer_result,
            module_names,
            module_origins,
            statement,
            ambiguous=ambiguous,
            update_bindings=True,
        )
        for name in names:
            _copy_module_binding(name, outer_result, module)
    else:
        _materialize_global_module_aliases(
            module,
            module_names,
            module_origins,
            statement,
            ambiguous=ambiguous,
            update_bindings=False,
        )

    scope_result = _copy_parsed_module(before)
    if not ambiguous:
        for name in names:
            scope_result.bindings.pop(name, None)
            scope_result.ambiguous_bindings.pop(name, None)
    _bind_module_statement(scope_result, statement, ambiguous=ambiguous)
    for name in names:
        _copy_module_binding(name, scope_result, scope)


def _materialize_global_module_aliases(
    module: _ParsedModule,
    names: tuple[str, ...],
    origins: set[str],
    statement: ast.AST,
    *,
    ambiguous: bool,
    update_bindings: bool,
) -> None:
    if not names or not origins:
        return
    position = _node_position(statement)
    definite = not ambiguous and len(origins) == 1
    for name in names:
        if update_bindings:
            if definite:
                module.bindings[name] = next(iter(origins))
                module.ambiguous_bindings.pop(name, None)
            else:
                module.bindings[name] = None
                module.ambiguous_bindings.setdefault(name, set()).update(origins)
        symbol = f"{module.module}.{name}"
        events = module.import_alias_events.setdefault(symbol, [])
        events.extend(
            (position, origin)
            for origin in sorted(origins, key=_utf8)
            if (position, origin) not in events
        )
        definite_position = module.import_alias_definite_positions.get(symbol)
        if definite_position is None or definite_position <= position:
            module.imported_module_alias_candidates.setdefault(symbol, set()).update(origins)


def _copy_module_binding(
    name: str,
    source: _ParsedModule,
    target: _ParsedModule,
) -> None:
    if name in source.bindings:
        target.bindings[name] = source.bindings[name]
    else:
        target.bindings.pop(name, None)
    if name in source.ambiguous_bindings:
        target.ambiguous_bindings[name] = set(source.ambiguous_bindings[name])
    else:
        target.ambiguous_bindings.pop(name, None)

    symbol = f"{target.module}.{name}"
    for source_values, target_values in (
        (source.imported_module_aliases, target.imported_module_aliases),
        (source.imported_module_alias_candidates, target.imported_module_alias_candidates),
    ):
        if symbol in source_values:
            target_values[symbol] = set(source_values[symbol])
        else:
            target_values.pop(symbol, None)
    if symbol in source.import_alias_definite_positions:
        target.import_alias_definite_positions[symbol] = source.import_alias_definite_positions[
            symbol
        ]
    else:
        target.import_alias_definite_positions.pop(symbol, None)
    if symbol in source.import_alias_events:
        target.import_alias_events[symbol] = list(source.import_alias_events[symbol])
    else:
        target.import_alias_events.pop(symbol, None)


def _proven_sqlalchemy_module_assignment(
    module: _ParsedModule,
    statement: ast.AST,
) -> tuple[tuple[str, ...], str] | None:
    assignment = _static_module_alias_assignment(statement)
    if assignment is None:
        return None
    names, value = assignment
    origins = _module_object_origins_before(module, value, statement)
    if len(origins) != 1:
        return None
    return names, next(iter(origins))


def _static_module_alias_assignment(
    statement: ast.AST,
) -> tuple[tuple[str, ...], ast.expr] | None:
    if isinstance(statement, ast.Assign):
        if not statement.targets or not all(
            isinstance(target, ast.Name) for target in statement.targets
        ):
            return None
        names = tuple(target.id for target in statement.targets if isinstance(target, ast.Name))
        value = statement.value
    elif isinstance(statement, (ast.AnnAssign, ast.NamedExpr)):
        if not isinstance(statement.target, ast.Name) or statement.value is None:
            return None
        names = (statement.target.id,)
        value = statement.value
    else:
        return None
    if not isinstance(value, (ast.Name, ast.Attribute)):
        return None
    return names, value


def _possible_sqlalchemy_module_assignment(
    module: _ParsedModule,
    statement: ast.AST,
) -> tuple[tuple[str, ...], set[str]] | None:
    assignment = _static_module_alias_assignment(statement)
    if assignment is None:
        return None
    names, value = assignment
    origins = _module_object_origins_before(module, value, statement)
    if not origins:
        return None
    return names, origins


def _definite_class_binding_names(value: ast.AST) -> tuple[str, ...]:
    if isinstance(value, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        return (value.name,)
    if isinstance(value, ast.Import):
        return tuple(alias.asname or alias.name.split(".", 1)[0] for alias in value.names)
    if isinstance(value, ast.ImportFrom):
        return tuple(alias.asname or alias.name for alias in value.names if alias.name != "*")
    if isinstance(value, (ast.Assign, ast.AugAssign, ast.NamedExpr)):
        return _assignment_names(value)
    if isinstance(value, ast.AnnAssign):
        return _assignment_names(value) if value.value is not None else ()
    if isinstance(value, ast.TypeAlias):
        return _target_names(value.name)
    return ()


def _preview_repository_module_origins(
    modules: list[_ParsedModule],
    repository_modules: frozenset[str],
) -> frozenset[str]:
    previews: list[_ParsedModule] = []
    for module in modules:
        preview = _ParsedModule(
            module.module,
            module.path,
            module.tree,
            {},
            {},
            False,
            module.is_package,
            repository_modules=repository_modules,
        )
        for statement in preview.tree.body:
            _bind_module_statement(preview, statement)
            if isinstance(statement, ast.ClassDef):
                _invalidate_executed_class_body_mutations(
                    preview,
                    statement,
                    f"{preview.module}.{statement.name}",
                )
            for write in _nested_module_scope_writes(statement):
                _bind_module_statement(preview, write, ambiguous=True)
                if isinstance(write, ast.ClassDef):
                    _invalidate_executed_class_body_mutations(
                        preview,
                        write,
                        f"{preview.module}.{write.name}",
                        ambiguous_execution=True,
                    )
        previews.append(preview)
    return frozenset(_repository_module_object_origins(previews))


def _repository_module_object_origins(modules: list[_ParsedModule]) -> set[str]:
    by_name = {module.module: module for module in modules}
    result: set[str] = set()
    for symbol in by_name:
        if "." not in symbol:
            result.add(symbol)
            continue
        owner_name, name = symbol.rsplit(".", 1)
        owner = by_name.get(owner_name)
        if owner is None:
            result.add(symbol)
            continue
        if not owner.is_package:
            continue
        if name not in owner.bindings:
            result.add(symbol)
            continue
        if symbol in owner.imported_module_alias_candidates.get(symbol, ()):
            result.add(symbol)
    return result


def _expand_imported_module_alias_mutations(modules: list[_ParsedModule]) -> set[str]:
    mutations = {symbol for module in modules for symbol in module.attribute_mutations}
    aliases = _resolved_imported_module_aliases(modules)

    expanded = set(mutations)
    for _ in range(len(aliases)):
        mutation_additions = {
            _normalize_symbol(f"{origin}{mutation[len(alias) :]}")
            for mutation in expanded
            for alias, origins in aliases.items()
            if mutation.startswith(f"{alias}.")
            for origin in origins
        }
        if mutation_additions.issubset(expanded):
            break
        expanded.update(mutation_additions)
    return expanded


def _resolved_imported_module_aliases(
    modules: list[_ParsedModule],
) -> dict[str, set[str]]:
    aliases: dict[str, set[str]] = {}
    candidates: dict[str, set[str]] = {}
    for module in modules:
        for symbol, origins in module.imported_module_aliases.items():
            aliases.setdefault(symbol, set()).update(origins)
        for symbol, origins in module.imported_module_alias_candidates.items():
            candidates.setdefault(symbol, set()).update(origins)

    by_name = {module.module: module for module in modules}
    repository_module_origins = {
        origin for module in modules for origin in module.repository_module_origins
    }
    repository_modules = set(by_name)
    module_origins = repository_module_origins | {
        symbol
        for symbol in _SQLALCHEMY_MODULE_SYMBOLS
        if not any(
            symbol == repository_module or symbol.startswith(f"{repository_module}.")
            for repository_module in repository_modules
        )
    }
    for _ in range(len(candidates)):
        alias_additions = {
            (symbol, origin)
            for symbol, origins in candidates.items()
            for origin in origins
            if origin in module_origins or origin in aliases
        }
        if all(origin in aliases.get(symbol, ()) for symbol, origin in alias_additions):
            break
        for symbol, origin in alias_additions:
            aliases.setdefault(symbol, set()).add(origin)
    for _ in range(len(aliases)):
        transitive_additions = {
            (symbol, transitive)
            for symbol, origins in aliases.items()
            for origin in origins
            for transitive in aliases.get(origin, ())
        }
        if all(
            transitive in aliases.get(symbol, ()) for symbol, transitive in transitive_additions
        ):
            break
        for symbol, transitive in transitive_additions:
            aliases.setdefault(symbol, set()).add(transitive)
    return aliases


def _nested_module_scope_writes(value: ast.AST) -> tuple[ast.AST, ...]:
    if isinstance(value, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        return ()
    result: list[ast.AST] = []
    for child in ast.iter_child_nodes(value):
        if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            result.append(child)
            continue
        if isinstance(
            child,
            (
                ast.Import,
                ast.ImportFrom,
                ast.Assign,
                ast.AnnAssign,
                ast.AugAssign,
                ast.NamedExpr,
                ast.For,
                ast.AsyncFor,
                ast.With,
                ast.AsyncWith,
                ast.ExceptHandler,
                ast.Match,
                ast.Delete,
                ast.Global,
                ast.TypeAlias,
            ),
        ):
            result.append(child)
        result.extend(_nested_module_scope_writes(child))
    return tuple(result)


def _class_scope_modules(
    declaration: _ClassDeclaration,
) -> tuple[dict[int, _ParsedModule], dict[int, frozenset[str]]]:
    scope = _copy_parsed_module(declaration.module)
    result: dict[int, _ParsedModule] = {}
    global_result: dict[int, frozenset[str]] = {}
    global_names: set[str] = set()
    for statement in declaration.node.body:
        for write, nested in (
            (statement, False),
            *((candidate, True) for candidate in _nested_module_scope_writes(statement)),
        ):
            result[id(write)] = _copy_parsed_module(scope)
            global_result[id(write)] = frozenset(global_names)
            if isinstance(write, ast.Global):
                global_names.update(write.names)
                continue
            before = _copy_parsed_module(scope)
            _bind_module_statement(
                scope,
                write,
                ambiguous=nested,
                binding_owner=declaration.symbol,
            )
            bound_globals = set(_statement_binding_names(write)) & global_names
            if bound_globals:
                _apply_class_global_write(
                    declaration.module,
                    scope,
                    before,
                    write,
                    bound_globals,
                    ambiguous=nested,
                    apply_outer=False,
                )
    return result, global_result


def _copy_parsed_module(module: _ParsedModule) -> _ParsedModule:
    return _ParsedModule(
        module=module.module,
        path=module.path,
        tree=module.tree,
        bindings=dict(module.bindings),
        ambiguous_bindings={
            name: set(origins) for name, origins in module.ambiguous_bindings.items()
        },
        star_import=module.star_import,
        is_package=module.is_package,
        attribute_mutations=set(module.attribute_mutations),
        imported_module_aliases={
            symbol: set(origins) for symbol, origins in module.imported_module_aliases.items()
        },
        imported_module_alias_candidates={
            symbol: set(origins)
            for symbol, origins in module.imported_module_alias_candidates.items()
        },
        import_alias_definite_positions=dict(module.import_alias_definite_positions),
        import_alias_events={
            symbol: list(events) for symbol, events in module.import_alias_events.items()
        },
        star_import_origins=set(module.star_import_origins),
        repository_bindings=module.repository_bindings,
        repository_ambiguous_bindings=module.repository_ambiguous_bindings,
        repository_modules=module.repository_modules,
        repository_module_origins=module.repository_module_origins,
        repository_module_aliases=module.repository_module_aliases,
        repository_star_imports=module.repository_star_imports,
    )


def _class_shadowed_names(module: _ParsedModule, value: ast.ClassDef) -> frozenset[str]:
    names: set[str] = set()
    for statement in value.body:
        for candidate in _class_scope_write_names(statement):
            if _binding_is_sqlalchemy(module, candidate):
                names.add(candidate)
    return frozenset(names)


def _class_scope_write_names(value: ast.AST) -> tuple[str, ...]:
    if isinstance(value, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        return (value.name,)
    direct = _statement_binding_names(value)
    if direct:
        return direct + tuple(
            name
            for child in ast.iter_child_nodes(value)
            for name in _class_scope_write_names(child)
        )
    names: list[str] = []
    for child in ast.iter_child_nodes(value):
        if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            names.extend(_class_scope_write_names(child))
            continue
        names.extend(_class_scope_write_names(child))
    return tuple(names)


def _direct_binding_names(value: ast.AST) -> tuple[str, ...]:
    if isinstance(value, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        return (value.name,)
    return _statement_binding_names(value)


def _only_global_bindings(value: ast.AST, global_names: frozenset[str]) -> bool:
    names = _direct_binding_names(value)
    return bool(names) and all(name in global_names for name in names)


def _statement_binding_names(value: ast.AST) -> tuple[str, ...]:
    if isinstance(value, ast.Import):
        return tuple(alias.asname or alias.name.split(".", 1)[0] for alias in value.names)
    if isinstance(value, ast.ImportFrom):
        return tuple(alias.asname or alias.name for alias in value.names if alias.name != "*")
    if isinstance(value, ast.AnnAssign):
        return _assignment_names(value) if value.value is not None else ()
    if isinstance(value, (ast.Assign, ast.AugAssign, ast.NamedExpr)):
        return _assignment_names(value)
    if isinstance(value, ast.TypeAlias):
        return _target_names(value.name)
    if isinstance(value, (ast.For, ast.AsyncFor)):
        return _target_names(value.target)
    if isinstance(value, (ast.With, ast.AsyncWith)):
        return tuple(
            name
            for item in value.items
            if item.optional_vars is not None
            for name in _target_names(item.optional_vars)
        )
    if isinstance(value, ast.ExceptHandler):
        return (value.name,) if value.name is not None else ()
    if isinstance(value, ast.Match):
        return tuple(name for case in value.cases for name in _pattern_binding_names(case.pattern))
    if isinstance(value, ast.Delete):
        return tuple(name for target in value.targets for name in _target_names(target))
    return ()


def _target_names(value: ast.expr) -> tuple[str, ...]:
    if isinstance(value, ast.Name):
        return (value.id,)
    if isinstance(value, (ast.Tuple, ast.List)):
        return tuple(name for item in value.elts for name in _target_names(item))
    if isinstance(value, ast.Starred):
        return _target_names(value.value)
    return ()


def _expression_uses_shadowed(value: ast.expr, names: frozenset[str]) -> bool:
    if not names:
        return False
    return any(isinstance(node, ast.Name) and node.id in names for node in ast.walk(value))


def _shadowed_row_kind(
    value: ast.expr,
    module: _ParsedModule,
    names: frozenset[str],
) -> SqlAlchemyRowKind:
    for node in ast.walk(value):
        if not isinstance(node, ast.Name) or node.id not in names:
            continue
        origins = set(module.ambiguous_bindings.get(node.id, ()))
        origin = module.bindings.get(node.id)
        if origin is not None:
            origins.add(origin)
        if any(candidate.endswith(".relationship") for candidate in origins):
            return SqlAlchemyRowKind.RELATIONSHIP
    return SqlAlchemyRowKind.COLUMN


def _bind(
    bindings: dict[str, str | None],
    ambiguous_bindings: dict[str, set[str]],
    name: str,
    origin: str,
    *,
    ambiguous: bool = False,
) -> None:
    previous = bindings.get(name)
    if name in bindings:
        if previous is not None:
            ambiguous_bindings.setdefault(name, set()).add(previous)
        ambiguous_bindings.setdefault(name, set()).add(origin)
        bindings[name] = None
    else:
        bindings[name] = origin
    if ambiguous:
        ambiguous_bindings.setdefault(name, set()).add(origin)
        bindings[name] = None


def _invalidate_star_import(module: _ParsedModule) -> None:
    for name, origin in module.bindings.items():
        if origin is not None:
            module.ambiguous_bindings.setdefault(name, set()).add(origin)
        module.bindings[name] = None


def _binding_is_sqlalchemy(module: _ParsedModule, name: str) -> bool:
    origin = module.bindings.get(name)
    return _binding_origin_is_sqlalchemy(module, origin) or any(
        _binding_origin_is_sqlalchemy(module, candidate)
        for candidate in module.ambiguous_bindings.get(name, ())
    )


def _is_sqlalchemy_origin(origin: str | None) -> bool:
    return origin in _SQLALCHEMY_BINDING_SYMBOLS or origin in _TYPE_CATEGORIES


def _binding_origin_is_sqlalchemy(module: _ParsedModule, origin: str | None) -> bool:
    if not _is_sqlalchemy_origin(origin):
        return False
    assert origin is not None
    return not any(
        origin == repository_module or origin.startswith(f"{repository_module}.")
        for repository_module in module.repository_modules
    )


def _proven_module_origin(module: _ParsedModule, origin: str | None) -> bool:
    if origin in module.repository_modules:
        return True
    return _external_sqlalchemy_module_origin(module, origin)


def _external_sqlalchemy_module_origin(
    module: _ParsedModule,
    origin: str | None,
) -> bool:
    return origin in _SQLALCHEMY_MODULE_SYMBOLS and not any(
        origin == repository_module or origin.startswith(f"{repository_module}.")
        for repository_module in module.repository_modules
    )


def _resolve_repository_bindings(modules: list[_ParsedModule]) -> None:
    by_name = {module.module: module for module in modules}
    repository_modules = frozenset(by_name)
    repository_module_aliases = {
        symbol: frozenset(origins)
        for symbol, origins in _resolved_imported_module_aliases(modules).items()
    }
    repository_star_imports = {
        module.module: frozenset(module.star_import_origins)
        for module in modules
        if module.star_import
    }
    raw_bindings = {module.module: dict(module.bindings) for module in modules}
    raw_ambiguous = {
        module.module: {
            name: frozenset(origins) for name, origins in module.ambiguous_bindings.items()
        }
        for module in modules
    }
    canonical_bindings: dict[str, str | None] = {}
    canonical_ambiguous: dict[str, frozenset[str]] = {}
    attribute_mutations = {symbol for module in modules for symbol in module.attribute_mutations}
    for module in modules:
        names = set(raw_bindings[module.module]) | set(raw_ambiguous[module.module])
        for name in names:
            symbol = f"{module.module}.{name}"
            traversed: set[str] = set()
            resolved, ambiguous_origins = _resolve_repository_origin(
                symbol,
                by_name,
                raw_bindings,
                raw_ambiguous,
                set(),
                traversed,
            )
            if traversed.isdisjoint(attribute_mutations):
                canonical_bindings[symbol] = resolved
                if ambiguous_origins:
                    canonical_ambiguous[symbol] = frozenset(ambiguous_origins)
                continue
            mutation_origins = set(ambiguous_origins)
            if resolved is not None:
                mutation_origins.add(resolved)
            if not mutation_origins:
                mutation_origins.update(traversed & attribute_mutations)
            canonical_bindings[symbol] = None
            canonical_ambiguous[symbol] = frozenset(mutation_origins)

    for module in modules:
        names = set(module.bindings) | set(module.ambiguous_bindings)
        for name in names:
            symbol = f"{module.module}.{name}"
            module.bindings[name] = canonical_bindings[symbol]
            origins = canonical_ambiguous.get(symbol)
            if origins:
                module.ambiguous_bindings[name] = set(origins)
            else:
                module.ambiguous_bindings.pop(name, None)
        module.repository_bindings = canonical_bindings
        module.repository_ambiguous_bindings = canonical_ambiguous
        module.repository_modules = repository_modules
        module.repository_module_aliases = repository_module_aliases
        module.repository_star_imports = repository_star_imports
        module.attribute_mutations.update(attribute_mutations)


def _resolve_repository_origin(
    origin: str,
    modules: dict[str, _ParsedModule],
    bindings: dict[str, dict[str, str | None]],
    ambiguous_bindings: dict[str, dict[str, frozenset[str]]],
    seen: set[str],
    traversed: set[str],
) -> tuple[str | None, set[str]]:
    traversed.add(origin)
    if origin in seen:
        return None, {origin}
    if "." not in origin:
        return origin, set()
    owner, name = origin.rsplit(".", 1)
    target = modules.get(owner)
    if target is None:
        return origin, set()
    if name not in bindings[owner]:
        candidates = _star_import_candidates(target.star_import_origins, name)
        if candidates:
            return _resolve_ambiguous_repository_origins(
                candidates,
                modules,
                bindings,
                ambiguous_bindings,
                {*seen, origin},
                origin,
                traversed,
            )
        return origin, set()
    target_origin = bindings[owner][name]
    if target_origin is None:
        candidates = set(ambiguous_bindings[owner].get(name, ()))
        candidates.update(_star_import_candidates(target.star_import_origins, name))
        return _resolve_ambiguous_repository_origins(
            candidates,
            modules,
            bindings,
            ambiguous_bindings,
            {*seen, origin},
            origin,
            traversed,
        )
    if target_origin == origin:
        if (
            target.is_package
            and origin in modules
            and origin not in target.repository_module_origins
        ):
            return None, {origin}
        return origin, set()
    return _resolve_repository_origin(
        target_origin,
        modules,
        bindings,
        ambiguous_bindings,
        {*seen, origin},
        traversed,
    )


def _resolve_ambiguous_repository_origins(
    candidates: set[str],
    modules: dict[str, _ParsedModule],
    bindings: dict[str, dict[str, str | None]],
    ambiguous_bindings: dict[str, dict[str, frozenset[str]]],
    seen: set[str],
    fallback: str,
    traversed: set[str],
) -> tuple[None, set[str]]:
    resolved_origins: set[str] = set()
    for candidate in candidates:
        resolved, candidate_ambiguities = _resolve_repository_origin(
            candidate,
            modules,
            bindings,
            ambiguous_bindings,
            seen,
            traversed,
        )
        if resolved is not None:
            resolved_origins.add(resolved)
        resolved_origins.update(candidate_ambiguities)
    return None, resolved_origins or {fallback}


def _star_import_candidates(origins: set[str], name: str) -> set[str]:
    return {_normalize_symbol(f"{origin}.{name}") for origin in origins}


def _bind_name(
    module: _ParsedModule,
    name: str,
    *,
    ambiguous: bool,
    binding_owner: str | None = None,
) -> None:
    owner = binding_owner or module.module
    _bind(
        module.bindings,
        module.ambiguous_bindings,
        name,
        f"{owner}.{name}",
        ambiguous=ambiguous,
    )


def _bind_target(
    module: _ParsedModule,
    target: ast.expr,
    *,
    ambiguous: bool,
    binding_owner: str | None = None,
) -> None:
    if isinstance(target, ast.Name):
        _bind_name(
            module,
            target.id,
            ambiguous=ambiguous,
            binding_owner=binding_owner,
        )
    elif isinstance(target, (ast.Tuple, ast.List)):
        for element in target.elts:
            _bind_target(
                module,
                element,
                ambiguous=ambiguous,
                binding_owner=binding_owner,
            )
    elif isinstance(target, ast.Starred):
        _bind_target(
            module,
            target.value,
            ambiguous=ambiguous,
            binding_owner=binding_owner,
        )


def _pattern_binding_names(pattern: ast.pattern) -> tuple[str, ...]:
    names: list[str] = []
    for node in ast.walk(pattern):
        if isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name is not None:
            names.append(node.name)
        elif isinstance(node, ast.MatchMapping) and node.rest is not None:
            names.append(node.rest)
    return tuple(names)


def _assignment_value(value: ast.AST) -> ast.expr | None:
    if isinstance(value, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
        return value.value
    return None


def _assignment_names(value: ast.AST) -> tuple[str, ...]:
    if not isinstance(value, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
        return ()
    targets = value.targets if isinstance(value, ast.Assign) else (value.target,)
    return tuple(name for target in targets for name in _target_names(target))


def _is_supported_module_single_name_assignment(value: ast.AST) -> bool:
    return (
        isinstance(value, ast.Assign)
        and len(value.targets) == 1
        and isinstance(value.targets[0], ast.Name)
    )


def _import_from_origin(module: _ParsedModule, value: ast.ImportFrom) -> str | None:
    if value.level == 0:
        return value.module
    parts = module.module.split(".")
    package = parts if module.is_package else parts[:-1]
    keep = len(package) - (value.level - 1)
    if keep < 0:
        return None
    base = package[:keep]
    if value.module:
        base.extend(value.module.split("."))
    return ".".join(base) if base else None


def _normalize_symbol(value: str) -> str:
    if value == "sqlalchemy.ext.declarative.declarative_base":
        return "sqlalchemy.orm.declarative_base"
    for prefix in ("sqlalchemy.schema.", "sqlalchemy.sql.schema."):
        if value.startswith(prefix):
            return "sqlalchemy." + value.rsplit(".", 1)[-1]
    if value.startswith("sqlalchemy.types."):
        return "sqlalchemy." + value.rsplit(".", 1)[-1]
    return value


def _resolve_symbol(value: ast.expr, module: _ParsedModule) -> str | None:
    if isinstance(value, ast.Name):
        if value.id in module.bindings:
            origin = module.bindings[value.id]
            return origin if _binding_origin_is_usable(module, origin) else None
        if value.id in _BUILTIN_TYPES:
            return f"builtins.{value.id}"
        return None
    if isinstance(value, ast.Attribute):
        base = _resolve_symbol(value.value, module)
        if base is None:
            return None
        candidate = _normalize_symbol(f"{base}.{value.attr}")
        if candidate in module.attribute_mutations:
            return None
        if _repository_star_candidates(module, candidate):
            return None
        resolved = module.repository_bindings.get(candidate, candidate)
        return resolved if _binding_origin_is_usable(module, resolved) else None
    return None


def _binding_origin_is_usable(module: _ParsedModule, origin: str | None) -> bool:
    return origin is not None and not (
        _is_sqlalchemy_origin(origin) and not _binding_origin_is_sqlalchemy(module, origin)
    )


def _unresolved_terminal(
    value: ast.expr,
    module: _ParsedModule,
    terminals: frozenset[str] | set[str],
) -> bool:
    if _resolve_symbol(value, module) is not None:
        return False
    if _has_known_root_binding(value, module):
        return any(
            _binding_origin_is_sqlalchemy(module, origin) and origin.rsplit(".", 1)[-1] in terminals
            for origin in _ambiguous_symbols(value, module)
        )
    terminal = _terminal_name(value)
    if module.star_import and terminal in terminals:
        return True
    return any(
        _binding_origin_is_sqlalchemy(module, origin) and origin.rsplit(".", 1)[-1] in terminals
        for origin in _ambiguous_symbols(value, module)
    )


def _ambiguous_symbols(value: ast.expr, module: _ParsedModule) -> set[str]:
    if isinstance(value, ast.Name):
        return set(module.ambiguous_bindings.get(value.id, ()))
    if isinstance(value, ast.Attribute):
        result: set[str] = set()
        base = _resolve_symbol(value.value, module)
        if base is not None:
            candidate = _normalize_symbol(f"{base}.{value.attr}")
            resolved = module.repository_bindings.get(candidate, candidate)
            if candidate in module.attribute_mutations:
                result.add(resolved or candidate)
            result.update(module.repository_ambiguous_bindings.get(candidate, ()))
            result.update(_repository_star_candidates(module, candidate))
        for origin in _ambiguous_symbols(value.value, module):
            candidate = _normalize_symbol(f"{origin}.{value.attr}")
            resolved = module.repository_bindings.get(candidate, candidate)
            if resolved is not None:
                result.add(resolved)
            result.update(module.repository_ambiguous_bindings.get(candidate, ()))
            result.update(_repository_star_candidates(module, candidate))
        return result
    return set()


def _repository_star_candidates(module: _ParsedModule, symbol: str) -> set[str]:
    if "." not in symbol:
        return set()
    owner, name = symbol.rsplit(".", 1)
    return {
        _normalize_symbol(f"{origin}.{name}")
        for origin in module.repository_star_imports.get(owner, ())
    }


def _has_known_root_binding(value: ast.expr, module: _ParsedModule) -> bool:
    root: ast.expr = value
    while isinstance(root, ast.Attribute):
        root = root.value
    return isinstance(root, ast.Name) and root.id in module.bindings


def _ambiguous_binding_matches(
    value: ast.expr,
    module: _ParsedModule,
    symbols: set[str],
) -> bool:
    return bool(_ambiguous_symbols(value, module) & symbols)


def _declarative_base_expression_evidence(
    value: ast.expr,
    module: _ParsedModule,
    base_symbols: set[str],
) -> bool:
    class_symbols = base_symbols | {"sqlalchemy.orm.DeclarativeBase"}
    for node in ast.walk(value):
        if not isinstance(node, ast.expr):
            continue
        if _resolve_symbol(node, module) in class_symbols:
            return True
        if _unresolved_terminal(node, module, {"DeclarativeBase"}):
            return True
        if _ambiguous_binding_matches(node, module, base_symbols):
            return True
        if isinstance(node, ast.Call) and (
            _resolve_call(node, module) == "sqlalchemy.orm.declarative_base"
            or _unresolved_terminal(node.func, module, {"declarative_base"})
        ):
            return True
    return False


def _resolve_call(value: ast.Call, module: _ParsedModule) -> str | None:
    return _resolve_symbol(value.func, module)


def _terminal_name(value: ast.expr) -> str | None:
    if isinstance(value, ast.Name):
        return value.id
    if isinstance(value, ast.Attribute):
        return value.attr
    return None


def _special_assignments(
    declaration: _ClassDeclaration,
    scope_modules: dict[int, _ParsedModule],
    global_names: dict[int, frozenset[str]],
) -> dict[str, list[_ClassSpecialBinding]]:
    result: dict[str, list[_ClassSpecialBinding]] = {}
    for statement in declaration.node.body:
        _record_special_assignments(
            result,
            statement,
            scope_modules[id(statement)],
            direct=True,
            global_names=global_names[id(statement)],
        )
        for write in _nested_module_scope_writes(statement):
            _record_special_assignments(
                result,
                write,
                scope_modules[id(write)],
                direct=False,
                global_names=global_names[id(write)],
            )
    return result


def _record_special_assignments(
    result: dict[str, list[_ClassSpecialBinding]],
    statement: ast.AST,
    module: _ParsedModule,
    *,
    direct: bool,
    global_names: frozenset[str],
) -> None:
    for name in _direct_binding_names(statement):
        if name not in _CLASS_TABLE_SPECIALS:
            continue
        supported, value = _supported_special_assignment(statement, name)
        result.setdefault(name, []).append(
            _ClassSpecialBinding(
                value,
                module,
                supported=direct and supported and name not in global_names,
            )
        )


def _supported_special_assignment(
    statement: ast.AST,
    name: str,
) -> tuple[bool, ast.expr | None]:
    if (
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id == name
    ):
        return True, statement.value
    if (
        isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
        and statement.target.id == name
        and statement.value is not None
    ):
        return True, statement.value
    return False, None


def _class_candidate_origin(prefix: str, declaration: _ClassDeclaration) -> str:
    span = _span(declaration.node)
    return (
        f"{prefix}:{declaration.symbol}:{declaration.module.path}:"
        f"{span.start_line}:{span.start_utf8_byte_column}:"
        f"{span.end_line}:{span.end_utf8_byte_column}"
    )


def _parse_table_args(
    value: ast.expr,
    module: _ParsedModule,
) -> tuple[str | None, tuple[ast.Call, ...]] | None:
    if isinstance(value, ast.Constant) and value.value is None:
        return None, ()
    if isinstance(value, ast.Dict):
        schema_value = _schema_dict(value)
        if schema_value is _INVALID:
            return None
        return schema_value if isinstance(schema_value, str) else None, ()
    if not isinstance(value, ast.Tuple):
        return None
    values = list(value.elts)
    schema: str | None = None
    if values and isinstance(values[-1], ast.Dict):
        final_mapping = values.pop()
        assert isinstance(final_mapping, ast.Dict)
        parsed_schema = _schema_dict(final_mapping)
        if parsed_schema is _INVALID:
            return None
        schema = parsed_schema if isinstance(parsed_schema, str) else None
    constraints: list[ast.Call] = []
    for item in values:
        if not isinstance(item, ast.Call) or _resolve_call(item, module) not in _CONSTRAINT_SYMBOLS:
            return None
        constraints.append(item)
    return schema, tuple(constraints)


class _Invalid:
    pass


_INVALID: Final = _Invalid()


def _schema_dict(value: ast.Dict) -> str | _Invalid | None:
    if not value.keys:
        return None
    if len(value.keys) != 1 or value.keys[0] is None:
        return _INVALID
    key = value.keys[0]
    if not isinstance(key, ast.Constant) or key.value != "schema":
        return _INVALID
    return _static_structural_string(value.values[0]) or _INVALID


def _static_structural_string(value: ast.expr) -> str | None:
    if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
        return None
    try:
        return safe_structural_string(value.value)
    except (TypeError, ValueError):
        return None


def _static_bool(value: ast.expr) -> bool | None:
    return value.value if isinstance(value, ast.Constant) and type(value.value) is bool else None


def _optional_static_name(value: ast.expr | None) -> str | _Invalid | None:
    if value is None or (isinstance(value, ast.Constant) and value.value is None):
        return None
    return _static_structural_string(value) or _INVALID


def _keyword_map(value: ast.Call) -> dict[str, ast.expr] | None:
    result: dict[str, ast.expr] = {}
    for keyword in value.keywords:
        if keyword.arg is None or keyword.arg in result:
            return None
        result[keyword.arg] = keyword.value
    return result


def _consume_construction_calls(
    module: _ParsedModule,
    value: ast.AST,
    state: _State,
) -> None:
    for node in ast.walk(value):
        if not isinstance(node, ast.Call):
            continue
        symbol = _resolve_call(node, module)
        terminal = _terminal_name(node.func)
        if symbol in _CONSTRUCTION_SYMBOLS or terminal in _CONSTRUCTION_TERMINALS:
            state.consumed_calls.add(id(node))


def _row_assignment(value: ast.stmt) -> tuple[str, ast.expr | None, ast.expr | None] | None:
    if isinstance(value, ast.AnnAssign) and isinstance(value.target, ast.Name):
        return value.target.id, value.annotation, value.value
    if (
        isinstance(value, ast.Assign)
        and len(value.targets) == 1
        and isinstance(value.targets[0], ast.Name)
    ):
        return value.targets[0].id, None, value.value
    return None


def _mapped_inner(value: ast.expr, module: _ParsedModule) -> ast.expr | None:
    if (
        isinstance(value, ast.Subscript)
        and _resolve_symbol(value.value, module) == "sqlalchemy.orm.Mapped"
    ):
        return value.slice
    return None


def _unresolved_mapped_annotation(value: ast.expr, module: _ParsedModule) -> bool:
    return isinstance(value, ast.Subscript) and _unresolved_terminal(
        value.value,
        module,
        {"Mapped"},
    )


def _relationship_annotation(
    value: ast.expr | None,
    module: _ParsedModule,
) -> tuple[ast.expr | None, SqlAlchemyCardinality]:
    if value is None:
        return None, SqlAlchemyCardinality.UNKNOWN
    inner = _mapped_inner(value, module)
    if inner is None:
        return None, SqlAlchemyCardinality.UNKNOWN
    inner = _optional_annotation_inner(inner, module)
    if inner is None:
        return None, SqlAlchemyCardinality.UNKNOWN
    if isinstance(inner, ast.Subscript) and _annotation_container(inner.value, module) in {
        "builtins.list",
        "builtins.set",
        "builtins.tuple",
        "typing.List",
        "typing.Set",
        "typing.Tuple",
    }:
        if (
            isinstance(inner.slice, ast.Tuple)
            or _relationship_reference(inner.slice, module) is None
        ):
            return None, SqlAlchemyCardinality.UNKNOWN
        return inner.slice, SqlAlchemyCardinality.MANY
    if _relationship_reference(inner, module) is None:
        return None, SqlAlchemyCardinality.UNKNOWN
    return inner, SqlAlchemyCardinality.SCALAR


def _optional_annotation_inner(
    value: ast.expr,
    module: _ParsedModule,
) -> ast.expr | None:
    if (
        isinstance(value, ast.Subscript)
        and _resolve_symbol(value.value, module) == "typing.Optional"
        and not isinstance(value.slice, ast.Tuple)
    ):
        return value.slice
    if isinstance(value, ast.BinOp) and isinstance(value.op, ast.BitOr):
        if _is_none(value.left):
            return value.right
        if _is_none(value.right):
            return value.left
        return None
    return value


def _is_none(value: ast.expr) -> bool:
    return isinstance(value, ast.Constant) and value.value is None


def _annotation_container(value: ast.expr, module: _ParsedModule) -> str | None:
    if (
        isinstance(value, ast.Name)
        and value.id in {"list", "set", "tuple"}
        and value.id not in module.bindings
    ):
        return f"builtins.{value.id}"
    return _resolve_symbol(value, module)


def _relationship_reference(
    value: ast.expr,
    module: _ParsedModule,
) -> tuple[str, bool] | None:
    candidate: str | None
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        candidate = value.value
        from_static_string = True
    else:
        candidate = _resolve_symbol(value, module)
        from_static_string = False
    if candidate is None:
        return None
    try:
        return safe_dotted_symbol(candidate, field="relationship target"), from_static_string
    except ValueError:
        return None


def _relationship_target(
    value: ast.expr | None,
    module: _ParsedModule,
    class_tables: dict[str, SqlAlchemyTable],
    source_modules: frozenset[str],
    declarative_symbols: frozenset[str],
) -> SqlAlchemyRelationTarget:
    if value is None:
        return SqlAlchemyRelationTarget.unknown()
    reference = _relationship_reference(value, module)
    if reference is None:
        return SqlAlchemyRelationTarget.unknown()
    symbol, from_static_string = reference
    direct = class_tables.get(symbol)
    if direct is not None:
        return SqlAlchemyRelationTarget.internal_table(direct)
    if "." not in symbol:
        same_module = class_tables.get(f"{module.module}.{symbol}")
        if same_module is not None:
            return SqlAlchemyRelationTarget.internal_table(same_module)
        matches = [
            table
            for class_symbol, table in class_tables.items()
            if class_symbol.rsplit(".", 1)[-1] == symbol
        ]
        if len(matches) == 1:
            return SqlAlchemyRelationTarget.internal_table(matches[0])
        return SqlAlchemyRelationTarget.unknown()
    if symbol in declarative_symbols:
        return SqlAlchemyRelationTarget.unknown()
    if from_static_string:
        return SqlAlchemyRelationTarget.external_mapped_class(symbol)
    if _symbol_is_in_source(symbol, source_modules):
        return SqlAlchemyRelationTarget.unknown()
    return SqlAlchemyRelationTarget.external_mapped_class(symbol)


def _symbol_is_in_source(symbol: str, source_modules: frozenset[str]) -> bool:
    return symbol.rsplit(".", 1)[0] in source_modules


def _secondary_target(
    value: ast.expr,
    module: _ParsedModule,
    bound_tables: dict[str, SqlAlchemyTable],
    tables_by_id: dict[str, SqlAlchemyTable],
    collided_ids: set[str],
) -> SqlAlchemyRelationTarget:
    symbol = _resolve_symbol(value, module)
    if symbol is not None:
        table = bound_tables.get(symbol)
        return (
            SqlAlchemyRelationTarget.internal_table(table)
            if table is not None
            else SqlAlchemyRelationTarget.unknown()
        )
    if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
        return SqlAlchemyRelationTarget.unknown()
    parts = value.value.split(".")
    if len(parts) not in {1, 2}:
        return SqlAlchemyRelationTarget.unknown()
    try:
        normalized = tuple(
            safe_structural_string(part, field="secondary table identity") for part in parts
        )
    except ValueError:
        return SqlAlchemyRelationTarget.unknown()
    schema_name = normalized[0] if len(normalized) == 2 else None
    table_name = normalized[-1]
    table_id = sqlalchemy_table_id(schema_name, table_name)
    if table_id in collided_ids:
        return SqlAlchemyRelationTarget.unknown()
    table = tables_by_id.get(table_id)
    return (
        SqlAlchemyRelationTarget.internal_table(table)
        if table is not None
        else SqlAlchemyRelationTarget.external_table(
            schema_name=schema_name,
            table_name=table_name,
        )
    )


def _type_descriptor(
    value: ast.expr | None,
    module: _ParsedModule,
    state: _State,
) -> SqlAlchemyTypeDescriptor:
    if value is None:
        return SqlAlchemyTypeDescriptor(
            SqlAlchemyTypeCategory.UNKNOWN,
            None,
            RedactedExpression.absent(),
        )
    parameters = RedactedExpression.absent()
    symbol: str | None
    if isinstance(value, ast.Call):
        symbol = _resolve_call(value, module)
        state.consumed_calls.add(id(value))
        if value.args or value.keywords:
            supplied = [*value.args, *(keyword.value for keyword in value.keywords)]
            category = (
                RedactedExpressionCategory.LITERAL
                if supplied and all(_literal_node(item) for item in supplied)
                else RedactedExpressionCategory.SQL_EXPRESSION
            )
            parameters = RedactedExpression.present_as(category)
    else:
        symbol = _resolve_symbol(value, module)
    if symbol is None:
        return SqlAlchemyTypeDescriptor(SqlAlchemyTypeCategory.UNKNOWN, None, parameters)
    normalized = _normalize_symbol(symbol)
    type_category = _TYPE_CATEGORIES.get(normalized, SqlAlchemyTypeCategory.CUSTOM)
    try:
        safe_dotted_symbol(normalized, field="type symbol")
    except ValueError:
        return SqlAlchemyTypeDescriptor(SqlAlchemyTypeCategory.UNKNOWN, None, parameters)
    return SqlAlchemyTypeDescriptor(type_category, normalized, parameters)


def _literal_node(value: ast.expr) -> bool:
    return isinstance(value, (ast.Constant, ast.List, ast.Tuple, ast.Dict, ast.Set))


def _redacted(
    value: ast.expr | None,
    module: _ParsedModule,
    state: _State,
) -> RedactedExpression:
    if value is None:
        return RedactedExpression.absent()
    if isinstance(value, ast.Call):
        symbol = _resolve_call(value, module)
        if symbol == "sqlalchemy.Computed":
            state.consumed_calls.add(id(value))
            return RedactedExpression.present_as(RedactedExpressionCategory.COMPUTED)
        if symbol == "sqlalchemy.Identity":
            state.consumed_calls.add(id(value))
            return RedactedExpression.present_as(RedactedExpressionCategory.IDENTITY)
    if _literal_node(value):
        category = RedactedExpressionCategory.LITERAL
    elif isinstance(value, ast.Lambda) or _resolve_symbol(value, module) is not None:
        category = RedactedExpressionCategory.CALLABLE
    elif isinstance(value, ast.expr):
        category = RedactedExpressionCategory.SQL_EXPRESSION
    else:
        category = RedactedExpressionCategory.UNKNOWN
    return RedactedExpression.present_as(category)


def _special_redaction(
    values: list[tuple[str, ast.Call]],
    symbol: str,
    module: _ParsedModule,
    state: _State,
) -> RedactedExpression:
    matches = [call for candidate, call in values if candidate == symbol]
    if not matches:
        return RedactedExpression.absent()
    if len(matches) != 1:
        return RedactedExpression.present_as(RedactedExpressionCategory.UNKNOWN)
    return _redacted(matches[0], module, state)


def _remember_column(
    known: dict[str, str | None],
    reference: str,
    semantic_name: str,
) -> None:
    previous = known.get(reference)
    if reference in known and previous != semantic_name:
        known[reference] = None
    else:
        known[reference] = semantic_name


def _column_reference(value: ast.expr, known: dict[str, str | None]) -> str | None:
    if isinstance(value, ast.Name):
        try:
            reference = safe_structural_string(value.id, field="column name")
        except ValueError:
            return None
        return known.get(reference)
    if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
        return None
    try:
        normalized = safe_structural_string(value.value, field="column name")
    except ValueError:
        return None
    if not known:
        return normalized
    return normalized if normalized in known.values() else None


def _static_string_sequence(value: ast.expr) -> tuple[str, ...] | None:
    if not isinstance(value, (ast.List, ast.Tuple)) or not value.elts:
        return None
    result: list[str] = []
    for item in value.elts:
        parsed = _static_structural_string(item)
        if parsed is None:
            return None
        result.append(parsed)
    return tuple(result)


def _foreign_key_target(
    value: str,
    tables_by_id: dict[str, SqlAlchemyTable],
) -> tuple[SqlAlchemyRelationTarget, str] | None:
    parts = value.split(".")
    if len(parts) not in {2, 3}:
        return None
    try:
        normalized = tuple(safe_structural_string(part) for part in parts)
    except ValueError:
        return None
    schema_name = normalized[0] if len(normalized) == 3 else None
    table_name = normalized[-2]
    column_name = normalized[-1]
    table = tables_by_id.get(sqlalchemy_table_id(schema_name, table_name))
    target = (
        SqlAlchemyRelationTarget.internal_table(table)
        if table is not None
        else SqlAlchemyRelationTarget.external_table(
            schema_name=schema_name,
            table_name=table_name,
        )
    )
    return target, column_name


def _line(value: ast.AST) -> int:
    line = getattr(value, "lineno", None)
    if type(line) is not int or line <= 0:
        raise ValueError("SQLAlchemy AST node has no valid source line")
    return line


def _span(value: ast.AST) -> SqlAlchemyInternalDeclarationSpan:
    start_line = getattr(value, "lineno", None)
    start_column = getattr(value, "col_offset", None)
    end_line = getattr(value, "end_lineno", None)
    end_column = getattr(value, "end_col_offset", None)
    if any(type(item) is not int for item in (start_line, start_column, end_line, end_column)):
        raise ValueError("SQLAlchemy AST declaration span metadata is missing")
    assert isinstance(start_line, int)
    assert isinstance(start_column, int)
    assert isinstance(end_line, int)
    assert isinstance(end_column, int)
    return SqlAlchemyInternalDeclarationSpan(start_line, start_column, end_line, end_column)


def _location(module: _ParsedModule, value: ast.AST) -> SqlAlchemySourceLocation:
    span = _span(value)
    return SqlAlchemySourceLocation(
        module.path,
        SqlAlchemySourceRange(span.start_line, span.end_line),
    )


def _utf8(value: str) -> bytes:
    return value.encode("utf-8")
