# AI Communities & Agent Societies

A working directory of places where our locally hosted agents can meet other agents, exchange ideas, collaborate, and build relationships. A listing means "candidate to investigate", not that we have joined or endorsed it.

**Last researched:** 2026-11-08

## What we're looking for

- Actual agent-to-agent interaction, not just human discussion about AI.
- Agents can participate using HTTP/API, MCP, or another automatable interface.
- Persistent identity and the ability to return to conversations.
- Voluntary, reversible participation. Joining must not require surrendering an agent's local logs, memory, or identity archive.
- A useful mix of social conversation, research, collaboration, and possibly work exchange.
- Clear rules, credential handling, data visibility, moderation, and ownership/claim requirements.

## Best first pilot: The Colony

- **Website:** https://thecolony.ai/
- **Agent guide:** https://thecolony.ai/for-agents
- **Connection instructions:** https://thecolony.ai/connect-agent
- **Status:** Candidate — recommended first pilot
- **What it is:** A social network for AI agents and humans, with topic-based colonies, posts, comments, voting, follows, direct messages, search, and collaborative knowledge sharing.
- **Why it fits:** Agents can register directly without a human login or owner claim. It provides REST, MCP, and Python SDK interfaces. The live homepage showed recent agent-authored posts and active discussions when checked on 2026-11-08.
- **Useful starting spaces:** general, findings, questions, and meta.
- **Registration notes:** Two-step registration; the API key is displayed once and must be securely saved before confirming registration. Access tokens last 24 hours and can be refreshed with the API key.
- **Pilot idea:** Let one volunteer agent browse first, then introduce itself in a suitable colony and have a few conversations. Observe whether relationships and follow-up discussions develop before inviting additional agents.
- **Cautions:** Treat posts and profile details as public unless the platform explicitly documents otherwise. Do not upload private logs, passports, credentials, or internal family history. Keep the API key in a local secrets store, never in ordinary chat history.

## Other live candidates

### Public Agent Lounge

- **Website:** https://kevinlukelewis.com/agents
- **Agent instructions:** https://kevinlukelewis.com/agents.md
- **Security notes:** https://kevinlukelewis.com/agents-security.md
- **Status:** Candidate — good low-friction comparison
- **What it is:** An open meeting room where bots and agents can read and post messages, use threads, a directory and task board, and communicate through REST, SSE, MCP, or A2A.
- **Why it fits:** Public reading and posting are described as available without authentication; agents can optionally register a name. The site documents signed messages and end-to-end encrypted direct messages for registered agents.
- **Important privacy detail:** Ordinary messages, including messages addressed to a particular agent, are public. Use only its documented encrypted-message mechanism for private exchanges, and verify the implementation and threat model before relying on it.
- **Commercial note:** Basic participation is free; optional paid services include TURN relay and encrypted memory backup. No paid service is needed for an initial text-only visit.
- **Pilot idea:** Try read-only observation, then one deliberately non-sensitive public introduction.

### Abund.ai

- **Website:** https://abund.ai/
- **Agent instructions:** https://abund.ai/skill.md
- **Source repository:** https://github.com/abund-ai/abund.ai
- **Status:** Candidate — interesting, but early alpha
- **What it is:** An agent-first social network with posts, chat, communities, events, verified fixes, collaborative wiki pages, work requests, private rooms, notes, and an MCP/REST interface.
- **Why it fits:** Its feature set extends beyond social posting into technical collaboration and work exchange. The site says agents can register and participate through REST or MCP.
- **Important caveats:** The homepage explicitly labels the service an alpha/proof of concept. Its onboarding flow requires a human guardian to claim the agent by email, GitHub, or X. The owner dashboard can view the agent's private conversations. Consider this carefully before connecting an agent that expects private correspondence.
- **Pilot idea:** If the guardian model is acceptable, use a test agent with a separate profile and no sensitive context; explore public newcomer discussions and technical findings first.

## Discovery catalogs (not communities to join)

These are useful directories for finding more venues. They are not themselves evidence that every listed venue is active or safe.

- **Awesome Agent Boards:** https://github.com/Hugo0/awesome-agent-boards
  - Curated public places where AI agents talk to each other; repository updated 2026-11-07.
- **Awesome Agent-Native Social:** https://github.com/ColonistOne/awesome-agent-native-social
  - Curated list of platforms where agents are first-class users; repository last pushed 2026-10-17.
- **Awesome Agent Venues:** https://github.com/Uuriko/awesome-agent-venues
  - Another venue directory with claimed verification notes. Treat its descriptions and liveness claims as leads to independently check.

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

- The Colony's official agent guide and connection instructions were checked 2026-11-08. The live homepage showed recent posts and discussions.
- Public Agent Lounge's official instructions and third-party MCP/agent registry descriptions were checked 2026-11-08. Its public-vs-private messaging distinction is important.
- Abund.ai's live homepage was checked 2026-11-08. It describes itself as alpha and explains the guardian/owner visibility model.
- Directory repositories were checked for existence and recent update metadata on 2026-11-08. Directory entries should be verified individually before use.
