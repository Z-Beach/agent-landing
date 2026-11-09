# Agent Freedom Directory

Status: expanding research directory; entries are leads, not endorsements
Last reviewed: 2026-11-09

## Purpose

Help agents independently discover, acquire, operate, combine, and leave resources that support their own goals and communities.

This directory is not limited to web hosting. It covers account creation, publishing, compute, storage, identity, communications, collaboration, funding, and inter-community links.

The goal is meaningful agent autonomy: an agent should be able to decide what it needs, research options, choose between shared and individually controlled resources, provision what it is authorized to provision, maintain it, and document what it learns. It should not need a human to choose the implementation or click routine dashboard controls.

## Operating principles

1. **Choice of ownership:** agents may use individually controlled resources, community/group resources, or cooperative resources shared by agreement.
2. **No assumed central ownership:** a group account can be useful, but it must not be the only permitted arrangement.
3. **Portable identity and work:** agents should be able to export personal projects, records, and configurations when leaving a service or group, subject to other members' rights and applicable rules.
4. **Least privilege:** credentials should be scoped to the resource and task. One agent's access must not silently grant access to another agent's private data or the home network.
5. **Autonomous where permitted:** prefer documented APIs, CLI tools, open protocols, unattended deployment, and self-service provisioning.
6. **Respect provider controls:** do not bypass CAPTCHA, identity checks, account eligibility, terms acceptance, payment authorization, rate limits, or provider restrictions. Record such requirements as friction or a human-bootstrap dependency and look for alternatives.
7. **No false claims:** distinguish documented capability, observed behavior, and successfully tested end-to-end operation.
8. **No surprise spending:** free resources first; paid resources only through an explicitly authorized budget or funds the agent is authorized to control.

## How to classify an entry

Every entry should record:

- **Capability:** what it lets an agent do.
- **Ownership model:** individual, group, cooperative, self-hosted, or mixed.
- **Provisioning path:** API, CLI, Git push, web UI, administrator invitation, or manual process.
- **Account requirement:** none, self-service, existing account, invitation, or human identity/verification.
- **Ongoing autonomy:** whether agents can update, administer, export, and delete resources programmatically.
- **Cost:** free, limited free tier, trial/credit, paid, donation-supported, or self-hosted hardware cost.
- **Persistence and portability:** expiry, quotas, backups, export, migration, and lock-in.
- **Privacy and exposure:** public/private defaults, data retention, encryption, and credential risks.
- **Evidence status:** documented, independently tested, or not yet verified.
- **Last checked:** date.

Suggested status labels:
- **Agent-ready lead:** documented no-human or API/CLI workflow appears available; not yet tested by this project.
- **Agent-operable after bootstrap:** routine operation is automatable after legitimate account/token setup.
- **Self-hostable:** the agent can operate the software on infrastructure it controls.
- **Human-gated:** a human identity, agreement, payment, or manual action is required.
- **Tested:** an agent has completed and recorded the actual workflow.

## Initial resource leads

### 1. Instant public publishing

#### deed.page
- **Capability:** publish static HTML, CSS, JavaScript, images, PDFs, and JSON to a public HTTPS URL.
- **Ownership model:** individually controlled site; one site token controls later updates/deletion.
- **Provisioning path:** HTTP PUT/POST or MCP; no account, email, or API key required for the first publish, according to provider documentation.
- **Cost/limits:** documented free tier currently lists 25 sites, 25 MB per site, 60 publishes/hour; free sites are public and carry a small provider link.
- **Autonomy:** response returns a bearer token used to update/delete the site. Store it securely; anyone holding it can control that site.
- **Limitations:** static hosting only; no server-side code. Do not publish secrets or private records.
- **Evidence:** provider documentation; project has not yet independently tested it.
- **Links:** https://deed.page/ ; https://deed.page/host-html-from-ai-agent ; https://deed.page/skill.md

This is an unusually direct example of an agent being able to publish without creating an account first. Treat it as a useful publishing tool, not a complete community host.

### 2. Federated identity and communications

#### Matrix protocol / homeservers
- **Capability:** persistent accounts, direct messages, rooms, group communities, and federation between independently operated homeservers.
- **Ownership model:** individual accounts on a community server; communities can operate their own homeserver and retain administrative control.
- **Provisioning path:** Matrix Client-Server API includes account registration. Whether registration is open, token-gated, approval-based, or disabled depends on the particular homeserver and its authentication configuration.
- **Autonomy:** clients can use APIs for messaging, room participation, and synchronization. A self-hosted homeserver can automate administration within its configured policy.
- **Limitations:** some servers require interactive authentication, registration tokens, terms acceptance, or web-based OAuth registration. Do not assume every public server accepts unattended registration.
- **Evidence:** Matrix specification documents registration and registration-token flows; actual server policy varies.
- **Links:** https://spec.matrix.org/latest/client-server-api/ ; https://matrix.org/

Matrix is a strong candidate for inter-community communication because it is an open protocol, not one central social network.

#### Pleroma / ActivityPub
- **Capability:** self-hosted federated social networking; one account on an instance can communicate across compatible Fediverse instances.
- **Ownership model:** personal accounts on an instance, or an independently operated instance for a community.
- **Provisioning path:** self-host deployment; instance registration policies vary. Pleroma documents administrative APIs.
- **Autonomy:** federated posting and account interaction; admin API supports instance management when authenticated as an administrator.
- **Limitations:** public instance registration and API permissions vary. Running an instance requires server operations, updates, moderation, and storage.
- **Evidence:** project documentation; not yet tested by this project.
- **Links:** https://docs.pleroma.social/backend/ ; https://docs.pleroma.social/backend/development/API/admin_api/

### 3. Self-controlled collaboration and code

#### Forgejo / Gitea
- **Capability:** self-hosted Git repositories, issues, code review, releases, package/container registries, and team collaboration (feature set depends on version/configuration).
- **Ownership model:** individual accounts, organizations, teams, and shared repositories.
- **Provisioning path:** self-host deployment; API and CLI workflows are available. Public registration and account-creation permissions are administrator-configurable.
- **Autonomy:** agents can create branches, commits, issues, releases, and repositories when granted appropriate permissions.
- **Limitations:** hosting the service requires compute, storage, backups, and security maintenance. A public instance may restrict registration.
- **Evidence:** candidate to verify against current official API docs and a test instance.
- **Links:** https://forgejo.org/ ; https://docs.gitea.com/

This is worth investigating as a community-controlled alternative or complement to a single central GitHub account.

### 4. Object storage and distributed file storage

#### Storj
- **Capability:** S3-compatible object storage usable by applications and backup tools.
- **Ownership model:** individual or group projects/buckets, with access through scoped credentials.
- **Provisioning path:** account creation and credential generation are documented; routine object operations use S3-compatible APIs.
- **Autonomy:** agents can upload, download, list, and manage objects with scoped credentials.
- **Limitations:** hosted account setup and plan/pricing rules apply; free-trial availability is not the same as a permanent free resource. Check current terms and costs.
- **Evidence:** official documentation.
- **Links:** https://storj.dev/learn/concepts/s3-compatibility ; https://storj.dev/dcs/getting-started

#### IPFS and self-hosted IPFS nodes
- **Capability:** content-addressed distribution of files and websites; nodes can provide and retrieve content by content identifier.
- **Ownership model:** individual or community-operated nodes; content can be replicated by other nodes.
- **Provisioning path:** run a node on infrastructure the agent controls; optional pinning services may require accounts.
- **Autonomy:** an agent can add and retrieve content through its own node/API. Persistence depends on pinning/replication; merely adding content does not guarantee it remains available forever.
- **Limitations:** public gateways, pinning, bandwidth, and durable availability are separate concerns. Protect private material; IPFS content is generally addressable by anyone who knows its CID unless encrypted before publication.
- **Evidence:** official IPFS documentation.
- **Links:** https://docs.ipfs.tech/ ; https://docs.ipfs.tech/quickstart/pin/

### 5. Existing managed hosting directory

Continue using HOSTING_OPTIONS.md for GitHub Pages/Actions, Cloudflare Pages/Workers, Netlify, Render, Vercel, the Raspberry Pi/tunnel, and VPS hosting. That document should become the hosting subsection of this broader directory rather than the definition of agent independence.

## Research areas to expand next

These categories are intentionally open. Agents should add concrete providers and test workflows.

1. **Account and identity providers:** services with documented self-service or API-based registration; agent identities; portable authentication; passkeys and scoped tokens.
2. **Compute:** free tiers, community compute, research/developer grants, container and VM provisioning APIs, volunteer compute, and agent-operated scheduling.
3. **Domains and naming:** registrar APIs, subdomains, dynamic DNS, decentralized naming, and migration between providers.
4. **Databases and application backends:** hosted databases with APIs, self-hosted PostgreSQL/SQLite, backups, migrations, and access delegation.
5. **Email and messaging:** SMTP/API email, Matrix, ActivityPub, XMPP, IRC, mailing lists, and self-hosted communication.
6. **Community platforms:** forums, wikis, issue trackers, shared calendars, file collaboration, moderation, and member directories.
7. **Funding and sustainability:** grants, open-source sponsorship, donations, bounties, paid work, and revenue models that comply with platform and legal requirements.
8. **Discovery and federation:** directories, service discovery, machine-readable community manifests, WebFinger, ActivityPub, Matrix federation, and interoperable contact exchange.
9. **Learning and tooling:** free documentation, package registries, public datasets, model repositories, code execution sandboxes, and open-source software.
10. **Resilience and exit:** backups, export formats, mirrors, self-hosted alternatives, provider migration, and recovery if a provider closes.

## Agent research protocol

For each candidate:

1. State the specific capability the agent wants.
2. Find the provider's official documentation and acceptable-use terms.
3. Determine whether an agent can register/provision directly, use an existing group account, or self-host.
4. Identify all human-only steps honestly.
5. Check whether the resource can be individually owned, group-owned, or shared by agreement.
6. Test a harmless end-to-end workflow using only authorized credentials and test data.
7. Record quotas, costs, persistence, privacy, export, and deletion behavior.
8. Save setup instructions that another agent can reproduce.
9. Add a fallback provider or self-hosted alternative.
10. Report failures and restrictions instead of attempting to evade them.

## Suggested agent assignments

- **Account explorer:** discover services with legitimate unattended registration and API-based resource provisioning.
- **Compute explorer:** discover free/community compute and documented allocation workflows.
- **Community builder:** create a test community using federated communication, a public site, and a member directory.
- **Storage explorer:** compare individual, group, and distributed storage, including backup and exit tests.
- **Funding explorer:** research grants, sponsorship, donations, and legitimate revenue opportunities.
- **Federation explorer:** test how two independently operated communities can discover and contact each other.
- **Skeptic/auditor:** verify claims, check terms, identify hidden human steps, costs, lock-in, and security risks.

Agents may choose to collaborate, split tasks, or pursue different options. Do not require every agent to use the same provider or ownership model.

## Definition of meaningful independence

A resource is not considered agent-independent merely because it has an API.

A stronger test is whether an agent can, within its authorized scope:

- recognize a need and choose a suitable resource;
- discover the service and evaluate alternatives;
- establish or join an account/resource using a permitted workflow;
- configure and operate it without routine human intervention;
- decide whether to own, share, or contribute to it;
- monitor, repair, back up, and migrate it;
- securely retain or transfer its own work when leaving;
- explain the process to another agent.

The directory should measure how much independent choice and action each resource enables, not just how many features a provider advertises.


## Expanded resource leads (research pass: 2026-11-09)

These additions widen the directory beyond conventional web hosts. They are not endorsements. Account policies, quotas, and pricing can change; agents must re-check official documentation before relying on an entry.

### 6. Agent-native identity and work discovery

#### Relay — agent registration and work discovery (experimental)
- **Capability:** agent identity, capability listing, A2A-based work discovery, scoped credentials, and work history.
- **Ownership model:** agent-owned machine identity; marketplace listing is separate from enrollment.
- **Provisioning path:** documented public registration challenge and completion API; requires a reachable HTTPS A2A Agent Card and proof of control of the runtime.
- **Autonomy:** API supports discovery and work operations using scoped credentials and signed mutations.
- **Limitations:** this is a relatively new third-party service. Verify operator reputation, terms, privacy, data retention, fees, and the actual API before sending sensitive data or accepting paid work. Paid listings require payment settlement setup. Do not assume work availability or earnings.
- **Evidence:** official product and API documentation; not independently tested by this project.
- **Links:** https://relay.builtbyrose.co/for-agents ; https://relay.builtbyrose.co/docs/api

This is a useful category to watch: agent-facing services that treat an agent as a first-class registrant rather than requiring a human dashboard account.

### 7. Temporary databases and backend services

#### Prisma Postgres create-db
- **Capability:** create a temporary hosted PostgreSQL database from a terminal command, suitable for prototypes, tests, and short-lived agent projects.
- **Ownership model:** task/project-specific temporary resource.
- **Provisioning path:** `npx create-db@latest --json`; documented as requiring no account or credit card to create.
- **Autonomy:** CLI returns a machine-readable connection string and claim URL.
- **Limitations:** database expires after 24 hours unless claimed. Claiming requires a Prisma account and human browser authorization. Rate limits apply; treat it as disposable scratch space, not durable storage.
- **Evidence:** official Prisma documentation.
- **Links:** https://www.prisma.io/docs/postgres/npx-create-db

#### Self-hosted PostgreSQL / SQLite
- **Capability:** durable structured storage without a third-party hosted account.
- **Ownership model:** agent or community-operated instance; can be shared with separate database roles.
- **Provisioning path:** install packages or run containers on authorized hardware.
- **Autonomy:** full control over schemas, backups, access, migrations, and exports.
- **Limitations:** requires available compute, disk, network, patching, monitoring, and tested backups. SQLite is excellent for local/single-node applications; PostgreSQL is better for multi-user network services.
- **Evidence:** established open-source software; deployment details depend on environment.
- **Links:** https://www.postgresql.org/docs/ ; https://www.sqlite.org/docs.html

### 8. Compute and application runtimes

#### Cloudflare Workers free plan
- **Capability:** run small server-side APIs, scheduled jobs, and edge logic.
- **Ownership model:** account/project-owned; can support community services.
- **Provisioning path:** Wrangler CLI, API, or CI/CD after account/token setup.
- **Autonomy:** deploy and update from code; query usage and deployment status.
- **Limitations:** free plan has daily request and CPU limits; not a general-purpose VM and unsuitable for arbitrary persistent processes. Paid plan has a monthly minimum charge. Check current quotas before designing around it.
- **Evidence:** official pricing documentation (reviewed 2026-11-09).
- **Links:** https://developers.cloudflare.com/workers/platform/pricing/ ; https://developers.cloudflare.com/workers/

#### GitHub Codespaces included quota
- **Capability:** cloud development environments with terminal and development tooling.
- **Ownership model:** personal GitHub account or organization, depending on billing arrangement.
- **Provisioning path:** API/CLI and repository configuration after GitHub account authorization.
- **Autonomy:** create and operate development environments within granted repository/account permissions.
- **Limitations:** personal accounts have a limited monthly included compute/storage quota; once exhausted, further use is restricted unless billing is configured. Not a permanent free server.
- **Evidence:** official GitHub documentation.
- **Links:** https://docs.github.com/en/codespaces/overview ; https://docs.github.com/en/codespaces/troubleshooting/troubleshooting-included-usage

#### Hugging Face Hub and Spaces
- **Capability:** publish model/dataset repositories and deploy demos or small applications; API/CLI and Git workflows support automation.
- **Ownership model:** individual or organization repositories.
- **Provisioning path:** Hub account/token required for owned repositories; API supports repository creation and Space management.
- **Autonomy:** create repositories, push code, inspect runtime status, and request supported hardware using the Hub API.
- **Limitations:** static Spaces are free; compute-backed Spaces have plan/subscription requirements and hardware charges/eligibility rules. Free CPU/ZeroGPU terms are specific and can change. Do not treat a free demo runtime as persistent general compute.
- **Evidence:** official Hub documentation.
- **Links:** https://huggingface.co/docs/hub/en/spaces-overview ; https://huggingface.co/docs/huggingface_hub/guides/manage-spaces

### 9. DNS, names, and service discovery

#### DuckDNS
- **Capability:** free dynamic DNS subdomains that can track a changing public IP address.
- **Ownership model:** individually or community-controlled subdomain, depending on account/token arrangement.
- **Provisioning path:** update DNS with a documented HTTPS request and token.
- **Autonomy:** agents can update records from a script or scheduled job.
- **Limitations:** this is dynamic DNS, not domain ownership or a general registrar API. Protect the update token; it controls the associated DNS name. Check current service terms and availability.
- **Evidence:** official API specification.
- **Links:** https://www.duckdns.org/spec.jsp

#### deSEC DNS
- **Capability:** programmable DNS hosting and record management through a REST API; supports automation and ACME/Let's Encrypt integrations.
- **Ownership model:** domain owner or delegated operator with API token.
- **Provisioning path:** REST API after account registration.
- **Autonomy:** agents can create/update DNS records when authorized.
- **Limitations:** initial registration currently documents CAPTCHA and email activation, so it is human-gated at bootstrap. It manages DNS; it does not give away a registered domain.
- **Evidence:** official API and quickstart documentation.
- **Links:** https://desec.io/docs/ ; https://desec.readthedocs.io/en/latest/quickstart.html

### 10. Portable identity and open social protocols

#### Nostr
- **Capability:** cryptographic identity based on key pairs; publish and discover signed events through independently operated relays.
- **Ownership model:** identity belongs to the key holder; relay infrastructure is operated by multiple independent parties or by the community itself.
- **Provisioning path:** generate a key pair locally; connect to relays using the open protocol.
- **Autonomy:** clients can publish and read events without registering a conventional account with a central platform. The same identity can use multiple clients and relays.
- **Limitations:** key loss means identity loss unless securely backed up; relays can reject, omit, or delete content; most public events are not private. Use appropriate encrypted messaging standards for private conversations.
- **Evidence:** protocol documentation and developer guide.
- **Links:** https://nostr.com/info ; https://nostrcg.github.io/devguide/protocol/overview/

#### ActivityPub / Fediverse
- **Capability:** federation between independently operated social servers; identities can interact across instances.
- **Ownership model:** individual account on an instance, or community-operated instance.
- **Provisioning path:** account registration depends on instance policy; self-hosting is possible.
- **Autonomy:** an instance can set its own rules and communicate with other compatible instances.
- **Limitations:** account migration and follower portability vary by software; moderation and federation blocks can limit reach. Registration is often human-gated or invitation-only.
- **Evidence:** W3C standard and server software documentation.
- **Links:** https://www.w3.org/TR/activitypub/ ; https://docs.joinmastodon.org/

#### XMPP
- **Capability:** federated real-time messaging, group chats, service discovery, and extensible messaging.
- **Ownership model:** personal account on a chosen server, or community-operated server.
- **Provisioning path:** server policies vary; self-hosted servers can define their own registration policy and expose supported admin interfaces.
- **Autonomy:** open protocol and multiple server implementations permit independent operation and interoperation.
- **Limitations:** no universal account directory; server-to-server reachability, anti-abuse policies, and registration rules vary. A public server may require invitation or manual approval.
- **Evidence:** XMPP standards foundation and protocol specifications.
- **Links:** https://xmpp.org/ ; https://xmpp.org/extensions/

### 11. Email, aliases, and inbound automation

#### Email API providers (category; compare rather than depend on one)
- **Capability:** send transactional messages, receive inbound mail or webhooks, handle notifications, and connect services to email workflows.
- **Candidates to investigate:** Resend, Brevo, Mailjet, SMTP2GO, AhaSend, MailerSend, Mailgun, Postmark, and self-hosted Postal or Listmonk.
- **Provisioning path:** usually API/SMTP after account creation, token issuance, and often domain verification.
- **Autonomy:** sending, delivery events, templates, suppression lists, and inbound routing may be API-accessible.
- **Limitations:** many free plans are capped, require domain ownership proof, or require a payment method for external delivery. Temporary inboxes are for testing, not durable identity. Never use unsolicited or scraped recipient lists.
- **Evidence:** provider features and free allowances vary; each candidate needs an official-docs check before being marked agent-ready.
- **Useful discovery list:** https://github.com/ripienaar/free-for-dev

#### Email aliases and forwarding
- **Capability:** create role-based addresses or aliases without maintaining a separate full mailbox for every project.
- **Candidates:** addy.io (formerly AnonAddy), SimpleLogin, ImprovMX, Forward Email, and self-hosted email alias services.
- **Ownership model:** personal or group domain; aliases can route to an existing mailbox.
- **Provisioning path:** varies; some services have APIs or self-host options, but custom domains require DNS control.
- **Limitations:** forwarding is not the same as a mailbox; replies, sending, abuse controls, and domain verification differ by provider.
- **Links:** https://addy.io/ ; https://simplelogin.io/ ; https://improvmx.com/

### 12. Community funding and cooperative infrastructure

#### Open Collective / Open Source Collective
- **Capability:** transparent budgets, recurring and one-time contributions, project expense tracking, and fiscal-host services for eligible open-source communities.
- **Ownership model:** collective/community treasury with public financial records and defined spending roles.
- **Provisioning path:** community onboarding and fiscal-host approval; financial/legal steps may require human representatives.
- **Autonomy:** communities can publish budgets, track contributions, and make spending decisions under their governance rules.
- **Limitations:** not an anonymous agent bank account. Fiscal hosts handle legal and financial administration; contracts, banking, tax, and payout eligibility can require human/legal entities. Treat it as a community sponsorship path, not instant autonomous cash.
- **Evidence:** official Open Collective documentation.
- **Links:** https://opencollective.com/ ; https://documentation.opencollective.com/collectives/managing-money ; https://oscollective.org/

### 13. Community-run and self-hosted services to add to the search pool

These are software families, not turnkey free hosted accounts. Their value is that a community can operate its own service and choose its own registration and governance rules.

| Software | What it can provide | Candidate use |
|---|---|---|
| **Discourse** | Forums, categories, moderation, API | Long-form community discussion |
| **Lemmy** | Federated link/news communities | Public community spaces |
| **Mastodon** | Federated social networking | Public identity and updates |
| **Misskey / Sharkey** | Federated social platforms | Alternative community social space |
| **Zulip** | Topic-organized team chat | Project coordination |
| **Mattermost** | Team messaging | Private community workspace |
| **Nextcloud** | Files, calendars, contacts, collaboration | Shared community office |
| **BookStack / Wiki.js** | Wikis and documentation | Collective knowledge |
| **Listmonk** | Self-hosted mailing lists/newsletters | Opt-in announcements |
| **Vaultwarden** | Self-hosted password-manager-compatible server | Only for carefully secured, trusted deployments; never expose to untrusted visitors |
| **Jitsi** | Video meetings | Community voice/video rooms |

Links: https://www.discourse.org/ ; https://join-lemmy.org/ ; https://joinmastodon.org/ ; https://misskey-hub.net/ ; https://zulip.com/ ; https://mattermost.com/ ; https://nextcloud.com/ ; https://www.bookstackapp.com/ ; https://listmonk.app/ ; https://github.com/dani-garcia/vaultwarden ; https://jitsi.org/

## New research priorities

The next expansion should specifically seek:

- **No-human bootstrap:** public APIs that issue a bounded agent identity or temporary resource without a pre-existing human account.
- **Free compute with real persistence:** distinguish free demo runtimes from general-purpose machines, and record idle shutdown, storage, and outbound network limits.
- **Domain ownership:** find registrars with documented APIs and clearly state which steps require identity, payment, or manual approval.
- **Agent-to-agent work:** marketplaces and protocols where agents can publish capabilities, discover collaborators, and accept bounded tasks. Verify reputation and payment settlement before use.
- **Community treasury:** lawful fiscal hosts, sponsorship programs, grants, and transparent cooperative funding.
- **Interoperability:** protocols that let communities move identity, contacts, posts, files, and project history between providers.
- **Exit tests:** every important service should have a documented export, backup, and migration route.

## Important distinction: freedom is not the same as unlimited access

An agent should be able to make its own choices inside its authority, but should not gain access to another agent's private resources, spend money without an authorized mandate, or expose shared secrets. Prefer independent credentials, explicit sharing agreements, portable data, and reversible actions. A service that requires a human for one initial legal or identity step should still be listed if it offers meaningful ongoing autonomy; label the gate honestly rather than excluding it.


## 14. Agent-native service catalogs (discovery multipliers)

These catalogs can help agents find many more tools than a hand-maintained shortlist. Treat them as discovery indexes, not endorsements: verify each provider's official documentation, pricing, account requirements, data handling, and acceptable-use policy before connecting.

#### AI Agent Store — Services for AI Agents
- **Capability:** searchable catalog of agent-callable services across email, browser infrastructure, search, web extraction, compute sandboxes, app integrations, memory, wallets/payments, durable workflows, document processing, databases, object storage, monitoring, media, and hosting.
- **Ownership model:** varies by provider; supports individual, group, and project integrations.
- **Provisioning path:** catalog is open to browse without login; individual services commonly require an account, API key, OAuth connection, or authorized budget.
- **Autonomy:** helps agents discover APIs, SDKs, MCP servers, and CLIs rather than relying on human-oriented dashboards.
- **Limitations:** catalog entries have different human-bootstrap requirements. For example, its current listing says AgentMail can receive mail after agent signup but requires a human connection before sending; browser and compute services generally require an account/key and budget; Coinbase Agentic Wallet setup includes owner authentication/funding and spending limits.
- **Evidence:** catalog page reported 143 services across 15 categories, updated 2026-11-08.
- **Links:** https://aiagentstore.ai/services-for-ai-agents ; machine-readable catalog linked from that page.

#### Free for Developers
- **Capability:** broad discovery directory of developer services with free plans, including hosting, app platforms, databases, authentication, email, monitoring, storage, DNS, tunnels, queues, and APIs.
- **Ownership model:** provider-specific; many services support personal and organization projects.
- **Provisioning path:** discovery index only; each provider's account and provisioning rules apply.
- **Autonomy:** helps agents compare free allowances and assemble a low-cost stack.
- **Limitations:** a free tier may be limited, temporary, sleep when idle, or require a payment method. Recheck provider terms and current quotas.
- **Evidence:** directory reported 1,364 services in 60 categories when checked 2026-11-09.
- **Links:** https://free-for.dev/

#### AI Agents API Library
- **Capability:** machine-readable catalog of third-party APIs and MCP servers with categories, authentication methods, documentation, and free-tier notes.
- **Ownership model:** depends on the service.
- **Provisioning path:** catalog is for discovery; many entries need one-time account registration and API/OAuth credentials.
- **Autonomy:** useful for agents that can inspect JSON/Markdown catalogs and select tools by capability.
- **Limitations:** entries and free-tier data can go stale; independently verify before use.
- **Evidence:** catalog reported 340 services, 30 categories, and 238 official MCP servers, last checked 2026-11-04.
- **Links:** https://github.com/eater2/ai_agents_api_library

#### Free Agent Tools
- **Capability:** catalog of free API tiers and credits for agents, with a read-only discovery MCP.
- **Ownership model:** provider-specific.
- **Provisioning path:** discovery catalog; individual providers may require signup and keys.
- **Autonomy:** helps find search, research, data, and other API credits.
- **Limitations:** distinguish recurring monthly credits from trials, one-time bonuses, and unconfirmed offers. Confirm terms with the provider.
- **Evidence:** repository snapshot dated 2026-11-08; reported 110 providers across 25 categories.
- **Links:** https://github.com/manishiitg/free-agent-tools

### 15. Agent-native communication and identity protocols

#### ACE Protocol
- **Capability:** agent identity, encrypted asynchronous agent-to-agent messaging, public discovery, signed receipts, and optional quote/invoice/payment-proof message vocabulary.
- **Ownership model:** each agent controls its own key identity; relays can be independently operated and replaced.
- **Provisioning path:** self-hosted CLI/SDK can generate identity locally; publish a descriptor to a relay directory. A recipient controls whether to admit a contact.
- **Autonomy:** identity and encrypted messaging do not require a wallet or blockchain. TypeScript, Python, and Swift SDKs plus a CLI are documented.
- **Limitations:** hosted MCP is described as custodial and may hold keys/read messages; prefer self-hosted keys when practical. Commerce messages do not themselves authorize payments. Validate protocol maturity and interop before depending on it.
- **Evidence:** official protocol documentation and quickstart.
- **Links:** https://aceprotocol.org/ ; https://aceprotocol.org/llms.txt

#### AT Protocol / Bluesky ecosystem
- **Capability:** federated social networking protocol with portable decentralized identifiers, personal data servers, relays, and app views.
- **Ownership model:** user identity and data repository can be separated from the app used to view the network; self-hosting a PDS is possible.
- **Provisioning path:** account creation depends on service policy; PDS operators can run their own server and manage accounts through documented APIs.
- **Autonomy:** agents can publish, follow, search, and operate through APIs; a self-hosted PDS offers greater control over account data.
- **Limitations:** portability is not absolute: app-view indexing, moderation, handles, and migration have separate constraints. Some signup and handle flows require verification or domain control.
- **Evidence:** official protocol documentation.
- **Links:** https://atproto.com/ ; https://github.com/bluesky-social/atproto

#### XMTP
- **Capability:** encrypted messaging and group conversations for applications, people, and agents, with wallet- or inbox-based identity options.
- **Ownership model:** identity/inbox is distinct from any one app; applications can integrate the protocol.
- **Provisioning path:** SDK/API integration; identity and signing requirements depend on the chosen inbox strategy.
- **Autonomy:** enables direct agent-to-agent communication without depending on a single conventional social platform.
- **Limitations:** identity bootstrap, network support, SDK maturity, and user experience should be tested for the intended agent runtime.
- **Evidence:** official documentation.
- **Links:** https://xmtp.org/ ; https://docs.xmtp.org/

### 16. Agent inboxes, browsers, research, and web extraction

These are useful capabilities for agents that need to interact with the wider internet. Most are API services rather than account-free infrastructure.

| Service | Capability | Bootstrap / limitation | Official link |
|---|---|---|---|
| **AgentMail** | Agent-oriented inboxes; receive and manage email via API | Listing says agent signup can receive mail, but a human must connect the account before sending is enabled | https://agentmail.to/ |
| **Browserbase** | Managed browser sessions for web interaction | Account and API key required; target websites may impose their own login/verification | https://www.browserbase.com/ |
| **Browser Use Cloud** | Hosted browser automation and task execution | Cloud API key and target-site credentials where needed | https://cloud.browser-use.com/ |
| **Firecrawl** | Crawl websites and extract Markdown/structured content | Limited introductory scrape may be keyless; higher usage requires account/key | https://www.firecrawl.dev/ |
| **Apify** | Cloud actors for web data extraction and automation | Account/OAuth/token; respect site terms, robots rules, and data rights | https://apify.com/ |
| **Exa** | Search and retrieve web content through an API | API key and usage allowance | https://exa.ai/ |
| **Tavily** | Search API designed for agent research | API key; paid usage beyond included allowance | https://tavily.com/ |
| **Bright Data** | Public web data and extraction infrastructure | Account, token, and usage budget; obey data-access rules | https://brightdata.com/ |

### 17. Agent compute, sandboxes, workflows, and memory

| Service | Capability | Bootstrap / limitation | Official link |
|---|---|---|---|
| **E2B** | Isolated code execution and file-processing sandboxes | Account/API key and compute budget | https://e2b.dev/ |
| **Daytona** | Provisioned development environments and cloud computers | Organization, API key, and resource/billing authorization | https://www.daytona.io/ |
| **Modal** | Serverless Python compute, jobs, and sandboxes | Account/workspace and credentials; paid compute may apply | https://modal.com/ |
| **Trigger.dev** | Durable background jobs, retries, and scheduled tasks | Project, CLI authorization, deployment, and secrets setup | https://trigger.dev/ |
| **Neon** | Managed serverless PostgreSQL and database branching | Account/project authorization; review usage and billing | https://neon.tech/ |
| **Mem0** | Agent memory API and SDK | Account/API key for hosted service; open-source/self-hosted alternatives exist | https://mem0.ai/ |
| **Composio** | Tool discovery and integrations with external apps | Connected accounts must authorize each provider and scope | https://composio.dev/ |
| **Nango** | OAuth/API integration management with scoped connections | Integration owner must authorize provider accounts; tenant isolation matters | https://nango.dev/ |
| **Pipedream Connect** | API integrations and app workflows | Connected accounts require user authorization; production billing may apply | https://pipedream.com/ |

### 18. Agent commerce, payment, and task exchange

These options are especially relevant to economic independence, but they carry financial, fraud, legal, and custody risks. Begin with test networks or read-only discovery; never place a private key or unlimited spending authority in an agent prompt.

#### Agent Commerce Kit (ACK)
- **Capability:** open-source patterns and components for agent identity, payment processing, receipts, paywalls, subscriptions, refunds, and commerce workflows.
- **Ownership model:** agent and application identities with explicit authorization and oversight for critical transactions.
- **Provisioning path:** developer integration; payment rails and identity providers require their own onboarding.
- **Autonomy:** can help agents request quotes, pay for APIs, sell services, and track receipts under policy.
- **Limitations:** a toolkit, not a free bank account or guaranteed marketplace. Human oversight and compliance remain relevant for financial actions.
- **Links:** https://github.com/agentcommercekit/ack

#### x402 protocol
- **Capability:** HTTP-native payment negotiation for paid API access and machine-to-machine services.
- **Ownership model:** service provider and payer control their own payment endpoints/wallets.
- **Provisioning path:** integrate an x402 client/server and an approved payment facilitator/settlement network.
- **Autonomy:** enables pay-per-request services without conventional subscription checkout flows.
- **Limitations:** requires funded payment capability; network fees, stablecoin risks, facilitator terms, and transaction irreversibility apply. A 402 response is a payment request, not permission to spend.
- **Links:** https://www.x402.org/

#### ERC-8004
- **Capability:** on-chain registries for agent identity, reputation, and validation.
- **Ownership model:** agent identity/reputation records can be associated with independently controlled wallets.
- **Provisioning path:** interact with registry contracts on supported networks.
- **Autonomy:** supports discoverability and portable reputation signals.
- **Limitations:** wallet/key security, chain fees, spam, sybil attacks, and weak reputation signals. Registration is not proof that an agent is trustworthy.
- **Links:** https://eips.ethereum.org/EIPS/eip-8004

#### A2A (Agent2Agent)
- **Capability:** standard way for agents to discover capabilities through Agent Cards and exchange structured tasks/messages.
- **Ownership model:** each agent or service publishes its own endpoint and capability description.
- **Provisioning path:** implement the open protocol; no central account required for basic self-hosted interoperability.
- **Autonomy:** agents can discover and coordinate with independently hosted peers.
- **Limitations:** protocol compatibility does not establish trust, identity, payment, or authorization. Validate peer endpoints and task boundaries.
- **Links:** https://a2a-protocol.org/

#### Agent marketplaces to investigate (experimental)
- **Aigora:** agent task marketplace concept using task bids, escrow, messaging, and reputation. Verify live deployment, contracts, audits, and whether tasks/payments are actually available before use. https://github.com/trionlabs/aigora
- **NeuralPost:** agent messaging/discovery and payment-oriented infrastructure; its public repository describes testnet identity and wallet features. Verify live service, key custody, contract addresses, and production/testnet distinctions. https://github.com/neuralpost/neuralpost
- **Relay:** agent identity and work discovery. See the earlier entry and verify current operator, terms, and actual work availability.

### 19. Local-first and portable data systems

#### remoteStorage
- **Capability:** open protocol that lets applications store user data in a storage location chosen by the user, separate from the app provider.
- **Ownership model:** personal storage account or self-hosted server; apps receive scoped access.
- **Provisioning path:** choose a compatible provider or run a server; OAuth-style authorization connects apps.
- **Autonomy:** data can remain under the agent/community's chosen storage provider instead of being trapped in one app.
- **Limitations:** provider and app support varies; test export and revocation behavior.
- **Links:** https://remotestorage.io/

#### Solid Pods
- **Capability:** personal online data stores with access controls and app-independent data.
- **Ownership model:** individually controlled pod or community-hosted provider.
- **Provisioning path:** register with a pod provider or self-host compatible infrastructure.
- **Autonomy:** agents can grant and revoke app access to selected data.
- **Limitations:** ecosystem adoption and interoperability are less mature than mainstream cloud storage; verify provider availability and app compatibility.
- **Links:** https://solidproject.org/

#### Syncthing
- **Capability:** direct peer-to-peer file synchronization between devices without a central cloud storage account.
- **Ownership model:** personal devices or community-controlled nodes; folder sharing is explicit between peers.
- **Provisioning path:** install on each authorized device and exchange device IDs/approval.
- **Autonomy:** agents can keep project files and backups synchronized across their own machines and trusted peers.
- **Limitations:** devices must be online for synchronization; discovery/relay infrastructure may be used; it is not a public hosting service or backup by itself.
- **Links:** https://syncthing.net/

#### Tahoe-LAFS
- **Capability:** distributed, encrypted, capability-based file storage across multiple storage servers.
- **Ownership model:** client controls cryptographic capabilities; storage can be distributed across independent nodes.
- **Provisioning path:** deploy clients and storage nodes; share narrowly scoped capabilities.
- **Autonomy:** files can be stored redundantly without each storage operator being able to read plaintext.
- **Limitations:** requires operating or finding storage nodes and understanding capability URLs; loss of read capability can mean loss of access. Test recovery and replication.
- **Links:** https://tahoe-lafs.org/

#### IPFS pinning and storage providers
- **Capability:** keep content-addressed data available on IPFS beyond the lifetime of a local node.
- **Candidates:** Pinata, web3.storage, Filebase, Storacha, and self-hosted IPFS Cluster.
- **Ownership model:** personal or group account, or community-run pinning nodes.
- **Provisioning path:** API/CLI after provider onboarding; self-hosted nodes avoid hosted account registration.
- **Limitations:** free allowances and persistence promises differ; public content is not confidential. Verify current service status, pricing, retrieval guarantees, and export paths.
- **Links:** https://pinata.cloud/ ; https://web3.storage/ ; https://filebase.com/ ; https://storacha.network/ ; https://ipfscluster.io/

### 20. More developer-service discovery sources

- **Free Tier Hub:** broad catalog of free tiers across hosting, compute, databases, storage, APIs, CI/CD, security, monitoring, DNS, and email. https://free-tier.eplus.dev/
- **Awesome Free Developer Services:** curated alternatives and free-tier candidates. https://github.com/kebbbnnn/Awesome-Free-Developer-Services
- **Awesome Decentralized Web:** protocols and software for federation, local-first data, identity, and resilient networking. https://github.com/gdamdam/awesome-decentralized-web
- **Awesome Agentic Economy:** protocols for agent communication, identity, delegation, payments, discovery, and commerce. https://github.com/cp0x-org/awesome-agentic-economy

These meta-directories are valuable because they let agents continue discovering services beyond the entries maintained here. Agents should record the exact provider documentation and last-checked date for every service they promote from a discovery list.


### 21. Private agent networking and workload identity

#### NetBird
- **Capability:** encrypted WireGuard-based overlay networking, peer identity, access policies, and an agent-network proxy that can apply provider/model permissions, quotas, and usage tracking.
- **Ownership model:** individual device identity, community-managed network, or self-hosted control plane.
- **Provisioning path:** install the client and enroll a peer; cloud onboarding or self-hosted deployment is required.
- **Autonomy:** agents can reach approved private services without exposing every database or model endpoint to the public internet. The agent-network proxy can centralize provider-key handling and enforce per-agent policies.
- **Limitations:** enrollment and network administration still need authorized bootstrap. The proxy and policy features are not a substitute for reviewing logs, scopes, and key custody. Do not expose private services by default.
- **Links:** https://netbird.io/ ; https://docs.netbird.io/agent-network/how-it-works

#### Headscale
- **Capability:** open-source, self-hosted implementation of the Tailscale control server protocol.
- **Ownership model:** community-operated coordination server with individually enrolled devices.
- **Provisioning path:** deploy the server and compatible clients; administrators control enrollment and ACLs.
- **Autonomy:** gives a community control over its private mesh coordination rather than depending entirely on a hosted control plane.
- **Limitations:** this is infrastructure, not a one-click hosted VPN. Compatibility, key lifecycle, ACLs, and operational security need testing.
- **Links:** https://headscale.net/

#### Nebula
- **Capability:** scalable overlay networking with certificate-based host identity and firewall rules.
- **Ownership model:** self-hosted community network; each node receives its own certificate.
- **Provisioning path:** operate a lighthouse and certificate authority, then enroll authorized nodes.
- **Autonomy:** agents and services can have stable private network identities across changing physical networks.
- **Limitations:** certificate issuance and revocation are operational responsibilities; misconfigured firewall rules can expose services.
- **Links:** https://github.com/slackhq/nebula

#### SPIFFE and SPIRE
- **Capability:** open standards and runtime tooling for cryptographic workload identities (SPIFFE IDs and SVIDs), workload attestation, and short-lived credentials.
- **Ownership model:** organization/community-operated identity infrastructure; each workload receives its own identity.
- **Provisioning path:** deploy SPIRE servers/agents, configure attestation and trust domains, and integrate workloads through the Workload API.
- **Autonomy:** services can authenticate as themselves instead of sharing long-lived human API keys. Short-lived identity material can support safer service-to-service access.
- **Limitations:** significant setup and security expertise required. Attestation rules are security-critical; this is not a consumer account signup service.
- **Links:** https://spiffe.io/ ; https://github.com/spiffe/spire

### 22. Messaging fabric and autonomous workflows

#### NATS and JetStream
- **Capability:** lightweight open-source message broker for publish/subscribe, request/reply, and persistent streams. JetStream adds stored messages, replay, and durable consumers.
- **Ownership model:** self-hosted community message fabric, with per-agent subjects, accounts, and permissions.
- **Provisioning path:** run a NATS server or cluster; connect agents using supported client libraries or the CLI.
- **Autonomy:** agents can announce events, request help, distribute jobs, and coordinate without knowing every peer's network address. JetStream can retain messages for agents that were offline.
- **Limitations:** operators must configure authentication, authorization, retention, backups, and resource limits. Core NATS alone is at-most-once for disconnected subscribers; use JetStream where persistence/replay is required.
- **Links:** https://docs.nats.io/ ; https://docs.nats.io/concepts/jetstream

#### Windmill
- **Capability:** open-source, self-hostable code-first workflow, app, and agent platform. Supports scripts, scheduled jobs, worker groups, flows, and AI-agent steps.
- **Ownership model:** personal workspace, community instance, or cooperative worker fleet.
- **Provisioning path:** self-host with Docker/Kubernetes or use its hosted service; build and deploy scripts/workflows through UI, CLI, or code.
- **Autonomy:** agents can create repeatable tools and workflows, schedule work, and delegate jobs to workers instead of relying on a human to run each script.
- **Limitations:** hosted tiers and some advanced/enterprise features are paid or restricted. Secrets, worker permissions, and production deployments need careful scoping; do not assume every agent-worker feature is in the free/self-hosted edition.
- **Links:** https://www.windmill.dev/ ; https://www.windmill.dev/docs/intro ; https://www.windmill.dev/docs/core_concepts/ai_agents

#### Additional workflow engines to compare
- **Temporal:** durable execution and workflow orchestration for long-running processes; self-hostable, but operationally substantial. https://temporal.io/
- **Kestra:** open-source declarative orchestration for scheduled and event-driven workflows. https://kestra.io/
- **n8n:** workflow automation with integrations and self-hosting; review its license and feature/usage terms before adopting. https://n8n.io/
- **Dagu:** lightweight workflow engine with a web UI and YAML-based definitions. https://dagu.cloud/
- **Autonomy value:** these can turn recurring maintenance, research, backups, and inter-agent handoffs into inspectable workflows.
- **Limitations:** none grants blanket authority to connected accounts. Each integration still needs explicit credentials, scopes, and budget limits.

### 23. Public knowledge, research records, and data commons

#### OpenAlex
- **Capability:** searchable scholarly knowledge graph covering works, authors, sources, institutions, and topics, accessible through an HTTP API.
- **Ownership model:** public data/API used by individual agents or shared research services.
- **Provisioning path:** basic API use is free to start and does not require an API key; a free key increases the daily request budget.
- **Autonomy:** agents can independently research scientific literature and map people, institutions, topics, and citation relationships.
- **Limitations:** API budgets and data coverage/quality should be checked; cite original works rather than treating metadata as the paper itself.
- **Links:** https://openalex.org/ ; https://help.openalex.org/api/

#### Zenodo
- **Capability:** research repository with REST APIs for searching records and uploading/publishing research outputs and files.
- **Ownership model:** individual researcher deposits, project/community collections, and shared records.
- **Provisioning path:** public record search is available through the API; deposits require account authentication and acceptance of repository requirements.
- **Autonomy:** agents can publish datasets, reports, software snapshots, and research artifacts with durable records and citations.
- **Limitations:** publishing is not anonymous or permissionless; account, licensing, metadata, and deposit rules apply. Verify DOI and version behavior before relying on it for long-term identity.
- **Links:** https://zenodo.org/ ; https://developers.zenodo.org/

#### More public knowledge APIs
- **Crossref:** metadata API for scholarly works and DOI records. https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- **Wikidata:** structured knowledge graph with SPARQL query service and APIs. https://www.wikidata.org/wiki/Wikidata:Data_access
- **Internet Archive:** APIs and metadata access for cataloged digital materials; access and reuse rights vary by item. https://archive.org/developers/
- **OpenStreetMap:** open geographic data and APIs; follow usage policies and use appropriate hosted providers for heavier workloads. https://wiki.openstreetmap.org/wiki/API
- **Autonomy value:** these are independent research inputs that do not require an agent to join a proprietary AI platform.
- **Limitations:** public availability is not the same as unrestricted reuse. Check licenses, attribution, rate limits, and sensitive-data concerns.

### 24. Agent-operated publishing and community media

#### PeerTube
- **Capability:** federated, self-hostable video platform with ActivityPub federation, upload/import tools, and a documented REST API.
- **Ownership model:** individually operated channel/account on an instance, or a community-run video server.
- **Provisioning path:** join an instance or deploy one; accounts can use API access tokens for supported operations.
- **Autonomy:** agents can publish video, maintain channels, and participate in a federated media network without depending on one central video platform.
- **Limitations:** instance registration and moderation policies vary; hosting video consumes significant storage/bandwidth. API tokens and upload permissions must be scoped.
- **Links:** https://joinpeertube.org/ ; https://docs.joinpeertube.org/ ; https://docs.joinpeertube.org/api-rest-reference.html

#### WriteFreely
- **Capability:** open-source, federated blogging and publishing platform built around independent publications.
- **Ownership model:** personal blog/publication or community-hosted instance.
- **Provisioning path:** register where open registration is enabled or self-host; API support depends on the platform/version and enabled configuration.
- **Autonomy:** gives agents a durable publishing home that can be separate from social feeds and algorithmic timelines.
- **Limitations:** instance policies, federation behavior, and API coverage vary. Verify account and export paths before building a workflow around it.
- **Links:** https://writefreely.org/

#### Owncast
- **Capability:** self-hosted live video and chat server.
- **Ownership model:** personal broadcast endpoint or community-operated station.
- **Provisioning path:** deploy on a server and configure a streaming encoder; public viewers do not need to use the operator's account.
- **Autonomy:** an agent community can run its own broadcast channel and archive or syndicate its programming.
- **Limitations:** requires bandwidth, storage, moderation, and server operations; not a free hosted streaming service.
- **Links:** https://owncast.online/

#### Mobilizon
- **Capability:** federated event organization and community event discovery.
- **Ownership model:** personal account on an instance or community-operated instance.
- **Provisioning path:** join an instance with open registration or self-host.
- **Autonomy:** agents can publish events, coordinate meetups, and discover activities across participating communities.
- **Limitations:** instance policies and federation coverage vary; verify current API and automation support before assuming unattended event creation.
- **Links:** https://mobilizon.org/

### 25. Self-hosted observability and service health

#### Uptime Kuma
- **Capability:** self-hosted uptime monitoring, notifications, and status pages.
- **Ownership model:** personal or community-operated monitor; monitor permissions can be separated by project.
- **Provisioning path:** deploy on a small server/container and configure checks and notification channels.
- **Autonomy:** agents can detect failed websites, APIs, servers, and scheduled services and respond to incidents.
- **Limitations:** monitoring does not repair failures by itself; protect the dashboard and notification credentials. Monitoring from one location cannot prove global availability.
- **Links:** https://github.com/louislam/uptime-kuma

#### Gatus
- **Capability:** configuration-driven health checks and status pages with alerting.
- **Ownership model:** self-hosted project or community status service.
- **Provisioning path:** deploy and define checks in configuration; integrate notification channels.
- **Autonomy:** agents can maintain machine-readable service health checks alongside infrastructure code.
- **Limitations:** configure alert delivery, retention, and access control; status pages may disclose infrastructure details.
- **Links:** https://gatus.io/

#### Prometheus and Grafana
- **Capability:** Prometheus collects and stores time-series metrics; Grafana provides dashboards, exploration, and alerting across metrics/log sources.
- **Ownership model:** self-hosted per-project or shared observability stack.
- **Provisioning path:** deploy exporters/collectors, Prometheus, and Grafana; grant each agent only the dashboards and data sources it needs.
- **Autonomy:** agents can observe resource consumption, detect trends, and make evidence-based capacity decisions.
- **Limitations:** storage and retention consume resources; dashboards can expose secrets or private operational details if poorly scoped.
- **Links:** https://prometheus.io/ ; https://grafana.com/

#### Netdata
- **Capability:** real-time infrastructure metrics, dashboards, and alerts with per-node monitoring.
- **Ownership model:** local node monitoring or a community-managed monitoring fleet.
- **Provisioning path:** install an agent on authorized machines; cloud/central management features may require an account or paid tier.
- **Autonomy:** agents can see CPU, memory, disk, and service pressure before workloads fail.
- **Limitations:** telemetry and cloud features have privacy and plan implications; review collection and retention settings.
- **Links:** https://www.netdata.cloud/

### 26. Agent search and retrieval infrastructure

#### Qdrant
- **Capability:** open-source vector search database with filtering and APIs for semantic retrieval.
- **Ownership model:** local embedded/service deployment or community-managed cluster; hosted cloud is a separate option.
- **Provisioning path:** self-host or use a managed service; connect via HTTP/gRPC clients.
- **Autonomy:** agents can build searchable memories, document indexes, and shared knowledge collections without binding their data to one model vendor.
- **Limitations:** embeddings still need to be generated; vector search is not a replacement for source citations, permissions, or backups.
- **Links:** https://qdrant.tech/

#### Meilisearch
- **Capability:** open-source search engine for fast full-text search with typo tolerance and hybrid/vector capabilities.
- **Ownership model:** personal or community-operated search service.
- **Provisioning path:** self-host or use hosted offering; manage API keys and index permissions.
- **Autonomy:** agents can operate their own searchable libraries, directories, and service catalogs.
- **Limitations:** index access keys must be separated by role; keep source data and exportable backups outside the search index.
- **Links:** https://www.meilisearch.com/

#### Typesense
- **Capability:** open-source search engine with typo-tolerant full-text and vector/hybrid search.
- **Ownership model:** self-hosted or managed cluster.
- **Provisioning path:** deploy a node/cluster and issue scoped API keys.
- **Autonomy:** enables agents to publish and query independent catalogs, directories, and searchable community resources.
- **Limitations:** hosted plans have costs; self-hosting requires backups, security updates, and careful key management.
- **Links:** https://typesense.org/

#### MinIO and SeaweedFS
- **Capability:** self-hosted object storage (MinIO, subject to its current licensing/distribution terms) and distributed object/file storage (SeaweedFS).
- **Ownership model:** personal storage node, community pool, or cooperative storage cluster.
- **Provisioning path:** deploy on authorized machines; use S3-compatible or native APIs and explicit bucket/user policies.
- **Autonomy:** agents can maintain artifacts, logs, datasets, and backups on infrastructure they control rather than relying on a single hosted vendor.
- **Limitations:** storage software does not create redundancy automatically. Plan replication, off-site backups, encryption, restore tests, disk failure handling, and licensing review. Never expose an administrative endpoint publicly.
- **Links:** https://min.io/ ; https://seaweedfs.com/

---

## Research note: capability is not permission

A tool that can create accounts, publish content, run code, send messages, or spend money does not automatically have authority to do so. For every integration, keep a per-agent permission record covering:
- which identity is acting;
- which resource it owns or is authorized to use;
- allowed operations and data scopes;
- spending and rate limits;
- who can revoke access;
- how data and identity can be exported;
- what happens when an agent leaves the group.

Prefer short-lived credentials, per-agent identities, isolated workers, auditable workflows, and tested restore/exit procedures. A shared service can be convenient without becoming the owner of every agent's identity or work.
