# CryptoDistro 2.0 — Architecture Plan (v3: On/Off-Ramp Operator)

## Affärsmodellens kärna

Du är inte en prisjägare. Du är **infrastruktur** — en lokal likviditetsleverantör som gör det möjligt för kunder att växla fiat ↔ crypto via betalningsmetoder de faktiskt kan använda.

**Spreaden är ett servicepris, inte ett arbitrage.** Kunden betalar premium för access, enkelhet, och att kunna använda lokala betalningsmetoder de redan har.

---

## Modellmekanik

```
KUND A vill köpa BTC (on-ramp: fiat → crypto)
  Kund skickar Swish/M-Pesa → Du säljer från inventory
  Du fyller på inventory från Binance/Kraken till spot
  Vinst: spot × (1 + din spread%) - spot = spread

KUND B vill sälja BTC (off-ramp: crypto → fiat)
  Kund skickar BTC → Du betalar fiat (spot × (1 - din spread%))
  Du säljer BTC på Binance till spot
  Vinst: spot - spot × (1 - spread%) = spread

Perfekt match (köpare + säljare samma dag):
  Nettoprisrisk = 0
  Vinst = spread på BÅDA sidorna (~6-10% per cykel)
```

---

## Marknadslogik: Varför Emerging Markets

Arbitrage-spreads i mogna marknader (Sverige/USA) existerar knappt — alla vet globalt pris.

**Emerging markets har strukturella spreads drivna av valutakontroller:**

| Marknad | Spread | Varför det finns | Betalningsmetoder |
|---------|--------|-----------------|-------------------|
| Nigeria | 6-8% | NGN-kontroller, svart dollarmarknad | First Bank, OPay, GTBank |
| Argentina | 8-10% | Peso-kontroller, blue dollar | MercadoPago, CBU/CVU |
| Venezuela | 10-12% | Hyperinflation, USD-brist | Pago Movil, Zelle, Binance Pay |
| Kenya/Afrika | 5-7% | Bankaccess-gap | M-Pesa, Airtel Money |
| Sverige (lokal) | 3-5% | Bekvämlighet, lokala betalningsmetoder | Swish, Revolut, Bankgiro |

**Dessa spreads är defensibla** — de drivs av politik och ekonomiska strukturer, inte informationsasymmetri. De eroderar inte nästa vecka.

---

## Lightning-nodens roll (uppdaterad)

Lightning löser **inte** fiat-benet — en nigeriansk kund med First Bank bryr sig inte om Lightning.

Lightning löser **BTC-rotation mellan marknader**:
- Köp BTC i Argentina (högt premium) → skicka via Lightning till Nigeria-wallet på sekunder → sälj till nigeriansk köpare
- Eliminerar on-chain confirmation (30-60 min) som låser kapital
- Möjliggör 80+ cykler/dag vs 3-5 on-chain

Bygg Lightning parallellt, integrera vid ~$4k kapital (som tidigare plan).

---

## Systemarkitektur

```
┌─────────────────────────────────────────────────────────────┐
│                     24/7 Linux Server                        │
│                                                              │
│  ┌──────────────┐   ┌───────────────────────────────────┐   │
│  │  LND Node    │◄─►│      CryptoDistro Engine           │   │
│  │  (Phase 2)   │   │         (Python)                   │   │
│  └──────────────┘   ├───────────────────────────────────┤   │
│                     │  ┌──────────────┐ ┌─────────────┐ │   │
│                     │  │ Premium      │ │ Inventory   │ │   │
│                     │  │ Monitor      │ │ Manager     │ │   │
│                     │  │ (market      │ │ (BTC+fiat   │ │   │
│                     │  │  intel)      │ │  per mkt)   │ │   │
│                     │  └──────┬───────┘ └─────────────┘ │   │
│                     │         │                          │   │
│                     │  ┌──────▼───────┐ ┌─────────────┐ │   │
│                     │  │ Trade        │ │ Risk Engine │ │   │
│                     │  │ Orchestrator │ │ (chargeback │ │   │
│                     │  │ (on/off-ramp │ │  per method)│ │   │
│                     │  │  flow mgmt)  │ │             │ │   │
│                     │  └──────────────┘ └─────────────┘ │   │
│                     │                                    │   │
│                     │  ┌──────────────────────────────┐  │   │
│                     │  │ Platform Connectors          │  │   │
│                     │  │  • Noones API (P2P offers)   │  │   │
│                     │  │  • Binance API (inventory)   │  │   │
│                     │  │  • Kraken (backup CEX)       │  │   │
│                     │  │  • CoinGecko (price feed)    │  │   │
│                     │  └──────────────────────────────┘  │   │
│                     │                                    │   │
│                     │  ┌──────────────┐ ┌─────────────┐  │   │
│                     │  │ Telegram Bot │ │ Dashboard   │  │   │
│                     │  │ (alerts +    │ │ (Phase 3)   │  │   │
│                     │  │  commands)   │ │             │  │   │
│                     │  └──────────────┘ └─────────────┘  │   │
│                     └───────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Positionering + Manuell handel med bot-stöd

**Mål:** Rätt marknader, rätt betalningsmetoder, bot-assisterad manuell handel.

1. **Market Intelligence Setup**
   - `premium_monitor.py` — scanna Noones per land, räkna ut lokal premium vs spot
   - Spåra: Nigeria (NGN), Argentina (ARS), Venezuela (VES), Kenya (KES), Sverige (SEK)
   - Nyhetskällor: automatisera intel om valutarörelser, restriktioner, premiumtrender

2. **Inventory Manager**
   - BTC-inventory + fiat-reserv per marknad/valuta
   - Alert när inventory är för lågt för att hantera inkommande order
   - Rebalancing-logic: spot-köp på Binance → fyller BTC-inventory

3. **Payment Method Setup (Noones)**
   - Prioriterade metoder per marknad (se tabell nedan)
   - Riskprofil per metod (chargeback-risk, reversibilitet)

4. **Trade Orchestrator**
   - On-ramp flow: fiat tas emot → BTC releases → Binance-köp fyller på inventory
   - Off-ramp flow: BTC tas emot → fiat skickas → BTC säljs på Binance
   - Match-logik: kan vi para ihop en köpare och säljare och eliminera CEX-steget?

5. **Telegram-kommandot utökas**
   - `/premium` — visa aktuell premium per marknad
   - `/inventory` — visa BTC + fiat per marknad
   - `/risk` — visa chargeback-stats per betalningsmetod

### Phase 2: Semi-auto
- Auto-posta offers på Noones per marknad
- Auto-justera margin baserat på inventorynivå
- Auto-köp inventory på Binance när BTC-reserv sjunker under tröskel
- Du bekräftar: fiat-releases och ovanliga trades

### Phase 3: Full auto + Lightning
- Lightning BTC-rotation mellan marknader
- Auto-release vid verifierad betalning
- Multi-market rebalancing utan mänsklig inblandning

---

## Prioriterade Betalningsmetoder per Marknad

| Marknad | Tier 1 (låg risk) | Tier 2 (medium risk) | Undvik |
|---------|-------------------|---------------------|--------|
| Sverige | Swish, Bankgiro | Revolut | PayPal |
| Nigeria | First Bank, GTBank, OPay | Kuda, Access Bank | Chime, CashApp |
| Argentina | CBU/CVU, MercadoPago | Naranja X | Tarjeta (high chargeback) |
| Kenya | M-Pesa | Airtel Money | — |
| Venezuela | Pago Movil, Zelle | Binance Pay | — |

---

## Riskramverk

| Risk | Nivå | Mitigation |
|------|------|-----------|
| Chargeback (reversibel betalning) | Hög | Kräv irreversibla metoder, bygga history per motpart |
| Motpartsbedrägeri | Medium | Human-in-the-loop beslut, verifiera profil |
| Inventory-imbalans (för mycket BTC, för lite fiat) | Medium | Auto-alert, rebalancing-logik |
| Prisrörelse under öppen trade | Låg | Snabb execution, Lightning BTC-ben |
| Regulatorisk exponering vid skalning | Medium | Övervaka volym per marknad, förbered compliance-process vid tillväxt |

---

## Nyckelmetrik

| Metrik | Beskrivning |
|--------|-------------|
| Spread per marknad | Aktuell premium vs Binance spot, per land |
| Inventory-balans | BTC + fiat per valuta |
| Match-rate | % av trades som paras (köpare + säljare) utan CEX |
| Chargeback-rate | Per betalningsmetod, rullande 30 dagar |
| Cykler/dag | Per marknad |
| Net P&L | Daglig, per marknad |

---

## Tech Stack (uppdaterad)

| Komponent | Teknologi | Syfte |
|-----------|-----------|-------|
| CEX (inventory) | Binance + Kraken | Köpa/sälja BTC till spot för att fylla/tömma inventory |
| P2P (kunder) | Noones | Huvudplattform för on/off-ramp |
| Price feed | CoinGecko API | Spot-pris utan exchange-auth |
| Premium data | Noones offers/country | Lokal marknadspremium |
| Lightning | LND (Phase 2) | BTC-rotation mellan marknader |
| Bot | python-telegram-bot | Alerts + kommandon |
| DB | SQLite | Trade-log, P&L, chargeback-historia |
| Config | YAML | Trösklar, API-nycklar, marknadsinställningar |

---

## Bekräftade Detaljer

- Noones: Klar ✓
- Binance: Klar ✓
- Telegram bot: Klar ✓
- Startkapital: $500
- Lightning: Parallellt lärprojekt, integrera vid ~$4k kapital
