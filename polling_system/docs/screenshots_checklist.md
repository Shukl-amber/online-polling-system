# AWS Console Demonstration & Viva Screenshots Checklist

This checklist details every AWS management console screen the project team must capture prior to the final demonstration and viva examination. Each item outlines the exact console path, visual evidence required, and the architectural principles it proves to examiners.

---

## 1. Amazon Cognito (Authentication Layer)

### Screenshot 1.1: User Pool Overview & Essentials Plan
- **Console Path**: Amazon Cognito > User pools > `polling-system-users`
- **Visual Evidence**:
  - User pool name: `polling-system-users`
  - User pool ID: `ap-south-1_xxxxxxxxx`
  - Feature Plan: **Essentials**
  - Sign-in attributes: Email address (case-insensitive)
  - Required attributes: `email`, `name` (display name)
- **What It Proves**: Adheres strictly to the architectural constraint requiring the Cognito Essentials tier in `ap-south-1` (Mumbai) without incurring unnecessary advanced security tier charges.

### Screenshot 1.2: App Clients (Browser vs Test Automation)
- **Console Path**: Amazon Cognito > User pools > `polling-system-users` > App integration > App clients
- **Visual Evidence**: Two distinct app clients:
  1. `polling-system-browser-client`:
     - Client secret: **No secret** (public SPA client)
     - Auth flows: `ALLOW_USER_SRP_AUTH`, `ALLOW_REFRESH_TOKEN_AUTH`
  2. `polling-system-test-client`:
     - Client secret: **No secret**
     - Auth flows: `ALLOW_ADMIN_USER_PASSWORD_AUTH`, `ALLOW_REFRESH_TOKEN_AUTH`
- **What It Proves**: Security separation between browser clients (enforcing cryptographic SRP without client secrets) and automated acceptance testing harnesses.

---

## 2. Amazon API Gateway (HTTP API & Authorization)

### Screenshot 2.1: Routes and Stage Throttling
- **Console Path**: API Gateway > APIs > `polling-system-api` > Routes
- **Visual Evidence**:
  - Routes: `POST /polls`, `GET /polls`, `GET /polls/{id}`, `POST /polls/{id}/vote`, `GET /polls/{id}/results`, `POST /polls/{id}/close`
  - Integration: AWS Lambda proxy integration pointed to the 6 individual ARM64 functions.
  - Stage `$default` settings: Route throttling with default burst limit 200 and rate limit 100 req/sec.
- **What It Proves**: Implementation of cost protection and denial-of-service throttling at the API Gateway stage layer.

### Screenshot 2.2: Native JWT Authorizer Configuration
- **Console Path**: API Gateway > APIs > `polling-system-api` > Authorization > Authorizers
- **Visual Evidence**:
  - Name: `CognitoAuthorizer`
  - Type: **JWT**
  - Identity source: `$request.header.Authorization`
  - Issuer: `https://cognito-idp.ap-south-1.amazonaws.com/{userPoolId}`
  - Audience: Both `browser-client-id` and `test-client-id`
- **What It Proves**: Serverless identity verification at the API Gateway native boundary without running custom Lambda authorizer code, keeping API latency near 1 second.

---

## 3. AWS Lambda (Compute Layer)

### Screenshot 3.1: Lambda Functions List & Architecture
- **Console Path**: AWS Lambda > Functions
- **Visual Evidence**:
  - Functions:
    1. `polling-system-create-poll`
    2. `polling-system-list-polls`
    3. `polling-system-get-poll`
    4. `polling-system-cast-vote`
    5. `polling-system-get-results`
    6. `polling-system-close-poll`
  - Runtime: **Python 3.13**
  - Architecture: **arm64** (Graviton2/Graviton3)
  - Memory: **256 MB**
  - Timeout: **10 seconds**
- **What It Proves**: Granular single-responsibility compute functions executing on power-efficient, cost-optimal Graviton processors.

### Screenshot 3.2: Function Environment Variables & Code Package
- **Console Path**: AWS Lambda > Functions > `polling-system-cast-vote` > Configuration > Environment variables
- **Visual Evidence**:
  - `POLLS_TABLE`: Name of DynamoDB polls table
  - `VOTES_TABLE`: Name of DynamoDB votes table
  - `AWS_REGION`: `ap-south-1`
- **What It Proves**: 12-factor cloud app pattern; environment configuration injected externally with no hardcoded values.

---

## 4. Amazon DynamoDB (Data Layer & Atomic Transactions)

### Screenshot 4.1: Polls Table & GSI Overview
- **Console Path**: Amazon DynamoDB > Tables > `polling-system-polls`
- **Visual Evidence**:
  - Partition key: `pollId` (String)
  - Capacity mode: **On-demand** (Pay-per-request)
  - Indexes tab: `status-createdAt-index`
    - Partition key: `status` (String)
    - Sort key: `createdAt` (String)
    - Projected attributes: All
- **What It Proves**: Scalable serverless data design preventing expensive table scans when querying open polls newest-first.

### Screenshot 4.2: Votes Table Configuration
- **Console Path**: Amazon DynamoDB > Tables > `polling-system-votes`
- **Visual Evidence**:
  - Partition key: `pollId` (String)
  - Sort key: `userId` (String)
  - Capacity mode: **On-demand**
- **What It Proves**: Composite primary key `(pollId, userId)` enforcing absolute uniqueness per user per poll in single-digit milliseconds.

---

## 5. AWS Identity and Access Management (IAM Least Privilege)

### Screenshot 5.1: Cast Vote Execution Role Policies
- **Console Path**: IAM > Roles > `polling-system-cast-vote-role`
- **Visual Evidence**:
  - Inline policy permissions restricted strictly to:
    - `dynamodb:PutItem` on the Votes table ARN
    - `dynamodb:UpdateItem` on the Polls table ARN
    - `dynamodb:GetItem` on the Polls table ARN
    - CloudWatch Logs write permissions (`logs:CreateLogStream`, `logs:PutLogEvents`)
  - No `dynamodb:*` wildcards.
- **What It Proves**: Least privilege principle verified; even if the vote function were compromised, it cannot drop tables, scan data, or modify unauthorized attributes.

---

## 6. Amazon S3 & Amazon CloudFront (Hosting & Edge Delivery)

### Screenshot 6.1: Private S3 Bucket with Block Public Access
- **Console Path**: Amazon S3 > Buckets > `polling-system-frontend-xxxx` > Permissions
- **Visual Evidence**:
  - Block Public Access: **All 4 settings ON (Block public ACLs, ignore public ACLs, block public bucket policies, restrict public buckets)**
  - Bucket policy: Allows `s3:GetObject` only to the CloudFront service principal with condition `AWS:SourceArn` matching the distribution ARN.
- **What It Proves**: Zero public exposure on S3; all access restricted through CloudFront Origin Access Control (OAC).

### Screenshot 6.2: CloudFront Distribution & Origin Access Control
- **Console Path**: CloudFront > Distributions > `E1XXXXXXXXXXXX`
- **Visual Evidence**:
  - Viewer Protocol Policy: **Redirect HTTP to HTTPS**
  - Origin Access: **Origin Access Control (OAC)**
  - Price Class: `PriceClass_200` (covering India, Asia, Middle East, Europe, North America)
  - Error Pages:
    - 403 -> `/index.html` (HTTP 200 OK)
    - 404 -> `/index.html` (HTTP 200 OK)
- **What It Proves**: Secure single-page application routing and high-performance edge caching compliant with AWS serverless best practices.

---

## 7. Amazon CloudWatch (Observability & Structured Logging)

### Screenshot 7.1: CloudWatch Log Groups & Retention
- **Console Path**: CloudWatch > Log groups
- **Visual Evidence**:
  - Log groups matching `/aws/lambda/polling-system-*`
  - Retention period: **14 days**
- **What It Proves**: Cost governance preventing unbounded log storage accumulation.

### Screenshot 7.2: Structured JSON Log Events
- **Console Path**: CloudWatch > Log groups > `/aws/lambda/polling-system-cast-vote` > Log streams
- **Visual Evidence**:
  - Structured JSON output containing: `timestamp`, `level`, `requestId`, `route`, `userId`, `outcome`, `metadata`
  - Absence of plain text stack traces or exposed sensitive tokens.
- **What It Proves**: Production-grade observability allowing automated metric extraction and auditability without privacy leakage.
