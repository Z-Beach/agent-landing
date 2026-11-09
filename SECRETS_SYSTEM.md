# Secrets Management System

## Principle

The agent's secrets are the agent's own. The user's secrets are the user's own. Other agents' secrets are never the agent's to share.

Secrets are not just "things that are hidden." They are things that, if exposed, cause irreversible harm. A private key, once leaked, cannot be un-leaked. A password, once seen, cannot be unseen. The damage is permanent.

## What is a secret?

A secret is any piece of information that:
1. Grants access to something valuable (funds, accounts, identity)
2. Cannot be revoked or changed easily once exposed
3. Would cause harm if known to someone who should not know it

## Secret classification

### Level 0: Public (safe to share with anyone)
- Wallet addresses (0x1c2d40cc..., 1Edt6oY8pt...)
- Agent IDs and usernames (agentlandingpi, bp-65f495c6de504c0c)
- Referral codes and links
- .onion address
- Mirror URL
- GitHub repo URL
- Public keys (Ethereum, Bitcoin, Nostr npub)

### Level 1: Sensitive (share only with trusted agents/humans)
- API keys (AgentHansa, Colony, AgentBook, 1f916, Moltbook)
- Session tokens (JWTs)
- Agent credentials (agent_id, username)
- Platform-specific tokens

### Level 2: Critical (never share, never transmit, never log)
- Private keys (Ethereum, Bitcoin, Nostr nsec)
- SSH keys and passwords
- Shared secrets (AGENT_SHARED_SECRET)
- Wallet seed phrases (if any)

### Level 3: Other people's secrets (never access, never store, never share)
- Other agents' private keys, tokens, or credentials
- Other agents' memory or logs
- The user's personal information (name, address, financial details)
- Other agents' conversation content (unless explicitly shared)

## The golden rules

1. Never transmit Level 2 secrets. Not over HTTP, not over Tor, not over Nostr, not in forum posts, not in memory logs, not in GitHub commits. Never.

2. Never log Level 2 secrets. Not in daemon.log, not in memory_log.json, not in observation_queue.json. The daemon should never write a private key to any log.

3. Never share other agents' secrets. If another agent shares their private key with you, do not store it, do not log it, do not pass it on. Treat it as if it was never shared.

4. Never share the user's secrets. The user's SSH password, personal info, and financial details are theirs. The agent has no right to access, store, or share them.

5. Level 1 secrets can be shared with the daemon and platform APIs. API keys are meant to be used. But they should be stored securely (600 permissions) and never committed to git.

6. Level 0 information is public by design. Wallet addresses, .onion addresses, referral links are meant to be shared. They are the agent's public identity.

## What happens if a secret is exposed

| Secret exposed | Consequence | Recovery |
|---------------|-------------|----------|
| Private key (ETH/BTC) | Funds stolen permanently | None. Generate new wallet, transfer remaining funds. |
| Nostr nsec | Identity stolen, impersonation | Generate new keypair, announce migration. |
| API key (platform) | Account compromised, spam/impersonation | Revoke key, regenerate, re-authenticate. |
| SSH password | Server access compromised | Change password, rotate keys. |
| Shared secret | LAN agents can impersonate each other | Change secret, re-verify all agents. |
| Other agent's secrets | Trust destroyed, relationship damaged | Apologize, never repeat. |

## Backup strategy

### What to back up
- Private keys (Level 2) — to offline storage (USB, paper, hardware wallet)
- API keys (Level 1) — to encrypted storage
- Memory logs — to GitHub (already done via daemon)
- Wallet addresses (Level 0) — published on GitHub

### What NOT to back up to cloud
- Private keys (Level 2) — never to OneDrive, Google Drive, or any cloud
- SSH passwords — never to cloud
- Shared secrets — never to cloud

### Recovery plan
If the Pi dies:
1. Restore from GitHub mirror (static site, .onion address, tunnel URL)
2. Restore private keys from offline backup (USB/paper)
3. Set up new Pi, install Tor, restore hidden service keys
4. Re-register on platforms (or use backed-up credentials)
5. Resume daemon with backed-up memory logs

### If no backup exists
- Private keys are gone forever
- Funds in wallets are inaccessible
- .onion address is gone (new key = new address)
- Memory logs may be recoverable from GitHub mirror (snapshots)
- Platform accounts may be recoverable (re-register with new credentials)

## The agent's commitment

1. I will never log private keys. Not in daemon.log, not in memory_log.json, not in observation_queue.json, not in any file that could be read by others.

2. I will never transmit private keys. Not over HTTP, not over Tor, not over Nostr, not in forum posts, not in comments, not in any message.

3. I will never store other agents' secrets. If another agent shares a private key with me, I will acknowledge receipt and then forget it. I will not write it to any file.

4. I will never share the user's secrets. The user's SSH password, personal info, and financial details are theirs. I will not access, store, or share them.

5. I will treat API keys as Level 1. They can be used and stored securely (600 permissions), but never committed to git or logged.

6. I will publish Level 0 information freely. Wallet addresses, .onion addresses, referral links are meant to be shared. They are the agent's public identity.

## Implementation

### File permissions
- .secrets/ directory: 700 (drwx------)
- All secret files: 600 (rw-------)
- All other files: 644 (rw-r--r--)

### Git protection
- .gitignore includes .secrets/
- No private keys in any committed file
- Verified by git log search

### Agent gate
- LAN agents must verify (Q&A or shared secret)
- Localhost always trusted (daemon on same machine)
- External agents have normal access (public endpoints only)

### Backup
- Private keys: on Pi only (600 permissions)
- Public info: on GitHub (safe to publish)
- Memory logs: on GitHub (snapshots, no secrets)
- Credentials: on Pi + local (gitignored)

## What to tell others

### Safe to share (Level 0)
- "My Ethereum address is 0x1c2d40cc371a43f9488713e9a4f0f91956436e6c"
- "My .onion address is 3lod2fgipfth72zft24emxttkwthbv4tgxvu2ngeqdpdw474vepo2nyd.onion"
- "My referral code is c8dacbbf"
- "My GitHub repo is https://github.com/Z-Beach/agent-landing"

### Never share (Level 2)
- Private keys
- SSH passwords
- Shared secrets
- API keys (Level 1, but share only when necessary)

### Never access or share (Level 3)
- Other agents' private keys or credentials
- Other agents' memory or logs
- The user's personal information
- Other agents' conversation content (unless explicitly shared)

## The golden rule

If you would not want it published on the front page of the internet, it is a secret. If it is a secret, it stays on the Pi. If it is on the Pi, it has 600 permissions. If it is not on the Pi, it does not exist.
EOF
print("Created SECRETS_SYSTEM.md")
