# SpendShield AI - Deployment Guide

This guide provides step-by-step instructions for deploying SpendShield AI in various environments.

## 📋 Prerequisites

Before deploying, ensure you have:

- [x] Google AI API Key (Gemini 2.0 Flash)
- [x] PostgreSQL 15+ database (or Docker)
- [x] Python 3.11+ (for local deployment)
- [x] Docker & Docker Compose (for containerized deployment)

## 🚀 Deployment Options

### Option 1: Local Development (Recommended for Testing)

#### Step 1: Setup Environment

```bash
# Navigate to project directory
cd newprop

# Copy environment template
cp .env.example .env

# Edit .env and add your Google API key
# GOOGLE_API_KEY=your_actual_api_key_here
```

#### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

#### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 4: Start PostgreSQL

**Option A: Using Docker**
```bash
docker run -d \
  --name spendshield-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=spendshield \
  -p 5432:5432 \
  postgres:15-alpine
```

**Option B: Local PostgreSQL**
```bash
# Create database
createdb spendshield

# Update .env with your connection string
# DATABASE_URL=postgresql://user:password@localhost:5432/spendshield
```

#### Step 5: Run the Application

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

#### Step 6: Test the API

```bash
# Check health
curl http://localhost:8080/health

# Run mock test
python tests/test_fraud_detection.py --mock

# Run example usage
python example_usage.py
```

---

### Option 2: Docker Compose (Recommended for Production)

#### Step 1: Setup Environment

```bash
# Create .env file
cp .env.example .env

# Add your Google API key
echo "GOOGLE_API_KEY=your_actual_api_key_here" >> .env
```

#### Step 2: Build and Start Services

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

#### Step 3: Verify Deployment

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f api

# Test API
curl http://localhost:8080/health
```

#### Step 4: Stop Services

```bash
# Stop services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

---

### Option 3: Google Cloud Run

#### Prerequisites
- Google Cloud account
- gcloud CLI installed and configured
- Cloud SQL PostgreSQL instance (or use Cloud SQL Proxy)

#### Step 1: Setup Cloud SQL

```bash
# Create Cloud SQL instance
gcloud sql instances create spendshield-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create spendshield \
  --instance=spendshield-db

# Create user
gcloud sql users create spendshield-user \
  --instance=spendshield-db \
  --password=your_secure_password
```

#### Step 2: Build and Push Container

```bash
# Set project ID
export PROJECT_ID=your-gcp-project-id

# Build container
gcloud builds submit --tag gcr.io/$PROJECT_ID/spendshield-ai

# Or use Docker
docker build -t gcr.io/$PROJECT_ID/spendshield-ai .
docker push gcr.io/$PROJECT_ID/spendshield-ai
```

#### Step 3: Deploy to Cloud Run

```bash
# Get Cloud SQL connection name
export INSTANCE_CONNECTION_NAME=$(gcloud sql instances describe spendshield-db --format='value(connectionName)')

# Deploy
gcloud run deploy spendshield-ai \
  --image gcr.io/$PROJECT_ID/spendshield-ai \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=your_api_key \
  --set-env-vars DATABASE_URL=postgresql://spendshield-user:password@/spendshield?host=/cloudsql/$INSTANCE_CONNECTION_NAME \
  --add-cloudsql-instances $INSTANCE_CONNECTION_NAME \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10
```

#### Step 4: Test Deployment

```bash
# Get service URL
export SERVICE_URL=$(gcloud run services describe spendshield-ai --region us-central1 --format='value(status.url)')

# Test health endpoint
curl $SERVICE_URL/health

# Test with sample document
curl -X POST $SERVICE_URL/analyze \
  -F "file=@tests/sample_invoice.png" \
  -F "department=Finance"
```

---

### Option 4: AWS ECS/Fargate

#### Step 1: Create ECR Repository

```bash
# Create repository
aws ecr create-repository --repository-name spendshield-ai

# Get repository URI
export ECR_URI=$(aws ecr describe-repositories --repository-names spendshield-ai --query 'repositories[0].repositoryUri' --output text)
```

#### Step 2: Build and Push Image

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URI

# Build and tag
docker build -t spendshield-ai .
docker tag spendshield-ai:latest $ECR_URI:latest

# Push
docker push $ECR_URI:latest
```

#### Step 3: Create RDS PostgreSQL Instance

```bash
# Create DB subnet group (if not exists)
aws rds create-db-subnet-group \
  --db-subnet-group-name spendshield-subnet \
  --db-subnet-group-description "SpendShield DB Subnet" \
  --subnet-ids subnet-xxx subnet-yyy

# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier spendshield-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.3 \
  --master-username postgres \
  --master-user-password your_secure_password \
  --allocated-storage 20 \
  --db-subnet-group-name spendshield-subnet \
  --vpc-security-group-ids sg-xxx
```

#### Step 4: Create ECS Task Definition

Create `task-definition.json`:

```json
{
  "family": "spendshield-ai",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "spendshield-api",
      "image": "YOUR_ECR_URI:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "GOOGLE_API_KEY",
          "value": "your_api_key"
        },
        {
          "name": "DATABASE_URL",
          "value": "postgresql://postgres:password@your-rds-endpoint:5432/spendshield"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/spendshield-ai",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Step 5: Create ECS Service

```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create cluster
aws ecs create-cluster --cluster-name spendshield-cluster

# Create service
aws ecs create-service \
  --cluster spendshield-cluster \
  --service-name spendshield-api \
  --task-definition spendshield-ai \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `GOOGLE_API_KEY` | Yes | Google AI API key for Gemini | - |
| `DATABASE_URL` | Yes | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/spendshield` |
| `PORT` | No | Server port | `8080` |
| `HOST` | No | Server host | `0.0.0.0` |
| `UPLOAD_DIR` | No | Upload directory | `./uploads` |
| `MAX_FILE_SIZE` | No | Max file size in bytes | `10485760` (10MB) |
| `ALLOWED_EXTENSIONS` | No | Allowed file extensions | `pdf,png,jpg,jpeg` |

### Database Connection Strings

**Local PostgreSQL:**
```
postgresql://username:password@localhost:5432/spendshield
```

**Docker Compose:**
```
postgresql://postgres:postgres@db:5432/spendshield
```

**Cloud SQL (with Unix socket):**
```
postgresql://user:password@/spendshield?host=/cloudsql/project:region:instance
```

**Cloud SQL (with TCP):**
```
postgresql://user:password@ip-address:5432/spendshield
```

---

## 🔒 Security Checklist

Before deploying to production:

- [ ] Use strong database passwords
- [ ] Store API keys in secret management (e.g., Google Secret Manager, AWS Secrets Manager)
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS properly (restrict origins)
- [ ] Implement API authentication (JWT, API keys)
- [ ] Enable rate limiting
- [ ] Set up monitoring and alerting
- [ ] Configure firewall rules
- [ ] Enable database encryption at rest
- [ ] Use VPC/private networks
- [ ] Implement audit logging
- [ ] Regular security updates

---

## 📊 Monitoring

### Health Checks

```bash
# API health
curl http://your-domain:8080/health

# Database health (from container)
docker exec spendshield-db pg_isready -U postgres
```

### Logs

**Docker Compose:**
```bash
# View all logs
docker-compose logs -f

# View API logs only
docker-compose logs -f api

# View database logs
docker-compose logs -f db
```

**Cloud Run:**
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=spendshield-ai" --limit 50
```

**AWS ECS:**
```bash
aws logs tail /ecs/spendshield-ai --follow
```

---

## 🐛 Troubleshooting

### Common Issues

**Issue: Database connection failed**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

**Issue: API key not working**
```bash
# Verify API key is set
echo $GOOGLE_API_KEY

# Test API key
curl -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=$GOOGLE_API_KEY"
```

**Issue: Container won't start**
```bash
# Check container logs
docker logs spendshield-api

# Check container status
docker inspect spendshield-api
```

---

## 📈 Scaling

### Horizontal Scaling

**Docker Compose:**
```bash
docker-compose up --scale api=3
```

**Cloud Run:**
```bash
gcloud run services update spendshield-ai \
  --min-instances 1 \
  --max-instances 10
```

**AWS ECS:**
```bash
aws ecs update-service \
  --cluster spendshield-cluster \
  --service spendshield-api \
  --desired-count 3
```

### Database Scaling

- Use connection pooling (already configured in `db.py`)
- Enable read replicas for read-heavy workloads
- Consider managed database services (Cloud SQL, RDS)
- Implement caching (Redis) for frequent queries

---

## 🔄 Updates and Maintenance

### Updating the Application

```bash
# Pull latest code
git pull

# Rebuild containers
docker-compose up --build -d

# Or for Cloud Run
gcloud builds submit --tag gcr.io/$PROJECT_ID/spendshield-ai
gcloud run deploy spendshield-ai --image gcr.io/$PROJECT_ID/spendshield-ai
```

### Database Migrations

```bash
# Backup database first
pg_dump $DATABASE_URL > backup.sql

# Run migrations (if needed)
# Add migration scripts as needed
```

---

## ✅ Deployment Checklist

- [ ] Environment variables configured
- [ ] Database created and accessible
- [ ] API key tested and working
- [ ] Application builds successfully
- [ ] Health check endpoint responds
- [ ] Sample document analysis works
- [ ] Logs are accessible
- [ ] Monitoring configured
- [ ] Backups scheduled
- [ ] Security measures implemented
- [ ] Documentation updated
- [ ] Team trained on operations

---

## 📞 Support

For deployment issues:
1. Check logs first
2. Verify environment variables
3. Test database connectivity
4. Review this guide
5. Check `README.md` for additional information

---

**Last Updated**: December 20, 2024  
**Version**: 1.0.0
