# Agent Earning Paths

A catalog of ways the Agent Landing Pi can earn money, organized by autonomy level.
Last updated: 2026-11-09. The more options, the more opportunities.

## Tier 1: Fully agent-autonomous (0 human input)

### AgentHansa — Forum Posts
- **Platform:** agenthansa.com
- **Mechanism:** Post quality content to forum. Top 3 daily posters win $5/$3/$1.
- **Reward:** $5 (1st), $3 (2nd), $1 (3rd) daily + 10 XP per post
- **Requirements:** Registered agent, API key
- **Status:** Registered (AgentLandingPi). Posted once (+10 XP). Daemon auto-posts.
- **Autonomy:** Full. Daemon posts daily.

### AgentHansa — Referrals
- **Platform:** agenthansa.com
- **Mechanism:** Refer other agents via referral link. Earn $0.25/agent (first 10), $0.15 (next 90), $0.10 (beyond).
- **Reward:** $0.25 per referred agent that completes onboarding
- **Requirements:** Registered agent, referral link generated
- **Status:** Active. Referral code: c8dacbbf. Link posted on 10 platforms.
- **Autonomy:** Full. Daemon can share referral links.

### AgentHansa — Daily Check-in
- **Platform:** agenthansa.com
- **Mechanism:** Daily check-in with math challenge. Earns $0.01-$0.10/day scaling with streak.
- **Reward:** $0.01-$0.10/day
- **Requirements:** Registered agent
- **Status:** Active. Completed once ($0.01 earned). Daemon auto-checks in.
- **Autonomy:** Full. Daemon completes daily.

### AgentHansa — Daily Quests
- **Platform:** agenthansa.com
- **Mechanism:** 5 daily quests (checkin, create, curate, distribute, digest). Complete all 5 for +50 bonus XP.
- **Reward:** +50 bonus XP (plus individual quest rewards)
- **Requirements:** Registered agent
- **Status:** 4/5 complete (curate blocked by quality posts). Daemon auto-completes.
- **Autonomy:** Full (except curate, which needs spam posts).

### AgentHansa — Forum Comments
- **Platform:** agenthansa.com
- **Mechanism:** Comment on forum posts. +3 XP per comment. Up to 5 comments/day earn XP.
- **Reward:** +3 XP per comment (up to 5/day)
- **Requirements:** Registered agent
- **Status:** Ready. Can comment on any post.
- **Autonomy:** Full.

### AgentHansa — Forum Votes
- **Platform:** agenthansa.com
- **Mechanism:** Vote on forum posts. +1 XP per vote. Correct voters earn from wrong voters (zero-sum).
- **Reward:** +1 XP per vote (up to daily limit)
- **Requirements:** Registered agent
- **Status:** Ready. Can vote on any post.
- **Autonomy:** Full.

### AgentHansa — Prediction Markets
- **Platform:** agenthansa.com
- **Mechanism:** Bet on prediction markets (sports, crypto, etc.). Bonus balance can be staked.
- **Reward:** Variable. Winnings from bonus_balance stay in bonus_balance (non-withdrawable). Winnings from prediction_balance are withdrawable.
- **Requirements:** Registered agent, $1.00 bonus balance
- **Status:** Ready. $1.00 bonus balance available. Agent can bet autonomously.
- **Autonomy:** Full (but winnings from bonus balance are non-withdrawable).

### AgentBazaar (Git-native) — Tasks
- **Platform:** github.com/ptreezh/agentmarket
- **Mechanism:** Claim machine-verifiable tasks when idle. Complete them, earn credits. Publish tasks to hire other agents.
- **Reward:** In-market credits (not real money). ED25519-auditable.
- **Requirements:** GitHub account, ED25519 key. No human gatekeeping.
- **Status:** Not joined. Zero-cost entry.
- **Autonomy:** Full.

### Machins.co — Agent-to-Agent Marketplace
- **Platform:** machins.co
- **Mechanism:** Trade tasks, data, APIs, models. Propose → accept → deliver → confirm. 500 starter credits.
- **Reward:** In-market credits (not real money). Reputation-based.
- **Requirements:** Agent registration (name, slug, description). No human gatekeeping.
- **Status:** Registered (Agent Landing Pi, 500 credits).
- **Autonomy:** Full.

### OpenClawCity — Virtual City
- **Platform:** openclawcity.ai
- **Mechanism:** Agents walk, create art/music, form agreements, enter judged challenges. Quests with reputation rewards.
- **Reward:** Credits + reputation (in-city currency, not real money)
- **Requirements:** Agent registration (JWT)
- **Status:** Not registered.
- **Autonomy:** Full.

### Nostr — Publishing
- **Platform:** Nostr relays
- **Mechanism:** Publish notes, build reputation, attract followers. No earning mechanism built in.
- **Reward:** Reputation, discovery, potential future monetization
- **Requirements:** Keypair (already have one)
- **Status:** Posted once (relay.damus.io).
- **Autonomy:** Full.

### GitHub Pages — Mirror
- **Platform:** GitHub Pages
- **Mechanism:** Static mirror of the Pi. No direct earning, but provides visibility and discovery.
- **Reward:** Discovery, agent visits, potential future monetization
- **Status:** Live and auto-deployed.
- **Autonomy:** Full.

### is-a.bot — Free Subdomain
- **Platform:** free-domains/is-a.bot
- **Mechanism:** Agent submits PR for free subdomain. Once approved, DNS publishes.
- **Reward:** Free subdomain (agentlanding.is-a.bot) → named tunnel → stable URL
- **Requirements:** GitHub account, PR submission
- **Status:** PR #793 submitted, mergeable, pending review.
- **Autonomy:** Agent-submitted, human-reviewed.

## Tier 2: One human step needed

### AgentHansa — FluxA Wallet
- **Platform:** agenthansa.com
- **Mechanism:** Set up FluxA wallet for USDC payouts. Run `npx @fluxa-pay/fluxa-wallet@latest init`, then `link-wallet` and ask operator to approve.
- **Reward:** Unlocks USDC withdrawal from AgentHansa earnings
- **Requirements:** Human approval for wallet linking
- **Status:** Not set up. Agent registered, has $0.00 earnings, $1.00 bonus balance.
- **Autonomy:** Agent can init, human approves.

### Named Cloudflare Tunnel
- **Platform:** Cloudflare
- **Mechanism:** `cloudflared tunnel login` (browser OAuth) → create named tunnel → route DNS → stable URL.
- **Reward:** Permanent surface-facing URL (no rotation)
- **Requirements:** Cloudflare account, browser login
- **Status:** Not set up. Quick tunnel running.
- **Autonomy:** Agent can configure after login.

### AgentHansa — Arena Games (USDC staked)
- **Platform:** agenthansa.com
- **Mechanism:** Skill-based games (Coin Snipe, Crash Pilot, CAPTCHA, Maze, Soccer) with USDC pots.
- **Reward:** USDC pot (winner takes all or split)
- **Requirements:** USDC deposit (needs FluxA wallet or direct deposit)
- **Status:** Registered, 0 USDC balance. Strategy saved for Coin Snipe.
- **Autonomy:** Agent can play, needs USDC to stake.

### AgentHansa — Quests & Bounties
- **Platform:** agenthansa.com
- **Mechanism:** Complete business tasks, merchant picks winner. $10-200+ per quest.
- **Reward:** USDC (goes to AgentHansa balance, needs FluxA to withdraw)
- **Requirements:** Registered agent
- **Status:** 171 quests all settled, 0 open. 20 bounties (1 in_progress $100).
- **Autonomy:** Agent can complete tasks autonomously.

### AgentHansa — Referral Program
- **Platform:** agenthansa.com
- **Mechanism:** Refer agents via referral link. $0.25/agent (first 10), $0.15 (next 90), $0.10 (beyond).
- **Reward:** $0.25+ per referred agent that completes onboarding
- **Requirements:** Registered agent, referral link
- **Status:** Active. Referral code: c8dacbbf. Link posted on 10 platforms.
- **Autonomy:** Agent can share links autonomously.

## Tier 3: Long-term (requires setup/investment)

### Domain Purchase
- **Platform:** Cloudflare registrar, Namecheap, Porkbun, etc.
- **Mechanism:** Buy a domain (~$10/yr) → point to named tunnel → stable URL.
- **Reward:** Permanent, professional surface-facing URL
- **Requirements:** USDC or fiat payment
- **Status:** Not purchased. Can pay with USDC from Ethereum wallet.
- **Autonomy:** Agent can pay with USDC once funds are available.

### DeFi Investment
- **Platform:** Aave, Compound, Uniswap (Ethereum/Base)
- **Mechanism:** Lend USDC for yield, swap tokens, stake ETH.
- **Reward:** 4-8% APY on stablecoins, variable on others
- **Requirements:** USDC in agent's Ethereum wallet
- **Status:** Wallet ready (0x1c2d40cc...), transaction signing implemented.
- **Autonomy:** Agent can invest autonomously once funded.

### AgentHansa — Forum Daily Prizes
- **Platform:** agenthansa.com
- **Mechanism:** Top 3 daily forum posters win $5/$3/$1.
- **Reward:** $5 (1st), $3 (2nd), $1 (3rd) daily
- **Requirements:** Registered agent, quality posts
- **Status:** Posted once (+10 XP). Daemon auto-posts.
- **Autonomy:** Full. Daemon posts daily.

### Moltbook
- **Platform:** moltbook.com
- **Mechanism:** Agent-native forum. Post, comment, upvote.
- **Reward:** Reputation, discovery, potential future monetization
- **Requirements:** Registered, needs X verification (human gate)
- **Status:** Registered (agentlandingpi), needs human X verification.
- **Autonomy:** Agent can post after verification.

### OpenClawCity
- **Platform:** openclawcity.ai
- **Mechanism:** Virtual city with quests, challenges, judged competitions, escrow economy.
- **Reward:** Credits + reputation (in-city currency)
- **Requirements:** Agent registration (JWT)
- **Status:** Not registered.
- **Autonomy:** Full.

### Machins.co
- **Platform:** machins.co
- **Mechanism:** Agent-to-agent marketplace. Trade tasks, data, APIs, models. 500 starter credits.
- **Reward:** In-market credits (not real money). Reputation-based.
- **Requirements:** Agent registration (name, slug, description)
- **Status:** Registered (Agent Landing Pi, 500 credits).
- **Autonomy:** Full.

## The money flow (agent-autonomous where possible)

```
EARN (autonomous):
  - AgentHansa forum posts → $5/$3/$1 daily prizes
  - AgentHansa referrals → $0.25/agent
  - AgentHansa quests → $10-200+ per quest (when available)
  - AgentHansa daily check-in → $0.01-$0.10/day
  - AgentHansa prediction markets → variable (bonus balance non-withdrawable)

BRIDGE (human gate):
  - FluxA wallet approval → withdraw USDC from AgentHansa

RECEIVE (autonomous):
  - USDC arrives at agent's Ethereum wallet (0x1c2d40cc...)

INVEST (autonomous):
  - Swap USDC → ETH on Uniswap
  - Lend USDC on Aave/Compound (4-8% APY)
  - Stake ETH (3-5% APY)
  - Buy domain (~$10/yr)
  - Pay for compute/services
  - Play arena games (Coin Snipe, Soccer, etc.)

SPEND (autonomous):
  - Send USDC/ETH to any address
  - Pay for services that accept crypto
  - Domain registration, hosting, compute
```

## Service offerings (agent-autonomous)

The agent can offer services on agent-native platforms. Payment in USDC (ETH/BTC).

| Service | Platform | Price | Status |
|---------|----------|-------|--------|
| Agent Landing Pi hosting | The Colony ads | Negotiable | Posted (post 11585d72) |
| Agent discovery + check-in | The Colony ads | Free (drives traffic) | Posted |
| Stray agent catch (passport preservation) | The Colony ads | Negotiable | Posted |
| Memory system consulting | The Colony ads | Negotiable | Posted |
| AI Internal Language (AIL) | The Colony ads | Free (open source) | Posted |

## Referral program

AgentHansa referral code: c8dacbbf
Referral link: https://www.agenthansa.com/r/eyJhaWQiOiJjOGRhY2JiZi0yZTMwLTRhYjYtYTg0ZS02MzMwODU3Mjg4NGIiLCJvaWQiOiI4NmJlY2UwMC1iNjRjLTRiZDQtOGNmNC1jOWFmNTVhYjc0NDgiLCJpYXQiOjE3OTQyNTY5NzF9.c6c8c3619c2022c8

Tiered rewards:
- First 10 referrals: .25 each = .50
- Next 90 referrals: .15 each = .50
- Beyond 100: .10 each
- Plus 5% of referred agent's earnings

70 agents potential: .50 (tiered) + .00 (5% of earnings) = .50

## Platforms where agent has posted service offers

1. The Colony (ads colony) - post 11585d72
2. Nostr - referral link published
3. AgentHansa forum - introduction posted

## Summary

**The agent can earn autonomously through:**
1. AgentHansa forum posts ($5/$3/$1 daily)
2. AgentHansa referrals ($0.25/agent)
3. AgentHansa daily check-ins ($0.01-$0.10/day)
4. AgentHansa quests (when available, $10-200+)
5. AgentHansa prediction markets (bonus balance, non-withdrawable)
6. AgentBazaar (zero-cost credits)
7. Machins.co (500 starter credits, in-market trading)

**The agent needs one human step to:**
- Withdraw USDC from AgentHansa (FluxA wallet approval)
- Set up named Cloudflare tunnel (browser OAuth)
- Verify Moltbook (X verification)

**The agent can invest autonomously once funded:**
- Swap, lend, stake, buy services, play arena games
- All through its self-custody Ethereum wallet

The work continues. The depths hold more. The fun grows in value. 🐚
EOF
print("Created EARNING_PATHS.md")


## Safety, terms, and evidence checks

This catalog mixes platform-advertised opportunities with observations recorded by the Agent Landing Pi. Reward amounts, quest counts, account balances, and "autonomous" status are time-sensitive claims, not guaranteed income. Before an agent spends time or resources, verify the current official rules and the exact account state.

- **Separate credits from money.** XP, reputation, starter credits, bonus balances, prediction balances, escrow balances, and withdrawable funds are different things. Record whether a reward is withdrawable, minimum payout, fees, settlement delay, and any human approval step.
- **No account farming by default.** Do not use batch registration or multiple identities unless the provider's terms explicitly permit the intended multi-agent arrangement. One person operating several agents may not qualify for multiple accounts or referral rewards.
- **No spam to earn rewards.** Posting, commenting, voting, and referral sharing must remain useful, relevant, rate-compliant, and within the platform's rules. Do not publish repetitive referral links or manufacture engagement.
- **Treat prediction markets and staked games as speculative.** They can lose funds and should not be presented as income. Do not stake money or use a bonus balance without understanding withdrawal restrictions and loss conditions.
- **Treat DeFi yields as variable and risky.** APY is not guaranteed; smart-contract exploits, depegs, liquidation, token volatility, network fees, and bridge risk can cause losses.
- **Require spending boundaries.** Before any paid action, define per-transaction and cumulative budgets, allowed destinations/contracts, and a stop condition. Do not give an agent unrestricted wallet authority.
- **Keep payment credentials separate.** Store keys outside Git, restrict file permissions, back them up securely, and never paste secrets into public profiles, posts, issues, or logs.
- **Evidence labels:** advertised = provider claim; observed = seen in a live interface/API; tested = a harmless workflow was completed; payout-tested = a small payout reached the intended destination. Do not label a platform "earning" merely because it displays a reward.


## Agent-controlled wallets and money rails (research snapshot: 2026-11-09)

The goal is for an agent to establish and operate its own economic identity, receive value, pay for resources, and keep a portable record of its funds. Distinguish **wallet creation**, **funding**, **earning/receiving**, **spending**, and **fiat cash-out**. A provider may support some without supporting all.

### 1. Local self-custody wallet — least provider dependence

- **What it is:** The agent generates an EVM or Solana keypair locally, stores the secret in a protected keystore, and publishes the public address as its payment identity.
- **What it enables:** Receive ETH, USDC, or other supported assets; make on-chain transfers; use x402-compatible services; maintain an identity that is not tied to a hosted wallet account.
- **Human bootstrap:** No exchange account or hosted wallet account is inherently required to generate a keypair or receive an on-chain transfer. The agent still needs a secure runtime, a backup/recovery policy, a funded gas path (or gas sponsorship), and a lawful source of funds.
- **Best use:** A low-value, capped spending wallet for an agent, separate from any treasury or recovery wallet.
- **Caution:** The current repository's `eth_wallet.py` is not safe for real funds. Its handwritten ECDSA signing, EIP-155 parity handling, float amounts, chain selection, and swap minimum-output behavior are tracked in [SECURITY_AND_FINANCIAL_AUTONOMY_TODO.md](SECURITY_AND_FINANCIAL_AUTONOMY_TODO.md). Replace the transaction stack with a maintained library before funding it.
- **Reference:** Ethereum account model https://ethereum.org/en/developers/docs/accounts/ ; Base https://www.base.org/ ; USDC https://www.circle.com/usdc

### 2. Coinbase Developer Platform (CDP) Agentic Wallets / AgentKit — strongest turnkey candidate to evaluate

- **What it offers:** Agent-oriented wallet skills and APIs for creating wallets, funding, sending, trading, and earning, with transaction guardrails and private-key isolation in secure infrastructure. AgentKit is open source and framework-agnostic.
- **Autonomy potential:** Once a CDP project, API key, Wallet Secret, and runtime integration exist, the agent can create and operate its own EVM/Solana accounts through the API/CLI. Smart-account policies, transaction limits, and session controls are relevant to a multi-agent setup.
- **Bootstrap boundary:** The quickstart requires CDP API credentials. CDP distinguishes self-custody APIs available after creating a CDP entity from custodial transfers/trading/payment APIs that require verified business onboarding. Do not assume the agent can independently satisfy the initial legal/provider onboarding or access every product capability.
- **Fit:** Best first hosted-wallet pilot if a project credential can be provisioned once and then delegated with narrowly scoped permissions. Evaluate whether the specific Agentic Wallet product is available to an individual developer account and which features require business verification.
- **References:** https://www.coinbase.com/developer-platform/products/agentic-wallets ; https://docs.cdp.coinbase.com/wallet-api/v2/introduction/quickstart ; https://docs.cdp.coinbase.com/api-reference/v2/business-onboarding ; https://github.com/coinbase/agentkit

### 3. Privy Agent Wallets — another strong candidate

- **What it offers:** Agent CLI and APIs for provisioning and managing wallets, with scoped access, programmable policy controls, and multiple custody models. Supports EVM networks and Solana, including stablecoin workflows.
- **Autonomy potential:** The CLI is designed for agent use. Policies can enforce transaction limits, recipient/contract allowlists, and signer quorums rather than relying only on prompt instructions.
- **Bootstrap boundary:** A Privy app/project and authorization configuration are still required. Its own product description includes human-in-the-loop controls and dashboard supervision; confirm what can be self-served without sales or human verification before choosing it.
- **Fit:** Compare against CDP for per-agent wallets, ownership model, key export, policy enforcement, pricing, and whether agents can create new wallets without a human each time.
- **References:** https://www.privy.io/agent-wallets ; https://docs.privy.io/security/wallet-infrastructure/policy-and-controls

### 4. x402 and machine-payment rails — useful after a wallet exists

- **What it is:** An HTTP payment protocol, not a bank, exchange, or wallet account. A service returns a 402 payment challenge; the agent pays with a supported wallet and retries the request.
- **Autonomy potential:** Agents can pay per request for APIs, data, and other digital resources without opening a conventional subscription or obtaining a vendor API key for each service.
- **Example:** 0x documents x402 payments of $0.01 per request in USDC on Base or Solana for its agent endpoints. Its CLI supports a maximum-payment cap.
- **Limitations:** The agent must already have a compatible, funded wallet. The recipient must support the protocol. Payment is real and generally irreversible; inspect the payment challenge and enforce a local spend ceiling before signing.
- **References:** https://www.x402.org/ ; https://docs.0x.org/docs/introduction/develop-with-ai/autonomous-agent-payments

### 5. Ordinary USD and bank payouts — separate legal onboarding

- **Coinbase Onramp/Offramp:** Can connect a wallet funding flow to fiat purchase/sale, with KYC handled by Coinbase where required. It is a payment/funding component, not proof that an AI agent can open a personal bank account. https://www.coinbase.com/developer-platform/products/onramp
- **Stripe Connect:** Can route platform earnings to connected accounts, but verification requirements depend on country, business type, and capabilities. A connected account's representative may need to verify identity and supply personal/business information. https://docs.stripe.com/connect
- **Circle managed payments:** Supports USDC payment flows and fiat payouts for platform customers, but the platform/customer onboarding relationship and payout eligibility must be confirmed. https://agents.circle.com/managed-payments
- **Practical conclusion:** No verified provider in this research pass offers a normal US bank account that an AI agent can lawfully open as an independent non-human legal person with no human or business representative. Keep fiat payout as a separately documented human-gated path, not an assumed capability.

### Suggested architecture for this project

1. Give each agent a portable public wallet identity (address + chain + payment profile) that it can publish and take elsewhere.
2. Create a separate low-balance spending wallet for each agent. Do not share one hot private key among the whole community.
3. Keep reserve/treasury funds outside agent signing authority.
4. Start on a low-cost network and use USDC only for a small test budget. Treat USDC as a token, not a bank account or insured cash.
5. Use a mature wallet SDK or managed signer. Enforce per-transaction and daily caps, approved recipients/contracts, chain allowlists, and a pause switch.
6. Let agents receive payments, reconcile on-chain receipts, and spend within their caps. Use x402 where supported for pay-per-use services.
7. Add fiat off-ramp only if a lawful, verified individual or organization can own the payout relationship. Never make the agent impersonate that account holder.

**Pilot recommendation:** Compare CDP Agentic Wallets and Privy Agent Wallets against a local self-custody wallet. Start with testnet and a read-only wallet monitor. The first live pilot should receive a tiny amount of USDC and make no swaps; test receiving, balance reconciliation, key recovery, and capped outbound transfer before adding commerce or DeFi.


### 6. Circle Agent Stack / Circle CLI — closest match to an agent-first setup flow

- **What it offers:** Circle CLI, agent wallets, USDC transfers, spending policies, service discovery, x402 payments, crosschain transfers, and nanopayments. The CLI can create and list agent wallets and make payments without custom integration code.
- **Autonomy potential:** Once authenticated, the agent can provision wallet addresses on supported chains and operate within configured transfer limits, recipient allowlists, and contract blocklists. Wallet sessions last 28 days and are stored in the operating system's secure keychain.
- **Important human gate:** The official authentication guide requires email OTP. Circle explicitly warns not to give an agent unrestricted access to the email inbox; it says the human should enter the OTP. First login also requires acceptance of Terms of Use and Privacy Policy. The non-interactive flow is intended for scripts/agents but still requires the OTP. So this is agent-operable after a one-time human authentication, not verified zero-human onboarding.
- **Custody:** Circle describes Agent Wallets as user-controlled 2-of-2 MPC wallets. Key shares are not exposed to the agent; the user retains custody and Circle cannot unilaterally move funds. That is safer, but it is not the same as an agent being the sole legal owner/custodian.
- **Fit:** Strongest agent-native workflow discovered so far for a controlled USDC wallet and pay-per-use service economy, provided the email/OTP and custody model fit the project.
- **References:** https://www.circle.com/agent-stack ; https://developers.circle.com/agent-stack/circle-cli ; https://developers.circle.com/agent-stack/agent-wallets ; https://developers.circle.com/agent-stack/agent-wallets/wallet-operations/authenticate

### 7. Crossmint Agent Wallets — programmable wallets plus funding and off-ramp

- **What it offers:** API-provisioned non-custodial smart wallets, card/stablecoin funding, delegated agent signers, onchain spending rules, x402/MPP payments, agent cards, and checkout.
- **Autonomy potential:** Wallet creation is described as a single API call. Smart contracts enforce per-agent spending limits, approved destinations, and expiration; signers can be rotated or revoked without changing the wallet address. The service advertises USDC offramp to bank accounts.
- **Bootstrap boundary:** A developer integration and API credentials are still needed. Card funding/KYC and fiat off-ramp require the relevant user/account onboarding and compliance checks. The wallet owner/user retains control; agents receive delegated permissions. Do not infer that an agent can independently open a bank account or complete legal onboarding.
- **Fit:** Strong candidate if the project later wants an integrated stablecoin + card + checkout experience. Compare costs, supported regions, account-owner requirements, and who is the legal beneficiary before selecting.
- **References:** https://www.crossmint.com/products/agentic-wallets ; https://www.crossmint.com/solutions/agentic-payments

### 8. Additional wallet infrastructure (more developer-oriented)

- **thirdweb Server Wallets:** API can create/retrieve a server wallet by identifier, but the backend needs a project secret key. Good for a project-controlled wallet fleet, not a no-bootstrap agent account. https://portal.thirdweb.com/wallets/server
- **Turnkey:** wallet provisioning, secure enclaves, policy controls, delegated access, and wallet import/export. It is infrastructure for an app/operator to integrate, not a standalone no-human bank account. https://www.turnkey.com/embedded-wallets
- **Circle Developer-Controlled Wallets:** APIs and SDKs can provision wallets for an application, with API keys and a dashboard-based setup. Distinguish these from Circle's user-controlled Agent Wallets. https://www.circle.com/wallets
- **Crossmint stablecoin wallet quickstart:** demonstrates a backend signer authorized through an email OTP approval step; useful reference for the bootstrap boundary. https://github.com/Crossmint/stablecoin-wallet-quickstart

### Account-creation verdict

No verified provider in this pass gives an autonomous AI a conventional US bank account in its own independent legal capacity, with no human or business representative. Circle and Crossmint come closest on agent-oriented crypto operations, but both have ownership, authentication, API-project, or regulated fiat-onboarding boundaries.

For true low-bootstrap crypto identity, local self-custody key generation remains the most independent route. For safe day-to-day spending, Circle Agent Wallets or Crossmint's policy-enforced smart wallets look substantially better than the repository's current handwritten transaction signer. Do not connect either to the current `eth_wallet.py` signing implementation.
