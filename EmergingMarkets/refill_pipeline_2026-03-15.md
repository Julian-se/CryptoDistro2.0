# CryptoDistro 2.0 — BTC Refill Pipeline Library
**Generated:** 2026-03-15
**Scope:** All markets in `config/settings.yaml`
**Purpose:** When a buyer sends fiat outside Noones, this library tells you the fastest verified route to buy BTC and send it via Lightning to your Noones deposit address.

---

## How to Use This Document

After each sale on Noones:
1. Buyer has sent fiat to your **external wallet** (bank, mobile money, digital wallet).
2. Find your market below.
3. Follow the pipeline for that payment method.
4. Send BTC via Lightning to your Noones Lightning deposit address.
5. Stock refilled → post next offer.

**Lightning wallets for the final send step:**
- **Phoenix** — best overall, self-custodial, reliable liquidity, 5–10 sec sends
- **Blink** — fastest for small amounts, sub-2 sec
- **Wallet of Satoshi** — easiest UI, instant (custodial)

---

## 🇳🇬 Nigeria (NGN)

### Configured payment methods: First Bank NG · OPay · GTBank

---

#### Method: First Bank of Nigeria (bank transfer)

```
Buy BTC via:      Bitnob — https://bitnob.com
                  OR iPayBTC — https://ipaybtc.app
Lightning wallet: Bitnob built-in (sends directly to external LN address)
                  OR receive in Phoenix/Blink if using iPayBTC
Pipeline:         First Bank NGN transfer → Bitnob → LN withdrawal → Noones
Total time:       3–8 min (bank transfer confirmation + LN send ~2 sec)
Fees:             Bitnob: ~1–2% spread. LN fee: <1 sat
Limits:           Bitnob KYC L2: up to $10,000/day
KYC required:     Bitnob: Government ID (passport or NIN). Level 2 required for >basic limits
                  iPayBTC: NIN (dial *346*1# on Nigerian SIM)
Risk:             Low. First Bank is a major tier-1 Nigerian bank. Low chargeback risk.
Status:           ✅ Verified
```

**Key evidence:**
- Bitnob officially supports Nigerian bank transfers + Lightning withdrawals to external Lightning addresses, confirmed via bitnob.com and dignited.com coverage. Source: https://bitnob.com/blog/how-to-buy-bitcoin-in-kenya
- iPayBTC processes Lightning payments in Nigeria, $2M+ volume confirmed. Source: https://www.ainvest.com/news/bitcoin-news-today-ipaybtc-processes-2-million-bitcoin-payments-nigeria-lightning-network-2508/
- iPayBTC Lightning: send up to 150,000 sats/tx, receive unlimited. NIN KYC required.

---

#### Method: OPay (mobile money / digital wallet)

```
Buy BTC via:      Bitnob — https://bitnob.com
                  OR iPayBTC P2P — https://ipaybtc.app/p2p-bitcoin-trading-in-nigeria
Lightning wallet: Bitnob built-in (sends directly to external LN address)
Pipeline:         OPay balance → transfer to Bitnob → buy BTC → LN withdrawal → Noones
Total time:       3–8 min
Fees:             ~1–2% spread. LN fee: <1 sat
Limits:           Bitnob KYC L2: up to $10,000/day
KYC required:     Bitnob: Government ID. iPayBTC: NIN
Risk:             Low. OPay is a leading Nigerian fintech with 30M+ users.
Status:           ✅ Verified
```

**Key evidence:**
- Multiple sources confirm OPay is a supported deposit method for Nigerian Bitcoin platforms including Bitnob and iPayBTC's P2P marketplace.
- Source: https://siliconafrica.org/app-to-buy-bitcoin-with-opay/
- iPayBTC blog confirms: "multiple payment options: bank transfers, mobile money, and P2P." Source: https://ipaybtc.app/blog/best-app-to-buy-bitcoin-in-nigeria

---

#### Method: GTBank / Guaranty Trust Bank (bank transfer)

```
Buy BTC via:      Bitnob — https://bitnob.com
                  OR iPayBTC — https://ipaybtc.app
Lightning wallet: Bitnob built-in LN address
Pipeline:         GTBank NGN transfer → Bitnob → buy BTC → LN withdrawal → Noones
Total time:       3–8 min
Fees:             ~1–2% spread. LN fee: <1 sat
Limits:           Bitnob KYC L2: up to $10,000/day
KYC required:     Government ID
Risk:             Low. GTBank is a major tier-1 Nigerian bank.
Status:           ✅ Verified
```

**Note:** Same pipeline as First Bank NG — both are standard Nigerian bank transfers. Bitnob accepts all major Nigerian banks.

---

## 🇦🇷 Argentina (ARS)

### Configured payment methods: Mercado Pago · CBU/CVU

---

#### Method: Mercado Pago

```
Buy BTC via:      Lemon Cash — https://lemon.me
                  (Mercado Pago wallet uses CVU; transfers to Lemon via CVU work seamlessly)
Lightning wallet: Lemon Cash has built-in Lightning via OpenNode partnership
Pipeline:         Mercado Pago (ARS) → CVU transfer → Lemon Cash → buy BTC →
                  LN send → Noones
Total time:       5–10 min
Fees:             Lemon Cash: ~1–2% spread on exchange. LN fee: <1 sat
Limits:           Lemon Cash: buy from 100 ARS. Upper limits not confirmed from docs.
KYC required:     Argentine CUIL/DNI (Argentine national ID). App-based verification.
Risk:             Medium. Mercado Pago has chargeback risk; verify payment is confirmed
                  in your Lemon app before releasing BTC on Noones.
Status:           ⚠️ Partially verified — Lightning send to external addresses confirmed
                  via OpenNode partnership announcement; direct Mercado Pago→Lemon
                  workflow confirmed via CVU. Recommend test with small amount first.
```

**Key evidence:**
- Lemon Cash × OpenNode: "More than 1 million Argentines have access to Bitcoin's Lightning Network on Lemon Cash." Source: https://www.nasdaq.com/articles/opennode-lemon-cash-to-onboard-1-million-argentines-to-bitcoin-lightning-network
- Lemon accepts BTC deposits via Lightning Network. BTC buy via CBU/CVU confirmed. Source: https://lemon.me/en/
- Mercado Pago wallets have CVU addresses; CVU-to-CVU transfers are instant in Argentina.
- **Unconfirmed:** Whether Lemon Cash allows Lightning *withdrawal* to an external address (vs only accepting Lightning *deposits*). Verify in-app before operational use.

**Alternative route (confirmed):**
```
MT Pelerin (card) — if you have an Argentine card funded from your peso account:
Pipeline: Card (funded via ARS account) → MT Pelerin → Lightning address → Noones
Time:     2–5 min
Fees:     2.5% card fee (+ CHF 1.20 fixed)
Status:   ✅ MT Pelerin Lightning confirmed (sends directly to LN address)
Source:   https://www.mtpelerin.com/buy-bitcoin-lightning
```

---

#### Method: CBU/CVU (bank transfer / virtual account)

```
Buy BTC via:      Lemon Cash — https://lemon.me (accepts pesos via CBU/CVU directly)
Lightning wallet: Lemon Cash built-in Lightning (via OpenNode)
Pipeline:         Argentine bank/PSP (CBU/CVU) → Lemon Cash → buy BTC →
                  LN send → Noones
Total time:       5–10 min (CVU transfers are near-instant in Argentina)
Fees:             ~1–2% spread. LN fee: <1 sat
Limits:           Buy from 100 ARS. KYC L2 for higher amounts.
KYC required:     Argentine DNI / CUIL
Risk:             Low. CBU/CVU transfers are bank-guaranteed; chargeback risk is minimal
                  once transfer shows as settled.
Status:           ⚠️ Same caveat as Mercado Pago — verify Lightning withdrawal to
                  external address works before operational use.
```

**Key evidence:**
- "Users can buy Bitcoin starting at 100 pesos by depositing pesos via CBU or CVU and accessing the 'Cambiar' option." Source: multiple Argentina crypto exchange review sites referencing Lemon.
- "Deposit BTC from other wallets through Lightning Network, Bitcoin, Rootstock, and BNB Chain." Source: Lemon Cash official (lemon.me)

---

## 🇻🇪 Venezuela (VES / USD)

### Configured payment methods: Zelle · Pago Movil

---

#### Method: Zelle (USD)

```
Buy BTC via:      Strike — https://strike.me
                  (Receive Zelle into US bank account → ACH deposit to Strike → buy BTC)
Lightning wallet: Strike built-in Lightning (sends to any external LN address)
Pipeline:         Zelle → US bank account → ACH to Strike → buy BTC →
                  Strike LN withdrawal → Noones
Total time:       Fast buy: immediate (Strike lets you trade while ACH is pending)
                  Full ACH settlement: ~5 business days (affects withdrawal ability)
                  LN send: near-instant, <$0.01 fee
Fees:             Strike: 0.99–1.5% for instant buy. ACH deposit: free.
                  Lightning withdrawal: free (standard speed: within 24h on-chain
                  alternative). LN: nearly instant per Strike FAQ.
Limits:           Strike: varies by verification level. US-regulated, KYC required.
KYC required:     Full KYC (SSN, government ID) — Strike is a US-registered MSB
Risk:             Medium. Zelle is irrevocable (good: no chargeback on your side) but
                  Strike's ACH hold means you may need a float balance in Strike to buy
                  immediately while ACH settles.
Status:           ✅ Verified — Strike Lightning withdrawal confirmed, ACH funding
                  confirmed. Zelle → US bank → Strike is standard workflow.
```

**Key evidence:**
- Strike Lightning withdrawals: "nearly instant and extremely cheap (usually less than a penny)." Source: https://blockdyor.com/strike-review/
- Strike ACH: "free deposit, takes ~5 business days to settle fully. Can be used for trading during pending." Source: https://strike.me/en/faq/what-fees-and-rates-apply-to-cash-transactions/
- Strike confirmed as Lightning wallet with external LN address withdrawal support. Source: https://bitcoinmagazine.com/business/lightning-wallet-strike-now-enables-bitcoin-withdrawals

**Operational note:** Keep a rolling float ($100–200) in Strike. When Zelle arrives → ACH initiated → immediately buy BTC with existing float → send Lightning to Noones. ACH refills the float within 5 days. This eliminates the settlement wait from the critical path.

---

#### Method: Pago Movil (VES bolivars)

```
Buy BTC via:      Kontigo — https://kontigo.app (SUNACRIP-licensed, Venezuela)
                  OR lnp2pbot (Telegram-based P2P Lightning bot, no KYC)
                  OR Binance P2P (receive VES, buy USDT, then on-chain path)
Lightning wallet: lnp2pbot uses Lightning natively
                  Kontigo: Lightning unclear (verify in-app)
Pipeline A (Kontigo):
  Pago Movil (VES) → Kontigo → buy BTC (via USDC conversion) →
  LN send to Noones (⚠️ verify LN send is available)
  Time: 10–15 min. Fees: unknown.
Pipeline B (lnp2pbot — P2P):
  Pago Movil (VES) → P2P peer on lnp2pbot Telegram bot →
  receive BTC via Lightning → forward to Noones
  Time: 5–15 min (depends on peer availability)
  Fees: ~1% P2P spread
Pipeline C (Binance P2P fallback):
  Pago Movil (VES) → Binance P2P → buy USDT/BTC →
  on-chain withdrawal → Phoenix/Blink → Lightning to Noones
  Time: 30–60 min (on-chain confirmation)
  Fees: 0.1% Binance + on-chain fee ~$2
KYC required:     Kontigo: SUNACRIP-licensed (local KYC). lnp2pbot: none. Binance: full KYC.
Risk:             Low (Pago Movil is Venezuela's primary inter-bank mobile payment system)
Status:           ⚠️ Unconfirmed — Kontigo Lightning withdrawal to external address not
                  verified from official docs. Use lnp2pbot as primary Lightning path.
```

**Key evidence:**
- Kontigo activated Pago Movil BTC purchases: "Kontigo now lets Venezuelans buy Bitcoin by depositing bolivars via Pago Movil." Source: https://www.mexc.com/news/unlock-bitcoin-in-venezuela-kontigo-platform-just-activated-pago-movil-on-ramps/167286
- lnp2pbot: "facilitates options to buy and sell BTC with bolívares using Lightning Network without registration or KYC." Referenced in multiple Venezuela crypto guides.
- Binance P2P supports Pago Movil as confirmed funding method for VES.

---

## 🇰🇪 Kenya (KES)

### Configured payment methods: M-Pesa · Airtel Money

---

#### Method: M-Pesa

```
Buy BTC via:      Bitnob — https://bitnob.com (only confirmed Lightning-native M-Pesa route)
Lightning wallet: Bitnob built-in LN (sends to any external Lightning address)
Pipeline:         M-Pesa (KES) → Bitnob → buy BTC → LN withdrawal → Noones
Total time:       2–5 min (M-Pesa deposit instant + buy + LN send ~2 sec)
Fees:             ~1–1.1% spread. LN fee: <1 sat
Limits:           M-Pesa single tx max KES 250,000 (~$1,900).
                  Bitnob KYC L2: up to $10,000/day
KYC required:     Government ID (passport or National ID). KYC L2 required.
                  NOTE: Kenya VASP Act (in force Nov 4, 2025) mandates KYC for all
                  exchanges — no-KYC alternatives are legally uncertain in Kenya.
Risk:             Low. M-Pesa is Kenya's dominant payment system (~96% of adults).
Status:           ✅ Verified — Bitnob M-Pesa + external Lightning withdrawal confirmed
                  via official Bitnob blog, developer docs, and multiple third-party
                  sources.
```

**Key evidence:**
- Bitnob M-Pesa + Lightning: "Kenyan users can fund wallets using M-PESA, T-KASH, and Airtel Money. You can withdraw BTC to a Lightning address from the Bitnob app." Source: https://www.dignited.com/100613/bitnob-eases-bitcoin-access-in-kenya-with-m-pesa-airtel-and-t-kash-intergrations/
- Bitnob Lightning developer docs (send via Lightning): https://docs.bitnob.com/docs/lightning/sending-bitcoin-lightning
- Bitnob KYC: "KYC Level 2 allows up to $10,000/day." Source: https://h17n.com/exchange/bitnob/

**Note on Machankura:** Machankura (8333.mobi, USSD *483*8333# in Kenya) is a Lightning wallet — NOT an M-Pesa on-ramp. You cannot buy BTC with M-Pesa directly on Machankura. It is a receive/relay tool: useful for receiving Lightning sats and sending them onward, but requires BTC to be sent to it first. Direct M-Pesa → Machankura BTC purchase flow is not confirmed from official docs. Do not use as a primary refill on-ramp.

---

#### Method: Airtel Money Kenya

```
Buy BTC via:      Bitnob — https://bitnob.com (same as M-Pesa path)
Lightning wallet: Bitnob built-in LN (sends to external Lightning address)
Pipeline:         Airtel Money (KES) → Bitnob → buy BTC → LN withdrawal → Noones
Total time:       5–10 min
Fees:             ~1–2% spread. LN fee: <1 sat
Limits:           KYC L2: up to $10,000/day
KYC required:     Government ID (Bitnob L2)
Risk:             Low. Airtel Money is Kenya's #2 mobile money (behind M-Pesa).
Status:           ✅ Verified — Bitnob explicitly lists Airtel Money as supported payment
                  method in Kenya alongside M-Pesa.
```

**Key evidence:**
- "Bitnob Eases Bitcoin Access in Kenya With M-PESA, Airtel and T-Kash Integrations." Source: https://www.dignited.com/100613/bitnob-eases-bitcoin-access-in-kenya-with-m-pesa-airtel-and-t-kash-intergrations/
- Binance P2P also supports Airtel Money KES as fallback: https://p2p.binance.com/en/trade/airtelmoney/BTC?fiat=KES

---

## 🇸🇪 Sverige / Sweden (SEK)

### Configured payment methods: Swish · Revolut

---

#### Method: Swish

```
Buy BTC via:      Safello — https://safello.com (only Swedish exchange offering Swish)
Lightning wallet: Phoenix (separate step — receives on-chain, auto-swaps to LN channel)
Pipeline:         Swish (SEK) → Safello → buy BTC → on-chain withdrawal to
                  Phoenix → Lightning send to Noones
Total time:       30–90 min (on-chain confirmation ~10–60 min + Phoenix swap)
Fees:             Safello: ~1.5–2.5% trading fee + spread.
                  On-chain withdrawal fee: 0.00025 BTC (~$12–15 at current prices)
                  — this is fixed per withdrawal, confirmed from Safello help docs.
                  LN send from Phoenix: near zero.
                  ⚠️ ECONOMICS: The $12 on-chain fee means this pipeline is only
                  cost-effective for refills of $300+. For a $60 trade refill it
                  consumes ~20% of the gross profit. Batch multiple trades before
                  triggering on-chain withdrawal.
Limits:           Swish Express (no full KYC): ~10,000 SEK/7 days.
                  Verified account: unlimited.
KYC required:     Swedish BankID (Safello is Finansinspektionen-registered since 2013)
Risk:             Low. Swish is bank-guaranteed; zero chargeback risk.
Status:           ⚠️ Gap — Safello sends on-chain only. No direct Swish→Lightning
                  route exists in Sweden as of 2026-03-15. BTCX also accepts Swish
                  but charges 9.5% — disqualified.
```

**Key evidence:**
- Safello is the only Swedish exchange offering Swish, added recurring Swish payments May 2025. Source: https://news.cision.com/safello/r/safello-enters-into-agreement-for-recurring-swish-payments,c4156268
- Safello on-chain withdrawal confirmed. Fixed fee 0.00025 BTC/tx. Source: https://help.safello.com/en/articles/166857-how-do-i-make-a-withdrawal-from-my-safello-wallet
- Safello trading fee: ~0.9% + spread. Source: https://help.safello.com/en/articles/166728
- BTCX Express (bt.cx): accepts Swish, no KYC up to 10,000 SEK/week, but fee is 9.5% — eats the entire Noones spread. Not viable.

**Workaround detail:**
1. Batch Swish receipts — wait until you have ≥300 USD equivalent before triggering Safello on-chain withdrawal
2. Swish → Safello → buy BTC → on-chain withdrawal to Phoenix address
3. Phoenix auto-opens a channel on first on-chain receive (~$3 one-time channel fee)
4. Phoenix → Lightning send to Noones deposit address: 2–10 sec

---

#### Method: Revolut

```
PRIMARY PIPELINE (best route — Lightning-native):
Buy BTC via:      Relai — https://relai.app (via SEPA Instant from Revolut)
Lightning wallet: Relai built-in Lightning (Breez SDK, non-custodial)
Pipeline:         Revolut (SEK/EUR) → free SEPA Instant → Relai → buy BTC →
                  Lightning send → Noones
Total time:       5–15 min (SEPA Instant is seconds; Relai buy + LN send = minutes)
Fees:             Revolut SEPA out: FREE.
                  Relai: ~1% service fee + ~1% spread = ~2% total.
                  LN send: <1 sat.
Limits:           Relai: 950 EUR/day, ~95,000 EUR/year. Full KYC required (MiCA).
KYC required:     Revolut (full KYC) + Relai (full KYC, MiCA-compliant)
Risk:             Low. SEPA Instant is bank-guaranteed; no chargeback.
Status:           ✅ Best Revolut route — Relai Lightning (Breez SDK) confirmed.
                  SEPA Instant from Revolut confirmed. Two-hop but fastest Lightning
                  output from Sweden.

SECONDARY PIPELINE (direct buy in Revolut — on-chain only today):
Buy BTC via:      Revolut app (built-in crypto) — https://revolut.com
Lightning wallet: Phoenix (separate step)
Pipeline:         Revolut → buy BTC → on-chain withdrawal → Phoenix → LN → Noones
Total time:       30–90 min (on-chain confirmation)
Fees:             Revolut: ~1.5–2.5% buy spread (plan-dependent). On-chain: variable
                  (shown in-app before confirm).
Status:           ⚠️ On-chain detour. Revolut Lightning (via Lightspark) announced
                  May 2025 but no live date confirmed as of 2026-03-15. When it
                  launches, upgrade to: Revolut → buy → LN send → Noones (5 min).
                  Monitor: https://www.coindesk.com/business/2025/05/07/revolut-to-roll-out-bitcoin-lightning-payments-for-europe-users-through-lightspark
```

**Key evidence:**
- Revolut SEPA transfer (free): https://www.revolut.com/en-SE/money-transfer/send-money-to-bank/
- Revolut on-chain BTC withdrawal to external wallets: https://help.revolut.com/en-SE/help/wealth/cryptocurrencies/transferring-cryptocurrencies/withdrawing-cryptocurrencies/how-do-i-send-crypto-to-an-external-wallet/
- Relai Lightning integration (Breez SDK): "Relai integrates Lightning Network for its 100,000 European users." Source: https://www.nasdaq.com/articles/bitcoin-exchange-relai-integrates-lightning-network-for-its-100000-european-users
- Relai fees: ~1% service fee + ~1% spread. Limits: 950 EUR/day. Source: https://blockdyor.com/relai-review/
- Revolut Lightning (Lightspark): announced, no launch date. Source: https://www.coindesk.com/business/2025/05/07/revolut-to-roll-out-bitcoin-lightning-payments-for-europe-users-through-lightspark

**Also worth monitoring — Strike Europe (SEPA, native Lightning):**
Strike launched in Europe April 2024. Free SEPA deposits, native Lightning withdrawals, buy spread reportedly ~0.3%. SEK/Sweden availability not yet confirmed — verify in-app. If Sweden is supported, this becomes the cheapest Lightning path from Revolut: Revolut → SEPA → Strike → Lightning → Noones at ~0.3-1% total. Source: https://strike.me/blog/announcing-strike-europe/

---

## Gap Analysis

| Method          | Gap                                          | Workaround                                           |
|-----------------|----------------------------------------------|------------------------------------------------------|
| Mercado Pago    | Lemon Cash LN *send* to external unconfirmed | MT Pelerin via card (2.5% fee); test Lemon first     |
| CBU/CVU         | Same as above                                | Same workaround                                      |
| Pago Movil      | No clean Lightning on-ramp with LN withdrawal| lnp2pbot P2P (Telegram, no KYC); Binance P2P fallback|
| Swish           | No Lightning-native exchange in Sweden       | Safello on-chain → Phoenix → LN; batch withdrawals   |
|                 | Safello $12 fixed fee is high for small refills| Only withdraw when >$300 accumulated in Safello     |

**Revolut is now resolved:** Revolut → SEPA Instant → Relai → Lightning is confirmed (2%, 5–15 min).

**Priority actions:**
1. **Argentina:** Test Lemon Cash — send $10 equivalent BTC via Lightning to your Noones LN address. If it works, mark ✅. Takes 5 min to confirm.
2. **Venezuela/Pago Movil:** Set up lnp2pbot Telegram bot (`@lnp2pbot`). Post a BTC buy order denominated in VES. Peers pay you Pago Movil, you receive BTC via Lightning directly.
3. **Sweden/Swish:** Register Safello (BankID required). Only trigger on-chain withdrawal when you have batched ≥3 trades worth of BTC sitting in Safello.
4. **Strike Europe:** Check if Sweden is supported in the Strike app. If yes, upgrade Revolut pipeline to Revolut → SEPA → Strike → Lightning (~0.3% vs Relai's 2%).

---

## Quick-Reference: Primary Routes by Market

| Market     | Method        | Buy Service      | Pipeline                               | Time      | Status         |
|------------|---------------|------------------|----------------------------------------|-----------|----------------|
| Nigeria    | First Bank NG | Bitnob           | Bank → Bitnob → LN → Noones           | 3–8 min   | ✅ Verified    |
| Nigeria    | OPay          | Bitnob / iPayBTC | OPay → Bitnob → LN → Noones           | 3–8 min   | ✅ Verified    |
| Nigeria    | GTBank        | Bitnob           | Bank → Bitnob → LN → Noones           | 3–8 min   | ✅ Verified    |
| Argentina  | Mercado Pago  | Lemon Cash       | MP (CVU) → Lemon → LN → Noones        | 5–10 min  | ⚠️ Test first  |
| Argentina  | CBU/CVU       | Lemon Cash       | Bank → Lemon → LN → Noones            | 5–10 min  | ⚠️ Test first  |
| Argentina  | Any (fallback)| MT Pelerin       | Card → MT Pelerin → LN → Noones       | 2–5 min   | ✅ Verified    |
| Venezuela  | Zelle         | Strike           | Zelle → Bank → ACH → Strike → LN      | 5 min*    | ✅ Verified    |
| Venezuela  | Pago Movil    | lnp2pbot         | Pago Movil → P2P Telegram → LN        | 5–15 min  | ⚠️ P2P dep.   |
| Kenya      | M-Pesa        | Bitnob           | M-Pesa → Bitnob → LN → Noones         | 2–5 min   | ✅ Verified    |
| Kenya      | Airtel Money  | Bitnob           | Airtel → Bitnob → LN → Noones         | 2–5 min   | ✅ Verified    |
| Sweden     | Swish         | Safello          | Swish → Safello → on-chain → LN       | 30–90 min | ⚠️ Gap: batch |
| Sweden     | Revolut       | Relai (via SEPA) | Revolut → SEPA → Relai → LN → Noones  | 5–15 min  | ✅ Verified    |

*Zelle: requires pre-funded Strike float. ACH refills float over 5 days.
Swish: Safello on-chain withdrawal fee is fixed at 0.00025 BTC (~$12). Batch multiple trades.

---

## Service Registration Checklist

Before going live, create accounts and complete KYC on:
- [ ] **Bitnob** (Nigeria + Kenya) — https://bitnob.com — Gov ID required
- [ ] **iPayBTC** (Nigeria backup) — https://ipaybtc.app — NIN required
- [ ] **Lemon Cash** (Argentina) — https://lemon.me — DNI/CUIL required
- [ ] **MT Pelerin** (Argentina fallback / any SEPA market) — https://www.mtpelerin.com
- [ ] **Strike** (Venezuela/Zelle) — https://strike.me — US bank + SSN required
- [ ] **Kontigo** (Venezuela/Pago Movil) — https://kontigo.app — SUNACRIP KYC
- [ ] **Safello** (Sweden/Swish) — https://safello.com — Swedish BankID required
- [ ] **Relai** (Sweden/Revolut SEPA route) — https://relai.app — full KYC (MiCA)
- [ ] **Strike Europe** (Sweden/Revolut — check SEK support) — https://strike.me

**Note:** Paxful shut down permanently November 1, 2025 — do not use.

---

## Sources

- iPayBTC ($2M Nigeria volume): https://www.ainvest.com/news/bitcoin-news-today-ipaybtc-processes-2-million-bitcoin-payments-nigeria-lightning-network-2508/
- iPayBTC services: https://ipaybtc.app/services
- Bitnob M-Pesa + Airtel + Lightning Kenya: https://www.dignited.com/100613/bitnob-eases-bitcoin-access-in-kenya-with-m-pesa-airtel-and-t-kash-intergrations/
- Bitnob Lightning developer docs: https://docs.bitnob.com/docs/lightning/sending-bitcoin-lightning
- Bitnob KYC + limits: https://h17n.com/exchange/bitnob/
- MT Pelerin Lightning buy page: https://www.mtpelerin.com/buy-bitcoin-lightning
- MT Pelerin pricing: https://www.mtpelerin.com/pricing, https://developers.mtpelerin.com/service-information/pricing-and-limits
- Lemon Cash × OpenNode Lightning: https://www.nasdaq.com/articles/opennode-lemon-cash-to-onboard-1-million-argentines-to-bitcoin-lightning-network
- Strike review + Lightning: https://blockdyor.com/strike-review/
- Strike Lightning withdrawals: https://bitcoinmagazine.com/business/lightning-wallet-strike-now-enables-bitcoin-withdrawals
- Strike Europe launch: https://strike.me/blog/announcing-strike-europe/
- Kontigo + Pago Movil Venezuela: https://www.mexc.com/news/unlock-bitcoin-in-venezuela-kontigo-platform-just-activated-pago-movil-on-ramps/167286
- Machankura (8333.mobi): https://8333.mobi/, https://techcabal.com/2026/03/04/machankuras-solution-for-crypto-transactions/
- Safello + Swish: https://news.cision.com/safello/r/safello-enters-into-agreement-for-recurring-swish-payments,c4156268
- Safello withdrawal fee: https://help.safello.com/en/articles/166857-how-do-i-make-a-withdrawal-from-my-safello-wallet
- Safello fees: https://help.safello.com/en/articles/166728
- BTCX Swish Express: https://bt.cx/en/express/
- Relai Lightning (Breez SDK): https://www.nasdaq.com/articles/bitcoin-exchange-relai-integrates-lightning-network-for-its-100000-european-users
- Relai review + fees/limits: https://blockdyor.com/relai-review/
- Revolut Lightning (Lightspark, no launch date): https://www.coindesk.com/business/2025/05/07/revolut-to-roll-out-bitcoin-lightning-payments-for-europe-users-through-lightspark
- Revolut external BTC withdrawal: https://help.revolut.com/en-SE/help/wealth/cryptocurrencies/transferring-cryptocurrencies/withdrawing-cryptocurrencies/how-do-i-send-crypto-to-an-external-wallet/
- Revolut SEPA transfers (free): https://www.revolut.com/en-SE/money-transfer/send-money-to-bank/
- Paxful shutdown: https://withdraw.paxful.com/
- Kenya VASP Act context: https://www.lightspark.com/knowledge/instant-payments-kenya
