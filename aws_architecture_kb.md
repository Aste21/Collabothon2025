## 1. API Gateway

Amazon API Gateway is a fully managed service that enables developers to create, deploy, maintain, secure, and scale APIs at any volume of requests.

What It Does

Serves as the entry point for HTTP/REST/WebSocket traffic.

Handles routing, authentication, throttling, and protocol transformations.

Provides managed integrations with:

Lambda functions

ECS/EKS services

Step Functions

VPC Link for private services

SQS, Kinesis, S3 (indirectly via Lambda)

Key Features

HTTP API — lightweight, cheaper, ideal for serverless workloads.

REST API — feature-rich (request/response mapping, usage plans).

WebSocket API — real-time two-way communication.

Authorization:

IAM Authorization

Cognito JWT Auth

Custom Lambda authorizers

Multiple deployments/stages (dev/stage/prod).

Built-in throttling, caching, monitoring, and Swagger/OpenAPI support.

Use Cases

Serverless backends

Multi-tenant SaaS APIs

Mobile backend services

Real-time chat (WebSocket)

Pricing (Ballpark)

HTTP API: ~$1.00 per 1M requests

REST API: ~$3.50 per 1M requests

WebSocket: ~$1.00 per 1M messages

Optional caching (per hour, depends on cache size)

## 2. Aurora

Amazon Aurora is a distributed, cloud-optimized relational database compatible with MySQL/PostgreSQL.

What It Does

Provides high throughput, low-latency relational queries.

Durable distributed storage automatically replicated to 6 copies across 3 AZs.

Supports multi-writer, read replicas, and cross-region replication.

Key Features

5× throughput of MySQL, 3× of PostgreSQL.

Storage auto-expands from 10GB → 128TB.

Aurora Serverless v2:

Scales compute continuously based on load.

Fast failover (seconds) with automated health monitoring.

Highly durable log-structured storage engine.

Use Cases

SaaS apps

High-traffic OLTP systems

Multi-tenant DB architectures

Financial platforms

Pricing

Compute (Serverless v2): ~0.12 USD per ACU hour

Storage: ~0.10 USD / GB-month

IO requests billed separately

## 3. CloudFront

Amazon CloudFront is AWS’s global CDN with 450+ edge locations.

What It Does

Caches content close to users.

Reduces latency for static/dynamic content.

Handles TLS at the edge.

Protects origins with Origin Access Control (OAC).

Key Features

Streaming support (HLS/DASH).

Integration with WAF, Shield, Lambda@Edge, CloudWatch.

Geo-restrictions, signed URLs, and signed cookies.

Origin failover between multiple origins.

Use Cases

Static websites

Video streaming

DDoS/latency protection

Global API acceleration

Pricing

~$0.085 / GB data-out

Requests are cheap (fractions of cents per 10k)

## 4. CloudTrail

Tracks all management and data events across AWS accounts.

What It Does

Logs every API call: user, service, timestamp, parameters.

Stores logs in S3 with optional encryption.

Integrates with CloudWatch, Athena, and GuardDuty.

Key Features

Multi-region trails.

Log integrity checks (immutability).

Event filtering and alerts.

Mandatory tool for compliance.

Use Cases

Audit and governance

Forensics after breaches

Security compliance (PCI, SOC2, HIPAA)

Pricing

Management event trail: 1 free per account

Data events billed per request

## 5. CloudWatch

Monitoring, logging, metrics, alerts, dashboards.

What It Does

Collects logs from Lambda/ECS/EC2.

Provides metric dashboards (CPU, memory, custom).

Triggers alarms (SNS, Slack, PagerDuty).

Enables distributed tracing (X-Ray integration).

Key Features

Metrics: CPU/memory/disk/network.

Logs: centralized log groups.

Alarms: threshold or anomaly detection.

Dashboards: custom widgets.

Use Cases

Observability

SRE monitoring

Business KPIs

Auto-scaling triggers

Pricing

Logs: ~$0.50/GB ingested

Metrics: ~$0.30/metric/month

Alarms: ~$0.10–0.20 each

## 6. DynamoDB

Fully managed, highly scalable NoSQL key-value/document database.

What It Does

Stores low-latency items at massive scale.

Supports 10M+ requests per second with hot-partition protection.

Offers Streams for change-tracking.

Key Features

On-Demand or Provisioned mode.

Global Tables for multi-region low-latency.

TTL for item expiration.

PartiQL SQL-like querying.

Use Cases

Gaming leaderboards

Ecommerce carts

IoT telemetry

Serverless applications

Pricing

Reads: ~$0.155 per 1M

Writes: ~$0.78 per 1M

Storage: ~$0.25/GB-month

## 7. EC2

Elastic Compute Cloud — virtual servers with OS-level control.

What It Does

Runs any Linux/Windows OS and application runtime.

Uses Nitro hypervisor for high performance.

Key Features

Hundreds of instance types.

Auto Scaling Groups.

Spot + Reserved + On-Demand models.

GPU/FPGA instance families.

Use Cases

Legacy apps

Custom machine images

HPC

Long-running compute workloads

Pricing

t3.micro: ~$8/month

gp3 disk: ~$0.08 / GB-month

## 8. Elastic Container Registry (ECR)

Private Docker registry hosted on AWS.

What It Does

Stores container images.

Scans images for vulnerabilities.

Integrates with ECS, EKS, CodeBuild, Lambda.

Key Features

Encryption at rest.

Replication across regions.

Lifecycle policies (clean old tags).

Use Cases

Microservices

CI/CD pipelines

Multi-environment deployments

Pricing

~$0.10 per GB-month

## 9. Elastic Container Service (ECS)

AWS-native container orchestration.

What It Does

Runs containers on EC2 or Fargate.

Handles service discovery, autoscaling, and load balancing.

Key Features

IAM roles per container.

Task definitions for reproducible deployment.

Tight integration with CloudWatch and ALB.

Use Cases

Microservices at scale

Batch workloads

Internal APIs

Pricing

ECS control plane is FREE

You only pay for EC2/Fargate compute

## 10. Elastic Kubernetes Service (EKS)

Managed Kubernetes control plane.

What It Does

Runs standard Kubernetes clusters fully integrated into AWS.

Supports EC2 or Fargate nodes.

Key Features

Automatic control-plane scaling and HA.

IAM-to-Kubernetes RBAC integration.

Add-ons for networking, metrics, ingress.

Use Cases

Kubernetes-native microservices

Hybrid cloud architectures

Data engineering pipelines

Pricing

~$0.10 per hour per cluster

## 11. Elastic Load Balancing

Load balancing platform with three main types.

Types

ALB – HTTP/HTTPS L7 load balancer

NLB – L4 ultra-low-latency load balancer

GLB – for network firewalls and appliances

Key Features

Path/host-based routing (ALB).

Static IPs (NLB).

Health checks.

TLS termination.

Use Cases

Web applications

Microservices

Multi-AZ failover

Pricing

ALB: ~$0.022–0.03/hr

NLB: ~$0.006–0.015/hr

## 12. EventBridge

Event bus for event-driven architectures.

What It Does

Routes events between services without coupling.

Processes SaaS events (Stripe, Auth0, etc.)

Key Features

Pattern-based filtering.

Scheduled events.

Dead-letter queues.

Use Cases

Microservice decoupling

Orchestration

Real-time event routing

Pricing

~$1 per 1M events

## 13. IAM (Identity and Access Management)

The central security system for AWS access.

What It Does

Defines who can access what and under what conditions.

Key Features

Users, groups, roles.

Policies (JSON) with allow/deny.

Permission boundaries.

Temporary STS tokens.

Use Cases

Least privilege

Multi-account setups

Identity federation

Pricing

Free

## 14. IoT Core

Cloud platform for IoT device messaging and management.

What It Does

Securely connects millions of devices.

Routes messages using MQTT, WebSockets, HTTP.

Key Features

Device registry + Digital Twin (Device Shadow).

Rules Engine → integrate with DynamoDB, S3, Lambda.

End-to-end encryption.

Use Cases

Smart home

Industrial telemetry

Fleet management

Pricing

~$1 per million messages

## 15. Lambda

Serverless compute for running code on-demand.

What It Does

Executes functions on triggers (HTTP, S3, Cron, EventBridge).

Auto-scales instantly.

Key Features

Pay-per-invocation + compute-time.

Multi-language support.

Concurrency controls.

Layers for shared dependencies.

Use Cases

Serverless APIs

ETL pipelines

Event-driven processing

Pricing

$0.20 per 1M calls

~$0.000004 per GB-second

## 16. Network Firewall

Managed VPC-level firewall.

What It Does

Inspects traffic between subnets, VPCs, and on-prem.

Key Features

Stateful deep packet inspection.

Rules for L3–L7.

Scalable throughput.

Use Cases

Enterprise compliance

Regulated industries

Layered security

Pricing

Per-firewall-hour

Per-GB inspection

## 17. RDS

Relational Database Service.

What It Does

Managed SQL engines: MySQL, PostgreSQL, MariaDB, Oracle, SQL Server.

Key Features

Multi-AZ failover.

Automated backups.

Read replicas.

Use Cases

Business applications

ERP/CRM

Financial systems

Pricing

db.t3.micro: ~13 USD/month

~$0.10/GB storage

## 18. Route 53

AWS’s DNS platform.

What It Does

Routes user traffic globally with near-zero latency.

Key Features

Latency-based routing.

Weighted routing.

Geo DNS.

Health checks.

Use Cases

Failover architectures

Multi-region deployments

Pricing

~$0.50 per hosted zone

~$0.40–0.60 per 1M queries

## 19. Secrets Manager

Secure secret storage with automatic rotation.

What It Does

Stores passwords, API keys, database credentials.

Automatically rotates secrets via Lambda hooks.

Key Features

Fine-grained IAM control.

Encryption via KMS.

Audit trail (CloudTrail).

Use Cases

API keys

DB credentials

Multi-environment CI/CD

Pricing

~$0.40 per secret/month

~$0.05 per 10k API calls

## 20. S3 (Simple Storage Service)

Highly durable object storage.

What It Does

Stores objects (files, images, logs, backups, datasets).

Supports event triggers → Lambda/EventBridge.

Provides lifecycle transitions to cheaper tiers.

Key Features

11 9’s durability.

Bucket policies & ACLs.

Versioning.

Cross-region replication.

Use Cases

File uploads

Log storage

Static website hosting

Data lakes

Pricing

Standard: ~$0.023 per GB-month

PUT/GET requests billed separately

## 21. Step Functions

Serverless workflow orchestrator for multi-step processes.

What It Does

Runs distributed workflows with retries/error handling.

Key Features

Parallel tasks.

Choice/Merge.

Map for batching.

Express vs Standard workflows.

Use Cases

Document pipelines

ML orchestration

Business workflows

Pricing

Standard: ~$0.025 per 1,000 transitions

Express: cheaper, high-volume

## 22. VPC (Virtual Private Cloud)

Customizable virtual network environment.

What It Does

Provides isolated IP ranges, routing, firewalling.

Key Features

Subnets (public/private).

NAT gateways.

VPC endpoints for S3/DynamoDB.

Security Groups & NACLs.

Use Cases

Secure backend systems

Hybrid networks

Multi-tier architectures

Pricing

VPC itself free

NAT gateway ~$32/month

VPC endpoints billed hourly
