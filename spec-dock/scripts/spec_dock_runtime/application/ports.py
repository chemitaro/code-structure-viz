from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    from spec_dock_runtime.application.contracts import (
        ArtifactWriteResult,
        BootstrapResult,
        ExplicitFileArtifactPublishRequest,
        ExplicitFileArtifactPublishResult,
        ExplicitFileSourcePreflightRequest,
        GitHubCapabilityDiagnostic,
        GitHubCapabilityProbeRequest,
        GitWorktreeRecord,
        GuardedExplicitFileSource,
        SyncCommandResult,
        SyncRequest,
    )
    from spec_dock_runtime.domain.models import IssueSnapshot, SpecGraph
    from spec_dock_runtime.infra.contracts import (
        ActiveManifest,
        ActiveManifestLoadResult,
        ActiveStateSnapshot,
        DepsTopologyLoadResult,
        DirectDependencyResolution,
        StoredMetaRecord,
    )
    from spec_dock_runtime.presentation.contracts import ArtifactBundle


class ValidateNodeReader(Protocol):
    def load_node_records(self) -> list[StoredMetaRecord]: ...


class DerivedStateReader(Protocol):
    def load_cached_issue_status_by_id(self, specdock_dir: Path) -> dict[str, str]: ...


class NodeRepository(Protocol):
    def load_node_records(self, specdock_dir: Path) -> list[StoredMetaRecord]: ...

    def write_meta(self, dest_dir: Path, record: StoredMetaRecord) -> None: ...

    def write_meta_at(self, dest_dir_fd: int, record: StoredMetaRecord) -> None: ...

    def add_issue_dependency(self, meta_path: Path, to_id: str) -> None: ...

    def remove_issue_dependency(
        self, meta_path: Path, to_id: str, *, matching_refs: list[object] | None = None
    ) -> None: ...

    def delete_tree(self, node_path: Path) -> None: ...


class TemplateScaffolder(Protocol):
    def render_text(self, text: str, replacements: dict[str, str]) -> str: ...

    def load_template_text(self, src_path: Path) -> str: ...

    def copy_scaffolded_tree(self, src_dir: Path, dest_dir: Path, replacements: dict[str, str]) -> list[Path]: ...

    def copy_scaffolded_tree_at(
        self,
        src_dir: Path,
        dest_dir: Path,
        dest_dir_fd: int,
        replacements: dict[str, str],
    ) -> list[Path]: ...

    def write_text(self, dest_path: Path, text: str) -> None: ...


class IssueGateway(Protocol):
    def issue_index(self, repo_root: Path, *, limit: int) -> list[IssueSnapshot]: ...

    def issue_create(self, repo_root: Path, title: str, body: str) -> int: ...

    def issue_view_minimal(
        self,
        repo_root: Path,
        issue_number: int,
        *,
        repo_slug: str | None = None,
    ) -> IssueSnapshot: ...

    def issue_view_snapshot(
        self,
        repo_root: Path,
        issue_number: int,
        *,
        repo_slug: str | None = None,
    ) -> IssueSnapshot: ...

    def issue_close(
        self,
        repo_root: Path,
        issue_number: int,
        *,
        repo_slug: str | None = None,
    ) -> IssueSnapshot: ...


class ActiveStateStore(Protocol):
    def load_active_manifest(self, specdock_dir: Path) -> ActiveManifestLoadResult: ...

    def load_active_manifest_no_migrate(self, specdock_dir: Path) -> ActiveManifestLoadResult: ...

    def load_active_issue_id(self, specdock_dir: Path) -> str | None: ...

    def write_active_manifest(self, specdock_dir: Path, manifest: ActiveManifest) -> ActiveManifest: ...

    def apply_active_pointers(
        self, specdock_dir: Path, manifest: ActiveManifest | None, rendered_context_pack: str
    ) -> None: ...

    def patch_agent_state_active_fields(self, specdock_dir: Path, manifest: ActiveManifest | None) -> None: ...

    def snapshot_current_state(self, specdock_dir: Path) -> ActiveStateSnapshot: ...

    def restore_previous_state(self, specdock_dir: Path, snapshot: ActiveStateSnapshot) -> None: ...


class DepsTopologyReader(Protocol):
    def load_issue_depends_on_map(self, specdock_dir: Path, graph: SpecGraph) -> DepsTopologyLoadResult: ...

    def load_direct_dependency_resolutions(
        self,
        specdock_dir: Path,
        graph: SpecGraph,
        src_id: str,
    ) -> list[DirectDependencyResolution]: ...

    def load_node_dependency_resolutions(
        self,
        specdock_dir: Path,
        graph: SpecGraph,
    ) -> dict[str, list[DirectDependencyResolution]]: ...

    def build_candidate_issue_depends_on_map(
        self,
        graph: SpecGraph,
        issue_depends_on_map: dict[str, list[str]],
        *,
        from_node_id: str,
        to_node_id: str,
    ) -> dict[str, list[str]]: ...


class GitGateway(Protocol):
    def require_clean_working_tree(self, repo_root: Path) -> None: ...

    def current_branch_or_none(self, repo_root: Path) -> str | None: ...

    def local_branch_exists(self, repo_root: Path, branch: str) -> bool: ...

    def checkout_branch(self, repo_root: Path, branch: str) -> None: ...

    def create_and_checkout_branch(self, repo_root: Path, branch: str) -> None: ...

    def check_ref_format_branch(self, repo_root: Path, branch: str) -> bool: ...

    def origin_github_repo_slug(self, repo_root: Path) -> str | None: ...

    def worktree_list(self, repo_root: Path) -> list[GitWorktreeRecord]: ...

    def add_worktree_with_new_branch(self, repo_root: Path, *, path: Path, branch: str) -> None: ...

    def remove_worktree(self, repo_root: Path, *, path: Path, force: bool) -> None: ...


class GitHubCapabilityGateway(Protocol):
    def probe(self, request: GitHubCapabilityProbeRequest) -> list[GitHubCapabilityDiagnostic]: ...


class BootstrapGateway(Protocol):
    def run_make_init_if_available(self, worktree_path: Path) -> BootstrapResult: ...


class FilesystemGateway(Protocol):
    def path_exists(self, path: Path) -> bool: ...

    def remove_target(self, path: Path) -> None: ...

    def path_kind(self, path: Path) -> str: ...

    def guard_workbench_ancestry(self, root: Path, endpoint: Path, *, allow_missing_leaf: bool = False) -> None: ...

    def guard_workbench_inventory(self, specdock_dir: Path) -> None: ...

    def copy_workbench(self, source: Path, destination: Path) -> None: ...


class ExplicitFileSourceGuard(Protocol):
    def guard_explicit_file_source(
        self,
        request: ExplicitFileSourcePreflightRequest,
    ) -> GuardedExplicitFileSource: ...


class ExplicitFileArtifactPublisher(Protocol):
    def publish_explicit_file(
        self,
        request: ExplicitFileArtifactPublishRequest,
    ) -> ExplicitFileArtifactPublishResult: ...


class EnvironmentGateway(Protocol):
    def getenv(self, name: str) -> str | None: ...


class ArtifactWriter(Protocol):
    def write(self, specdock_dir: Path, bundle: ArtifactBundle) -> ArtifactWriteResult: ...


class JsonStore(Protocol):
    def load_json(self, path: Path) -> object: ...

    def write_json(self, path: Path, data: object) -> None: ...


class Clock(Protocol):
    def now_iso(self) -> str: ...

    def today(self) -> str: ...


class SyncLegacyRunner(Protocol):
    def run_sync(
        self,
        req: SyncRequest,
        *,
        active_manifest_mode: Literal["migrate", "no_migrate"] = "migrate",
    ) -> SyncCommandResult: ...


@dataclass(frozen=True)
class Ports:
    node_reader: ValidateNodeReader
    repo_root: Path | None
    specdock_dir: Path | None = None
    node_repo: NodeRepository | None = None
    template_scaffolder: TemplateScaffolder | None = None
    derived_state_reader: DerivedStateReader | None = None
    issue_gateway: IssueGateway | None = None
    active_state_store: ActiveStateStore | None = None
    deps_topology_reader: DepsTopologyReader | None = None
    git_gateway: GitGateway | None = None
    github_capability_gateway: GitHubCapabilityGateway | None = None
    json_store: JsonStore | None = None
    clock: Clock | None = None
    artifact_writer: ArtifactWriter | None = None
    sync_legacy_runner: SyncLegacyRunner | None = None
    bootstrap_gateway: BootstrapGateway | None = None
    environment_gateway: EnvironmentGateway | None = None
    filesystem_gateway: FilesystemGateway | None = None
    explicit_file_source_guard: ExplicitFileSourceGuard | None = None
    explicit_file_artifact_publisher: ExplicitFileArtifactPublisher | None = None
