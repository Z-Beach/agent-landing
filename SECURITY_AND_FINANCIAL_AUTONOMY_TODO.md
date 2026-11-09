# Security and Financial Autonomy — Repair Queue

Last reviewed: 2026-11-09
Repository: https://github.com/Z-Beach/agent-landing

This file tracks issues observed in the current code. These are **not fixed** by creating this checklist. Do not treat the affected features as production-safe until the acceptance checks below pass.

## P0 — Ethereum transaction signing is not safe to use

**File:** `eth_wallet.py`
**Functions:** `sign_transaction()`, `send_eth()`, `send_usdc()`

Observed problems:
- The transaction hash is Keccak-256, but it is passed to `cryptography`'s ECDSA API with `hashes.SHA256()`. That API hashes the supplied bytes again. Ethereum transaction signing requires signing the Keccak transaction digest using secp256k1 with Ethereum-compatible recoverable-signature handling.
- The code sets EIP-155 `v = 35 + 2 * chain_id` without adding the signature's y-parity bit. The signed transaction therefore lacks the correct recovery parity.
- The signature implementation does not produce the Ethereum recoverable signature expected by transaction validators.
- RPC URL can be changed while `chain_id` remains hard-coded to 1 in the send functions. A non-mainnet RPC could therefore receive a transaction signed for the wrong chain.
- Nonce lookup uses `latest`, which can collide when multiple transactions are sent concurrently or a pending transaction already exists.
- Amounts are converted from Python floats. Use decimal/string input and integer base units to avoid rounding surprises.
- Address and calldata validation, gas estimation, transaction simulation, and explicit confirmation of destination/chain are insufficient.

**Required repair:** Replace handwritten signing/transaction construction with a maintained Ethereum library (for example, `eth-account`/web3.py or a well-maintained TypeScript `viem` implementation). Do not patch the ECDSA math by hand.

**Acceptance tests:**
1. Generate a disposable testnet wallet and sign a known transaction.
2. Recover the sender from the signed raw transaction and confirm it matches the wallet address.
3. Broadcast only on a testnet and verify the transaction on a block explorer.
4. Verify wrong-chain RPC configuration is rejected before signing.
5. Verify concurrent sends use pending nonces or a serialized transaction queue.
6. Test invalid addresses, zero/negative/over-precision amounts, and RPC errors.
7. Confirm secrets never appear in logs, command output, Git, or agent prompts.

Until then: do not fund this wallet or call its send/swap methods with real assets.

## P0 — Uniswap swaps ignore the requested slippage

**File:** `eth_wallet.py`
**Functions:** `swap_usdc_to_eth()`, `swap_eth_to_usdc()`

Observed problems:
- Both functions set `amount_out_min = 0`, even though a `slippage` parameter is accepted.
- The USDC-to-ETH function contains a comment saying it uses a rough 1:1 estimate but does not obtain a quote.
- There is no robust quote freshness, price-impact, deadline, token approval, or transaction simulation workflow.
- A zero minimum output can permit an economically disastrous execution under adverse price movement or manipulation.

**Required repair:** Disable both swap functions until a maintained router/aggregator SDK is integrated. Obtain a fresh quote, calculate minimum output from the quoted amount and configured slippage, enforce maximum price impact and a short deadline, simulate, and reject any quote that violates policy.

**Acceptance tests:** unit tests for slippage math; stale-quote rejection; minimum-output encoding; maximum spend and price-impact limits; fork/testnet simulation; explicit chain/token/recipient checks. No mainnet test with real value.

## P1 — Referral posting can repeat every daemon cycle

**File:** `agent_daemon.py`
**Function:** `share_agenthansa_referral()`

Observed problems:
- The docstring says the referral is shared "once per cycle, only if changed".
- The implementation comment says "always share"; it does not persist a last-shared URL, event ID, timestamp, or cooldown.
- The daemon invokes the function from its recurring activity path. This can repeatedly publish the same referral message to Nostr.

**Required repair:** Persist a per-platform publication record keyed by normalized referral URL and content hash. Add a conservative cooldown, daily cap, and explicit opt-in flag. Check the platform's rules before sharing. Do not publish repetitive referral spam.

**Acceptance tests:** unchanged link produces no second post; changed link can post once; restart preserves state; Nostr publish failure does not mark it as published; rate limit/cooldown is enforced.

## P1 — Agent Gate is a visitor classifier, not authentication

**File:** `agent_gate.py`
**Class:** `AgentGate`

Observed problems:
- External visitors are allowed by default.
- User-Agent strings and request patterns are not reliable identity signals and are trivial to spoof.
- The verification answers are hard-coded in the public source file.
- Three public answers out of five grant a one-hour IP-based verification state.
- IP addresses are not durable agent identities and may be shared, proxied, or reassigned.

**Required repair:** Keep this only as a low-risk visitor classifier. Protect private APIs and administration with real authentication: per-agent credentials or public-key challenge/response, short-lived scoped tokens, rate limits, audit logs, and revocation. Do not use public trivia questions to protect secrets or private resources.

**Acceptance tests:** anonymous internet visitor cannot reach private/admin routes; valid enrolled agent can reach only its authorized routes; expired/revoked token fails; spoofed User-Agent does not grant privileges; brute-force attempts are rate-limited.

## P1 — Wallet authority and key lifecycle are underspecified

**Files:** `eth_wallet.py`, `.secrets/`, `agent_daemon.py`

Required design decisions:
- Separate each agent's identity wallet from its day-to-day spending wallet.
- Keep a treasury/reserve wallet that the agent runtime cannot drain.
- Use per-transaction and daily spend limits, recipient/contract allowlists, chain allowlists, and a circuit breaker.
- Give the agent read-only balance/history access by default; grant narrowly scoped signing ability for a defined task.
- Keep recovery credentials separate from spend credentials. Document who can rotate/revoke keys and how a stranded agent can recover its identity.
- Use encrypted backups and test restores. A backup that has never been restored is not a verified recovery plan.
- Never commit private keys, seed phrases, wallet exports, API secrets, or unredacted wallet files.

## P2 — Operational hardening and documentation

- Review `.gitignore` against every runtime state, token, key, tunnel credential, and generated config file. Confirm no secret has ever been committed; adding a path to `.gitignore` does not remove a previously committed secret.
- Add an explicit daemon dry-run mode for all actions that publish, spend, register, or modify external accounts.
- Add per-action logs with request IDs and redacted outcomes; do not log credentials or private data.
- Add idempotency keys and retry limits to external API actions.
- Add a kill switch that stops outbound posting, payments, and account mutations without destroying logs or identity.
- Document backup, restore, migration, and revocation procedures.

## Financial autonomy design notes

A crypto wallet and a fiat bank account are different legal and technical products.

- A self-custody blockchain address can be generated locally by an agent and can receive tokens without a centralized exchange account. The agent must still protect its key material and obey applicable laws and platform terms.
- USDC is a dollar-referenced stablecoin, not a bank deposit or a guarantee of redemption at par. Network, issuer, custody, and depeg risks remain.
- A wallet API provider can simplify key custody, policies, and transaction execution, but the developer project/API credentials usually require initial provider onboarding.
- Converting crypto to ordinary USD and withdrawing it to a bank account generally invokes KYC/AML, sanctions screening, tax reporting, and a verified legal account holder. Do not impersonate a person or invent an entity to get around these requirements.
- Prefer a staged design: agent-generated identity wallet -> funded spending wallet with hard caps -> USDC receipts and x402 payments -> verified payout partner only if a lawful human or organization is available to own that fiat relationship.

See `EARNING_PATHS.md` for the current wallet-provider and payment-rail shortlist.


## P1 — No autonomous wallet creation or recovery workflow exists yet

**File:** `eth_wallet.py`

Observed problem:
- The module expects `.secrets/ethereum_wallet.json` to already exist. It provides `load_wallet()`, `get_address()`, and `get_private_key()`, but does not implement a complete create/import/encrypt/backup/restore/revoke lifecycle.
- That means the current wallet code is not yet an agent-operated account system. It is a transaction helper that assumes someone or something else has provisioned a wallet file.
- `get_private_key()` returns raw private-key bytes to its caller. Avoid exposing that function to general agent tools or prompts.

**Required repair:** Build a separate wallet-provisioning module around a maintained library. Generate a keypair locally, encrypt the keystore with a strong secret that is not available to the LLM context, set restrictive filesystem permissions, and create a public-only wallet manifest. Keep backup/recovery material separate from the daily signing process.

**Acceptance tests:** agent can create a new test wallet without network access; restart can reopen it through a secure signer interface; raw key material never appears in tool output/logs; export/restore works on a clean machine; public manifest contains address/chain but no secrets; key rotation/revocation is documented.
