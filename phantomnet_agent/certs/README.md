# Runtime-generated certificate material

Do not commit certificates, public keys, private keys, PKCS#12 bundles, or environment files in this directory. The historical generated artifacts were removed because any key committed to source control must be treated as exposed.

For governed endpoint-command signing, provision a fresh trusted public certificate or public key outside Git and mount it at the path configured by `PHANTOMNET_AGENT_COMMAND_TRUSTED_CERT_PATH`. The matching private signing key belongs only in the governed command producer’s runtime secret injection as `PHANTOMNET_AGENT_COMMAND_SIGNING_PRIVATE_KEY`.

See [`docs/ENDPOINT_COMMAND_SIGNING_PROVISIONING.md`](../../docs/ENDPOINT_COMMAND_SIGNING_PROVISIONING.md) for the fail-closed protocol and required controlled-device validation evidence.
