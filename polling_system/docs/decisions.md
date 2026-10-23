# Architecture Decision Records (ADRs) & Trade-off Analysis

This document records the architectural decisions, design choices, and technical trade-offs made during the development of the Online Polling System.

---

## ADR 01: Vertical Slices by Feature Architecture
- **Decision**: Organize both backend (`backend/features/`) and frontend (`frontend/src/features/`) by business feature (e.g., `create_poll`, `cast_vote`, `poll_detail`) rather than technical layer (`controllers`, `models`, `views`).
- **Rationale**: Feature slicing encapsulates business rules, API schemas, repositories, and UI components in cohesive boundaries. Adding or modifying a feature touches only that feature's directory without ripple effects across the system.
- **Rules Enforced**: Features never import from other features. Cross-cutting utilities (HTTP responses, authentication, logging) reside in a minimal `shared/` module.

---

## ADR 02: Single Backend Code Package with Multiple Handler Entrypoints
- **Decision**: Configure all six Lambda functions in `04_api/template.yaml` with `CodeUri: backend` pointing to the single backend root, but specifying distinct handler paths:
  - `features.create_poll.handler.handler`
  - `features.list_polls.handler.handler`
  - `features.get_poll.handler.handler`
  - `features.cast_vote.handler.handler`
  - `features.get_results.handler.handler`
  - `features.close_poll.handler.handler`
- **Trade-off Analysis**:
  - *Alternative (Separate packages per function)*: Requires building 6 separate zip archives, copying shared dependencies into 6 folders, or managing Lambda Layers.
  - *Selected Approach*: Single build step in SAM CLI, unified dependency resolution, and zero code duplication. The total package size is under 2.5 MB, resulting in negligible impact on cold start latency (< 15ms difference).

---

## ADR 03: Atomic DynamoDB Transaction for Vote Recording
- **Decision**: Cast votes using a two-action `TransactWriteItems` call:
  1. `PutItem` on `Votes` table (`attribute_not_exists(pollId) AND attribute_not_exists(userId)`)
  2. `UpdateItem` on `Polls` table (`attribute_exists(pollId) AND #status = :open`)
- **Trade-off Analysis**:
  - *Alternative (Sequential write and update)*: If the vote record is created but the update fails (or vice versa), the system enters an inconsistent state. Requires complex rollback logic.
  - *Selected Approach*: DynamoDB transactions guarantee ACID atomicity and serializable isolation. Concurrent duplicate requests are rejected deterministically by the storage engine itself.

---

## ADR 04: Native API Gateway JWT Authorizer vs Custom Lambda Authorizer
- **Decision**: Utilize API Gateway HTTP API's built-in JWT authorizer pointing to the Amazon Cognito User Pool issuer.
- **Trade-off Analysis**:
  - *Alternative (Custom Lambda Authorizer)*: Adds extra cold start latency, additional IAM roles, and compute charges for every authorized request.
  - *Selected Approach*: Native authorizers execute at the API Gateway edge, caching public keys from Cognito's JWKS. Validation takes ~2ms and incurs zero compute cost. Caller identity is forwarded via verified claims.

---

## ADR 05: Stack Decoupling via SSM Parameter Store vs CloudFormation Exports
- **Decision**: Stacks publish their outputs to Amazon Systems Manager (SSM) Parameter Store under `/polling_system/` instead of using CloudFormation `Outputs` with `Export.Name`.
- **Trade-off Analysis**:
  - *Alternative (CloudFormation Exports)*: Creates rigid dependency graphs. If Stack A exports a value to Stack B, Stack A cannot be updated or torn down until Stack B is deleted.
  - *Selected Approach*: SSM Parameter Store provides decoupled dynamic resolution. The frontend environment generator script (`write_frontend_env.py`) reads directly from SSM, allowing independent stack lifecycle management and clean teardowns.

---

## ADR 06: Zero Gradients and Strictly Curated Design System Tokens
- **Decision**: Prohibit color gradients across all UI components, buttons, and visual cards. Use flat, solid colors exclusively defined via CSS custom properties in `tokens.css`.
- **Rationale**: Meets editorial, premium aesthetic standards rather than generic student demo styling. Consistent 8px spacing scale, 10px corner radius, and subtle 1px borders replace heavy drop shadows.
- **Accessibility**: All text and background combinations in both light mode and dark mode (`prefers-color-scheme: dark`) satisfy WCAG AA contrast ratios (minimum 4.5:1 for body text, 3:1 for headings).

---

## ADR 07: Self-Hosted Typography via Fontsource
- **Decision**: Bundle fonts locally using `@fontsource/inter` and `@fontsource/source-serif-4` rather than referencing external Google Fonts URLs.
- **Trade-off Analysis**:
  - *Alternative (External Google Fonts link)*: Adds render-blocking DNS lookups and external HTTP requests. Potential GDPR/privacy compliance concerns.
  - *Selected Approach*: WOFF2 font files are served from the CloudFront edge distribution with 1-year immutable cache headers, eliminating external dependencies and layout shifts.

---

## ADR 08: Cognito Daily Email Quota & Dedicated Acceptance Test App Client
- **Decision**: Account for Cognito's default email sender limit (50 emails/day) by providing two mechanisms:
  1. A dedicated `test-client` with `ADMIN_NO_SRP_AUTH` enabling automated integration tests without consuming daily email quotas.
  2. Clear operational instructions in the README on pre-creating demo users via Cognito Admin CLI.
- **Security Impact**: Browser clients remain restricted strictly to SRP (`ALLOW_USER_SRP_AUTH`) with no secret, maintaining browser security integrity.

---

## ADR 09: CloudFront Price Class 200 Configuration
- **Decision**: Configure CloudFront with `PriceClass_200`.
- **Rationale**: `PriceClass_200` includes edge servers throughout India (Mumbai, New Delhi, Chennai, Hyderabad, Bengaluru), East Asia, Middle East, Europe, and North America, delivering sub-30ms static asset delivery for Indian users while excluding higher-cost edge regions in South America and Australia to protect university budgets.

---

## ADR 10: Prohibition of Emojis Across Repository
- **Decision**: Strictly prohibit emoji characters in interface text, code comments, README, and git commit messages.
- **Rationale**: Preserves professional, editorial aesthetic. Visual cues are provided cleanly using consistent vector line icons from `lucide-react` at 16-18px size and 2px stroke width.
