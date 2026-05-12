# DF-KPM-Drawdown-Monitor [CRUX-MK]

**Welle-42 Foundation-DF: Variante-D-Compliance-Monitor**
**Per `~/.claude/rules/kpm-sizing.md`**

## Zweck

Überwacht Drawdown-Caps fuer KPM-Familien-Vermoegen:
- Soft-Brake 15%: Position-Reduktion 50% + Review-Pflicht
- Hard-Cap 20%: Trading-Pause + Martin-Phronesis-Gate
- Absolute-No-Go 25%: Familien-Notfall-Protokoll
- HIVE-Score-Check: >0.7 = Leverage-OK, <0.5 = auto-Deleverage

## K_0-MAX-Berührung

Direct-Überwachung Familien-Vermoegen-Drawdown.
- Sandbox-Default mit Mock-Drawdown-Time-Series
- Phronesis-Pflicht Martin pre-Real-Mode
- ENV-Var: `DF_KPM_DRAWDOWN_REAL_ENABLED=false`

[CRUX-MK]
