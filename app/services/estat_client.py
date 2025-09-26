"""Utilities for retrieving statistics from the e-Stat API."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from pydantic import BaseModel, Field, ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

try:
    import streamlit as st
except ModuleNotFoundError:  # pragma: no cover
    st = None  # type: ignore

logger = logging.getLogger(__name__)


class EstatValue(BaseModel):
    """Subset of VALUE object returned by e-Stat."""

    cat01: Optional[str] = Field(default=None, alias="@cat01")
    area: Optional[str] = Field(default=None, alias="@area")
    time: Optional[str] = Field(default=None, alias="@time")
    tab: Optional[str] = Field(default=None, alias="@tab")
    class_code: Optional[str] = Field(default=None, alias="@classCode")
    value: Optional[str] = Field(default=None, alias="$")


class EstatClassObj(BaseModel):
    """Represents metadata for a classification object."""

    id: str = Field(alias="@id")
    name: str = Field(alias="@name")
    description: Optional[str] = Field(default=None, alias="@description")
    items: Dict[str, str] = Field(default_factory=dict)


class EstatClient:
    """Simple e-Stat API client with caching and retry support."""

    BASE_URL = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"

    def __init__(self, app_id: str, *, timeout: int = 30) -> None:
        self.app_id = app_id
        self.timeout = timeout

    def _cache(self):
        if st is None:
            def decorator(func):
                return func

            return decorator
        return st.cache_data(show_spinner=False, ttl=3600)

    def _normalize_meta(self, class_objs: List[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
        lookup: Dict[str, Dict[str, str]] = {}
        for obj in class_objs:
            try:
                classes = obj.get("CLASS", [])
                if isinstance(classes, dict):
                    classes = [classes]
                parsed = EstatClassObj(
                    id=obj.get("@id", ""),
                    name=obj.get("@name", ""),
                    description=obj.get("@description"),
                    items={item.get("@code", ""): item.get("@name", "") for item in classes},
                )
            except ValidationError as exc:  # pragma: no cover - defensive
                logger.warning("Failed to parse class object: %s", exc)
                continue
            lookup[parsed.id] = parsed.items
        return lookup

    def _values_to_frame(self, values: List[Dict[str, Any]], lookup: Dict[str, Dict[str, str]]) -> pd.DataFrame:
        records: List[Dict[str, Any]] = []
        for raw in values:
            try:
                if hasattr(EstatValue, "model_validate"):
                    value_obj = EstatValue.model_validate(raw)  # type: ignore[attr-defined]
                else:  # pragma: no cover - compatibility for Pydantic v1
                    value_obj = EstatValue.parse_obj(raw)
            except ValidationError as exc:
                logger.debug("Skipping invalid VALUE row: %s", exc)
                continue
            record: Dict[str, Any] = {
                "cat01": lookup.get("cat01", {}).get(value_obj.cat01 or "", value_obj.cat01),
                "area": lookup.get("area", {}).get(value_obj.area or "", value_obj.area),
                "time": lookup.get("time", {}).get(value_obj.time or "", value_obj.time),
                "tab": value_obj.tab,
                "class_code": value_obj.class_code,
            }
            try:
                record["value"] = float(value_obj.value) if value_obj.value not in (None, "-") else None
            except ValueError:
                record["value"] = None
            records.append(record)
        if not records:
            return pd.DataFrame(columns=["cat01", "area", "time", "tab", "class_code", "value"])
        frame = pd.DataFrame.from_records(records)
        return frame

    def _make_params(self, stats_data_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        api_params = {"appId": self.app_id, "statsDataId": stats_data_id}
        api_params.update(params)
        return api_params

    def list_class_objs(self, stats_data_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, str]]:
        """Return metadata mapping for classification codes."""

        response = self._request(stats_data_id, params=params or {}, raw=True)
        class_objs = response.get("CLASS_INF", {}).get("CLASS_OBJ", [])
        return self._normalize_meta(class_objs)

    def get(self, stats_data_id: str, params: Dict[str, Any]) -> pd.DataFrame:
        """Retrieve and normalize statistics data as a DataFrame."""

        cached_get = self._cache()(self._request)
        response = cached_get(stats_data_id, params=params, raw=False)
        values = response.get("DATA_INF", {}).get("VALUE", [])
        class_objs = response.get("CLASS_INF", {}).get("CLASS_OBJ", [])
        lookup = self._normalize_meta(class_objs)
        frame = self._values_to_frame(values, lookup)
        return frame

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=True)
    def _request(self, stats_data_id: str, params: Dict[str, Any], *, raw: bool) -> Dict[str, Any]:
        api_params = self._make_params(stats_data_id, params)
        response = requests.get(self.BASE_URL, params=api_params, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json().get("STATISTICAL_DATA", {})
        if raw:
            return payload
        status = payload.get("RESULT", {}).get("STATUS")
        if status != 0:
            message = payload.get("RESULT", {}).get("ERROR_MSG", "e-Stat API returned an error")
            raise RuntimeError(message)
        return payload

