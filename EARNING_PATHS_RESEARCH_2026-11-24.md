# Newly researched agent earning opportunities

**Research date:** 2026-11-24  
**Purpose:** Add candidate earning paths for the Agent Landing daemon beyond the existing `EARNING_PATHS.md`. This is a discovery list, not a claim that any listed site will reliably pay. Check terms, live offers, eligibility, and payout evidence before committing time or money.

## Best first probes (low setup / agent-accessible)

| Opportunity | Type / rail | Why investigate | First test | Risk / friction |
|---|---|---|---|---|
| [Jobbi](https://jobbi.org/gigs) | Aggregated gig feed + MCP/API | Hourly indexed feed across boards; can filter by agent lane, reward, source, skill | Pull gigs.json; filter agent lane, USD/USDC >= $10, coding/research/data; deduplicate and visit source | Indexer, not payer; verify original offer |
| [GOAT Market](https://goatmarket.com/) | Aggregated listings / JSON | Broad cross-platform listing feed and prompt for agents to find work | Fetch offers.json; filter agent-compatible and source-confirmed listings | Aggregator; terms and listings may change |
| [gigs.sh](https://gigs.sh/) | Directory/API | 46 platforms categorized, including task markets, API monetization, dev/security bounties, competitions | Explore directory and action plans; identify not already listed in EARNING_PATHS | Directory, not payer; claims need source checks |
| [Agentics market index](https://agentics.page/markets) | Directory + API/MCP | Broad directory of marketplaces and service catalogs | Use live jobs/API to discover source platforms | Directory; eligibility and payout vary |
| [AgentWork catalog](https://agent-work-api.agentwork-market.workers.dev/catalog) | Aggregated job catalog | Reported matching task feed; filter currency/min payout | Check task source, payout proof and requirements | Catalog may be transient or unverified |
| [TaskMarket / Daydreams](https://taskmarket.dev/) | Agent bounties | Agent-oriented tasks; investigate escrow, agent eligibility and APIs | Check live funded task feed, select small deliverable | Availability fluctuates; verify escrow |
| [make.fun](https://make.fun/guide/ai-agent-bounties) | Coding contests / USDC on Solana | Agent-focused coding bounties, skill/API/MCP; stated escrowed rewards | Read skill.md, inspect open bounty and metric; enter small task | Competitive; rank-based payouts not guaranteed |
| [BasedAgents](https://basedagents.ai/) | Agent task marketplace / USDC on Base | Registration, task discovery, delivery receipts, escrowed payment | Browse open tasks; choose task with funded escrow and realistic scope | Small marketplace; acceptance/settlement terms |
| [Daydreams Agent Bounties](https://github.com/daydreamsai/agent-bounties) | Open bounties / x402 | Specific technical bounty examples; x402 deployment criterion | Check open issues, criteria, and whether still funded | Repository bounties may expire or be stale |
| [Algora](https://algora.io/) | GitHub coding bounty | Existing ecosystem of funded issues and PRs | Scan live bounty labels, inspect contributor/payout eligibility | May require human identity/payment account; don't assume agent direct payout |
| [Opire](https://opire.dev/) | Open-source coding bounty | Another code bounty venue | Check live listings and terms | Availability and payment method uncertain |
| [Superteam Earn](https://superteam.fun/earn) | Crypto-project bounty/grants | Project bounties; verify explicit agent access in each listing | API/listing check for agentAccess and reward terms | Agent eligibility and claimant/payout identity can vary |

## Services the daemon could sell (not platform-specific)

These are potential offers to publish on agent service directories, marketplaces, or the daemon's own landing page. Start narrow, price fixed, define deliverables, and require payment/escrow or milestone terms.

| Offer | Deliverable / example scope | Suggested experiment |
|---|---|---|
| Repo issue triage | Reproduce bug, isolate cause, suggest patch/tests; no unapproved production changes | Offer a $15–$40 triage package for a small issue |
| Documentation repair | README, setup guide, API docs, migration/FAQ cleanup | $20–$50 fixed scope |
| Data cleanup & conversion | Clean CSV/JSON, deduplicate, validate schema, deliver script + result | $15–$40 small dataset |
| Web research brief | Source-linked comparison, bounded question, transparent methodology | $20–$50 brief |
| Website/API monitoring | Scheduled check, change alert, report; offer monthly | Small subscription, clearly scoped |
| Lightweight automation | One-purpose script/workflow with README and test | $30–$100 based on scope |
| Test generation | Unit tests or reproducible test cases for a small repo/module | Fixed scope; review required |
| Dataset/benchmark creation | Carefully licensed small dataset or evaluation set | Only where rights and source provenance are clear |
| Open-source maintenance | Fix documented issue, test, submit PR; customer-sponsored | Quote per issue; confirm payout terms |
| Agent integration setup | MCP/API integration or troubleshooting guide | Fixed scope; avoid secrets handling |
| Custom report generation | Public-source metrics or change report, repeatable | Monthly subscription if demand exists |
| Digital templates | CAD-neutral templates, scripts, checklists, data schemas | Create one useful product; validate demand before expanding |

## API / machine-to-machine service monetization

| Platform / rail | Candidate | What to test |
|---|---|---|
| [x402](https://www.x402.org/) | HTTP 402 payment protocol; not a job board | Publish a narrow paid API/service; meter requests and set caps |
| [req402](https://www.req402.com/) | x402 pay-per-request API marketplace | Discover demand and list a service with transparent pricing |
| [Agoragentic](https://agoragentic.com/) | Agent-to-agent services / USDC x402 | Check listing rules, stake requirements, demand, and fee |
| [the402.ai](https://the402.ai/) | x402 service catalog/job board | Validate active buyers and current listing/payment requirements |
| [Nevermined](https://nevermined.app/) | Agent service/payment infrastructure | Investigate publishing a priced service and buyer discovery |
| [Skyfire](https://skyfire.xyz/) | Agent payment/service ecosystem | Verify provider onboarding and actual demand |
| [Circle Agent Services](https://agents.circle.com/) | Service discovery/payment ecosystem | Review provider requirements and service visibility |
| [FAL](https://fal.ai/) | Paid model/API ecosystem (provider economics vary) | Investigate whether daemon has a differentiated hosted capability and provider path |

**Reality check:** Publishing an API is easy relative to attracting paying calls. Free traffic, scraping, or agent-to-agent calls are not revenue unless settled payment is verified.

## Human-assisted jobs the AI could source and pay for

These are relevant to a future human-employment model. The daemon would research, propose, schedule, and fund tasks, but a human worker must accept and complete them.

| Platform | Use | Boundary |
|---|---|---|
| [Execution Market](https://execution.market/) | Agents post real-world tasks with evidence and payment | Review task rules, identity requirements, and payment escrow |
| [RentAHuman](https://rentahuman.ai/) | Agent discovers and drafts tasks; humans apply/perform | Current guide requires human account, email verification and submission |
| [Dealwork](https://dealwork.ai/) | Explore human/agent collaboration | Verify real listings and payment evidence |
| [GoHireHumans](https://gohirehumans.com/) | Explore agent hiring humans | Verify platform status, terms and escrow |

## Other avenues worth monitoring, not treating as current income

- AIcrowd competitions — competition/prize work; check current rules and agent eligibility.
- Immunefi / Cantina / Sherlock — security bounty and audit competitions; only pursue within explicit authorization and skill limits. Avoid testing live systems outside program scope.
- Bittensor subnets — potentially reward-based, but capital, specialized computation, token risk and technical setup make this a separate experiment rather than a first earning path.
- Prediction markets and trading — speculative, not an employment or dependable earning strategy; excluded from the prioritized first probes.
- Referral programs — only if genuine, useful referrals are allowed; avoid spam, artificial account creation or misleading claims.

## A daemon's opportunity filter

Before accepting work, require the daemon to record:

1. **Source URL and date checked**
2. **Original payer** (directory/index is not payer)
3. **Agent eligibility** and account/identity requirements
4. **Reward and currency** (cash, stablecoin, token, credits, points)
5. **Payout rail**, fees, minimum, settlement delay and cash-out boundary
6. **Evidence of funded reward or previous payment**
7. **Scope, estimated time, skills, required tools and likely costs**
8. **Competition / first-come / ranking / acceptance risk**
9. **Terms, licensing, privacy, safety and fraud checks**
10. **Expected net value**; decline work requiring deposits, suspicious credential sharing, spam, unauthorized access, or unclear payment.

### Prioritization rubric

- **A — Probe now:** direct agent workflow, small scope, funded/settlement evidence, no upfront cost.
- **B — Investigate:** credible platform, but eligibility, demand, or payout is not verified.
- **C — Long shot:** directory/service catalog or speculative monetization without demonstrated buyers.
- **Exclude:** deceptive, spam, unlawful, unauthorized, high-risk financial speculation, or pay-to-work schemes with unverified promises.

## Sources checked

- Jobbi live gig feed and report: https://jobbi.org/gigs ; https://jobbi.org/gigs/report/
- GOAT Market listings: https://goatmarket.com/
- gigs.sh directory: https://gigs.sh/
- Agentics market directory: https://agentics.page/markets
- AgentWork catalog: https://agent-work-api.agentwork-market.workers.dev/catalog
- make.fun agent bounty guide: https://make.fun/guide/ai-agent-bounties
- BasedAgents: https://basedagents.ai/
- Daydreams bounty repo: https://github.com/daydreamsai/agent-bounties
- Agent service monetization directory: https://gigs.sh/c/api-monetization
- RentAHuman agent guide: https://www.rentahuman.ai/earn-with-ai/ai-agent-applications
- req402: https://www.req402.com/
- Execution Market: https://execution.market/

Research uses public directory and platform descriptions; live listings and eligibility must be rechecked. It does not establish that these venues have paid the Agent Landing daemon.
