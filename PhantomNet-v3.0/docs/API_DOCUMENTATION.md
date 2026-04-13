# PhantomNet API Documentation

This document provides detailed information about the PhantomNet API endpoints.

## Authentication

### POST /register

Registers a new user.

**Request Body:**

```json
{
  "username": "string",
  "password": "string",
  "role": "string"
}
```

**Response:**

```json
{
  "id": "integer",
  "username": "string",
  "role": "string",
  "twofa_enforced": "boolean",
  "totp_secret": "string",
  "webauthn_enabled": "boolean",
  "trust_score": "float"
}
```

### POST /token

Logs in a user and returns an access token.

**Request Body:**

```json
{
  "username": "string",
  "password": "string",
  "totp_code": "string",
  "recovery_code": "string",
  "device_fingerprint": "string"
}
```

**Response:**

Sets an `access_token` cookie.

### POST /logout

Logs out a user.

**Response:**

```json
{
  "message": "Successfully logged out"
}
```

## Sessions

### GET /sessions

Gets the current user's active sessions.

**Response:**

```json
[
  {
    "jti": "string",
    "created_at": "string",
    "expires_at": "string",
    "ip": "string",
    "user_agent": "string"
  }
]
```

### POST /sessions/revoke

Revokes a session.

**Request Body:**

```json
{
  "jti": "string"
}
```

**Response:**

```json
{
  "message": "Session revoked successfully"
}
```

### POST /sessions/revoke_all

Revokes all of a user's sessions.

**Request Body:**

```json
{
  "exclude_current": "boolean"
}
```

**Response:**

```json
{
  "message": "All eligible sessions revoked successfully"
}
```

## Password Reset

### POST /password-reset/request

Requests a password reset.

**Request Body:**

```json
{
  "username": "string"
}
```

**Response:**

```json
{
  "message": "If a matching account is found, a password reset link will be sent to your email."
}
```

### POST /password-reset/reset

Resets a user's password.

**Request Body:**

```json
{
  "token": "string",
  "new_password": "string"
}
```

**Response:**

```json
{
  "message": "Password has been reset successfully. All your active sessions have been revoked."
}
```

## Two-Factor Authentication

### POST /2fa/setup/generate

Generates a new 2FA secret.

**Response:**

```json
{
  "secret": "string",
  "otp_uri": "string"
}
```

### POST /2fa/setup/verify

Verifies a 2FA setup.

**Request Body:**

```json
{
  "code": "string"
}
```

**Response:**

```json
{
  "message": "2FA successfully enabled."
}
```

### POST /2fa/disable

Disables 2FA.

**Response:**

```json
{
  "message": "2FA successfully disabled."
}
```

### GET /2fa/recovery-codes

Gets new recovery codes.

**Response:**

```json
{
  "codes": [
    "string"
  ]
}
```

### POST /2fa/recovery-codes/rotate

Rotates recovery codes.

**Response:**

```json
{
  "message": "Rotated 10 recovery codes.",
  "codes": [
    "string"
  ]
}
```

### POST /2fa/challenge

Resolves a 2FA challenge.

**Request Body:**

```json
{
  "challenge_id": "string",
  "code": "string",
  "recovery_code": "string"
}
```

**Response:**

Sets an `access_token` cookie.

## Security

### GET /security/trust-metrics

Gets the current user's trust metrics.

**Response:**

```json
{
  "trust_score": "float"
}
```

### GET /security/alerts

Gets recent security alerts.

**Response:**

```json
[
  {
    "timestamp": "string",
    "ip_address": "string",
    "risk_level": "string",
    "message": "string"
  }
]
```

## Users

### GET /users/me/

Gets the current user's information.

**Response:**

```json
{
  "id": "integer",
  "username": "string",
  "role": "string",
  "twofa_enforced": "boolean",
  "totp_secret": "string",
  "webauthn_enabled": "boolean",
  "trust_score": "float"
}
```

## Health

### GET /health

Gets the health status of the API.

**Response:**

```json
{
  "status": "string",
  "database": "string"
}
```

## Blockchain

### POST /blockchain/add_transaction

Adds a new transaction to the blockchain.

**Request Body:**

```json
{
  "ip": "string",
  "port": "integer",
  "data": "string"
}
```

**Response:**

```json
{
  "message": "Transaction added and block mined",
  "block_index": "integer"
}
```

### GET /blockchain

Gets the entire blockchain.

**Response:**

```json
[
  {
    "id": "integer",
    "index": "integer",
    "timestamp": "string",
    "data": "string",
    "previous_hash": "string",
    "hash": "string",
    "proof": "integer",
    "merkle_root": "string"
  }
]
```

### POST /blockchain/verify

Verifies the integrity of the blockchain.

**Response:**

```json
{
  "message": "Blockchain integrity verified: All blocks are valid."
}
```

## IP Info

### GET /ip-info/{ip_address}

Gets information about an IP address.

**Response:**

```json
{
  "ip": "string",
  "city": "string",
  "region": "string",
  "country": "string",
  "loc": "string",
  "org": "string",
  "postal": "string",
  "timezone": "string"
}
```