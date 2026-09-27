# CONTRACTS

Cross-domain interfaces only. No business logic.

## Contracts
- core -> all domains: identity/config/language/authority
- assistant -> creative: Camera/Studio/Gallery requests
- assistant -> daily-story: story menu/status
- daily-story -> web-distribution: approved publication payload
- creative -> web-distribution: approved gallery/public payload
- guardian: isolated group-security boundary
- external daily-story repository: archive contract

Direct imports into another domain's internals are forbidden in the target architecture.
