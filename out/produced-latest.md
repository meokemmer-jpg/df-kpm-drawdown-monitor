# df-kpm-drawdown-monitor — PRODUKTION [CRUX-MK]
*2026-06-09T15:57:16.902954+00:00 | ollama-local/kemmer-14b-ctx8k*

# DF-KPM-Drawdown-Monitor Dokumentation

## Zweck und Umfang

Die Dark Factory `df-kpm-drawdown-monitor` überwacht die Drawdown-Caps für Familien-Vermögen in Echtzeit. Sie berücksichtigt spezifische Regeln, um das finanzielle Risiko durch Positionsenkung und Trading-Pausen zu minimieren.

### Spezifikationen

- **Soft-Brake:** Bei einem Drawdown von 7,5% wird eine Positionsenkung um 25% vorgenommen und ein Review-Prozess initiiert. Dieser Wert wurde aufgrund der KPM-Schwellwerte angepasst, die einen früheren Warnhinweis erlauben.
- **Hard-Cap:** Bei einer Drawdown-Grenze von 10% setzt die Plattform automatisch eine Trading-Pause und löst einen Phronesis-Frageprozess (Martin-Phronesis-Gate) aus. Dies entspricht den KPM-Schwellwerten, um drastische Verluste zu verhindern.
- **Absolute No-Go:** Ein Drawdown von 12,5% löst das Familien-Notfallprotokoll aus, was dringende finanzielle Maßnahmen erfordert. Dies entspricht der maximalen Toleranzgrenze des Vermögensmanagement.

### Überwachungskriterien
Die Überwachungslogik basiert auf einem dynamischen Kelly-Fraktionsmodell mit kontextadaptem Währungsspektrum zwischen 0.25 und 0.40. Diese Anpassungen werden durch eine HIVE-Scorer-Wertkontrolle unterstützt:

- **HIVE-Score > 0.7:** Zugelassene Leverage-Operationen.
- **HIVE-Score < 0.5:** Automatische Deleveraging-Prozesse werden ausgelöst.

### Operationelle Details
Die Monitor-Funktion nutzt die Datei `~/.claude/rules/kpm-sizing.md` als Regelsatz und ist durch eine Sandbox-Umgebung mit Mock-Drawdown-Time-Series definiert, um im Testmodus die Richtigkeit der Logik zu überprüfen. Der Übergang zur Real-Mode (Echtzeitüberwachung) erfolgt nur nach Phronesis-Pflichterfüllung durch Martin und ein explizites Aktivierungssignal (`DF_KPM_DRAWDOWN_REAL_ENABLED=true`).

### Datenfelder
Die Überwachungsdaten werden in der Datei `src/kpm_trading_monitor.py` definiert, die folgende Felder enthält:

- **timestamp_iso**: Zeitstempel für jede Messung.
- **portfolio_value_eur**: Aktuelles Portfoliowert in EUR.
- **drawdown_pct**: Drawdown-Prozentsatz seit dem Höchststand.
- **drawdown_state**: Enum-Wert, der den aktuellen Zustand des Drawdowns beschreibt (Soft-Brake, Hard-Cap, Absolute-No-Go).

### Umgebungsbereiche
Die Monitor-Funktion hängt von zwei Umgebungsvariablen ab:

- `DF_KPM_DRAWDOWN_REAL_ENABLED`: Aktiviert den Echtzeit-Monitoring-Modus.
- `PHRONESIS_TICKET`: Gilt als Bestätigung, dass die Phronesis-Pflichten erfüllt wurden und der Monitor in Real-Mode betrieben wird.

## Implementierungsdetails

### KPM Variante-D (Drawdown-Caps)

Die KPM-Variante D verwendet Drawdown-Grenzwerte:

| Stufe | Drawdown-Prozent | Aktion |
|-------|------------------|--------|
| Soft-Brake | 7,5% | Positionen reduzieren um 25%, Review-Pflicht eingeleitet. |
| Hard-Cap | 10% | Trading-Pause, Phronesis-Frageprozess aktiviert (Martin-Phronesis-Gate). |
| Absolute-No-Go | 12,5% | Familien-Notfallprotokoll ausgelöst, dringende finanzielle Maßnahmen notwendig. |

### Integration in Dark Factory System

Die Drawdown-Monitor-Funktion wird integriert in das Dark Factory System:

| Stufe | CapLevel | DF-Aktion |
|-------|----------|-----------|
| Soft-Brake | 7,5% | Positionsenkung um 25%, Review-Pflicht. |
| Hard-Cap | 10% | Trading-Pause eingeleitet, Phronesis-Frageprozess aktiviert (Martin-Phronesis-Gate). |
| Absolute-No-Go | 12,5% | Familien-Notfallprotokoll ausgelöst, notwendige finanzielle Maßnahmen durchgeführt. |

### Sandbox-Umgebung

Im Testmodus läuft die Drawdown-Monitor-Funktion in einer Sandbox-Umgebung mit Mock-Daten:

- **Mock-Time-Series:** Eine fiktive Zeitreihen-Datensatz wird verwendet, um den Drawdown-Prozentsatz zu simulieren.
- **Review-Pflicht:** Bei erreichen des Soft-Brake-Level (7,5%) wird ein Review-Prozess initiiert.
- **Trading-Pause:** Bei Erreichung des Hard-Cap-Level (10%) wird eine Trading-Pause eingeleitet.

### Phronesis-Kontrolle

Bevor die Drawdown-Monitor-Funktion in Real-Mode betrieben wird, muss der Phronesis-Prozess durch Martin abgeschlossen sein:

- **Phronesis-Ticket:** Ein Phronesis-Ticket bestätigt das erfolgreiche Abschließen des Phronesis-Prozesses.
- **Aktivierungssignal:** Der Befehl `DF_KPM_DRAWDOWN_REAL_ENABLED=true` aktiviert den Echtzeit-Monitoring-Modus.

## Datenfelder und Umgebungsbereiche

### Überwachungsdaten in `src/kpm_trading_monitor.py`

Die Datei enthält die folgenden Felder:

```python
class DrawdownMonitorData:
    def __init__(self, timestamp_iso: str, portfolio_value_eur: float, drawdown_pct: float, drawdown_state: Enum):
        self.timestamp_iso = timestamp_iso  # Zeitstempel für jede Messung.
        self.portfolio_value_eur = portfolio_value_eur  # Aktuelles Portfoliowert in EUR.
        self.drawdown_pct = drawdown_pct  # Drawdown-Prozentsatz seit dem Höchststand.
        self.drawdown_state = drawdown_state  # Enum-Wert, der den aktuellen Zustand des Drawdowns beschreibt (Soft-Brake, Hard-Cap, Absolute-No-Go).
```

### Umgebungsbereiche

- `DF_KPM_DRAWDOWN_REAL_ENABLED`: Diese Variable steuert die Aktivierung des Echtzeit-Monitoring-Modus. Wenn sie auf "true" gesetzt wird, startet der Monitor in Real-Time.
- `PHRONESIS_TICKET`: Ein Bestätigungs-Ticket, dass alle Phronesis-Pflichten erfüllt sind.

## Überwachung und Protokollierung

### Soft-Brake-Level (7,5%)

Bei erreichen dieses Levels wird eine Positionsenkung um 25% vorgenommen und ein Review-Prozess initiiert. Die Daten werden protokolliert und die Familie Kemmer benachrichtigt.

### Hard-Cap-Level (10%)

In diesem Fall setzt die Plattform automatisch eine Trading-Pause und löst einen Phronesis-Frageprozess aus, um sicherzustellen, dass alle notwendigen Maßnahmen ergriffen werden. Die Familie Kemmer wird über die Situation informiert.

### Absolute-No-Go-Level (12,5%)

Bei Erreichen dieses Levels wird das Familien-Notfallprotokoll aktiviert und dringende finanzielle Maßnahmen durchgeführt. Dies schließt ein sofortiges Handeln mit den betroffenen Finanzinstituten ein.

## Schlussfolgerung

Die Dark Factory `df-kpm-drawdown-monitor` bietet eine effektive Methode zur Echtzeit-Überwachung und Minimierung des finanziellen Risikos durch Drawdown-Caps. Durch die Integration der KPM-Variante D in das DF-System können drastische Verluste vermieden werden und Sicherheitsmaßnahmen frühzeitig initiiert werden.