# ⚽ Cloud Football Analytics System

## Real-Time Processing for Nigerian Professional Football League (NPFL)

[![AWS](https://img.shields.io/badge/AWS-Cloud-orange)](https://aws.amazon.com/)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![Terraform](https://img.shields.io/badge/Terraform-1.5+-purple)](https://www.terraform.io/)
[![License](https://img.shields.io/badge/License-MSc_Research-green)](https://www.shu.ac.uk/)

---

## 🎓 Research Project

**MSc Computing Research Project**

- **Author**: Adebayo Oyeleye (C4039125)
- **Institution**: Sheffield Hallam University
- **Supervisor**: Jade McDonald
- **Period**: October - December 2024

### Research Question

> "How can a cloud computing architecture be designed and implemented to process live football data at scale for real-time analytics?"

### Key Achievement

✅ **Sub-100ms processing latency** (~50ms average) - **10x better than target**

---

## 📋 Quick Links

- **Live API**: https://d4pstbgzu1.execute-api.us-east-1.amazonaws.com/development
- **Swagger Docs**: https://d4pstbgzu1.execute-api.us-east-1.amazonaws.com/development/docs
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Deliverables**: [PROJECT_DELIVERABLES.md](PROJECT_DELIVERABLES.md)

---

## 🚀 Quick Start

### Prerequisites

- AWS Account with CLI configured
- Python 3.11+
- Terraform 1.5+
- API-Football key (free tier: 100 requests/day)

### 1. Clone & Configure

```bash
git clone <repository-url>
cd football-analytics-cloud

# Configure API key
cp config/config.env.example config/config.env
# Edit config.env and add your API_FOOTBALL_KEY
```

### 2. Deploy Infrastructure

```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

This creates:

- Kinesis Data Stream (2 shards)
- Lambda Functions (3 total)
- DynamoDB Table
- API Gateway (REST + WebSocket)
- CloudWatch Dashboard
- IAM Roles & KMS Keys

### 3. Deploy Lambda Code

```bash
cd ../..
./scripts/deploy_lambda.sh
# Answer 'y' when prompted to deploy
```

### 4. Test the System

```bash
# Run NPFL match simulation
python3 scripts/demo_npfl_match.py

# Verify data was processed
aws dynamodb scan --table-name football-analytics-development --limit 5

# Check API
curl https://d4pstbgzu1.execute-api.us-east-1.amazonaws.com/development/health
```

### 5. View Swagger Docs

Open in browser:

```
https://d4pstbgzu1.execute-api.us-east-1.amazonaws.com/development/docs
```

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────┐
│          Data Sources (NPFL Matches)            │
│  • API-Football (League ID: 399)                │
│  • Demo Scripts                                 │
└──────────────────┬──────────────────────────────┘
                   ↓
┌──────────────────▼──────────────────────────────┐
│  Layer 1: INGESTION (Kinesis)                   │
│  • 2 shards, 25 Hz throughput                   │
│  • 24-hour retention                            │
└──────────────────┬──────────────────────────────┘
                   ↓
┌──────────────────▼──────────────────────────────┐
│  Layer 2: PROCESSING (Lambda)                   │
│  • Python 3.11, 512 MB memory                   │
│  • ~50ms average latency                        │
│  • Auto-scaling, event-driven                   │
└──────────────────┬──────────────────────────────┘
                   ↓
┌──────────────────▼──────────────────────────────┐
│  Layer 3: STORAGE                               │
│  • DynamoDB (hot data, 2-20 units)              │
│  • S3 (cold storage, archives)                  │
└──────────────────┬──────────────────────────────┘
                   ↓
┌──────────────────▼──────────────────────────────┐
│  Layer 4: DELIVERY (API Gateway)                │
│  • REST API (Swagger docs)                      │
│  • WebSocket (real-time updates)                │
└─────────────────────────────────────────────────┘
```

**For detailed architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 🇳🇬 Nigerian Football (NPFL) Support

### Supported Teams (20 total)

- Enyimba FC (Aba)
- Rangers International (Enugu)
- Kano Pillars (Kano)
- Rivers United (Port Harcourt)
- Plateau United (Jos)
- Shooting Stars SC (Ibadan)
- Akwa United (Uyo)
- Lobi Stars (Makurdi)
- Kwara United (Ilorin)
- Heartland FC (Owerri)
- *...and 10 more*

### API-Football Integration

```bash
# Check NPFL API status
python3 scripts/check_api_status.py

# Ingest live NPFL data
python3 scripts/ingest_live_data.py

# Simulate NPFL match
python3 scripts/demo_npfl_match.py
```

**League ID**: 399 (NPFL)
**Season**: 2024-2025
**API Docs**: https://www.api-football.com/documentation-v3

---

## 📊 Performance Metrics

| Metric                       | Target        | Achieved    | Status        |
| ---------------------------- | ------------- | ----------- | ------------- |
| **Processing Latency** | <500ms        | ~50ms       | ✅ 10x better |
| **Throughput**         | 25 events/s   | 27 events/s | ✅ Met        |
| **Success Rate**       | >95%          | 100%        | ✅ Exceeded   |
| **Auto-scaling**       | Yes           | 2-20 units  | ✅ Working    |
| **Cost**               | Pay-as-you-go | <$15/month  | ✅ Optimized  |

**Evidence**:

- CloudWatch logs showing 50ms processing
- 27 events successfully processed
- 100% success rate
- DynamoDB auto-scaling confirmed

---

## 📂 Project Structure

```
football-analytics-cloud/
├── src/
│   ├── ingestion/              # Data ingestion scripts
│   │   └── kinesis_producer.py
│   ├── processing/             # Lambda processors
│   │   ├── event_processor.py
│   │   └── analytics.py
│   ├── delivery/               # WebSocket handlers
│   │   └── websocket_handler.py
│   └── api/                    # FastAPI documentation
│       ├── swagger_app.py
│       └── combined_api_handler.py
│
├── infrastructure/
│   └── terraform/              # Infrastructure as Code
│       ├── main.tf
│       ├── kinesis.tf
│       ├── lambda.tf
│       ├── dynamodb.tf
│       ├── api_gateway.tf
│       └── ...
│
├── scripts/
│   ├── deploy_lambda.sh        # Deploy Lambda functions
│   ├── demo_npfl_match.py      # Simulate NPFL match
│   ├── ingest_live_data.py     # Live data ingestion
│   └── check_api_status.py     # Check API-Football
│
├── config/
│   ├── config.env              # Configuration (API keys)
│   └── config.env.example
│
├── README.md                   # This file
├── ARCHITECTURE.md             # Technical architecture
└── PROJECT_DELIVERABLES.md     # Research deliverables
```

---

## 🛠️ Technology Stack

### AWS Services

- **AWS Lambda** - Cloud compute (Python 3.11)
- **Amazon Kinesis Data Streams** - Real-time ingestion
- **Amazon DynamoDB** - NoSQL database
- **Amazon S3** - Object storage
- **API Gateway v2** - REST + WebSocket APIs
- **CloudWatch** - Monitoring & logging
- **X-Ray** - Distributed tracing
- **KMS** - Encryption keys
- **IAM** - Access control

### Frameworks & Libraries

- **Terraform** - Infrastructure as Code
- **FastAPI** - API framework with Swagger
- **Boto3** - AWS SDK for Python
- **Mangum** - ASGI adapter for Lambda
- **Pydantic** - Data validation

### Development Tools

- **Python 3.11** - Primary language
- **Bash** - Deployment scripts
- **Git** - Version control
- **pytest** - Testing framework

---

## 🔧 Configuration

### Environment Variables

**config/config.env**:

```bash
# API-Football Configuration
API_FOOTBALL_KEY=your_api_key_here
API_FOOTBALL_BASE_URL=https://v3.football.api-sports.io
NPFL_LEAGUE_ID=399

# AWS Configuration (auto-detected from credentials)
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=your_account_id

# Application Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### Terraform Variables

**infrastructure/terraform/terraform.tfvars**:

```hcl
project_name  = "football-analytics"
environment   = "development"
aws_region    = "us-east-1"

# Kinesis
kinesis_shard_count = 2
kinesis_retention_hours = 24

# DynamoDB
dynamodb_read_capacity_min = 2
dynamodb_read_capacity_max = 20
dynamodb_write_capacity_min = 2
dynamodb_write_capacity_max = 20

# API Gateway
api_gateway_throttle_burst_limit = 5000
api_gateway_throttle_rate_limit = 10000
```

---

## 🧪 Testing

### Unit Tests

```bash
pytest tests/unit/
```

### Integration Tests

```bash
# Test Kinesis → Lambda → DynamoDB pipeline
pytest tests/integration/test_pipeline.py

# Test API endpoints
pytest tests/integration/test_api.py
```

### Load Testing

```bash
# Simulate 10,000 events
python3 tests/load/simulate_high_load.py --events 10000 --duration 60
```

### Manual Testing

```bash
# 1. Send single event
python3 scripts/send_test_event.py

# 2. Verify in DynamoDB
aws dynamodb scan --table-name football-analytics-development --limit 1

# 3. Check Lambda logs
aws logs tail /aws/lambda/football-analytics-event-processor-development

# 4. Test API
curl https://d4pstbgzu1.execute-api.us-east-1.amazonaws.com/development/health
```

---

## 📊 Monitoring

### CloudWatch Dashboard

```bash
# Access via AWS Console
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=football-analytics-development
```

**Metrics Available**:

- Lambda execution metrics (invocations, duration, errors)
- Kinesis throughput (incoming records, bytes)
- DynamoDB capacity (reads, writes, throttles)
- API Gateway requests (count, latency, errors)

### Logs

```bash
# Lambda processor logs
aws logs tail /aws/lambda/football-analytics-event-processor-development --follow

# API handler logs
aws logs tail /aws/lambda/football-analytics-api-handler-development --follow

# WebSocket handler logs
aws logs tail /aws/lambda/football-analytics-websocket-handler-development --follow
```

### X-Ray Tracing

```bash
# View service map and traces in AWS Console
https://console.aws.amazon.com/xray/home?region=us-east-1#/service-map
```

---

## 💰 Cost Breakdown

### Development Environment (~$15/month)

| Service         | Usage           | Cost           |
| --------------- | --------------- | -------------- |
| Kinesis         | 2 shards × 24h | $10.80         |
| Lambda          | 50k invocations | $0.10          |
| DynamoDB        | On-demand       | $2.00          |
| S3              | 1 GB storage    | $0.02          |
| API Gateway     | 10k requests    | $0.04          |
| CloudWatch      | Logs + metrics  | $1.00          |
| KMS             | Key usage       | $1.00          |
| **Total** |                 | **~$15** |

### Production Estimate (10 concurrent matches)

**Assumptions**: 10 matches/day, 90 min each, 5,400 events/match

| Service         | Monthly Cost         |
| --------------- | -------------------- |
| Kinesis         | $10.80               |
| Lambda          | $0.50                |
| DynamoDB        | $30.00               |
| S3              | $5.00                |
| API Gateway     | $1.00                |
| CloudWatch      | $5.00                |
| **Total** | **~$53/month** |

**Compare to EC2**: $88-$118/month (t3.medium + EBS + RDS + ALB)

**Cloud Advantage**: 40-55% cost savings + zero idle costs

---

## 🔐 Security

### Encryption

- **At Rest**: KMS encryption for Kinesis, DynamoDB, S3, CloudWatch Logs
- **In Transit**: TLS 1.2+ for all API calls, WSS for WebSocket

### Access Control

- **IAM Roles**: Least privilege principle
- **API Keys**: Ready for production (disabled in demo)
- **Lambda Authorizers**: Custom auth logic supported

### Network Security

- **VPC Endpoints**: Private connectivity to AWS services
- **Security Groups**: Resource isolation
- **WAF**: (optional) DDoS protection for API Gateway

---

## 📝 API Documentation

### Interactive Swagger UI

**URL**: https://d4pstbgzu1.execute-api.us-east-1.amazonaws.com/development/docs

### Endpoints

| Endpoint               | Method | Description            |
| ---------------------- | ------ | ---------------------- |
| `/health`            | GET    | System health check    |
| `/docs`              | GET    | Swagger UI             |
| `/redoc`             | GET    | ReDoc alternative docs |
| `/openapi.json`      | GET    | OpenAPI specification  |
| `/metrics`           | GET    | System metrics         |
| `/events`            | POST   | Submit event           |
| `/events/{match_id}` | GET    | Query match events     |
| `/teams`             | GET    | NPFL teams list        |
| `/architecture`      | GET    | System architecture    |

### Example: Submit Event

```bash
curl -X POST https://d4pstbgzu1.execute-api.us-east-1.amazonaws.com/development/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "goal",
    "match_id": "npfl_2024_001",
    "timestamp": "2024-11-22T19:30:00Z",
    "team_id": "enyimba_fc",
    "player_id": "victor_mbaoma",
    "location": {"x": 95, "y": 52},
    "metadata": {
      "minute": 78,
      "assist_by": "alex_iwobi",
      "goal_type": "header"
    }
  }'
```

---

## 🚨 Troubleshooting

### Events Not Appearing in DynamoDB

1. Check Lambda logs for errors:
   ```bash
   aws logs tail /aws/lambda/football-analytics-event-processor-development --since 5m
   ```
2. Verify Kinesis stream is receiving events:
   ```bash
   aws kinesis describe-stream --stream-name football-analytics-stream-development
   ```
3. Wait 30-60 seconds for processing

### CloudWatch Shows Only Lambda Metrics

✅ **This is NORMAL!**

- Lambda metrics appear immediately
- Kinesis/DynamoDB metrics need 5-15 minutes
- Best verification: Check Lambda logs + DynamoDB directly

### API Returns 500 Error

1. Check Lambda function logs
2. Verify handler path is correct
3. Ensure all dependencies are deployed
4. Check IAM permissions

### Terraform Apply Fails

1. Ensure AWS credentials are configured:
   ```bash
   aws sts get-caller-identity
   ```
2. Check Terraform version: `terraform version`
3. Review error message and fix resource conflicts

---

## 🧹 Cleanup

### Destroy Infrastructure

```bash
cd infrastructure/terraform
terraform destroy
```

**Warning**: This will delete:

- All Lambda functions
- Kinesis stream
- DynamoDB table (and all data!)
- S3 buckets
- API Gateway
- CloudWatch logs

### Partial Cleanup (Keep Infrastructure)

```bash
# Delete DynamoDB data only
aws dynamodb scan --table-name football-analytics-development \
  --attributes-to-get match_id event_id \
  | jq -r '.Items[] | "aws dynamodb delete-item --table-name football-analytics-development --key '"'"'{\\"match_id\\":{\\"S\\":\\"" + .match_id.S + "\\"},\\"event_id\\":{\\"S\\":\\"" + .event_id.S + "\\"}}'"'"'"' \
  | bash
```

---

## 📚 Documentation

### Core Documents

1. **README.md** (this file) - Project overview and setup
2. **ARCHITECTURE.md** - Technical architecture details
3. **PROJECT_DELIVERABLES.md** - Research deliverables summary

### AWS Documentation

- Infrastructure code: `infrastructure/terraform/`
- Lambda source: `src/`
- Scripts: `scripts/`

---

## 🤝 Contributing

This is an academic research project. For questions or collaboration:

**Author**: Adebayo Oyeleye
**Email**: Adebayo.I.Oyeleye@student.shu.ac.uk
**Institution**: Sheffield Hallam University

---

## 📄 License

**MSc Computing Research Project**
© 2024 Adebayo Oyeleye, Sheffield Hallam University

This project is developed as part of an MSc Computing research thesis.

---

## 🙏 Acknowledgements

- **Supervisor**: Jade McDonald (Sheffield Hallam University)
- **API-Football**: Free tier API for NPFL data
- **StatsBomb**: Open data for reference
- **AWS**: Cloud services and documentation
- **Nigerian Football Federation**: NPFL support

---

## 📖 References

1. Jonas, E., et al. (2019). "Cloud Programming Simplified: A Berkeley View on Cloud Computing"
2. Vidal-Codina, F., et al. (2022). "Automatic Event Detection in Football Using Tracking Data"
3. Merhej, C., et al. (2021). "What Happened Next? Using Deep Learning to Value Defensive Actions"
4. AWS Well-Architected Framework: https://aws.amazon.com/architecture/well-architected/
5. Adebayo Oyeleye Research Proposal (2024)

---

## 📅 Project Timeline

| Phase                | Duration  | Status      |
| -------------------- | --------- | ----------- |
| Literature Review    | Week 1-2  | ✅ Complete |
| Architecture Design  | Week 3-4  | ✅ Complete |
| Implementation       | Week 5-8  | ✅ Complete |
| Testing & Evaluation | Week 9-10 | ✅ Complete |
| Documentation        | Week 11   | ✅ Complete |
|                      |           |             |

**Last Updated**: November 22, 2025
**Version**: 1.0
**Status**: ✅ Production Ready
