# Git Guardians / Security Checklist

- [ ] All secrets and credentials are stored in environment variables or .env files (never in code)
- [ ] No hardcoded API keys, tokens, or passwords
- [ ] Sensitive files (e.g., .env, *.pem) are in .gitignore
- [ ] Dependencies are regularly updated and checked for vulnerabilities
- [ ] Use pre-commit hooks for security scanning (e.g., detect secrets)
- [ ] Enable branch protection and require PR reviews
- [ ] Use least privilege for API keys and tokens
- [ ] Review third-party packages for security
- [ ] Enable 2FA for repository maintainers
- [ ] Monitor CI logs for accidental secret leaks

## Tools
- [GitGuardian](https://www.gitguardian.com/) for secret scanning
- [Bandit](https://bandit.readthedocs.io/) for Python security linting
- [Safety](https://pyup.io/safety/) for dependency vulnerability checks
