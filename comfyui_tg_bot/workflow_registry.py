from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from comfyui_tg_bot.models import WorkflowConfig


class WorkflowRegistryError(RuntimeError):
    pass


class WorkflowRegistry:
    def __init__(self, workflow_dir: Path) -> None:
        self.workflow_dir = workflow_dir
        self._configs: dict[str, WorkflowConfig] = {}
        self._graphs: dict[str, dict[str, Any]] = {}

    @property
    def workflow_ids(self) -> list[str]:
        return sorted(self._configs)

    @property
    def configs(self) -> dict[str, WorkflowConfig]:
        return self._configs.copy()

    def load(self) -> None:
        if not self.workflow_dir.exists():
            raise WorkflowRegistryError(f"Workflow directory does not exist: {self.workflow_dir}")

        configs: dict[str, WorkflowConfig] = {}
        graphs: dict[str, dict[str, Any]] = {}

        for config_path in sorted(self.workflow_dir.glob("*.config.json")):
            config = self._load_config(config_path)
            graph_path = self.workflow_dir / config.workflow_file
            graph = self._load_graph(graph_path)
            self._validate_mapping(config=config, graph=graph)

            if config.id in configs:
                raise WorkflowRegistryError(f"Duplicate workflow id: {config.id}")

            configs[config.id] = config
            graphs[config.id] = graph

        if not configs:
            raise WorkflowRegistryError(
                f"No workflow config files found in {self.workflow_dir}. "
                "Expected files matching *.config.json."
            )

        if not any(config.is_default for config in configs.values()):
            raise WorkflowRegistryError("At least one workflow must be marked as is_default=true.")

        self._configs = configs
        self._graphs = graphs

    def get_config(self, workflow_id: str) -> WorkflowConfig:
        try:
            return self._configs[workflow_id]
        except KeyError as exc:
            raise WorkflowRegistryError(f"Unknown workflow id: {workflow_id}") from exc

    def get_graph(self, workflow_id: str) -> dict[str, Any]:
        try:
            return deepcopy(self._graphs[workflow_id])
        except KeyError as exc:
            raise WorkflowRegistryError(f"Unknown workflow id: {workflow_id}") from exc

    def get_default_config(self) -> WorkflowConfig:
        for config in self._configs.values():
            if config.is_default:
                return config
        raise WorkflowRegistryError("No default workflow is loaded.")

    def _load_config(self, path: Path) -> WorkflowConfig:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return WorkflowConfig.model_validate(data)

    def _load_graph(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise WorkflowRegistryError(f"Workflow graph does not exist: {path}")

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise WorkflowRegistryError(f"Workflow graph must be a JSON object: {path}")

        return data

    def _validate_mapping(self, config: WorkflowConfig, graph: dict[str, Any]) -> None:
        for field_name, mapping in config.fields.items():
            node_id = mapping.target.node_id
            input_name = mapping.target.input

            if node_id not in graph:
                raise WorkflowRegistryError(
                    f"Workflow {config.id} field {field_name} points to missing node {node_id}."
                )

            node = graph[node_id]
            inputs = node.get("inputs") if isinstance(node, dict) else None
            if not isinstance(inputs, dict) or input_name not in inputs:
                raise WorkflowRegistryError(
                    f"Workflow {config.id} field {field_name} points to missing input "
                    f"{node_id}.{input_name}."
                )
