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
