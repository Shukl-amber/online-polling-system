# Technical Service Justification & Alternatives Analysis

This document provides technical justification for every AWS service selected in the Online Polling System architecture, contrasting each choice against rejected alternatives.

---

## 1. Compute: AWS Lambda (ARM64, Python 3.13)

### Why It Fits
- **Zero Idle Cost**: Functions execute on demand; demonstration pauses incur zero compute fees.
- **Microsecond Cold Starts & Performance**: Python 3.13 on Graviton (ARM64) architecture provides ~20% better price-performance ratio and lower latency compared to x86_64.
- **Granular Least Privilege**: Each of the 6 feature slices runs under an independent execution role containing only the exact IAM permissions required for its database operations.
- **Automatic Concurrency Scaling**: Handles burst traffic (such as an entire classroom voting at once) without cluster provisioning or container pre-warming.

### Alternatives Considered and Rejected
- **AWS Fargate (Amazon ECS)**: Rejected because running even a single container 24/7 incurs baseline costs (~$15-$30/month) outside the free tier. Requires container registry management, VPC networking, and health check monitoring.
- **Amazon EC2**: Rejected due to operational overhead (patching, OS hardening, load balancing) and high ongoing idle cost. Violates serverless brief constraints.
- **Lambda Function URLs**: Rejected because Function URLs lack native JWT authentication from Cognito and native stage throttling, requiring custom authorization logic in every function.

---

## 2. Ingress & Authorization: API Gateway HTTP API with Native JWT Authorizer

### Why It Fits
- **Native OIDC/JWT Authorizer**: Directly verifies Cognito User Pool ID tokens at the gateway edge before invoking Lambda. Unauthenticated requests are rejected with HTTP 401 without consuming Lambda execution compute.
- **Ultra-Low Latency**: HTTP APIs (v2) are designed for serverless workloads, delivering ~60% lower latency and ~70% lower cost than REST APIs (v1).
- **Built-in CORS & Throttling**: Native stage throttling protects downstream services from Denial-of-Service and cost overruns.

### Alternatives Considered and Rejected
- **API Gateway REST API**: Rejected due to higher latency, complex resource policy syntax, and unnecessary features (API keys, SOAP conversion, XML transformation) that add cost and overhead.
- **Application Load Balancer (ALB)**: Rejected because an ALB incurs minimum hourly charges (~$16-$22/month) regardless of request volume. Native Cognito integration on ALB requires redirect flows intended for web applications rather than RESTful SPAs.

---

## 3. Database: Amazon DynamoDB (On-Demand Mode)

### Why It Fits
- **Atomic Transactions (`TransactWriteItems`)**: Allows atomic execution of two conditional operations:
  1. `PutItem` on `Votes` table (`attribute_not_exists(pollId) AND attribute_not_exists(userId)`)
  2. `UpdateItem` on `Polls` table (`attribute_exists(pollId) AND #st = :open`)
  This guarantees duplicate vote prevention even when concurrent requests arrive within milliseconds.
- **Deterministic Single-Digit Millisecond Latency**: Key-value primary lookups execute in 1-4 ms.
- **Zero Capacity Planning**: `PAY_PER_REQUEST` billing charges strictly per read and write request with zero provisioned capacity waste.
- **Targeted Secondary Index**: `status-createdAt-index` GSI enables querying open polls in reverse chronological order without expensive full table scans.

### Alternatives Considered and Rejected
- **Amazon Aurora Serverless v2**: Rejected due to minimum ACU scaling baselines (0.5 ACU costs ~$43/month) and connection pooling complexities with ephemeral Lambda functions.
- **Amazon RDS (PostgreSQL/MySQL)**: Rejected due to connection exhaustion risks with serverless concurrency, requirement for RDS Proxy (additional cost), and persistent DB instance charges.
- **DocumentDB / MongoDB**: Rejected due to provisioned cluster pricing and lack of serverless native IAM integration.

---

## 4. Identity: Amazon Cognito User Pool (Essentials Plan)

### Why It Fits
- **Native Standards Compliance**: Implements OpenID Connect (OIDC) and OAuth 2.0 with JSON Web Tokens (JWT).
- **Secure SRP Authentication**: Secure Remote Password (SRP) protocol authenticates the browser client without transmitting passwords in plain text over the wire.
- **Dual App Clients**:
  - `browser-client`: Configured strictly with SRP (no secret) for browser security.
  - `test-client`: Configured with `ADMIN_NO_SRP_AUTH` enabling automated integration and acceptance test suites.
- **Cost Effectiveness**: Free tier permanently covers up to 50,000 monthly active users (MAUs).

### Alternatives Considered and Rejected
- **Auth0 / Okta**: Rejected because external identity providers require outbound internet calls, introducing external dependency risks, network latency, and third-party subscription overhead.
- **Custom JWT via Database & Bcrypt**: Rejected because rolling custom auth introduces security vulnerabilities (salt management, token revocation, timing attacks) and violates quality guidelines.

---

## 5. Web Hosting: Private Amazon S3 with Amazon CloudFront and OAC

### Why It Fits
- **Origin Access Control (OAC)**: S3 bucket has 100% Block Public Access enabled; content can only be retrieved by the designated CloudFront distribution principal.
- **SPA Custom Error Responses**: Mappings of HTTP 403 and 404 to `/index.html` with status 200 allow client-side React Router routing to function seamlessly across deep links.
- **Edge Caching & Compression**: CloudFront automatically caches static CSS, JS, and self-hosted fonts close to users across edge locations, minimizing latency.
- **HTTPS Enforcement**: Automatic TLS 1.3 encryption and HTTP-to-HTTPS redirect.

### Alternatives Considered and Rejected
- **S3 Public Website Hosting**: Rejected because it requires disabling S3 Block Public Access and exposes the S3 endpoint publicly without HTTPS or modern TLS configuration.
- **AWS Amplify Hosting**: Rejected as per brief constraints prohibiting Amplify CLI or full-stack managed backends.

---

## 6. Infrastructure as Code: AWS SAM (Modular Multi-Stack Architecture)

### Why It Fits
- **Separation of Concerns**: Stacks are partitioned into 4 distinct lifecycle deployables:
  1. `01_auth` (Cognito User Pool)
  2. `02_data` (DynamoDB Tables)
  3. `03_hosting` (S3 & CloudFront)
  4. `04_api` (API Gateway & Lambdas)
- **Decoupled Parameter Resolution**: Stacks communicate via SSM Parameter Store rather than brittle CloudFormation cross-stack exports, avoiding export lock-in during refactoring.
- **Native Serverless Transforms**: SAM shorthand simplifies Lambda roles, API integrations, and log group declaration.

### Alternatives Considered and Rejected
- **Monolithic CloudFormation Template**: Rejected because a single change to frontend or API risks rolling back database or user authentication state.
- **Terraform / OpenTofu**: Rejected because AWS SAM provides native integration with CloudWatch, Lambda packaging, and AWS-managed serverless policies.
