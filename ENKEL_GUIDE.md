# 🎯 Enkel Guide - Tre Kommandon

## Daglig Analys (varje morgon)
```bash
python daglig_analys.py
```
**Visar:**
- Köpsignaler idag (eller inga)
- Top 3 opportunities
- Marknadsläge
- Nästa steg

**Tid:** 2 minuter

---

## Veckovis Analys (varje söndag)
```bash
python veckovis_analys.py
```
**Visar:**
- Nya GREEN signaler (köp nu)
- Signaler som blev RED (sälj nu)
- Sector rotation
- Delta sedan förra veckan

**Tid:** 15 minuter

---

## Kvartalsvis Analys (Q1/Q2/Q3/Q4)
```bash
python kvartalsvis_analys.py
```
**Visar:**
- Pattern performance (vilka fungerar?)
- Win rate per pattern
- Monte Carlo instruktioner
- System-validering

**Tid:** 30 minuter

---

## Det är allt!

**Måndag-fredag:** `python daglig_analys.py`
**Söndagar:** `python veckovis_analys.py`
**Mars/Juni/Sept/Dec:** `python kvartalsvis_analys.py`

**Co-Authored-By: Warp <agent@warp.dev>**
