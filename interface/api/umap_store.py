import json
import pickle
from pathlib import Path
from typing import Any, Dict, List

from develop.config import umap as umap_pipeline


class UmapStore:
    def __init__(self, config_dir: Path = None):
        self.config_dir = config_dir or umap_pipeline.CONFIG_DIR
        self.embedding_path = self.config_dir / "umap_embeddings.json"
        self.model_path = self.config_dir / "umap_model.pkl"
        self.spec_path = self.config_dir / "umap_feature_spec.pkl"
        self._embeddings_cache: List[Dict[str, Any]] = []

    def _load_embeddings(self) -> List[Dict[str, Any]]:
        with self.embedding_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def ensure_fit(self) -> None:
        if not (self.embedding_path.exists() and self.model_path.exists() and self.spec_path.exists()):
            self._fit_initial()
        if not self._embeddings_cache:
            self._embeddings_cache = self._load_embeddings()

    def _fit_initial(self) -> None:
        dishes = umap_pipeline._load_json(self.config_dir / "dishes.json")
        beverages = umap_pipeline._load_json(self.config_dir / "beverages.json")
        ingredients_data = umap_pipeline._load_json(self.config_dir / "ingredients.json")
        cases_payload = umap_pipeline._load_json(self.config_dir / "initial_cases.json")

        dishes_by_id = {d["id"]: d for d in dishes}
        beverages_by_id = {b["id"]: b for b in beverages}

        raw_cases = cases_payload.get("cases", cases_payload)
        cases = umap_pipeline.normalize_cases(raw_cases)

        umap_pipeline.validate_case_refs(cases, dishes_by_id, beverages_by_id)

        embedding, artifacts, reducer = umap_pipeline.fit_umap(
            cases,
            dishes_by_id,
            beverages_by_id,
            ingredients_data,
            n_neighbors=15,
            min_dist=0.1,
            metric="cosine",
            random_state=42,
        )
        records = umap_pipeline.build_embedding_output(cases, embedding)

        with self.embedding_path.open("w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=True)
        with self.model_path.open("wb") as f:
            pickle.dump(reducer, f)
        with self.spec_path.open("wb") as f:
            pickle.dump(artifacts, f)

        self._embeddings_cache = records

    def get_embeddings(self) -> List[Dict[str, Any]]:
        self.ensure_fit()
        return self._embeddings_cache

    def transform_cases(self, cases_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        self.ensure_fit()

        dishes = umap_pipeline._load_json(self.config_dir / "dishes.json")
        beverages = umap_pipeline._load_json(self.config_dir / "beverages.json")
        ingredients_data = umap_pipeline._load_json(self.config_dir / "ingredients.json")
        dishes_by_id = {d["id"]: d for d in dishes}
        beverages_by_id = {b["id"]: b for b in beverages}

        raw_cases = cases_payload.get("cases", cases_payload)
        cases = umap_pipeline.normalize_cases(raw_cases)
        umap_pipeline.validate_case_refs(cases, dishes_by_id, beverages_by_id)

        with self.model_path.open("rb") as f:
            reducer = pickle.load(f)
        with self.spec_path.open("rb") as f:
            artifacts = pickle.load(f)

        embedding = umap_pipeline.transform_cases(
            cases,
            dishes_by_id,
            beverages_by_id,
            ingredients_data,
            artifacts,
            reducer,
        )
        return umap_pipeline.build_embedding_output(cases, embedding)

    def upsert_case_embedding(self, case_payload: Dict[str, Any]) -> Dict[str, Any]:
        self.ensure_fit()

        records = self.transform_cases({"cases": [case_payload]})
        if not records:
            raise ValueError("Failed to build embedding for retained case.")

        record = records[0]
        case_id = record.get("case_id")
        if not case_id:
            raise ValueError("Retained case missing case_id for embedding.")

        existing_index = next(
            (idx for idx, item in enumerate(self._embeddings_cache) if item.get("case_id") == case_id),
            None,
        )
        if existing_index is None:
            record["case_index"] = len(self._embeddings_cache)
            self._embeddings_cache.append(record)
        else:
            record["case_index"] = self._embeddings_cache[existing_index].get("case_index", existing_index)
            self._embeddings_cache[existing_index] = record

        return record
