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
