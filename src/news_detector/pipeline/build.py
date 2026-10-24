"""Convert clean article JSONL files into stratified CSV datasets."""

import argparse
import csv
import hashlib
import json
import logging
import math
import os
import tempfile
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import cast

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT_DIR = PROJECT_ROOT / "data" / "clean"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

ARTICLE_FIELDS = (
    "article_id",
    "domain",
    "stratum",
    "url",
    "crawl_id",
    "warc_filename",
    "warc_offset",
    "warc_length",
    "pub_date",
    "pub_year",
    "title",
    "crawl_timestamp",
    "author_present",
    "n_words",
    "languages",
    "text_sha1",
    "text",
)
OUTPUT_FIELDS = (*ARTICLE_FIELDS, "label")
SPLIT_NAMES = ("train", "dev", "test")
SUPPORTED_YEARS = frozenset(range(2020, 2026))
GOLD_YEARS = frozenset(range(2020, 2023))

CsvValue = str | int | float | bool | None
StratificationKey = tuple[int, str, str]


class PipelineError(ValueError):
    """Input data cannot be converted safely."""


@dataclass(frozen=True)
class Record:
    """One validated source row and its split metadata."""

    values: dict[str, CsvValue]
    source: Path
    line_number: int

    @property
    def article_id(self) -> str:
        return cast(str, self.values["article_id"])

    @property
    def text_sha1(self) -> str:
        return cast(str, self.values["text_sha1"])

    @property
    def stratification_key(self) -> StratificationKey:
        return (
            cast(int, self.values["pub_year"]),
            cast(str, self.values["domain"]),
            cast(str, self.values["stratum"]),
        )


@dataclass(frozen=True)
class BuildSummary:
    """Counts produced by one pipeline run."""

    total: int
    split_counts: dict[str, int]
    label_counts: dict[str, int]


def _validate_row(raw: object, source: Path, line_number: int) -> Record:
    location = f"{source}:{line_number}"
    if not isinstance(raw, dict):
        raise PipelineError(f"{location}: expected a JSON object")

    raw_mapping = cast(dict[object, object], raw)
    if not all(isinstance(key, str) for key in raw_mapping):
        raise PipelineError(f"{location}: every JSON key must be a string")
    mapping = cast(dict[str, object], raw_mapping)
    missing = set(ARTICLE_FIELDS) - mapping.keys()
    extra = mapping.keys() - set(ARTICLE_FIELDS)
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing fields: {', '.join(sorted(missing))}")
        if extra:
            details.append(f"unexpected fields: {', '.join(sorted(extra))}")
        raise PipelineError(f"{location}: {'; '.join(details)}")

    for field, value in mapping.items():
        if not isinstance(value, str | int | float | bool | type(None)):
            raise PipelineError(f"{location}: field {field!r} must contain a scalar")

    year = mapping["pub_year"]
    if not isinstance(year, int) or isinstance(year, bool):
        raise PipelineError(f"{location}: pub_year must be an integer")
    if year not in SUPPORTED_YEARS:
        raise PipelineError(
            f"{location}: unsupported pub_year {year}; expected 2020-2025"
        )

    for field in ("article_id", "domain", "stratum", "text_sha1"):
        if not isinstance(mapping[field], str) or not mapping[field]:
            raise PipelineError(f"{location}: {field} must be a non-empty string")

    values = {field: cast(CsvValue, mapping[field]) for field in ARTICLE_FIELDS}
    return Record(values=values, source=source, line_number=line_number)


def load_records(input_dir: Path) -> list[Record]:
    """Load and validate every ``<year>/*.jsonl`` record."""
    paths = sorted(input_dir.glob("*/*.jsonl"))
    if not paths:
        raise PipelineError(f"No JSONL files found under {input_dir}")

    records: list[Record] = []
    for path in paths:
        try:
            directory_year = int(path.parent.name)
        except ValueError as exc:
            raise PipelineError(f"{path}: parent directory must be a year") from exc
        if directory_year not in SUPPORTED_YEARS:
            raise PipelineError(
                f"{path}: unsupported year directory; expected one of 2020-2025"
            )

        try:
            lines = path.open(encoding="utf-8")
        except OSError as exc:
            raise PipelineError(f"Cannot read {path}: {exc}") from exc
        with lines:
            for line_number, line in enumerate(lines, start=1):
                if not line.strip():
                    continue
                try:
                    raw: object = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise PipelineError(
                        f"{path}:{line_number}: invalid JSON: {exc}"
                    ) from exc
                record = _validate_row(raw, path, line_number)
                if record.stratification_key[0] != directory_year:
                    raise PipelineError(
                        f"{path}:{line_number}: pub_year does not match its directory"
                    )
                records.append(record)
    if not records:
        raise PipelineError(f"JSONL files under {input_dir} contain no records")
    return records


class _DisjointSet:
    """Join records that have the same article ID or body hash."""

    def __init__(self, size: int) -> None:
        self.parent = list(range(size))

    def find(self, item: int) -> int:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left: int, right: int) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root


def _duplicate_groups(records: list[Record], seed: int) -> list[list[int]]:
    disjoint_set = _DisjointSet(len(records))
    owners: dict[tuple[str, str], int] = {}
    for index, record in enumerate(records):
        for identity in (
            ("article_id", record.article_id),
            ("text_sha1", record.text_sha1),
        ):
            owner = owners.setdefault(identity, index)
            disjoint_set.union(owner, index)

    groups: defaultdict[int, list[int]] = defaultdict(list)
    for index in range(len(records)):
        groups[disjoint_set.find(index)].append(index)

    def stable_random_key(group: list[int]) -> bytes:
        identities = sorted(
            f"{records[index].article_id}:{records[index].text_sha1}" for index in group
        )
        value = f"{seed}|{'|'.join(identities)}".encode()
        return hashlib.sha256(value).digest()

    return sorted(groups.values(), key=stable_random_key)


def _integer_targets(size: int, ratios: tuple[float, float, float]) -> dict[str, int]:
    exact = [size * ratio for ratio in ratios]
    counts = [math.floor(value) for value in exact]
    remainder = size - sum(counts)
    order = sorted(
        range(len(SPLIT_NAMES)),
        key=lambda index: (-(exact[index] - counts[index]), index),
    )
    for index in order[:remainder]:
        counts[index] += 1
    return dict(zip(SPLIT_NAMES, counts, strict=True))


@dataclass
class _FlowEdge:
    target: int
    reverse: int
    capacity: int


def _add_flow_edge(
    graph: list[list[_FlowEdge]], source: int, target: int, capacity: int
) -> _FlowEdge:
    forward = _FlowEdge(target=target, reverse=len(graph[target]), capacity=capacity)
    backward = _FlowEdge(target=source, reverse=len(graph[source]), capacity=0)
    graph[source].append(forward)
    graph[target].append(backward)
    return forward


def _push_flow(
    graph: list[list[_FlowEdge]],
    levels: list[int],
    next_edge: list[int],
    node: int,
    sink: int,
    available: int,
) -> int:
    if node == sink:
        return available
    while next_edge[node] < len(graph[node]):
        edge = graph[node][next_edge[node]]
        if edge.capacity > 0 and levels[edge.target] == levels[node] + 1:
            sent = _push_flow(
                graph,
                levels,
                next_edge,
                edge.target,
                sink,
                min(available, edge.capacity),
            )
            if sent:
                edge.capacity -= sent
                graph[edge.target][edge.reverse].capacity += sent
                return sent
        next_edge[node] += 1
    return 0


def _stratum_targets(
    stratum_sizes: Counter[StratificationKey],
    ratios: tuple[float, float, float],
    seed: int,
) -> dict[StratificationKey, dict[str, int]]:
    """Round per-stratum targets while preserving exact global split sizes."""

    def stable_key(value: object) -> bytes:
        return hashlib.sha256(f"{seed}|{value!r}".encode()).digest()

    keys = sorted(stratum_sizes, key=stable_key)
    targets: dict[StratificationKey, dict[str, int]] = {}
    fractional_parts: dict[tuple[StratificationKey, str], float] = {}
    unassigned: dict[StratificationKey, int] = {}
    for key in keys:
        exact = [stratum_sizes[key] * ratio for ratio in ratios]
        floors = [math.floor(value) for value in exact]
        targets[key] = dict(zip(SPLIT_NAMES, floors, strict=True))
        unassigned[key] = stratum_sizes[key] - sum(floors)
        for split, value, floor in zip(SPLIT_NAMES, exact, floors, strict=True):
            fractional_parts[(key, split)] = value - floor

    global_targets = _integer_targets(sum(stratum_sizes.values()), ratios)
    deficits = {
        split: global_targets[split] - sum(targets[key][split] for key in keys)
        for split in SPLIT_NAMES
    }

    # This small max-flow problem assigns each stratum's remainder to distinct
    # splits. Therefore every cell is a floor or ceil of its ideal size, while
    # the column totals exactly match the requested global ratios.
    source = 0
    first_key_node = 1
    first_split_node = first_key_node + len(keys)
    sink = first_split_node + len(SPLIT_NAMES)
    graph: list[list[_FlowEdge]] = [[] for _ in range(sink + 1)]
    edges: dict[tuple[StratificationKey, str], _FlowEdge] = {}
    for key_index, key in enumerate(keys):
        key_node = first_key_node + key_index
        _add_flow_edge(graph, source, key_node, unassigned[key])
        ordered_splits = sorted(
            SPLIT_NAMES,
            key=lambda split: (
                -fractional_parts[(key, split)],
                stable_key((key, split)),
            ),
        )
        for split in ordered_splits:
            split_node = first_split_node + SPLIT_NAMES.index(split)
            edges[(key, split)] = _add_flow_edge(graph, key_node, split_node, 1)
    for split_index, split in enumerate(SPLIT_NAMES):
        _add_flow_edge(graph, first_split_node + split_index, sink, deficits[split])

    required_flow = sum(unassigned.values())
    flow = 0
    while flow < required_flow:
        levels = [-1] * len(graph)
        levels[source] = 0
        queue = deque([source])
        while queue:
            node = queue.popleft()
            for edge in graph[node]:
                if edge.capacity > 0 and levels[edge.target] < 0:
                    levels[edge.target] = levels[node] + 1
                    queue.append(edge.target)
        if levels[sink] < 0:
            raise PipelineError("Cannot round stratification targets consistently")

        next_edge = [0] * len(graph)

        while (
            sent := _push_flow(
                graph,
                levels,
                next_edge,
                source,
                sink,
                required_flow - flow,
            )
        ) > 0:
            flow += sent

    for (key, split), edge in edges.items():
        if edge.capacity == 0:
            targets[key][split] += 1
    return targets


def _assignment_score(
    split: str,
    contribution: Counter[StratificationKey],
    group_size: int,
    targets: dict[StratificationKey, dict[str, int]],
    assigned: dict[StratificationKey, dict[str, int]],
    global_targets: dict[str, int],
    global_assigned: dict[str, int],
) -> tuple[int, int, int]:
    accommodated = 0
    overflow = 0
    for key, count in contribution.items():
        remaining = targets[key][split] - assigned[key][split]
        accommodated += min(count, max(remaining, 0))
        overflow += max(count - max(remaining, 0), 0)
    global_remaining = global_targets[split] - global_assigned[split]
    global_fit = min(group_size, max(global_remaining, 0))
    return accommodated, -overflow, global_fit


def stratified_split(
    records: list[Record],
    *,
    ratios: tuple[float, float, float],
    seed: int,
) -> dict[str, list[Record]]:
    """Split records by year, domain and source stratum without duplicate leakage."""
    if any(ratio < 0 for ratio in ratios) or not math.isclose(sum(ratios), 1.0):
        raise PipelineError("Split ratios must be non-negative and sum to 1")

    stratum_sizes = Counter(record.stratification_key for record in records)
    targets = _stratum_targets(stratum_sizes, ratios, seed)
    global_targets = _integer_targets(len(records), ratios)
    assigned = {key: dict.fromkeys(SPLIT_NAMES, 0) for key in stratum_sizes}
    global_assigned = dict.fromkeys(SPLIT_NAMES, 0)
    assignments: dict[int, str] = {}

    for group in _duplicate_groups(records, seed):
        contribution = Counter(records[index].stratification_key for index in group)
        chosen = max(
            SPLIT_NAMES,
            key=lambda split: _assignment_score(
                split,
                contribution,
                len(group),
                targets,
                assigned,
                global_targets,
                global_assigned,
            ),
        )
        for key, count in contribution.items():
            assigned[key][chosen] += count
        global_assigned[chosen] += len(group)
        for index in group:
            assignments[index] = chosen

    result: dict[str, list[Record]] = {split: [] for split in SPLIT_NAMES}
    for index, record in enumerate(records):
        result[assignments[index]].append(record)
    return result


def _label(record: Record) -> str:
    year = record.stratification_key[0]
    return "0" if year in GOLD_YEARS else ""


def _write_csv(path: Path, records: list[Record]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow({**record.values, "label": _label(record)})


def build_dataset(
    input_dir: Path = DEFAULT_INPUT_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    *,
    ratios: tuple[float, float, float] = (0.8, 0.1, 0.1),
    seed: int = 42,
) -> BuildSummary:
    """Build train, development and test CSV files from clean JSONL files."""
    records = load_records(input_dir)
    splits = stratified_split(records, ratios=ratios, seed=seed)
    output_dir.mkdir(parents=True, exist_ok=True)

    staged_paths: dict[str, Path] = {}
    try:
        with tempfile.TemporaryDirectory(
            dir=output_dir, prefix=".pipeline-"
        ) as staging:
            staging_dir = Path(staging)
            for split, split_records in splits.items():
                staged_path = staging_dir / f"{split}.csv"
                _write_csv(staged_path, split_records)
                staged_paths[split] = staged_path
            for split in SPLIT_NAMES:
                os.replace(staged_paths[split], output_dir / f"{split}.csv")
    except OSError as exc:
        raise PipelineError(f"Cannot write CSV files to {output_dir}: {exc}") from exc

    split_counts = {
        split: len(split_records) for split, split_records in splits.items()
    }
    label_counts = Counter(_label(record) for record in records)
    return BuildSummary(
        total=len(records),
        split_counts=split_counts,
        label_counts=dict(label_counts),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build stratified train/dev/test CSVs from clean article JSONL files."
    )
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--dev-ratio", type=float, default=0.1)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    return parser


def main() -> None:
    """Run the pipeline from the command line."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = _parser()
    args = parser.parse_args()
    try:
        summary = build_dataset(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            ratios=(args.train_ratio, args.dev_ratio, args.test_ratio),
            seed=args.seed,
        )
    except PipelineError as exc:
        parser.error(str(exc))
    logger.info(
        "Built %d rows: train=%d, dev=%d, test=%d (label 0=%d, unlabeled=%d)",
        summary.total,
        summary.split_counts["train"],
        summary.split_counts["dev"],
        summary.split_counts["test"],
        summary.label_counts.get("0", 0),
        summary.label_counts.get("", 0),
    )
