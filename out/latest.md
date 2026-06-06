# df-kpm-drawdown-monitor — Output [CRUX-MK]
*Autonom aktiviert 2026-06-05T10:53:18.591064+00:00 | ollama-local/qwen2.5:14b-instruct*

# DF-KPM-Drawdown-Monitor Dokumentation

## Zweck und Umfang
Die Dark Factory `df-kpm-drawdown-monitor` überwacht die Drawdown-Caps für 
Familien-Vermögen in Echtzeit. Sie berücksichtigt spezifische Regeln, um da
das finanzielle Risiko durch Positionenreduktion und Trading-Pausen zu mini
minimieren.

### Spezifikationen

- **Soft-Brake:** Bei einem Drawdown von 15% wird eine Positionsenkung um 5
50% vorgenommen und ein Review-Prozess initiiert.
- **Hard-Cap:** Bei einer Drawdown-Grenze von 20% setzt die Plattform autom
automatisch eine Trading-Pause und löst einen Phronesis-Frageprozess (Marti
(Martin-Phronesis-Gate) aus.
- **Absolute No-Go:** Ein Drawdown von 25% löst das Familien-Notfallprotoko
Familien-Notfallprotokoll aus, was dringende finanzielle Maßnahmen erforder
erfordert.

### Überwachungskriterien
Die Überwachungslogik basiert auf einem dynamischen Kelly-Fraktionsmodell m
mit kontextadaptem Währungsspektrum zwischen 0.25 und 0.40. Diese Anpassung
Anpassungen werden durch eine HIVE-Scorer-Wertkontrolle unterstützt:

- **HIVE-Score > 0.7:** Zugelassene Leverage-Operationen.
- **HIVE-Score < 0.5:** Automatische Deleveraging-Prozesse werden ausgelöst
ausgelöst.

### Operationelle Details
Die Monitor-Funktion nutzt die Datei `~/.claude/rules/kpm-sizing.md` als Re
Regelsatz und ist durch eine Sandbox-Umgebung mit Mock-Drawdown-Time-Series
Mock-Drawdown-Time-Series definiert, um im Testmodus die Richtigkeit der Lo
Logik zu überprüfen. Der Übergang zur Real-Mode (Echtzeitüberwachung) erfol
erfolgt nur nach Phronesis-Pflichterfüllung durch Martin und ein explizites
explizites Aktivierungssignal (`DF_KPM_DRAWDOWN_REAL_ENABLED=true`).

### Datenfelder
Die Überwachungsdaten werden in der Datei `src/kpm_trading_monitor.py` defi
definiert, die folgende Felder enthält:

- **timestamp_iso**: Zeitstempel für jede Messung.
- **portfolio_value_eur**: Aktuelles Portfoliowert in EUR.
- **drawdown_pct**: Drawdown-Prozentsatz seit dem Höchststand.
- **drawdown_state**: Enum-Wert, der den aktuellen Zustand des Drawdowns be
beschreibt (Soft-Brake, Hard-Cap, Absolute-No-Go).

### Umgebungsbereiche
Die Monitor-Funktion hängt von zwei Umgebungsvariablen ab:

- `DF_KPM_DRAWDOWN_REAL_ENABLED`: Aktiviert den Echtzeit-Monitoring-Modus.
- `PHRONESIS_TICKET`: Gilt als Bestätigung, dass die Phronesis-Pflichten er
erfüllt wurden und der Monitor in der Real-Mode betrieben werden kann.

Diese Dokumentation stellt sicher, dass alle relevanten Überwachungsregeln 
klar definiert sind und die Familie Kemmer über eine präzise und flexible M
Methode zur Risikomanagement verfügt.