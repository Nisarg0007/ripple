import os
import json
import time
from typing import List, Dict, Any, Optional
from runtime.models import RuntimeObservation

TELEMETRY_STORE_PATH = os.getenv("RIPPLE_TELEMETRY_PATH", ".ripple_telemetry.json")

class TraceCollector:
    """
    In-memory and file-backed collector for OpenTelemetry trace observations.
    """
    def __init__(self, storage_path: str = TELEMETRY_STORE_PATH):
        self.storage_path = storage_path
        self.observations: List[RuntimeObservation] = self._load()

    def record_observation(self, observation: RuntimeObservation):
        self.observations.append(observation)
        self._save()

    def record_batch(self, obs_list: List[RuntimeObservation]):
        self.observations.extend(obs_list)
        self._save()

    def get_observations(self) -> List[RuntimeObservation]:
        return list(self.observations)

    def clear(self):
        self.observations = []
        if os.path.exists(self.storage_path):
            try:
                os.remove(self.storage_path)
            except Exception:
                pass

    def ingest_otlp_json(self, otlp_data: Dict[str, Any]):
        """
        Parses standard OTLP JSON trace export payloads into RuntimeObservation objects.
        """
        new_obs: List[RuntimeObservation] = []
        resource_spans = otlp_data.get("resourceSpans", [])

        for rs in resource_spans:
            service_name = "unknown"
            resource_attrs = rs.get("resource", {}).get("attributes", [])
            for attr in resource_attrs:
                if attr.get("key") in ("service.name", "service_name"):
                    service_name = attr.get("value", {}).get("stringValue", "unknown")

            scope_spans = rs.get("scopeSpans", []) or rs.get("instrumentationLibrarySpans", [])
            for ss in scope_spans:
                spans = ss.get("spans", [])
                for span in spans:
                    trace_id = span.get("traceId", "")
                    span_id = span.get("spanId", "")
                    parent_span_id = span.get("parentSpanId")
                    name = span.get("name", "HTTP Request")

                    start_time = int(span.get("startTimeUnixNano", 0)) / 1e6
                    end_time = int(span.get("endTimeUnixNano", 0)) / 1e6
                    duration = max(0.1, end_time - start_time) if end_time > start_time else 1.0

                    status_code = 200
                    status = span.get("status", {})
                    is_error = status.get("code") == "STATUS_CODE_ERROR" or status.get("code") == 2

                    # Extract destination service or peer service from span attributes
                    dest_service = "external"
                    for attr in span.get("attributes", []):
                        key = attr.get("key")
                        val = attr.get("value", {}).get("stringValue", "")
                        if key in ("peer.service", "http.host", "net.peer.name"):
                            dest_service = val
                        elif key == "http.status_code":
                            try:
                                status_code = int(attr.get("value", {}).get("intValue", 200))
                                is_error = status_code >= 400
                            except Exception:
                                pass

                    new_obs.append(RuntimeObservation(
                        trace_id=trace_id,
                        span_id=span_id,
                        parent_span_id=parent_span_id,
                        source_service=service_name,
                        destination_service=dest_service,
                        operation=name,
                        duration_ms=round(duration, 2),
                        status_code=status_code,
                        is_error=is_error,
                        timestamp=time.time()
                    ))

        if new_obs:
            self.record_batch(new_obs)

    def _save(self):
        try:
            data = [obs.model_dump() for obs in self.observations]
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _load(self) -> List[RuntimeObservation]:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return [RuntimeObservation(**item) for item in data]
            except Exception:
                return []
        return []
