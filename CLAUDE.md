# CryptoDistro 2.0 — Project Context

## Business Model
P2P on/off-ramp operator. Buy BTC at spot on Binance. Sell to customers in emerging markets via Noones at a structural premium (6–12%). Earn the spread as a service fee. The premium is driven by currency controls and USD access scarcity — not information asymmetry. It is structurally stable.

## Key Discovery: Noones has built-in Lightning
NoOnes has an integrated Lightning wallet. No need for a separate Lightning node, channel management, uptime monitoring, or channel.db backups. BTC leg settles in seconds. The fiat leg (buyer sending Mercado Pago / First Bank Nigeria / Zelle) takes 15–30 min and cannot be automated — that is the real bottleneck.

## Simulation Model Parameters
Source: `EmergingMarkets/noones_lightning_simulator_260315.html`

```
START_CAPITAL     = $500
BASE_TRADE_SIZE   = $60
MAX_TRADE_SIZE    = $200

# Cycles per day (Lightning)
cycles_per_day = floor(60 / fiat_verification_minutes × active_hours_per_day)

# Reputation ramp (days 1–10)
rep_factor = 0.35 + 0.65 × (day / 10)   # day <= 10
rep_factor = 1.0                          # day > 10

# Chargeback rates
CB_LIGHTNING   = 1.2% / week  (Lightning buyers are more tech-savvy)
CB_ONCHAIN     = 2.5% / week

# On-chain cycles (for comparison)
onchain_cycles = floor(1.3 × active_hours)  # ~45 min confirmation time
```

## Market Scenarios
| Scenario      | Market     | Spread | Fiat verif. | Hours/day |
|---------------|------------|--------|-------------|-----------|
| Conservative  | Nigeria    | 6%     | 25 min      | 8h        |
| Realistic     | Argentina  | 9%     | 20 min      | 10h       |
| Optimistic    | Venezuela  | 12%    | 15 min      | 12h       |

## Fiat Refill Loop (after a sale)
Fiat lands outside Noones (Skrill, Zelle, OPay, Mercado Pago). Must buy BTC and send via Lightning to Noones to refill stock.

| Fiat method         | Buy BTC via          | Lightning wallet | → Noones |
|---------------------|----------------------|------------------|----------|
| Skrill              | Skrill built-in      | Phoenix / Blink  | instant  |
| Nigeria mobile money| iPayBTC              | Phoenix / Blink  | instant  |
| Mercado Pago (ARS)  | MT Pelerin           | Phoenix / Blink  | instant  |
| Zelle (USD)         | Ramp Network/MoonPay | Phoenix / Blink  | instant  |

Recommended Lightning wallets: Phoenix (best overall), Blink (fastest small amounts), Wallet of Satoshi (easiest UI).

## Scaling Logic
```
$500 capital × Lightning velocity ≈ $1,500–$2,000 on-chain equivalent volume
```
Velocity advantage: 2–4× vs on-chain (not 100× as with a dedicated node — fiat verification is now the ceiling, not BTC settlement). Scaling ceiling = human time to verify fiat payments. Delegatable once volume is validated.

## Architecture Layers (Lager model)
- **Lager 1** (Scanning): Fully automated. Market premiums, competitor offers, FX rates.
- **Lager 2** (CEX execution): Fully automated. Buy BTC back on Binance after each sale.
- **Lager 3** (P2P counterparty): Human-in-the-loop. Verify fiat, release escrow, assess risk.

## Target Markets (in priority order)
1. **Nigeria (NGN)** — largest Africa volume, First Bank / GTBank / OPay
2. **Argentina (ARS)** — high demand, Mercado Pago, fast settlement
3. **Venezuela (VES)** — Zelle (USD-denominated, eliminates FX risk on fiat leg)
4. **Kenya (KES)** — M-Pesa, low chargeback risk
5. **Sweden (SEK)** — home market, Swish, low spread but reliable

## Regulatory Position
Noones does not target Europe as primary market and is not MiCA-licensed. P2P advertiser function is fully operational. No KYB barrier to posting offers.
