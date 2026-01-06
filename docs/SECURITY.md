# Security Policy

## Supported Versions

Security updates are provided for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue in SecureVision, please report it responsibly.

### DO NOT Create Public Issues

**Please do not open public GitHub issues for security vulnerabilities**, as this could put users at risk.

### How to Report

Send security reports via email to:

**Email:** michaelflppv@gmail.com

**Subject:** `[SECURITY] SecureVision Vulnerability Report`

### What to Include

Please provide as much information as possible:

1. **Description** of the vulnerability
2. **Steps to reproduce** the issue
3. **Potential impact** and severity assessment
4. **Affected versions** (if known)
5. **Proof of concept** code (if applicable)
6. **Suggested fix** (if you have one)

### Response Timeline

We aim to respond to security reports according to this timeline:

- **Initial Response:** Within 72 hours
- **Vulnerability Assessment:** Within 7 days
- **Fix Development:** Depends on severity
  - Critical: Within 7 days
  - High: Within 14 days
  - Medium: Within 30 days
  - Low: Next release cycle
- **Public Disclosure:** After fix is released and users have time to update (minimum 7 days)

### Responsible Disclosure

We follow coordinated vulnerability disclosure:

1. You report the vulnerability privately
2. We confirm and assess the issue
3. We develop and test a fix
4. We release the fix and notify users
5. After users have time to update, we publicly disclose the vulnerability with credit to the reporter (if desired)

## Security Best Practices

### For Users

When deploying SecureVision, follow these security best practices:

#### Network Security

1. **Never expose the API directly to the internet**
   - Use localhost binding: `SECUREVISION__API__HOST=127.0.0.1`
   - Or use VPN for remote access

2. **Enable authentication**
   ```bash
   # Generate strong token
   export SECUREVISION__API__AUTH_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
   ```

3. **Use HTTPS for remote access**
   - Deploy behind reverse proxy (Nginx)
   - Use Let's Encrypt for SSL certificates
   - See [DEPLOYMENT.md](DEPLOYMENT.md) for setup

4. **Firewall configuration**
   ```bash
   # Only allow local access to API
   sudo ufw deny 8000/tcp
   sudo ufw allow from 127.0.0.1 to any port 8000
   ```

#### Camera Security

1. **Secure camera credentials**
   - Never commit passwords to git
   - Use environment variables
   - Use strong, unique passwords

2. **Isolate camera network**
   - Place cameras on separate VLAN
   - Restrict internet access for cameras
   - Use firmware with latest security patches

3. **RTSP URL security**
   ```bash
   # Bad - credentials in code
   url = "rtsp://admin:password123@camera.local:554/stream"

   # Good - credentials in environment
   url = os.getenv("SECUREVISION__VIDEO__SOURCE__URL")
   ```

#### File and Database Security

1. **Protect sensitive files**
   ```bash
   # Restrict permissions
   chmod 600 .env
   chmod 700 data/
   chown securevision:securevision data/
   ```

2. **Backup encryption**
   ```bash
   # Encrypt backups
   gpg --encrypt --recipient you@example.com data/events.db
   ```

3. **Regular updates**
   ```bash
   # Keep dependencies updated
   poetry update
   pre-commit autoupdate
   ```

#### Application Security

1. **Run as non-root user**
   ```bash
   # Create dedicated user
   sudo useradd -r -s /bin/false securevision
   sudo -u securevision poetry run securevision-api
   ```

2. **Use systemd hardening**
   See [DEPLOYMENT.md](DEPLOYMENT.md) for hardened systemd service configuration.

3. **Monitor logs**
   ```bash
   # Watch for suspicious activity
   sudo journalctl -u securevision-api -f
   ```

### For Developers

When contributing to SecureVision:

#### Code Security

1. **Input Validation**
   - Always validate and sanitize user inputs
   - Use Pydantic models for type safety
   - Avoid SQL injection (use parameterized queries)

2. **Dependency Management**
   - Keep dependencies updated
   - Review security advisories
   - Use `poetry show --outdated` regularly

3. **Secrets Management**
   - Never commit secrets to git
   - Use environment variables
   - Add sensitive files to `.gitignore`

4. **Error Handling**
   - Don't expose stack traces to API responses
   - Log errors securely
   - Sanitize error messages

#### Code Review

All security-relevant changes should:
- Be reviewed by at least one maintainer
- Include tests for security features
- Update documentation
- Follow secure coding guidelines

#### Testing

1. **Security Tests**
   - Test authentication/authorization
   - Test input validation
   - Test for common vulnerabilities (XSS, CSRF, etc.)

2. **Dependency Scanning**
   ```bash
   # Check for known vulnerabilities
   poetry run pip-audit
   ```

## Known Security Considerations

### Camera Credentials in URLs

RTSP URLs often include credentials in plain text:
```
rtsp://user:pass@camera.local:554/stream
```

**Mitigation:**
- Store URLs in environment variables (not in code)
- Restrict access to `.env` files
- Use camera-level authentication where possible

### SQLite Database

SQLite databases are stored as files without built-in encryption.

**Mitigation:**
- Restrict file permissions (`chmod 600`)
- Use filesystem-level encryption if needed
- Regularly backup and clean up old events

### WebSocket Authentication

Current WebSocket implementation doesn't require authentication.

**Mitigation:**
- Only bind to localhost by default
- Use VPN or reverse proxy for remote access
- Future: Add token-based WebSocket authentication

### No Built-in HTTPS

SecureVision API doesn't include built-in HTTPS support.

**Mitigation:**
- Use reverse proxy (Nginx) for HTTPS
- Never expose API directly to internet
- See [DEPLOYMENT.md](DEPLOYMENT.md) for Nginx configuration

## Security Features

### Current Features

- **Local Processing:** All data processing happens locally (no cloud)
- **Optional Authentication:** Bearer token authentication for API
- **Input Validation:** Pydantic-based configuration validation
- **SQL Injection Protection:** Parameterized queries via SQLAlchemy
- **CORS Configuration:** Configurable CORS policies

### Planned Features

- WebSocket authentication (token-based)
- Rate limiting for API endpoints
- Audit logging for sensitive operations
- Enhanced input sanitization
- Two-factor authentication option

## Security Updates

Security updates will be announced via:

1. **GitHub Security Advisories**: Primary notification method
2. **Release Notes**: Documented in [CHANGELOG.md](CHANGELOG.md)
3. **GitHub Releases**: Tagged releases with security notes

Subscribe to repository notifications to receive security updates.

## Vulnerability Disclosure Examples

### Example Report

```
Subject: [SECURITY] SecureVision Vulnerability Report

Description:
API endpoint /events allows unauthorized access when auth_token is set
to empty string, bypassing authentication checks.

Steps to Reproduce:
1. Set SECUREVISION__API__AUTH_TOKEN=""
2. Start API server
3. Access /events endpoint without Authorization header
4. Endpoint returns data without authentication

Impact:
Confidential event data exposed without authentication. Severity: HIGH

Affected Versions:
0.1.0 and earlier

Suggested Fix:
Modify verify_token() to treat empty string as None:
if _auth_token is None or _auth_token == "":
    return
```

### Good Practices

**Do:**
- Report privately via email
- Provide detailed reproduction steps
- Suggest fixes if possible
- Allow time for fix before public disclosure

**Don't:**
- Post vulnerabilities publicly
- Exploit vulnerabilities on production systems
- Demand ransom or compensation
- Disclose before fix is available

## Credits

We appreciate security researchers who responsibly disclose vulnerabilities. With your permission, we will credit you in:
- Security advisories
- Release notes
- This document

Thank you for helping keep SecureVision secure!

## Additional Resources

- [OWASP Top Ten](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
