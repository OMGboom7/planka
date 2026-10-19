# Internal CA for outgoing notifications

Place the CA certificate used by your self-signed/internal HTTPS endpoints here as
`internal-ca.crt` (PEM). It is mounted read-only into the Planka container at
`/app/certs` and passed to the Python notification sender through
`REQUESTS_CA_BUNDLE`.

- The certificate is read on every notification, so replacing the file takes
  effect immediately; no container restart is required.
- If the endpoint uses a chain, append the whole chain to the same file.
- If the file is missing, Planka logs a warning and falls back to the bundled
  certifi store (self-signed endpoints will fail).
- Private keys never belong here.
