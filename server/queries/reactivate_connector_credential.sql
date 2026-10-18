UPDATE connector_credentials
SET token_digest = ?, revoked = 0, revision = revision + 1
WHERE identifier = 1 AND revoked = 1;
