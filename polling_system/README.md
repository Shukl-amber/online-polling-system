# Online Polling System on AWS Serverless

A robust, production-grade Online Polling System built with AWS serverless services. Designed for high correctness, multi-threaded duplicate vote prevention via atomic DynamoDB transactions, least-privilege security, and an editorial frontend interface.

---

## 1. Project Overview

- **Core Capabilities**: Authenticated users create polls with 2 to 6 unique options, vote once per poll, view dynamic aggregated results with count and percentage in tabular numerals, and close their own polls.
- **Concurrency & Correctness**: Atomic DynamoDB transactions (`TransactWriteItems`) strictly prevent duplicate voting, even under simultaneous concurrent race conditions.
- **Zero Idle Baseline Cost**: 100% serverless architecture on AWS Free Tier within region `ap-south-1` (Mumbai).
- **Design Aesthetic**: Minimal, editorial aesthetic adhering strictly to flat solid colors (no gradients), vector line icons (no emojis), and self-hosted typography with zero external font requests.

---

## 2. Prerequisites & Minimum Tool Versions

Before deploying, ensure the following tools are installed and configured:

| Dependency | Minimum Version | Verification Command | Purpose |
| :--- | :--- | :--- | :--- |
| **AWS CLI** | v2.15.0+ | `aws --version` | AWS account credentials and management |
| **AWS SAM CLI** | v1.120.0+ | `sam --version` | Building and deploying CloudFormation stacks |
| **Python** | 3.12 or 3.13 | `python --version` | Backend Lambda runtime and test execution |
| **Node.js** | v22.0.0+ (LTS) | `node --version` | Frontend Vite build and Vitest runner |
| **npm** | v10.0.0+ | `npm --version` | Frontend dependency management |

Set your active AWS region to `ap-south-1` (Mumbai):
```bash
aws configure set default.region ap-south-1
```

---

## 3. Architecture & Deployables

The system is organized into modular vertical slices and deployed as four sequential AWS SAM units plus a frontend publishing step. Stacks communicate dynamically via AWS SSM Parameter Store under the `/polling_system/` namespace.

```
polling_system/
  infra/
    01_auth/template.yaml      # Cognito User Pool and App Clients
    02_data/template.yaml      # DynamoDB Polls & Votes Tables + GSI
    03_hosting/template.yaml   # Private S3 Bucket, CloudFront OAC, Custom Error Pages
    04_api/template.yaml       # HTTP API, JWT Authorizer, 6 Lambda Functions, Throttling
  backend/
    features/                  # create_poll, list_polls, get_poll, cast_vote, get_results, close_poll
    shared/                    # dynamo.py, http.py, auth.py, errors.py, logging.py
  frontend/
    src/features/              # auth, polls_list, create_poll, poll_detail
    src/shared/                # tokens.css, api.ts, components, hooks
  scripts/
    write_frontend_env.py      # Generates frontend/.env from deployed SSM parameters
    publish_frontend.py        # Builds frontend, uploads to S3, invalidates CloudFront
    run_acceptance_tests.py    # Executes T1-T13 acceptance test scenarios
  docs/                        # Architecture diagram, viva defense, ADRs, checklist, costs
```

---

## 4. Deployment Guide (Deploy Order)

Deploy the units in exact numerical order.

### Deployable 1: 01_auth (Authentication Layer)
- **Purpose**: Creates the Amazon Cognito User Pool on the Essentials plan, the browser app client (SRP authentication without secret), and the acceptance test app client (`ADMIN_NO_SRP_AUTH`).
- **Prerequisites**: Configured AWS CLI with credentials in `ap-south-1`.
- **Deploy Commands**:
  ```bash
  cd infra/01_auth
  sam build
  sam deploy --stack-name polling-system-auth --resolve-s3 --capabilities CAPABILITY_IAM
  cd ../..
  ```
- **Expected Output**: CloudFormation stack `polling-system-auth` creates `AWS::Cognito::UserPool`, `AWS::Cognito::UserPoolClient` (x2), and publishes parameters to SSM:
  - `/polling_system/user_pool_id`
  - `/polling_system/user_pool_arn`
  - `/polling_system/browser_client_id`
  - `/polling_system/test_client_id`
- **Verification**:
  ```bash
  aws ssm get-parameters-by-path --path /polling_system/
  ```
- **Teardown**:
  ```bash
  sam delete --stack-name polling-system-auth --no-prompts
  ```
*Verified against: Amazon Cognito Developer Guide (User Pool Essentials Feature Plan & SRP Auth, checked 23 October 2026).*

---

### Deployable 2: 02_data (Data Layer)
- **Purpose**: Provisions the DynamoDB `Polls` table (with GSI `status-createdAt-index`) and the `Votes` table with on-demand capacity (`PAY_PER_REQUEST`).
- **Prerequisites**: Deployable 1 completed.
- **Deploy Commands**:
  ```bash
  cd infra/02_data
  sam build
  sam deploy --stack-name polling-system-data --resolve-s3
  cd ../..
  ```
- **Expected Output**: Stack `polling-system-data` creates tables and publishes SSM parameters:
  - `/polling_system/polls_table_name`
  - `/polling_system/polls_table_arn`
  - `/polling_system/votes_table_name`
  - `/polling_system/votes_table_arn`
- **Verification**:
  ```bash
  # PowerShell (Windows)
  aws dynamodb describe-table --table-name (aws ssm get-parameter --name /polling_system/polls_table_name --query Parameter.Value --output text) --query "Table.TableStatus" --output text

  # Bash / zsh
  aws dynamodb describe-table --table-name $(aws ssm get-parameter --name /polling_system/polls_table_name --query Parameter.Value --output text) --query "Table.TableStatus" --output text
  ```
- **Teardown**:
  ```bash
  sam delete --stack-name polling-system-data --no-prompts
  ```
*Verified against: Amazon DynamoDB Developer Guide (Transactional Write Items & Global Secondary Indexes, checked 23 October 2026).*

---

### Deployable 3: 03_hosting (Edge & Web Hosting Layer)
- **Purpose**: Provisions a private S3 bucket with 100% Block Public Access, CloudFront Distribution with Origin Access Control (OAC), and custom SPA error responses (403 and 404 mapped to `/index.html` with status 200).
- **Prerequisites**: Deployable 2 completed.
- **Deploy Commands**:
  ```bash
  cd infra/03_hosting
  sam build
  sam deploy --stack-name polling-system-hosting --resolve-s3
  cd ../..
  ```
- **Expected Output**: Stack `polling-system-hosting` outputs and publishes:
  - `/polling_system/frontend_bucket_name`
  - `/polling_system/distribution_id`
  - `/polling_system/cloudfront_domain`
- **Verification**:
  ```bash
  aws ssm get-parameter --name /polling_system/cloudfront_domain --query Parameter.Value --output text
  ```
- **Teardown**:
  ```bash
  # PowerShell (Windows)
  $BUCKET = aws ssm get-parameter --name /polling_system/frontend_bucket_name --query Parameter.Value --output text
  aws s3 rm s3://$BUCKET --recursive

  # Bash
  BUCKET=$(aws ssm get-parameter --name /polling_system/frontend_bucket_name --query Parameter.Value --output text)
  aws s3 rm s3://$BUCKET --recursive

  sam delete --stack-name polling-system-hosting --no-prompts
  ```
*Verified against: Amazon CloudFront Developer Guide (Origin Access Control & SPA Custom Error Pages, checked 23 October 2026).*

---

### Deployable 4: 04_api (API Gateway & Compute Layer)
- **Purpose**: Creates the API Gateway HTTP API, native JWT authorizer bound to Cognito, default stage throttling, and the six ARM64 Python 3.13 Lambda functions. Configures allowed CORS origins to include the CloudFront domain and `http://localhost:5173`.
- **Prerequisites**: Deployables 1, 2, and 3 completed.
- **Deploy Commands**:
  ```bash
  cd infra/04_api
  sam build
  sam deploy --stack-name polling-system-api --resolve-s3 --capabilities CAPABILITY_IAM
  cd ../..
  ```
- **Expected Output**: Stack `polling-system-api` outputs API URL and publishes:
  - `/polling_system/api_url`
- **Verification**:
  ```bash
  # PowerShell (Windows)
  curl.exe -i "$((aws ssm get-parameter --name /polling_system/api_url --query Parameter.Value --output text))/polls"

  # Bash
  curl -i $(aws ssm get-parameter --name /polling_system/api_url --query Parameter.Value --output text)/polls
  # Should return HTTP 401 Unauthorized (proves JWT authorizer enforcement)
  ```
- **Teardown**:
  ```bash
  sam delete --stack-name polling-system-api --no-prompts
  ```
*Verified against: Amazon API Gateway HTTP API Guide (Native JWT Authorizer and Stage Throttling, checked 23 October 2026).*

---

### Deployable 5: Frontend Configuration and Publish
- **Purpose**: Generates `frontend/.env` from deployed SSM parameters, builds the production Vite bundle, uploads static assets to S3 with correct cache headers, and invalidates CloudFront.
- **Prerequisites**: Stacks 01 through 04 deployed.
- **Execution Commands**:
  ```bash
  # 1. Generate frontend configuration
  python scripts/write_frontend_env.py

  # 2. Build, upload, and invalidate cache
  python scripts/publish_frontend.py
  ```
- **Verification**: Open the CloudFront domain in any browser. The application loads the editorial authentication screen securely over HTTPS.
- **Local Development**:
  ```bash
  cd frontend
  npm run dev
  # Access at http://localhost:5173
  ```

---

## 5. Testing & Quality Verification

### 5.1 Backend Unit Tests (pytest + moto)
Runs 17 unit tests per feature slice covering success paths, validation errors, closed polls, unknown polls, and sequential duplicate votes:
```bash
pytest -v
```

### 5.2 Frontend Unit Tests (Vitest + React Testing Library)
Runs form validation, dynamic options, voting lock, results rendering, and 409 duplicate handling tests:
```bash
cd frontend
npm test
npm run build
npm run lint
cd ..
```

### 5.3 Code Quality & Formatting (ruff)
```bash
ruff check backend scripts
ruff format --check backend scripts
```

### 5.4 End-to-End Acceptance Tests (Against Deployed Cloud Infrastructure)
Runs scenarios **T1 through T13** against the live AWS deployment. Multi-threaded test **T8** proves true concurrency on real DynamoDB:
```bash
python scripts/run_acceptance_tests.py
```
This generates the full execution report at `docs/test_report.md`.

---

## 6. Full Teardown Procedure

To guarantee zero ongoing costs, delete resources in exact reverse deployment order:

```bash
# Step 1: Empty and delete S3 bucket contents
BUCKET=$(aws ssm get-parameter --name /polling_system/frontend_bucket_name --query Parameter.Value --output text)
aws s3 rm s3://$BUCKET --recursive

# Step 2: Delete Stacks in Reverse Order
sam delete --stack-name polling-system-api --no-prompts
sam delete --stack-name polling-system-hosting --no-prompts
sam delete --stack-name polling-system-data --no-prompts
sam delete --stack-name polling-system-auth --no-prompts

# Step 3: Remove generated local environment
rm frontend/.env
```

---

## 7. Operational Notes (Cognito Email Quotas)

Amazon Cognito User Pools default email sender is throttled at **50 emails per calendar day**. For live academic demonstrations and testing:
1. Automated acceptance testing utilizes `scripts/run_acceptance_tests.py`, which leverages `admin_create_user` and `admin_set_user_password` via the test client to bypass email quotas.
2. To pre-create demo users for live viva presentation without consuming email quota:
   ```bash
   USER_POOL_ID=$(aws ssm get-parameter --name /polling_system/user_pool_id --query Parameter.Value --output text)
   aws cognito-idp admin-create-user --user-pool-id $USER_POOL_ID --username demo@example.com --user-attributes Name=email,Value=demo@example.com Name=email_verified,Value=true Name=name,Value="Demo User" --message-action SUPPRESS
   aws cognito-idp admin-set-user-password --user-pool-id $USER_POOL_ID --username demo@example.com --password "DemoUser123!Safe" --permanent
   ```
