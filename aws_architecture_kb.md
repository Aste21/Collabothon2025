# AWS Architecture and Pricing Knowledge Base

## 1. Typical architectures

### 1.1 Simple landing page or marketing site
- Static HTML/JS/CSS.
- Services:
  - Amazon S3 for static file hosting.
  - Amazon CloudFront as CDN.
  - Optional: Amazon Route 53 for domain.

Rough monthly cost, small traffic:
- S3 storage: a few GB → a few USD.
- Data transfer + CloudFront: 1–10 USD for low traffic.
- Route 53 hosted zone + DNS queries: a few USD.

### 1.2 Standard web application (frontend + backend + database)
Components:
- Frontend SPA: S3 + CloudFront.
- Backend API:
  - Option A: Amazon API Gateway + AWS Lambda (serverless).
  - Option B: Application Load Balancer + Amazon ECS/EC2.
- Database:
  - Amazon RDS (PostgreSQL/MySQL) or Amazon Aurora.
- User authentication:
  - Amazon Cognito.
- File uploads (images, documents):
  - Amazon S3.

Rough cost tiers:
- Small (few thousand users/month):
  - API (Lambda + API Gateway): tens of USD.
  - RDS small instance: tens of USD.
  - S3 + CloudFront: few USD–tens of USD.
  - Total: typically in the range of 50–200 USD/month.
- Medium (tens of thousands of users/month):
  - Total: a few hundred USD/month.
- Large (hundreds of thousands+):
  - Total: thousands of USD/month and up.

### 1.3 E-commerce application
Similar to 1.2, plus:
- Payments integration (Stripe/Adyen, etc.).
- Caching layer:
  - Amazon ElastiCache (Redis).
- Search:
  - Amazon OpenSearch Service.

Costs:
- Same base as 1.2 + extra for OpenSearch and ElastiCache.

### 1.4 Analytics / reporting system
- Data ingestion:
  - Amazon Kinesis or AWS Glue jobs.
- Storage:
  - Amazon S3 (data lake).
- Query:
  - Amazon Athena or Amazon Redshift.
- Visualization:
  - Amazon QuickSight.

Costs depend mainly on:
- Data volume stored in S3.
- Scanned data in Athena or size of Redshift cluster.
- Number of QuickSight users.

### 1.5 LLM/AI application (chatbot, RAG)
- Frontend: S3 + CloudFront or Amplify.
- Backend:
  - API Gateway + Lambda or ECS service.
- Vector store / search:
  - Amazon OpenSearch Serverless or a self-managed vector DB on EC2/EKS.
- Model hosting:
  - Option A: AWS Bedrock (managed LLM).
  - Option B: self-hosted model on GPU EC2 or ECS/EKS with GPUs.
- Knowledge base:
  - Documents in S3.

Costs:
- Bedrock: cost per tokens (input/output).
- Self-hosted GPU: cost per GPU hour (EC2 or ECS/EKS tasks).
- S3 + search + API + monitoring: incremental.

---

## 2. Pricing estimation patterns

The assistant should produce approximate pricing, not exact quotes. It should:
- Always mention that prices depend on region and usage.
- Provide ballpark monthly ranges (e.g. 50–150 USD, 200–800 USD).
- Clearly state assumptions (number of users, requests, stored data).

General rules of thumb:
- Small web app (few thousand users/month, light usage):
  - Often 50–200 USD/month on AWS.
- Medium web app (tens of thousands of users/month):
  - A few hundred USD/month.
- Heavy workloads or GPUs:
  - From a few hundred to thousands USD/month.

The assistant should:
- Ask for scale hints, such as:
  - “Roughly how many active users per month?”
  - “Do you expect many images or videos?”
  - “Do you need real-time processing or is batch processing fine?”
- Use these hints to pick small / medium / large tier.

---

## 3. Mapping from user described needs to AWS services

Examples:

- “Web app with login, profiles, and pictures”:
  - S3 for images.
  - CloudFront CDN.
  - Cognito for auth.
  - Lambda + API Gateway or ECS for backend.
  - RDS for relational data.

- “Internal dashboard with scheduled reports”:
  - S3 for data.
  - Glue/Athena for processing.
  - QuickSight for visualizations.
  - EventBridge or Lambda for scheduling.

- “Mobile app backend”:
  - API Gateway + Lambda.
  - DynamoDB or RDS.
  - S3 for assets.
  - Cognito for auth.
  - SNS for push notifications.

The assistant should:
- Translate user description into such a component list.
- Name AWS services explicitly.

---

## 4. How the assistant should answer

When a user describes their system, the assistant should:

1. Summarize the requirements in simple words.
2. Propose an AWS architecture:
   - list main components,
   - name AWS services,
   - briefly explain each service’s role.
3. Provide a cost estimate:
   - small/medium/large tier based on scale.
   - a rough monthly range (e.g. “around 80–150 USD/month for this setup at your scale”).
4. Add a short explanation:
   - why AWS is a good fit (reliability, security, managed services).
   - what future growth path could look like (scaling up easily).

If the input is missing critical details about scale, the assistant should first ask:
- “To estimate cost, I need a rough idea of users per month and how heavy the usage is. Can you estimate that?”
