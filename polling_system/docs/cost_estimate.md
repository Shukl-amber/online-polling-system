# Cost Estimate and Capacity Model

This document outlines the operational cost model for the Online Polling System running in region **ap-south-1 (Mumbai)**.

In accordance with university project standards, **prices are not invented**. Standard workload metrics and free-tier allowances are modeled below, with dedicated price columns ready to be populated directly from official quotes via the [AWS Pricing Calculator](https://calculator.aws/).

---

## 1. Workload Assumptions (Demo & University Scale)

| Parameter | Moderate Demonstration Load | Peak University Class Load |
| :--- | :--- | :--- |
| **Monthly Active Users (MAU)** | 100 users | 2,500 users |
| **Polls Created per Month** | 50 polls | 500 polls |
| **Votes Cast per Month** | 1,000 votes | 25,000 votes |
| **Poll Result Views per Month** | 2,000 views | 50,000 views |
| **Average Payload Size** | 1.5 KB per request | 1.5 KB per request |
| **Static Asset Page Views** | 5,000 views / month | 100,000 views / month |
| **Average Frontend Transfer** | 150 KB per cold load | 150 KB per cold load |

---

## 2. Service-by-Service Free Tier & Pricing Breakdown

All resources operate under the AWS Free Tier allowances or pay-per-use serverless models with zero idle baseline cost.

| Service | Architecture Role | Free Tier Allowance | Consumption Metric (Monthly Demo) | AWS Pricing Calculator Estimate (USD) |
| :--- | :--- | :--- | :--- | :--- |
| **Amazon Cognito** | Authentication & Directory (Essentials Plan) | 50,000 MAUs free per month on Lite & Essentials tiers | 100 MAUs (~0.2% of free tier) | *[To be filled from AWS Calculator]* |
| **API Gateway HTTP API** | Ingress Routing, Native JWT Authorization | 1,000,000 API calls free per month for first 12 months | ~3,550 API calls (~0.35% of free tier) | *[To be filled from AWS Calculator]* |
| **AWS Lambda (arm64)** | Business Logic & Atomic Orchestration | 1,000,000 requests & 3,200,000 seconds of compute time per month | 3,550 requests @ 256MB / ~100ms average duration | *[To be filled from AWS Calculator]* |
| **Amazon DynamoDB** | Persistent Storage (On-Demand Capacity) | 25 GB storage free permanently; on-demand pay-per-request | < 5 MB storage, ~1,500 WRUs, ~5,000 RRUs | *[To be filled from AWS Calculator]* |
| **Amazon S3** | Static Website Asset Storage | 5 GB standard storage free for first 12 months | ~2.5 MB total static bundle size | *[To be filled from AWS Calculator]* |
| **Amazon CloudFront** | Global Content Delivery & OAC HTTPS | 1 TB data transfer out & 10,000,000 HTTP/S requests free permanently | ~50 MB transfer out, ~5,000 requests | *[To be filled from AWS Calculator]* |
| **Amazon CloudWatch** | Structured Logging & Metrics | 5 GB log data ingestion & 5 GB archive storage free | < 50 MB log data with 14-day retention | *[To be filled from AWS Calculator]* |
| **SSM Parameter Store** | Standard Configuration Storage | Standard parameters are free of charge | 9 standard parameters stored | **$0.00 (Free permanent)** |

---

## 3. Cost Governance and Safeguards

1. **Default Route Throttling**: API Gateway stage default throttling is fixed at **burst limit 200** and **rate limit 100 requests per second** to prevent automated DDoS or brute-force cost spikes.
2. **Short Lambda Timeout**: Lambda timeout is capped at **10 seconds** with **256 MB memory**, preventing runaway hanging requests.
3. **Log Retention Limits**: All CloudWatch Log Groups declare an explicit **14-day retention window**, preventing indefinite storage fee creep.
4. **On-Demand Capacity Mode**: DynamoDB uses `PAY_PER_REQUEST` so zero charges accrue when the application is idle.
5. **No Long-Running Servers**: Zero EC2 instances, containers, or provisioned NAT gateways are deployed.
