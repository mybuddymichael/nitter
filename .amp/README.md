# RSS deployment on an Amp Box

The deployment runs three services: the RSS proxy, Nitter, and Redis.
Only the RSS proxy listens on the public deployment port.
Nitter listens on `127.0.0.1:18080`. Redis listens on `127.0.0.1:16379`.
Redis stores a disposable cache without disk persistence.

## Private data survives deployments

These files belong in `AMP_DEPLOYMENT_DATA_DIRECTORY`, not in Git:

- `nitter.conf`: the imported Nitter configuration, including its HMAC key.
- `sessions.jsonl`: the X session cookies.
- `allowed-users.txt`: one allowed X username per line.

The backend writes `runtime.conf` from the imported configuration at startup.
It replaces the hostname with `AMP_DEPLOYMENT_URL` and selects the internal ports above.
It preserves the cache durations, RSS restrictions, preferences, and HMAC key.
The source configuration remains unchanged.

## Build and deploy

The build requires Linux x64, Nim 2.2, Nimble, GCC, make, curl, `libpcre3-dev`, and `libsass-dev`.
The release includes Nitter, its public assets, PCRE, and Redis 7.2.17.
The build verifies the Redis archive against its published SHA-256 digest.
The Box supplies Python, glibc, OpenSSL, and CA certificates.

1. Commit the code on the deployment branch.
2. Push that branch to the fork.
3. Run `amp boxes deploy --on <owner>/<box> --name <deployment> --branch <branch> --public`.
4. Copy each private file with `amp boxes cp <file> <owner>/<box>:<file> --deployment <deployment>`.
5. Set the private files to mode `600` with an app command.
6. If the first deployment failed before the files arrived, run the deployment command again.

The RSS reader cannot use an Amp sign-in page. This deployment therefore uses a public URL with an account allowlist.
The proxy returns `404` for other accounts and frontend pages.
`/healthz` checks only the proxy. A real feed request must return HTTP 200, valid RSS, and at least one item.

## Move a portal hostname only after verification

1. Verify the new deployment without the portal hostname.
2. Get approval to move the hostname.
3. Run `amp boxes deploy --domain <hostname> --take-over`.
4. Verify feeds through the hostname without an Amp browser session.
5. Update the health-check schedule to use the Box.

Amp cannot move a deployment hostname back to a thread portal.
Keep the old services and the current health-check schedule unchanged until the move receives approval.
