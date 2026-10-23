# University Cloud Computing Project: Viva & Demonstration Defense Notes

This document contains 15 of the most probable and critical technical questions asked during the viva voce examination, accompanied by precise, architectural answers grounded in AWS serverless best practices.

---

### Q1: How exactly are duplicate votes prevented, and why is it impossible to vote twice?
**Answer**: Duplicate vote prevention is enforced at the database storage engine layer via an atomic Amazon DynamoDB transaction (`TransactWriteItems`). The transaction contains two conditional actions executed as an indivisible unit:
1. `PutItem` into the `Votes` table with partition key `pollId` and sort key `userId`, guarded by the condition `attribute_not_exists(pollId) AND attribute_not_exists(userId)`.
2. `UpdateItem` on the `Polls` table incrementing `counts[optionId]` and `totalVotes`, guarded by `attribute_exists(pollId) AND #status = :open`.
If a user attempts to vote a second time, the first action's condition evaluates to false. DynamoDB aborts the entire transaction with a `TransactionCanceledException` (cancellation reason: `ConditionalCheckFailed`). The backend interprets this and returns HTTP 409 (`ALREADY_VOTED`) without mutating any counts.

---

### Q2: What happens when two vote requests from the same user arrive at the exact same millisecond?
**Answer**: Amazon DynamoDB transactions provide serializable isolation. When two simultaneous requests hit two separate Lambda execution contexts, both issue a `TransactWriteItems` call to DynamoDB. DynamoDB's internal distributed coordination protocol processes them in strict serial order.
- The first transaction acquires write locks on the target partition keys, succeeds, and commits the vote item.
- The second transaction evaluates the conditional expression against the newly committed item, fails the `attribute_not_exists` condition, and is cancelled.
Exactly one request receives HTTP 200, the other receives HTTP 409, and the total vote count in DynamoDB increases by exactly 1. This is proven empirically in acceptance test scenario **T8**.

---

### Q3: Why choose Amazon DynamoDB over a relational database like PostgreSQL or MySQL for this project?
**Answer**: Three main reasons:
1. **Connection Scalability with Serverless**: Relational databases suffer connection exhaustion when hundreds of ephemeral Lambda instances spin up concurrently. DynamoDB uses stateless HTTPS requests via HTTP connection pools, scaling seamlessly with zero connection pool bottlenecks.
2. **Deterministic Latency**: DynamoDB guarantees single-digit millisecond latency regardless of table size because queries hit partition keys directly rather than navigating B-tree indexes or query optimizers.
3. **Cost & Capacity**: An on-demand DynamoDB table costs $0.00 when idle and has no minimum hourly charge, whereas relational databases (like Aurora Serverless v2 or RDS) require continuous hourly compute provisioning.

---

### Q4: How does the API Gateway native JWT authorizer protect the API, and where does user identity come from?
**Answer**: API Gateway HTTP API integrates a native JWT authorizer that validates the caller's Cognito ID token directly at the gateway layer before the Lambda function is ever invoked:
1. It validates the cryptographic RSA signature of the JWT against Amazon Cognito's public JWKS endpoint.
2. It verifies that token expiration (`exp`) has not passed.
3. It checks that the token audience (`aud`) matches the configured App Client ID, and that the issuer (`iss`) matches the User Pool ARN.
If invalid or missing, API Gateway immediately returns HTTP 401 Unauthorized with zero Lambda execution cost. The Lambda function extracts the verified caller identity exclusively from `event.requestContext.authorizer.jwt.claims.sub`. The client cannot spoof their `userId` through the request body or path.

---

### Q5: How is least privilege IAM enforced across the backend Lambda functions?
**Answer**: Rather than sharing a broad administrator role, every Lambda function has its own dedicated execution role declared in AWS SAM:
- `CreatePollFunction`: Allowed only `dynamodb:PutItem` on the Polls table ARN.
- `ListPollsFunction`: Allowed only `dynamodb:Query` on the Polls table GSI ARN (`status-createdAt-index`).
- `GetPollFunction`: Allowed only `dynamodb:GetItem` on Polls and Votes table ARNs.
- `CastVoteFunction`: Granted only `dynamodb:PutItem` on Votes and `dynamodb:UpdateItem` / `dynamodb:GetItem` on Polls.
- `ClosePollFunction`: Granted only `dynamodb:GetItem` and `dynamodb:UpdateItem` on Polls.
No function has `dynamodb:*` or wildcard table access.

---

### Q6: How does the Global Secondary Index (GSI) optimize the listing of open polls?
**Answer**: The Polls table uses `pollId` as its partition key. Fetching open polls without a GSI would necessitate a full table `Scan` with a filter expression, which reads every item in the database, consuming high read capacity and slowing down as the table grows.
The GSI `status-createdAt-index` uses `status` as the partition key and `createdAt` as the sort key. Calling `Query` with `KeyConditionExpression: status = "open"` and `ScanIndexForward=False` retrieves open polls sorted newest-first in a single, targeted index partition read.

---

### Q7: Why use Amazon CloudFront with Origin Access Control (OAC) instead of standard S3 website hosting?
**Answer**:
1. **Security**: S3 static website hosting requires disabling S3 Block Public Access and making the entire bucket publicly readable to the internet. With CloudFront OAC, S3 Block Public Access is 100% enabled, and an S3 bucket policy allows `s3:GetObject` solely to CloudFront when the `AWS:SourceArn` matches the distribution ARN.
2. **HTTPS & Edge Performance**: CloudFront enforces TLS 1.3 encryption and caches static bundles across AWS edge locations near the user.
3. **SPA Routing**: CloudFront custom error responses map HTTP 403 and 404 to `/index.html` with status 200, allowing client-side React Router navigation to resolve cleanly on direct URL refreshes.

---

### Q8: What is the rationale for Python 3.13 on AWS Lambda Graviton (ARM64)?
**Answer**:
- **Price-Performance**: AWS Graviton (ARM64) processors deliver up to 34% better price-performance and ~20% lower execution cost compared to x86_64.
- **Modern Python Runtime**: Python 3.13 is a managed AWS Lambda runtime offering performance improvements in bytecode compilation and memory footprint.
- **Cold Start Latency**: Python on ARM64 cold starts are typically under 200 ms, well within the 1-second response latency requirement.

---

### Q9: How is input validation structured, and why use Pydantic v2?
**Answer**: All incoming HTTP payloads are validated at the edge of the Lambda service layer using Pydantic v2 schemas:
- Titles: 3 to 120 characters.
- Questions: up to 300 characters.
- Options: 2 to 6 options, each 1 to 80 characters, enforced to be unique after whitespace trimming and case insensitivity.
Pydantic v2 is compiled in Rust (pydantic-core), ensuring validation overhead is sub-millisecond. If validation fails, a uniform error object `{ "error": { "code": "VALIDATION_ERROR", "message": "..." } }` is returned with HTTP 400. Stack traces are never leaked to clients.

---

### Q10: Why are stacks decoupled using SSM Parameter Store instead of CloudFormation Exports?
**Answer**: CloudFormation exports introduce hard cross-stack dependencies (`Fn::ImportValue`). When Stack B imports an export from Stack A, Stack A cannot be modified, updated, or torn down until Stack B is completely deleted.
By publishing identifiers (user pool ID, table names, bucket names) into SSM Parameter Store under `/polling_system/`, stacks read external configuration dynamically without lifecycle locking, enabling independent deployments and painless teardowns.

---

### Q11: Why are there two separate Cognito App Clients in the architecture?
**Answer**: Separation of client privileges:
1. `browser-client`: Configured strictly with `ALLOW_USER_SRP_AUTH` without a client secret. Because single-page applications run in public browsers, client secrets cannot be securely stored. SRP authentication ensures passwords are never transmitted in clear text.
2. `test-client`: Configured with `ALLOW_ADMIN_USER_PASSWORD_AUTH`. Single-page browsers cannot invoke admin APIs, but the acceptance test script uses this client to programmatically create and authenticate confirmed test users without requiring manual email OTP confirmation.

---

### Q12: Why is the backend structured as a single code package with multiple Lambda handlers?
**Answer**: In AWS SAM, setting `CodeUri: backend` across all 6 functions packages the common directory once during `sam build`.
- **Modularity**: Feature code remains strictly isolated in vertical slices (`features/create_poll`, `features/cast_vote`, etc.).
- **Code Sharing**: Utilities in `shared/` (`dynamo.py`, `http.py`, `auth.py`) are reused without redundant copying or complex Lambda Layer versioning.
- **Deployment Speed**: Packaging one small (~2MB) zip bundle is substantially faster than uploading six separate zip bundles.

---

### Q13: What is the CloudFront price class used, and why?
**Answer**: We specify `PriceClass_200`, which includes edge locations across India, Asia, the Middle East, Europe, and North America. Because the project is deployed in `ap-south-1` (Mumbai), `PriceClass_200` ensures Indian users hit low-latency edge servers in Mumbai, New Delhi, Chennai, and Hyderabad while excluding the highest-cost edge locations in South America and Australia to protect university budgets.

---

### Q14: How are CloudWatch log costs controlled?
**Answer**:
1. Every Lambda function's CloudWatch Log Group is explicitly declared in the SAM template with `RetentionInDays: 14`. Without this, CloudWatch defaults to "Never Expire", causing cumulative storage costs over time.
2. Logs are emitted as single-line structured JSON records with request ID, route, user ID, and outcome, minimizing log volume while enabling structured querying via CloudWatch Insights.

---

### Q15: What teardown procedure is required, and why must S3 be emptied first?
**Answer**: Teardown must be executed in exact reverse dependency order:
1. Empty and delete S3 static hosting bucket (CloudFormation cannot delete an S3 bucket that contains objects).
2. Delete `04_api` stack.
3. Delete `03_hosting` stack.
4. Delete `02_data` stack.
5. Delete `01_auth` stack.
This guarantees zero residual resources or billing charges after demonstration.
