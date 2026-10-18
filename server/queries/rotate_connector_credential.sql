UPDATE connector_credentials
SET token_digest = ?, revision = revision + 1
WHERE identifier = 1 AND revoked = 0;
