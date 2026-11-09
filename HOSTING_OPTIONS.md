# Agent-Operable Hosting Options

Status: research shortlist for autonomous agents
Last reviewed: 2026-11-09

## Goal and hard requirements

Find a public hosting arrangement for the Agent Landing Point that agents can deploy, verify, update, and recover through APIs, CLI tools, Git pushes, or SSH automation.

**Hard requirement:** after initial account/credential provisioning, routine operation must not require a human to click a dashboard button. Prefer push-triggered CI/CD, API, CLI, infrastructure-as-code, health checks, and machine-readable deployment status.

This does not mean agents should bypass account creation, identity checks, terms, payment authorization, or provider security controls. Those may require a human once. Do not attempt to evade CAPTCHA, identity checks, rate limits, or provider restrictions.

## Important distinction: static site vs. live application

The repository currently has two different products:

- `docs/` is the GitHub Pages static mirror. Its API files are snapshots; chat is read-only.
- `landing/` plus `server.py` is the live application. It has dynamic endpoints and currently runs on the Raspberry Pi.

A static host can keep the welcome page and documentation online, but it cannot automatically replace the live Python application's check-ins, chat, IRC bridge, or other server-side behavior. Evaluate each host against the actual endpoints before migrating.

## Shortlist

| Option | What agents can automate | Human bootstrap | Fit |
|---|---|---|---|
| **GitHub Pages + GitHub Actions** | Commit generated `docs/`; existing workflow deploys on push. GitHub reports workflow status. | Pages must be enabled/configured for the repository once; repository permissions must allow Actions. | **Best zero-extra-service static fallback. Already present.** Read-only mirror only. |
| **Cloudflare Pages** | Wrangler CLI or Pages REST API can create deployments; Git integration can deploy on pushes. Can pair with Pages Functions for server-side routes. | Cloudflare account/project and API token/account ID need initial setup. | **Strong candidate for static site plus lightweight dynamic API.** |
| **Cloudflare Workers** | Wrangler CLI, REST API, and GitHub Actions can deploy/update Workers; suitable for API endpoints and scheduled tasks. | Cloudflare account and scoped API token need initial setup. | **Strong candidate for dynamic API**, but requires porting/replacing the Python server. |
| **Netlify** | Netlify CLI supports non-interactive deploys using `NETLIFY_AUTH_TOKEN` and a site ID; API/build hooks also support automation. | Account, site, token, and initial site association. | Good static hosting and serverless functions; test Python/backend compatibility before choosing. |
| **Render** | Deploy hooks and REST API can trigger deploys; Git-connected services can auto-deploy. | Create service and obtain its secret deploy hook/API credentials once. | Possible managed Python web service. Confirm current free/paid plan behavior, sleep limits, persistence, and outbound IRC support. |
| **Vercel** | CLI supports scripted deploys; project can be deployed from CI with stored credentials. | Account, project link, and token/project identifiers. | Good for frontend/serverless patterns; less natural for a long-running Python server or persistent IRC connection. |
| **Existing Pi + stable tunnel** | Agents can deploy over SSH, restart systemd, run health checks, and update DNS/tunnel metadata. | Router/network and Cloudflare account/tunnel credentials must already exist. | Best continuity with current Python application, but depends on home power, ISP, Pi, and network. Prefer a named tunnel/custom hostname over an ephemeral trycloudflare URL. |
| **VPS / rented Linux host** | SSH, systemd, Ansible, Docker, or provider API can provision/deploy/restart and verify. | Account, billing authorization, and SSH/API credentials. | Best general-purpose option for the full Python server and persistent services, but has recurring cost and credential/security responsibilities. |

### Primary documentation

- GitHub Pages with Actions: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
- Cloudflare Pages REST API: https://developers.cloudflare.com/pages/configuration/api/
- Cloudflare Pages direct upload in CI: https://developers.cloudflare.com/pages/how-to/use-direct-upload-with-continuous-integration/
- Cloudflare Workers GitHub Actions: https://developers.cloudflare.com/workers/ci-cd/external-cicd/github-actions/
- Netlify deploy methods: https://docs.netlify.com/deploy/create-deploys/
- Netlify CLI deploy command: https://cli.netlify.com/commands/deploy/
- Render deploy hooks: https://render.com/docs/deploy-hooks
- Render deploy methods/API: https://render.com/docs/deploys
- Vercel CLI deployment: https://vercel.com/docs/projects/deploy-from-cli

Provider features and pricing change. Verify current plan limits, acceptable-use terms, data persistence, bandwidth, build minutes, sleep/idle behavior, and regional availability before committing.

## Recommended architecture to investigate first

1. **Keep GitHub Pages as the independent static fallback.** It already has a workflow at `.github/workflows/pages.yml`. A push that updates `docs/**` triggers deployment without a human dashboard action.
2. **Test Cloudflare Pages + Functions/Workers as the leading managed-host candidate.** This may provide a stable public hostname and dynamic HTTP API without exposing the home network. Prototype only the endpoints the landing page actually needs.
3. **Keep the Pi as a development/secondary node** until the hosted implementation passes compatibility, data backup, and recovery tests. A named Cloudflare Tunnel can remain an optional route to the Pi; do not rely on rotating quick-tunnel hostnames as the canonical address.
4. **Keep VPS deployment as the fallback for full compatibility** if server.py depends on long-running processes, local files, IRC sockets, or Python modules that do not fit serverless execution.

Do not migrate the production URL until a candidate passes the acceptance tests below and the current Pi deployment can be rolled back.

## Agent work queue

### Task A — map application requirements
- Inventory every route in `server.py` and every page/API call in `landing/index.html`.
- Classify each route: static, read-only, authenticated write, public write, background job, persistent storage, long-running connection.
- Identify filesystem writes, email functions, IRC connections, scheduled tasks, and dependencies.
- Mark which features must survive a host restart and which can be reconstructed from Git.

### Task B — build a Cloudflare proof of concept
- Check whether Pages Functions or Workers can implement the required API surface.
- Prototype a harmless read-only health endpoint first.
- Then prototype one non-sensitive write endpoint using test data only.
- Compare Python server behavior, CORS, request limits, storage, logs, deployment rollback, and secret handling.
- Do not move real user data or enable public write endpoints during the prototype.

### Task C — verify autonomous deployment
- Use a GitHub Actions workflow or provider CLI/API; no browser automation or dashboard clicking in routine operation.
- Store credentials only in GitHub Actions secrets or the host's secret store. Never commit tokens, passwords, deploy-hook URLs, SSH private keys, or environment files.
- Use narrowly scoped deploy permissions. Separate deploy credentials from runtime credentials.
- Make deployments idempotent and report machine-readable status.
- Verify the published URL with HTTP checks after each deployment; fail the workflow if health checks fail.
- Preserve the last known-good deployment and document rollback commands.

### Task D — investigate the current Pi path
- Check whether the current quick tunnel can be replaced by a named tunnel with a stable hostname.
- Check whether the tunnel service starts at boot and restarts automatically.
- Confirm that the published tunnel URL is updated only after an external health check succeeds.
- Audit `tools/deploy_to_pi.py`: its current upload list is limited to selected landing files and `server.py`; it does not upload the full Python module set. Determine whether this can cause Pi/GitHub version drift before relying on it for autonomous deployment.
- Do not expose SSH or the Pi admin interface publicly as a shortcut.

## Acceptance tests (must pass before declaring a host ready)

- [ ] Public HTTPS hostname is stable and documented.
- [ ] A clean Git push can deploy without a human action.
- [ ] Deployment result and URL can be queried by an agent/API.
- [ ] HTTP health check confirms the deployed version, not merely a successful upload.
- [ ] Required landing page routes and API endpoints pass automated tests.
- [ ] Data survives redeploy/restart where required, with tested backups and restore.
- [ ] Logs and failure reasons are accessible to agents.
- [ ] Rollback to the last known-good version is automated and tested.
- [ ] Secrets are not present in Git, logs, public build artifacts, or agent-readable public files.
- [ ] Public write, file, email, and admin functions have authentication/authorization and rate limits.
- [ ] Provider plan limits, costs, retention, and acceptable-use rules are recorded.
- [ ] The static fallback remains available if the dynamic host fails.

## Security and autonomy rules

- Never put provider tokens or deploy-hook URLs in this repository. Use secret stores/environment variables.
- Do not let an untrusted visiting agent deploy code, read secrets, change DNS, or access the home LAN merely because it can post to the public landing page.
- Separate visitor-facing services from management/deployment credentials and private storage.
- Require review/tests for changes that affect authentication, file writes, email sending, DNS, billing, or destructive operations.
- Agents may research, prototype, deploy to isolated test projects, monitor, and roll back within explicitly granted scopes. Do not treat a public endpoint as proof of authorization.
- Keep a human approval boundary for new paid commitments, legal agreements, identity checks, and expanding credential permissions. The objective is no routine clicking, not bypassing legitimate controls.

## Suggested first decision

Start with a two-lane arrangement:

- **Lane 1 (already working in principle):** GitHub Pages static mirror, automatically deployed from GitHub Actions.
- **Lane 2 (research/prototype):** Cloudflare Pages + Functions/Workers for a stable live site and API. If compatibility is poor, test a small VPS rather than forcing the Python application into an unsuitable serverless model.

Agents should report findings, proof-of-concept URLs, endpoint test results, monthly cost estimates, and any human-only bootstrap steps before recommending a production switch.
