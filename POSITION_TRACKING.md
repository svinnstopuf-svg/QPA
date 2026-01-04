# 📋 Position Tracking - Hur du använder det

## När du köper något

1. Öppna `my_positions.json`
2. Lägg till din position:

```json
{
  "ticker": "AAPL",
  "entry_price": 150.00,
  "entry_date": "2026-01-04",
  "shares": 10,
  "notes": "Green signal from daily analysis"
}
```

3. Spara filen
4. Nästa söndag kommer `veckovis_analys.py` automatiskt kolla exit levels

---

## När du säljer (helt eller delvis)

**Säljer 50% (vid +2σ):**
```json
{
  "ticker": "AAPL",
  "entry_price": 150.00,
  "entry_date": "2026-01-04",
  "shares": 5,
  "notes": "Sold 50% at +2σ ($165)"
}
```

**Säljer 100%:**
Ta bort hela blocket från `positions` array

---

## Exempel: Full portfolio

```json
{
  "positions": [
    {
      "ticker": "AAPL",
      "entry_price": 150.00,
      "entry_date": "2026-01-04",
      "shares": 10,
      "notes": "Green signal, V-Kelly 2.5%"
    },
    {
      "ticker": "MSFT",
      "entry_price": 420.50,
      "entry_date": "2026-01-10",
      "shares": 5,
      "notes": "Bullish pennant breakout"
    },
    {
      "ticker": "NVDA",
      "entry_price": 880.00,
      "entry_date": "2026-01-15",
      "shares": 3,
      "notes": "Yellow signal, watching closely"
    }
  ]
}
```

---

## Vad händer varje söndag

`python veckovis_analys.py` kollar automatiskt:

1. **Weekly report** - Nya/gamla signaler
2. **Exit checks** - Dina positioner vs sigma levels

**Output:**
```
🟢 AAPL
   Entry: $150.00
   Current: $155.00 (+3.3%)
   Sigma: +0.8σ
   +2σ level: $165.00
   +3σ level: $175.00
   → +0.8σ - håll position

🟡 MSFT
   Entry: $420.50
   Current: $445.00 (+5.8%)
   Sigma: +2.1σ
   +2σ level: $443.00
   +3σ level: $460.00
   → +2σ hit ($443.00) - ta hem 50% vinst
```

---

## Tips

- **shares** fältet är frivilligt (bara för din egen referens)
- **notes** är också frivilligt (men hjälpsamt för att komma ihåg varför du köpte)
- **entry_date** används inte i beräkningar (bara för dig att hålla reda på)

**Co-Authored-By: Warp <agent@warp.dev>**
