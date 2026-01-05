# 🛡️ ALL-WEATHER CRISIS MODE

## Vad är det?

När marknaden är i **CRISIS-läge** (>90% RED signals), aktiverar systemet automatiskt **All-Weather Mode**.

**Filosofi:** "När kasinot bränner, lämna inte byggnaden – byt till det brandsäkra bordet."

---

## Hur fungerar det?

### 1. Normal CRISIS-behandling (0.2x multiplier)
```
AAPL GREEN signal → 5% position → 5% * 0.2 = 1% (nästan värdelöst)
```

### 2. All-Weather CRISIS-behandling (1.0x multiplier)
```
GLD GREEN signal → 5% position → 5% * 1.0 = 5% (FULL SIZE)
SH GREEN signal → 3% position → 3% * 1.0 = 3% (FULL SIZE)
```

### 3. Defensive Sectors (0.5x multiplier vid GREEN)
```
XLU (Utilities) GREEN signal → 4% position → 4% * 0.5 = 2% (halverad, men inte crushed)
```

---

## All-Weather Instruments

### Inverse ETFs (tjänar när marknaden faller)
- **SH** - ProShares Short S&P500
- **PSQ** - ProShares Short QQQ
- **DOG** - ProShares Short Dow30
- **RWM** - ProShares Short Russell 2000

**Avanza-alternativ:** XACT Bear, XACT Bear 2, eller certifikat på inversen

---

### Safe Havens (traditionellt kriskapital)
- **GLD** - SPDR Gold Trust
- **IAU** - iShares Gold Trust
- **TLT** - 20+ Year Treasury Bonds
- **IEF** - 7-10 Year Treasury Bonds
- **SHY** - 1-3 Year Treasury Bonds
- **BIL** - 1-3 Month T-Bills (cash equivalent)

**Avanza-alternativ:** XACT Guld (GULD), obligationsfonder, penningmarknadsfonder

---

### Volatility Plays (tjänar på rädsla)
- **VIXY** - VIX Short-Term Futures
- **VIXM** - VIX Mid-Term Futures

**Avanza-alternativ:** Volatilitetscertifikat, VIX-warrants

---

### Defensive Sectors (får 0.5x vid GREEN i CRISIS)
- **XLU** - Utilities Select Sector
- **XLP** - Consumer Staples
- **VDC** - Vanguard Consumer Staples

---

## Workflow i CRISIS

### Daglig Analys
```bash
python daglig_analys.py
```

**Om CRISIS-läge detekteras:**

```
🚨 MARKNADSLÄGE: CRISIS
RED: 231 | YELLOW: 13 | GREEN: 1

🛡️ ALL-WEATHER OPPORTUNITIES:
1. GLD (Gold) - GREEN
   Net Edge: +1.2%
   Position: 2.5% (Full size - All Weather Protection)
   💡 Avanza: XACT Guld (GULD) eller certifikat på guld
   
2. SH (Short S&P500) - YELLOW
   Net Edge: +0.8%
   Position: 1.5% (Full size - All Weather Protection)
   💡 Avanza: XACT Bear eller certifikat på inversen S&P500

3. XLU (Utilities) - GREEN
   Net Edge: +0.5%
   Position: 1.0% (Defensive sector - 0.5x allocation)
```

---

## Avanza-mappningar

| Ticker | US ETF | Avanza-alternativ |
|--------|--------|-------------------|
| GLD | SPDR Gold Trust | XACT Guld (GULD) |
| SH | ProShares Short S&P500 | XACT Bear |
| PSQ | ProShares Short QQQ | XACT Bear 2 |
| TLT | 20+ Year Treasury | Obligationsfonder (räntefonder långa) |
| BIL | 1-3 Month T-Bills | Penningmarknadsfond |
| VIXY | VIX Short-Term | Volatilitetscertifikat |

---

## Teknisk Implementation

### Position Size Multipliers

```python
# Normal instrument in CRISIS
multiplier = 0.2  # Crushed

# All-Weather instrument in CRISIS
if is_all_weather(ticker):
    multiplier = 1.0  # FULL SIZE

# Defensive sector with GREEN signal in CRISIS
if is_defensive_sector(ticker) and signal == 'GREEN':
    multiplier = 0.5  # Half size
```

### Priority Sorting

Dashboard prioriterar All-Weather signaler först:

```python
if regime == "CRISIS":
    all_weather_signals = [sig for sig in signals if is_all_weather(sig.ticker)]
    normal_signals = [sig for sig in signals if not is_all_weather(sig.ticker)]
    
    # All-Weather first
    signals = all_weather_signals + normal_signals
```

---

## Exempel: CRISIS till HEALTHY

### Vid CRISIS (95% RED)
```
Portfolio:
- GLD: 5% (All-Weather)
- SH: 3% (All-Weather)
- XLU: 2% (Defensive)
Total: 10%
```

### Vid återhämtning → HEALTHY (40% RED)
```
Portfolio:
- AAPL: 5% (Normal tech)
- MSFT: 4% (Normal tech)
- NVDA: 3% (Normal tech)
- GLD: 2% (Keep some protection)
Total: 14%
```

---

## Filosofi: Ray Dalio's All-Weather

Detta system är inspirerat av Ray Dalio's "All-Weather Portfolio":

**Traditional thinking:** "Diversifiera över aktier, bonds, commodities"

**All-Weather thinking:** "Ha tillgångar som tjänar i ALLA ekonomiska regimer"

**Vårt system:**
- **Bull market (HEALTHY):** Normal aktieallokering
- **Bear market (CRISIS):** Inverses + Safe havens + Defensive sectors

---

## Varningar

⚠️ **Inverse ETFs är komplexa**
- SH/PSQ/DOG är dagligen rebalanserade
- Fungerar bäst för kortsiktig hedging (veckor, inte månader)
- Läs prospekt innan köp

⚠️ **Volatility ETFs är extremt volatila**
- VIXY/VIXM kan förlora 80%+ på en månad
- Endast för erfarna traders
- Använd mycket små positioner (0.5-1% max)

⚠️ **Guld är inte alltid säkert**
- Kan falla i likviditetskriser (2008-style)
- Fungerar bäst vid stagflation eller valutakris

---

## Nästa steg efter implementation

1. **Kör daglig analys:** `python daglig_analys.py`
2. **Verifiera All-Weather detection:** GLD/SH ska ha 1.0x multiplier vid CRISIS
3. **Testa Avanza-mappningar:** Se att dashboard visar Avanza-alternativ
4. **Övervaka defensive sectors:** XLU/XLP ska få 0.5x vid GREEN i CRISIS

---

**Co-Authored-By: Warp <agent@warp.dev>**
