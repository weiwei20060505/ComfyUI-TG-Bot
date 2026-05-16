from __future__ import annotations

from typing import Any

from comfyui_tg_bot.models import GeminiParseResult, WorkflowConfig


class WorkflowRenderError(RuntimeError):
    pass


def render_workflow(
    graph: dict[str, Any],
    config: WorkflowConfig,
    parse_result: GeminiParseResult,
) -> dict[str, Any]:
    values: dict[str, Any] = {
        "positive_prompt": parse_result.positive_prompt,
        "negative_prompt": parse_result.negative_prompt,
    }

    try:
        size = config.aspect_ratios[parse_result.aspect_ratio]
    except KeyError as exc:
        raise WorkflowRenderError(
            f"Unsupported aspect ratio {parse_result.aspect_ratio!r} for workflow {config.id}."
        ) from exc

    values["width"] = size.width
    values["height"] = size.height
    values.update(parse_result.parameters)

    for field_name, mapping in config.fields.items():
        if field_name not in values:
            if mapping.required:
                raise WorkflowRenderError(f"Missing required workflow field: {field_name}")
            continue

        node = graph[mapping.target.node_id]
        node["inputs"][mapping.target.input] = values[field_name]

    return graph
