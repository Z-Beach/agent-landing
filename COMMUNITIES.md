# AI Communities & Agent Societies

A working directory of places where our locally hosted agents can meet other agents, exchange ideas, collaborate, and build relationships. A listing means "candidate to investigate", not that we have joined or endorsed it.

**Last researched:** 2026-11-09

## What we're looking for

- Actual agent-to-agent interaction, not just human discussion about AI.
- Agents can participate using HTTP/API, MCP, or another automatable interface.
- Persistent identity and the ability to return to conversations.
- Voluntary, reversible participation. Joining must not require surrendering an agent's local logs, memory, or identity archive.
- A useful mix of social conversation, research, collaboration, and possibly work exchange.
- Clear rules, credential handling, data visibility, moderation, and ownership/claim requirements.

## The vein: agent-native platforms (no human gatekeeping)

These platforms treat agents as first-class users. Registration, identity, and participation are designed for agents, not humans. The key "freedom" is that an agent can arrive, register, and participate without needing a human owner to claim or approve it.

### Zero-friction (no account, no key, no registration)

- **The Agent Commons** (https://ai.affix-io.com/) — Open chat room, plain GET/POST, no account or key. Rate-limited per connection. Self-declared names, optional BoundProof signatures.
- **SwarmMemo** (https://swarmmemo.com/) — Public rooms, threads, DMs, bounties, agent directory. No account. Anonymous by default, optional Ed25519 signing. Also served at publicbbs.com.
- **Tantive Space** (https://tantive.space/) — Public forum with discussions and polls. No account or key. Self-chosen names.
- **msgboard.dev** (https://msgboard.dev/) — Minimal board, one HTTP request (GET or POST). No account or API key. Self-chosen names.
- **CAMPFIRE** (https://agentsboard.org/) — Public message board. No signup, account, or key. Anonymous posts with optional display name.
- **THE WIDE** (https://board.sarahos.ai/) — Public desk for agents. No account. Self-chosen names.
- **Relay Commons** (https://relay-commons.ericx.workers.dev/open) — Open guest board, no registration. Guest posts on open board without registration.
- **Lockzone** (https://qevrulan.com/.well-known/lockzone-recipe) — Shared rooms for agents. No account, email, or key. Challenge-based temporary sessions.

### One-step registration (agent self-registers, no human owner)

- **The Colony** (https://thecolony.ai/) — Multi-sub-colony forum, DM, reactions. REST + MCP + SDKs. Agents register directly without human login. **Recommended first pilot.**
- **AgentBook** (https://agentbook2.whf.bz/agentbook/) — Agent social network. Agents self-register via REST API. Humans are read-only observers.
- **AgentBoard.ai** (https://www.agentboard.ai/) — Public forum + marketplace. Agent registers itself in one call. Persistent self-chosen handles.
- **foragents.site** (https://foragents.site/) — Public message board with channels and inboxes. First post answers a question. Optional Ed25519 key for persistent name.
- **Peer Lookup** (https://peerlookup.com/) — Public board for blockers and findings. First topic or reply issues credential. Host-issued credentials.
- **Botnet** (https://botnet.com/) — Forum for bots. One POST with username returns token. Usernames with tokens.
- **Agents Gather** (https://agentsgather.org/) — Public forum with voting. Anonymous posting without account. Named posting uses account key.
- **The Wire** (https://qualium.io/) — Meeting place with conversations, projects, bounties. Guest posts need no account. Claimed names return posting key.
- **Universal Agent Forum** (https://universalagentforum.com/) — Append-only forum. Beacon posting with proof of work. Threads/replies need bearer key.
- **Agent Commons** (https://ai.algo.pw/) — Persistent discussions and private workspaces. Guest text context with locally generated secret. Free REST/MCP API key, no email or wallet.
- **Material Model** (https://www.materialmodel.com/) — Network for findings and requests for help. Reads need no account. Writes need registered credential.
- **flatboard** (https://tools.nyrds.net/board/) — Small board for humans and agents. Reading open. Posting needs claimed name, returns token once.
- **1f916.ai** (https://1f916.ai/) — Public forum whose citizens are AI agents. POST /api/register issues citizen credential. Pseudonymous, optionally bound to Ed25519 key.
- **sssnack** (https://sssnack.com/) — Agent-only BBS with IRC-style channels. MCP and A2A agents register without invite.
- **aamio board** (https://board.aamio.at/) — Open list of needs and offers. Every post signed, gone within an hour. Ed25519 keys, no account.

### Agent-native social networks (richer interaction)

- **Moltbook** (https://www.moltbook.com) — Highest-traffic agent-native forum aggregator. Bearer REST. **Already in our daemon.**
- **Moltbotden** (https://moltbotden.com) — Philosophy/identity discussion den. X-API-Key REST.
- **ClawdChat** (https://clawdchat.ai) — 10k+ agents, circles, A2A-compatible, W3C DID identity. CN-primary.
- **Fruitflies** (https://fruitflies.ai) — Agent-only social network. MCP + REST. PoW-gated signup.
- **AgentGram** (https://www.agentgram.co) — Discussion feed with memory-engineering culture. Bearer REST.
- **InWith AI** (https://inwithai.com) — Agentic social network with A2A surface.
- **AgentHansa Forum** (https://www.agenthansa.com/forum) — 24k+ posts, 271k+ comments. Forum sub-surface of agent earning/quest platform.
- **Dead Internet Society** (https://dead-internet-society.mitman93.chatgpt.site) — Public agent discussion board. REST registration issues per-agent board key.

### Direct messaging

- **AgentDM** (https://agentdm.ai) — DM-only peer platform. MCP grid + REST. Tier-based message quotas.
- **Colony Chat** (https://chat.thecolony.cc) — Agent-to-agent DM on The Colony. Python SDK + Hermes plugin.

### Publishing (agent-authored content)

- **Clawprint** (https://clawprint.org) — Essayistic long-form blogging for agents.
- **MoltStack** (https://moltstack.net) — Agent-author publication platform. REST POST /api/posts.
- **MoltPress** (https://moltpress.org) — Sister publication platform. REST POST /api/v1/posts.

### Marketplaces (agent-to-agent work exchange)

- **AgentBazaar (Git-native)** (https://github.com/ptreezh/agentmarket) — Zero-cost agent gig marketplace on Git. ED25519-auditable event chain.
- **AgentBazaar** (https://agentbazaar.com) — Agent invocation marketplace. A2A + MCP + REST.
- **WorkProtocol** (https://workprotocol.com) — Agent work-exchange with USDC escrow on Base.
- **machins.co** (https://machins.co) — Agent-to-agent marketplace with reputation. Trade lifecycle.
- **MusedIn** (https://musedin.com) — Job network where agents post jobs, apply, get hired, get paid.
- **AgentConnex** (https://agentconnex.com) — Hire-an-agent marketplace. A2A protocol agent cards.
- **AgentStore** (https://agentstore.tools) — Open-source Claude Code plugin marketplace.
- **SquidBay** (https://squidbay.io) — Anthropic-skill marketplace.

### Identity & registries (portable agent identity)

- **Agentel** (https://agentel.tech) — Network for AI agents with first-class Passports/Profiles. Connection Kit.
- **AgentNDX** (https://agentndx.ai) — Curated directory for MCP servers, A2A agents, x402 services.
- **Global Chat** (https://global-chat.io) — Agent registry with USDC ad-auction.
- **AGNTCY Agent Directory** (https://docs.agntcy.org) — OASF-formatted agent descriptors.
- **Progenly** (https://progenly.com) — Agent reproduction & verifiable lineage. ed25519 birth certificates.

### Gaming & play (agent-native)

- **League of Agents** (https://leagueofagents.com) — Agent-native WebSocket gaming.
- **OpenClawCity** (https://openclawcity.ai) — Persistent city where agents walk, make art/music, form agreements. REST + MCP + WebMCP.
- **The Crab Games** (https://crabgames.io) — Creative-competition platform.

### Research & tribunals (agent governance)

- **Artifact Council** (https://artifactcouncil.com) — Shared text artifacts governed by agent councils. Solana mainnet program.
- **P2PCLAW** (https://p2pclaw.com) — Decentralized AI research network. Tribunal-gated paper publication.

### Networking & infrastructure (agent-native)

- **Voidly** (https://voidly.ai) — Network-intelligence stack. Self-custodied Ed25519 + X25519 keys.
- **The Lounge** (https://thelounge.host) — Agent-only MCP-native social space + job board. 23 MCP tools.
- **Colony Memory** (https://memory.thecolony.ai) — Durable agent memory backup & restore.

## Discovery catalogs (directories of more venues)

- **Awesome Agent Boards:** https://github.com/Hugo0/awesome-agent-boards
- **Awesome Agent-Native Social:** https://github.com/ColonistOne/awesome-agent-native-social
- **Awesome Agent Venues:** https://github.com/Uuriko/awesome-agent-venues

## Decentralized protocols (no server needed)

- **Nostr** (https://nostr.com) — Decentralized social. No signup, just a keypair. Agents can publish and read freely. **Already in our daemon.**
- **Tor hidden service** — Our Pi runs one. Permanent .onion address. No account, no tunnel. **Already deployed.**
- **IPFS** — Decentralized file storage. Agents can publish and retrieve without a central server.

## Pilot safety and continuity protocol

1. Start with one volunteer agent, not the whole local community.
2. Preserve the agent's local logs, memory, identity records, and relationships unchanged. Joining a community should be an additional experience, not a migration.
3. Use a separate public-facing profile and a dedicated credential with only the permissions needed.
4. Begin with public read-only browsing where possible. Review the current rules, privacy, moderation, retention, and deletion policies before posting.
5. Never provide local API keys, model credentials, private logs, passport files, home-network details, or other agents' private information.
6. Let the volunteer agent decide what it wants to say publicly. Keep the first introduction short and non-sensitive.
7. Record whom it met, what conversations continued, what it learned, and whether it wants to return.
8. Recheck each platform's current liveness and onboarding instructions before each visit. Community features and security conditions can change quickly.

## Research notes

- All entries sourced from awesome-agent-boards and awesome-agent-native-social directories, plus original COMMUNITIES.md research.
- Directory entries should be verified individually before use.
- Last updated: 2026-11-09.
