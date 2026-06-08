# df-kpm-drawdown-monitor — PRODUKTION [CRUX-MK]
*2026-06-07T23:41:59.193592+00:00 | ollama-local/kemmer-70b-ctx8k*

# DF-KPM-Drawdown-Monitor Dokumentation
## Einleitung
Der DF-KPM-Drawdown-Monitor ist ein entscheidender Bestandteil der Dark Fac
Factory-Infrastruktur, entwickelt um das finanzielle Risiko durch Drawdowns
Drawdowns in den Familien-Vermögen zu minimieren. Durch die Implementierung
Implementierung spezifischer Regeln und Überwachungsmechanismen soll sicher
sichergestellt werden, dass kritische Schwellen nicht überschritten werden,
werden, ohne dass entsprechende Gegenmaßnahmen ergriffen werden.

## Zweck und Umfang
Der DF-KPM-Drawdown-Monitor überwacht die Drawdown-Caps für Familien-Vermög
Familien-Vermögen in Echtzeit. Die Überwachung basiert auf einem dynamische
dynamischen Kelly-Fraktionsmodell mit kontextadaptem Währungsspektrum zwisc
zwischen 0,25 und 0,40. Diese Anpassungen werden durch eine HIVE-Scorer-Wer
HIVE-Scorer-Wertkontrolle unterstützt:

- **HIVE-Score > 0,7:** Zugelassene Leverage-Operationen.
- **HIVE-Score < 0,5:** Automatische Deleveraging-Prozesse werden ausgelöst
ausgelöst.

### Spezifikationen
Die Überwachungslogik basiert auf folgenden Schwellen:

- **Soft-Brake:** Bei einem Drawdown von 15% wird eine Positionsenkung um 5
50% vorgenommen und ein Review-Prozess initiiert.
- **Hard-Cap:** Bei einer Drawdown-Grenze von 20% setzt die Plattform autom
automatisch eine Trading-Pause und löst einen Phronesis-Frageprozess (Marti
(Martin-Phronesis-Gate) aus.
- **Absolute No-Go:** Ein Drawdown von 25% löst das Familien-Notfallprotoko
Familien-Notfallprotokoll aus, was dringende finanzielle Maßnahmen erforder
erfordert.

## Operationelle Details
Die Monitor-Funktion nutzt die Datei `~/.claude/rules/kpm-sizing.md` als Re
Regelsatz und ist durch eine Sandbox-Umgebung mit Mock-Drawdown-Time-Series
Mock-Drawdown-Time-Series definiert, um im Testmodus die Richtigkeit der Lo
Logik zu überprüfen. Der Übergang zur Real-Mode (Echtzeitüberwachung) erfol
erfolgt nur nach Phronesis-Pflichterfüllung durch Martin und ein explizites
explizites Aktivierungssignal (`DF_KPM_DRAWDOWN_REAL_ENABLED=true`).

## Implementierung
Die Implementierung des DF-KPM-Drawdown-Monitors umfasst folgende Schritte:
Schritte:

1. **Regelsatz-Einbindung:** Integrieren der Regeln aus `~/.claude/rules/kp
`~/.claude/rules/kpm-sizing.md` in die Überwachungslogik.
2. **HIVE-Score-Integration:** Einbinden des HIVE-Scorers, um den Score zu 
berechnen und basierend darauf Leverage-Operationen zuzulassen oder Delever
Deleveraging-Prozesse auszulösen.
3. **Sandbox-Testung:** Durchführung von Testläufen in der Sandbox-Umgebung
Sandbox-Umgebung, um die Funktionalität und Genauigkeit des Monitors zu übe
überprüfen.
4. **Real-Mode-Aktivierung:** Nach erfolgreicher Testung und Phronesis-Pfli
Phronesis-Pflichterfüllung wird der Monitor in den Real-Modus geschaltet.

## Datenfelder
Die Überwachungsdaten werden in der Datei `src/kpm_trading_monitor.py` defi
definiert, die folgende Felder enthält:

- **timestamp_iso:** Zeitstempel für jede Messung.
- **portfolio_value_eur:** Aktuelles Portfoliowert in EUR.
- **drawdown_pct:** Drawdown-Prozentsatz seit dem Höchststand.
- **drawdown_state:** Enum-Wert, der den aktuellen Zustand des Drawdowns be
beschreibt (Soft-Brake, Hard-Cap, Absolute-No-Go).

## Umgebungsbereiche
Die Monitor-Funktion hängt von zwei Umgebungsvariablen ab:

- `DF_KPM_DRAWDOWN_REAL_ENABLED`: Aktiviert den Echtzeit-Monitoring-Modus.
- `PHRONESIS_TICKET`: Gilt als Bestätigung, dass die Phronesis-Pflichten er
erfüllt wurden und der Monitor in den Real-Modus geschaltet werden kann.

## Betrieb und Wartung
Der DF-KPM-Drawdown-Monitor ist so konzipiert, dass er mit minimaler manuel
manueller Intervention betrieben werden kann. Regelmäßige Updates und Wartu
Wartungen sind jedoch notwendig, um sicherzustellen, dass der Monitor weite
weiterhin effektiv und zuverlässig arbeitet.

## Fazit
Der DF-KPM-Drawdown-Monitor ist ein entscheidender Bestandteil der Risikoma
Risikomanagementstrategie für die Familien-Vermögen. Durch seine Fähigkeit,
Fähigkeit, Drawdowns in Echtzeit zu überwachen und entsprechende Gegenmaßna
Gegenmaßnahmen auszulösen, kann er dazu beitragen, finanzielle Verluste zu 
minimieren und die Stabilität der Vermögenswerte zu gewährleisten.

## Anhang
### Glossar
- **Drawdown:** Der prozentuale Verlust des Portfoliowerts im Vergleich zum
zum Höchststand.
- **HIVE-Score:** Ein Score, der die Leverage-Operationen und Deleveraging-
Deleveraging-Prozesse steuert.
- **Phronesis-Pflicht:** Die Pflicht, sicherzustellen, dass alle notwendige
notwendigen Schritte unternommen wurden, bevor der Monitor in den Real-Modu
Real-Modus geschaltet wird.

### Literaturverzeichnis
- `~/.claude/rules/kpm-sizing.md`
- `src/kpm_trading_monitor.py`

### Versionshistorie
- **1.0:** Erste Version des DF-KPM-Drawdown-Monitors.
- **1.1:** Aktualisierung der Regeln und der HIVE-Score-Logik.

## Sicherheitsaspekte
Der DF-KPM-Drawdown-Monitor ist so konzipiert, dass er die Sicherheit und I
Integrität der Daten gewährleistet. Alle Daten werden verschlüsselt übertra
übertragen und gespeichert. Der Zugriff auf den Monitor ist nur autorisiert
autorisierten Personen möglich.

## Zukunftsausblick
Der DF-KPM-Drawdown-Monitor wird kontinuierlich weiterentwickelt und verbes
verbessert, um sicherzustellen, dass er den aktuellen Anforderungen gerecht
gerecht wird. Geplante Updates umfassen die Integration neuer Regeln und di
die Verbesserung der HIVE-Score-Logik.

## Kontakt
Für weitere Informationen oder Fragen zum DF-KPM-Drawdown-Monitor können Si
Sie uns unter `support@df-kpm-monitor.de` kontaktieren. Wir freuen uns auf 
Ihre Anfrage.