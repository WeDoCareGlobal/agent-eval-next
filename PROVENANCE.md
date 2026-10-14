# Provenance and validation

Derived from https://github.com/WeDoCareGlobal-CC/agent-eval at commit c56a6e524f47f58b8c741a840d6d7d4279230330. Module blob: c9c8d169881586e4fa5814ce2d177cef02124f19. Apache-2.0 LICENSE preserved. No private source or credentials copied.

Fixes: hashlib.b256 crash; success accounting for allowed calls that failed; JSON trace enum serialization. Validation: five independent regression tests passed with Python 3.12.

In-memory storage remains. Durable persistence, authentication, integration contracts, packaging, and deployment remain PROPOSED. This is a development component, not a production release.
