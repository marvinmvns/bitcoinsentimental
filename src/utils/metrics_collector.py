import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class AlertRule:
    metric: str
    condition: str  # 'gt' or 'lt'
    threshold: float
    severity: str
    message: str


class MetricsCollector:
    """Simple in-memory metrics collector with optional persistence."""

    def __init__(self, storage_file: Optional[Path] = None):
        self.storage_file = storage_file or (
            Path.home() / '.btc-trading' / 'metrics.json'
        )
        self.metrics: List[Dict] = []
        self.alerts: List[Dict] = []
        self.rules: List[AlertRule] = []
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    # ------------------------------------------------------------------
    def _load(self) -> None:
        if self.storage_file.exists():
            try:
                data = json.loads(self.storage_file.read_text())
                self.metrics = data.get('metrics', [])
                self.alerts = data.get('alerts', [])
            except Exception:
                # Se falhar ao carregar, iniciar vazio
                self.metrics = []
                self.alerts = []

    def _save(self) -> None:
        try:
            data = {'metrics': self.metrics, 'alerts': self.alerts}
            self.storage_file.write_text(json.dumps(data, indent=2))
        except Exception:
            pass  # Não interromper fluxo se salvar falhar

    # ------------------------------------------------------------------
    def add_alert_rule(
        self,
        metric: str,
        condition: str,
        threshold: float,
        severity: str,
        message: str,
    ) -> None:
        self.rules.append(
            AlertRule(metric, condition, threshold, severity, message)
        )

    def record_metric(
        self, name: str, value: float, unit: Optional[str] = None
    ) -> None:
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'name': name,
            'value': value
        }
        if unit:
            entry['unit'] = unit
        self.metrics.append(entry)
        self._check_alerts(name, value)
        self._save()

    # ------------------------------------------------------------------
    def _check_alerts(self, name: str, value: float) -> None:
        for rule in self.rules:
            if rule.metric != name:
                continue
            triggered = False
            if rule.condition == 'gt' and value > rule.threshold:
                triggered = True
            elif rule.condition == 'lt' and value < rule.threshold:
                triggered = True
            if triggered:
                self.alerts.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'metric': name,
                    'value': value,
                    'severity': rule.severity,
                    'message': rule.message
                })

    # ------------------------------------------------------------------
    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = []
        for alert in self.alerts:
            try:
                ts = datetime.fromisoformat(alert['timestamp'])
            except Exception:
                continue
            if ts >= cutoff:
                recent.append(alert)
        return sorted(recent, key=lambda x: x['timestamp'], reverse=True)


# Instância global usada pela CLI
metrics_collector = MetricsCollector()
