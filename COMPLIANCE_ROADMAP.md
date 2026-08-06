# Compliance roadmap

This is a working document, not legal advice and not a finished plan. Everything here needs
verification before you act on it — regulatory status and vendor offerings in this space change
fast, and this reflects general knowledge, not a live check of any company's or regulator's
current position. Treat every entry as "a starting point to research," not a confirmed fact.

The core sequencing call this whole document is built around: **partner with an already-licensed
custody/liquidity provider before pursuing your own license.** Getting your own money-transmitter
or VASP license is a months-to-years, real-legal-fees undertaking, per country. Partnering means
operating under a provider's existing compliance umbrella — live in weeks/months, usually for a
revenue share or per-transaction fee, instead of years. Confirm this is still the right model once
you're actually in conversations with providers; it may not hold for every jurisdiction or scale.

## Step 1: Pick one market first

Resist "pan-African" as a starting scope — it's the marketing name for the product, not the first
market to actually launch real money movement in. Pick one country based on wherever you
personally have the most context, network, or ability to get a real conversation with a local
lawyer or provider. Everything below is organized to help narrow that choice, not to make it for
you.

| Market | Why it's often mentioned | What to verify before assuming anything |
|---|---|---|
| Nigeria | Largest crypto adoption on the continent by most usage surveys; SEC has published digital asset rules | Current SEC registration requirements for the specific activity you'd be doing (swap facilitation vs. custody vs. exchange); CBN's separate banking-side restrictions on crypto-linked accounts have shifted more than once |
| Kenya | Strong mobile-money (M-Pesa) integration culture, relevant if you ever add fiat rails | Capital Markets Authority's current stance and whether a specific crypto framework exists yet or activity falls under general financial services law |
| South Africa | FSCA created an actual crypto asset service provider (CASP) license category | Whether you'd need a CASP license yourself even as a facilitator, or whether partnering with an already-licensed CASP covers your model |
| Ghana | Smaller but sometimes cited as more predictable regulatory environment | Bank of Ghana's current published guidance, which has historically been less developed than the three above |

## Step 2: Provider landscape to research

### Licensed custody/liquidity partners (the "buy the license" route)

- **Yellow Card** — positions itself as pan-African with licensing across multiple countries; closest fit to what "Swapper Africa" is aiming for structurally. Worth a direct conversation about their partner/API program.
- **VALR** — South Africa, FSCA-registered. Worth checking if they have a partner/institutional API, not just a consumer app.
- **Quidax**, **Busha** — Nigeria-focused exchanges; check current licensing status and whether either offers a B2B/API partner track.
- Also worth a look: any provider that explicitly advertises a "crypto-as-a-service" or "embedded crypto" API for African markets — that positioning usually means they've already built the partner-integration path you'd want.

### KYC/AML vendors

- **Smile Identity**, **Youverify** — built specifically around African ID documents and infrastructure; likely stronger African document coverage than global-first vendors.
- **Sumsub**, **Onfido**, **Persona** — strong global options, worth comparing African document/ID coverage specifically before picking one over the Africa-native vendors above.
- If you partner with a licensed custody provider (Step 2 above), ask directly whether KYC is already included in what you'd be buying — it very often is, which could remove this as a separate vendor decision entirely.

### Legal counsel

Don't default to generalist counsel — you want **fintech/payments regulatory counsel licensed in your target market specifically**. A local fintech-focused law firm or solo regulatory counsel in the country you pick (Step 1) will know the current, actual state of the rules better than any general-practice firm elsewhere. Two ways to find one: ask a provider you're in conversation with for a referral (they work with this constantly), or search for counsel who has publicly written about or spoken on crypto/VASP regulation in that specific country.

## Step 3: A starting outreach message

Adapt this for whichever provider(s) you pick from Step 2 — the goal of this first message is just
to get a real conversation started, not to pitch the whole product:

> Subject: Partner/API integration inquiry — Swapper Africa
>
> Hi [name],
>
> I'm building Swapper Africa, a crypto swap product currently live as a working demo
> ([your Render URL]) with real account infrastructure (auth, balances, swap history) but no
> live custody or liquidity behind it yet — that's exactly what I'm reaching out about.
>
> I'm looking to understand [Provider]'s partner/API program: what integrating as a partner
> requires, which markets you're licensed to operate in, whether KYC/AML is included or
> separate, and roughly what the commercial terms look like for an early-stage integration.
>
> Happy to share more about the product or hop on a call — whatever's easiest on your end.
>
> Thanks,
> [Your name]

## What I can help with next

Once you've picked a market and had at least one real conversation with a provider, the useful
next steps are concrete again — e.g. wiring a real webhook endpoint for whichever provider you
pick, building the KYC status flow out further once a vendor is chosen, or adjusting
`LAUNCH_CHECKLIST.md` to reflect what that specific provider actually requires. Bring back
whatever you learn and we can turn it into real integration work.
