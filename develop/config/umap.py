#!/usr/bin/env python3
"""
UMAP pipeline for initial cases with full join features.

This script mirrors umap_initial_cases_with_outcomes.ipynb and:
- fits UMAP on initial cases,
- persists model + feature artifacts,
- transforms new cases without retraining.
"""

from __future__ import annotations

import argparse
import json
import pickle
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler

try:
    import umap
except ImportError as exc:  # pragma: no cover - runtime guard
    raise ImportError("umap-learn is required. Install with: pip install umap-learn") from exc


CONFIG_DIR = Path(__file__).resolve().parent


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _normalize_list(values: Any) -> List[str]:
    if values is None:
        return []
    if isinstance(values, list):
        return [str(v).strip().lower() for v in values if v is not None]
    return [str(values).strip().lower()]


def _normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip().lower()
    return value


def _extract_menu_id(menu_item: Any) -> Any:
    if isinstance(menu_item, dict):
        return menu_item.get("id")
    return menu_item


def _normalize_case_schema(case: Dict[str, Any]) -> Dict[str, Any]:
    if "event" in case and "starter" in case:
        return dict(case)
    if "request" in case and "menu" in case:
        req = case.get("request") or {}
        menu = case.get("menu") or {}
        return {
            "id": case.get("id"),
            "event": req.get("event_type"),
            "season": req.get("season"),
            "price_min": req.get("price_min"),
            "price_max": req.get("price_max"),
            "num_guests": req.get("num_guests"),
            "required_diets": req.get("required_diets", []),
            "restricted_ingredients": req.get("restricted_ingredients", []),
            "starter": _extract_menu_id(menu.get("starter")),
            "main": _extract_menu_id(menu.get("main_course")),
            "dessert": _extract_menu_id(menu.get("dessert")),
            "beverage": _extract_menu_id(menu.get("beverage")),
            "style": req.get("preferred_style") or menu.get("dominant_style"),
            "culture": req.get("cultural_preference") or menu.get("cultural_theme"),
            "success": case.get("success", True),
            "feedback": case.get("feedback_score", case.get("feedback", 0.0)),
        }
    return dict(case)


def _normalize_case_values(case: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(case)
    for key in ["event", "season", "style", "culture"]:
        normalized[key] = _normalize_value(normalized.get(key))
    normalized["required_diets"] = _normalize_list(normalized.get("required_diets"))
    normalized["restricted_ingredients"] = _normalize_list(
        normalized.get("restricted_ingredients")
    )
    return normalized


def normalize_cases(cases: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []
    for case in cases:
        norm_case = _normalize_case_schema(case)
        norm_case = _normalize_case_values(norm_case)
        normalized.append(norm_case)
    return normalized


def validate_case_refs(
    cases: List[Dict[str, Any]],
    dishes_by_id: Dict[str, Dict[str, Any]],
    beverages_by_id: Dict[str, Dict[str, Any]],
) -> None:
    missing = {"starter": set(), "main": set(), "dessert": set(), "beverage": set()}
    for case in cases:
        for key in ["starter", "main", "dessert"]:
            value = case.get(key)
            if value not in dishes_by_id:
                missing[key].add(value)
        bev = case.get("beverage")
        if bev not in beverages_by_id:
            missing["beverage"].add(bev)
    missing_counts = {k: len(v) for k, v in missing.items() if v}
    if missing_counts:
        raise ValueError(f"Missing dish/beverage ids: {missing_counts}")


def _build_ingredient_maps(ingredients_data: Dict[str, Any]) -> Tuple[Dict[str, set], Dict[str, Any]]:
    groups = ingredients_data["groups"]
    ingredient_meta_raw = ingredients_data.get("ingredient_to_cultures", {})
    ingredient_meta = {}
    for key, value in ingredient_meta_raw.items():
        ingredient_meta[key.strip().lower()] = value

    ingredient_to_groups = defaultdict(set)
    for group_name, items in groups.items():
        for item in items:
            item_key = item.strip().lower()
            ingredient_to_groups[item_key].add(group_name)

    return ingredient_to_groups, ingredient_meta


def _collect_ingredient_features(
    ingredients: Iterable[str],
    ingredient_to_groups: Dict[str, set],
    ingredient_meta: Dict[str, Any],
) -> Tuple[List[str], List[str], List[str], List[str], List[str]]:
    raw = set()
    group_set = set()
    culture_set = set()
    noncompliant_set = set()
    unmapped = []
    for item in ingredients:
        key = str(item).strip().lower()
        if not key:
            continue
        raw.add(key)
        if key in ingredient_to_groups:
            group_set.update(ingredient_to_groups[key])
        else:
            unmapped.append(key)
        meta = ingredient_meta.get(key)
        if meta:
            culture_set.update(meta.get("cultures", []))
            noncompliant_set.update(meta.get("non_compliant_labels", []))
    return (
        sorted(raw),
        sorted(group_set),
        sorted(culture_set),
        sorted(noncompliant_set),
        unmapped,
    )


def build_feature_frame(
    cases: List[Dict[str, Any]],
    dishes_by_id: Dict[str, Dict[str, Any]],
    beverages_by_id: Dict[str, Dict[str, Any]],
    ingredients_data: Dict[str, Any],
) -> Tuple[pd.DataFrame, Counter]:
    ingredient_to_groups, ingredient_meta = _build_ingredient_maps(ingredients_data)

    case_base_cols = [
        "event",
        "season",
        "num_guests",
        "required_diets",
        "restricted_ingredients",
        "style",
        "culture",
        "success",
        "feedback",
        "price_min",
        "price_max",
    ]

    dish_num_fields = ["price", "calories", "max_guests"]
    dish_cat_fields = ["dish_type", "category", "complexity", "temperature"]
    dish_list_fields = ["styles", "seasons", "flavors", "diets", "compatible_beverages"]

    rows = []
    unmapped_counter = Counter()

    for case in cases:
        row = {col: case.get(col) for col in case_base_cols}
        row["success"] = int(bool(row.get("success")))
        row["required_diets"] = row.get("required_diets") or []
        row["restricted_ingredients"] = row.get("restricted_ingredients") or []

        for course in ["starter", "main", "dessert"]:
            dish = dishes_by_id[case.get(course)]
            for field in dish_num_fields:
                row[f"{course}_{field}"] = dish.get(field)
            for field in dish_cat_fields:
                row[f"{course}_{field}"] = dish.get(field)
            for field in dish_list_fields:
                row[f"{course}_{field}"] = dish.get(field) or []

            raw, groups_found, cultures_found, noncompliant_found, unmapped = (
                _collect_ingredient_features(
                    dish.get("ingredients", []), ingredient_to_groups, ingredient_meta
                )
            )
            unmapped_counter.update(unmapped)
            row[f"{course}_ingredients"] = raw
            row[f"{course}_ingredient_groups"] = groups_found
            row[f"{course}_ingredient_cultures"] = cultures_found
            row[f"{course}_ingredient_noncompliant"] = noncompliant_found

        beverage = beverages_by_id[case.get("beverage")]
        row["beverage_price"] = beverage.get("price")
        row["beverage_alcoholic"] = int(bool(beverage.get("alcoholic")))
        row["beverage_type"] = beverage.get("type")
        row["beverage_subtype"] = beverage.get("subtype") or "none"

        rows.append(row)

    feature_df = pd.DataFrame(rows)
    return feature_df, unmapped_counter


def _binarize_list_column(
    df: pd.DataFrame, column: str, prefix: str, classes: Optional[List[str]]
) -> Tuple[pd.DataFrame, List[str]]:
    values = df[column].apply(lambda x: x if isinstance(x, list) else [])
    if classes is None:
        mlb = MultiLabelBinarizer()
        data = mlb.fit_transform(values)
        classes = list(mlb.classes_)
    else:
        mlb = MultiLabelBinarizer(classes=classes)
        mlb.fit([[]])
        data = mlb.transform(values)
    if data.size == 0:
        return pd.DataFrame(index=df.index), classes
    return (
        pd.DataFrame(
            data,
            columns=[f"{prefix}__{c}" for c in classes],
            index=df.index,
        ),
        classes,
    )


def build_feature_matrix(
    feature_df: pd.DataFrame,
    fit: bool,
    artifacts: Optional[Dict[str, Any]] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    list_cols = {
        "required_diets": "required_diet",
        "restricted_ingredients": "restricted_ing",
    }
    for course in ["starter", "main", "dessert"]:
        list_cols.update(
            {
                f"{course}_styles": f"{course}_style",
                f"{course}_seasons": f"{course}_season",
                f"{course}_flavors": f"{course}_flavor",
                f"{course}_diets": f"{course}_diet",
                f"{course}_compatible_beverages": f"{course}_compat_bev",
                f"{course}_ingredients": f"{course}_ingredient",
                f"{course}_ingredient_groups": f"{course}_ingredient_group",
                f"{course}_ingredient_cultures": f"{course}_ingredient_culture",
                f"{course}_ingredient_noncompliant": f"{course}_ingredient_noncompliant",
            }
        )

    list_frames = []
    list_classes = {} if fit else artifacts.get("list_classes", {})
    for col, prefix in list_cols.items():
        classes = None if fit else list_classes.get(col, [])
        frame, classes = _binarize_list_column(feature_df, col, prefix, classes)
        list_frames.append(frame)
        if fit:
            list_classes[col] = classes

    list_ohe_df = pd.concat(list_frames, axis=1)

    cat_cols = [
        "event",
        "season",
        "style",
        "culture",
        "beverage_type",
        "beverage_subtype",
    ]
    for course in ["starter", "main", "dessert"]:
        cat_cols.extend(
            [
                f"{course}_dish_type",
                f"{course}_category",
                f"{course}_complexity",
                f"{course}_temperature",
            ]
        )

    cat_df = feature_df[cat_cols].copy()
    for col in cat_cols:
        cat_df[col] = cat_df[col].fillna("none").astype(str).str.lower()
    cat_df = pd.get_dummies(cat_df, prefix=cat_cols, dtype=int)

    if fit:
        cat_columns = list(cat_df.columns)
    else:
        cat_columns = artifacts.get("cat_columns", [])
        cat_df = cat_df.reindex(columns=cat_columns, fill_value=0)

    numeric_cols = [
        "num_guests",
        "price_min",
        "price_max",
        "feedback",
        "beverage_price",
    ]
    for course in ["starter", "main", "dessert"]:
        numeric_cols.extend(
            [
                f"{course}_price",
                f"{course}_calories",
                f"{course}_max_guests",
            ]
        )

    numeric_df = feature_df[numeric_cols].fillna(0)
    if fit:
        scaler = StandardScaler()
        numeric_scaled = scaler.fit_transform(numeric_df)
    else:
        scaler = artifacts["scaler"]
        numeric_scaled = scaler.transform(numeric_df)
    numeric_scaled = pd.DataFrame(
        numeric_scaled,
        columns=[f"num__{c}" for c in numeric_cols],
        index=feature_df.index,
    )

    binary_cols = ["success", "beverage_alcoholic"]
    binary_df = feature_df[binary_cols].fillna(0).astype(int)

    X_df = pd.concat([numeric_scaled, cat_df, list_ohe_df, binary_df], axis=1)

    if fit:
        feature_columns = list(X_df.columns)
    else:
        feature_columns = artifacts.get("feature_columns", [])
        X_df = X_df.reindex(columns=feature_columns, fill_value=0)

    artifacts_out = {
        "list_classes": list_classes,
        "cat_columns": cat_columns,
        "numeric_cols": numeric_cols,
        "binary_cols": binary_cols,
        "feature_columns": feature_columns,
        "scaler": scaler,
    }

    return X_df, artifacts_out


def build_embedding_output(
    cases: List[Dict[str, Any]],
    embedding: np.ndarray,
) -> List[Dict[str, Any]]:
    records = []
    for idx, case in enumerate(cases):
        record = {
            "case_index": idx,
            "case_id": case.get("id"),
            "event": case.get("event"),
            "season": case.get("season"),
            "style": case.get("style"),
            "culture": case.get("culture"),
            "success": bool(case.get("success")),
            "feedback": case.get("feedback"),
            "price_min": case.get("price_min"),
            "price_max": case.get("price_max"),
            "num_guests": case.get("num_guests"),
            "starter": case.get("starter"),
            "main": case.get("main"),
            "dessert": case.get("dessert"),
            "beverage": case.get("beverage"),
            "umap_1": float(embedding[idx, 0]),
            "umap_2": float(embedding[idx, 1]),
        }
        records.append(record)
    return records


def fit_umap(
    cases: List[Dict[str, Any]],
    dishes_by_id: Dict[str, Dict[str, Any]],
    beverages_by_id: Dict[str, Dict[str, Any]],
    ingredients_data: Dict[str, Any],
    n_neighbors: int,
    min_dist: float,
    metric: str,
    random_state: int,
) -> Tuple[np.ndarray, Dict[str, Any], Any]:
    feature_df, _ = build_feature_frame(cases, dishes_by_id, beverages_by_id, ingredients_data)
    X_df, artifacts = build_feature_matrix(feature_df, fit=True)
    if len(X_df) < 2:
        raise ValueError("Need at least 2 cases to fit UMAP.")
    nn = min(n_neighbors, max(2, len(X_df) - 1))
    reducer = umap.UMAP(
        n_neighbors=nn,
        min_dist=min_dist,
        metric=metric,
        random_state=random_state,
    )
    embedding = reducer.fit_transform(X_df.values)
    return embedding, artifacts, reducer


def transform_cases(
    cases: List[Dict[str, Any]],
    dishes_by_id: Dict[str, Dict[str, Any]],
    beverages_by_id: Dict[str, Dict[str, Any]],
    ingredients_data: Dict[str, Any],
    artifacts: Dict[str, Any],
    reducer: Any,
) -> np.ndarray:
    feature_df, _ = build_feature_frame(cases, dishes_by_id, beverages_by_id, ingredients_data)
    X_df, _ = build_feature_matrix(feature_df, fit=False, artifacts=artifacts)
    return reducer.transform(X_df.values)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="UMAP pipeline for CBR cases.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fit_parser = subparsers.add_parser("fit", help="Fit UMAP on initial cases.")
    fit_parser.add_argument(
        "--cases",
        type=Path,
        default=CONFIG_DIR / "initial_cases.json",
        help="Path to cases JSON (default: initial_cases.json).",
    )
    fit_parser.add_argument(
        "--output",
        type=Path,
        default=CONFIG_DIR / "umap_embeddings.json",
        help="Output JSON for embeddings.",
    )
    fit_parser.add_argument(
        "--model",
        type=Path,
        default=CONFIG_DIR / "umap_model.pkl",
        help="Output path for UMAP model pickle.",
    )
    fit_parser.add_argument(
        "--spec",
        type=Path,
        default=CONFIG_DIR / "umap_feature_spec.pkl",
        help="Output path for feature artifacts pickle.",
    )
    fit_parser.add_argument("--n-neighbors", type=int, default=15)
    fit_parser.add_argument("--min-dist", type=float, default=0.1)
    fit_parser.add_argument("--metric", type=str, default="cosine")
    fit_parser.add_argument("--random-state", type=int, default=42)

    transform_parser = subparsers.add_parser("transform", help="Transform new cases.")
    transform_parser.add_argument(
        "--cases",
        type=Path,
        required=True,
        help="Path to cases JSON to transform.",
    )
    transform_parser.add_argument(
        "--output",
        type=Path,
        default=CONFIG_DIR / "umap_embeddings_new.json",
        help="Output JSON for embeddings.",
    )
    transform_parser.add_argument(
        "--model",
        type=Path,
        default=CONFIG_DIR / "umap_model.pkl",
        help="Path to UMAP model pickle.",
    )
    transform_parser.add_argument(
        "--spec",
        type=Path,
        default=CONFIG_DIR / "umap_feature_spec.pkl",
        help="Path to feature artifacts pickle.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    dishes = _load_json(CONFIG_DIR / "dishes.json")
    beverages = _load_json(CONFIG_DIR / "beverages.json")
    ingredients_data = _load_json(CONFIG_DIR / "ingredients.json")

    dishes_by_id = {d["id"]: d for d in dishes}
    beverages_by_id = {b["id"]: b for b in beverages}

    cases_payload = _load_json(args.cases)
    raw_cases = cases_payload.get("cases", cases_payload)
    cases = normalize_cases(raw_cases)

    validate_case_refs(cases, dishes_by_id, beverages_by_id)

    if args.command == "fit":
        embedding, artifacts, reducer = fit_umap(
            cases,
            dishes_by_id,
            beverages_by_id,
            ingredients_data,
            n_neighbors=args.n_neighbors,
            min_dist=args.min_dist,
            metric=args.metric,
            random_state=args.random_state,
        )
        records = build_embedding_output(cases, embedding)

        with args.output.open("w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=True)
        with args.model.open("wb") as f:
            pickle.dump(reducer, f)
        with args.spec.open("wb") as f:
            pickle.dump(artifacts, f)

        print(f"Saved embeddings: {args.output}")
        print(f"Saved model: {args.model}")
        print(f"Saved feature spec: {args.spec}")

    elif args.command == "transform":
        with args.model.open("rb") as f:
            reducer = pickle.load(f)
        with args.spec.open("rb") as f:
            artifacts = pickle.load(f)

        embedding = transform_cases(
            cases,
            dishes_by_id,
            beverages_by_id,
            ingredients_data,
            artifacts,
            reducer,
        )
        records = build_embedding_output(cases, embedding)
        with args.output.open("w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=True)
        print(f"Saved embeddings: {args.output}")


if __name__ == "__main__":
    main()
