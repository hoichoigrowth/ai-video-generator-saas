# 🎬 AI Video Generator SaaS - Production Deployment

![AI Video Generator](https://img.shields.io/badge/AI%20Video%20Generator-v2.0.0-blue)
![Docker](https://img.shields.io/badge/Docker-Ready-green)
![Production](https://img.shields.io/badge/Production-Ready-brightgreen)

A complete, self-hosted AI-powered video generation SaaS platform that transforms text scripts into professional videos using multiple AI services.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- 4GB+ RAM available
- API keys for AI services (OpenAI, Anthropic, Google AI, PiAPI)

### 1-Minute Deployment

```bash
# Clone and setup
git clone <repository-url>
cd AI-video-generator

# Configure environment (add your API keys)
cp .env.example .env
nano .env  # Add your API keys

# Start everything
./scripts/start.sh
```

**Access Your Application:**
- 🌐 Frontend: http://localhost:3000
- 📖 API Docs: http://localhost:8000/docs
- 🗄️ MinIO Console: http://localhost:9001
- 📊 Monitoring: http://localhost:3001 (Grafana)

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React         │    │   FastAPI        │    │   PostgreSQL    │
│   Frontend      │───▶│   Backend        │───▶│   Database      │
│   (Port 3000)   │    │   (Port 8000)    │    │   (Port 5432)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌──────────────────┐    ┌─────────────────┐
         │              │   Redis          │    │   MinIO         │
         └──────────────│   Cache/Queues   │    │   File Storage  │
                        │   (Port 6379)    │    │   (Port 9000)   │
                        └──────────────────┘    └─────────────────┘
```

### Service Components

- **Frontend**: React application with TailwindCSS
- **Backend**: FastAPI with async PostgreSQL + Redis
- **Database**: PostgreSQL with full ACID compliance
- **Storage**: MinIO S3-compatible object storage
- **Queues**: Redis for approval workflows
- **Monitoring**: Prometheus + Grafana stack
- **Reverse Proxy**: Nginx for production routing

## 🎯 Key Features

### ✅ **Self-Hosted & Open Source**
- No dependency on Google Workspace or external SaaS
- Complete data ownership and privacy control
- Cost-effective alternative to cloud services

### 🤖 **Multi-LLM AI Pipeline**
- **Screenplay Generation**: OpenAI GPT-4, Claude, Google Gemini
- **Shot Division**: Automatic scene breakdown for vertical video
- **Character Design**: AI-powered character extraction & generation
- **Scene Generation**: Midjourney integration via PiAPI
- **Video Generation**: Kling AI for final video production

### 🔄 **Workflow Management**
- Custom approval system (replaces GoToHuman)
- Real-time WebSocket notifications
- Priority-based task queues
- Comprehensive audit trails

### 📊 **Data Export & Analytics**
- CSV, Excel, PDF export capabilities
- Production planning reports
- Character design summaries
- Project analytics dashboard

## 🛠️ Installation Guide

### Environment Setup

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Configure API keys in `.env`:**
   ```env
   # Required API Keys
   OPENAI_API_KEY=sk-your_openai_key_here
   ANTHROPIC_API_KEY=sk-ant-your_anthropic_key_here
   GOOGLE_API_KEY=your_google_ai_key_here
   PIAPI_KEY=your_piapi_key_here
   KLING_API_KEY=your_kling_key_here  # Optional
   ```

3. **Customize database settings (optional):**
   ```env
   POSTGRES_PASSWORD=your_secure_password
   MINIO_SECRET_KEY=your_secure_minio_key
   GRAFANA_PASSWORD=your_grafana_password
   ```

### Quick Commands

| Command | Description |
|---------|-------------|
| `./scripts/start.sh` | Start all services |
| `./scripts/stop.sh` | Stop all services |
| `./scripts/reset.sh` | Reset everything (⚠️ deletes data) |
| `./scripts/logs.sh` | View service logs |
| `./scripts/logs.sh backend` | View specific service logs |

### Health Checks

```bash
# Run comprehensive health checks
docker-compose -f docker-compose.production.yml run --rm backend python scripts/health_check.py

# Test complete workflow
docker-compose -f docker-compose.production.yml run --rm backend python scripts/test_workflow.py
```

## 📚 API Documentation

### Core Endpoints

```http
# Project Management
POST /api/v1/projects                    # Create project
GET  /api/v1/projects                    # List projects
GET  /api/v1/projects/{id}               # Get project details

# File Operations
POST /api/v1/projects/{id}/upload-script # Upload script
POST /api/v1/projects/{id}/screenplay    # Store screenplay

# Approval System
POST /api/v1/approvals                   # Create approval request
GET  /api/v1/approvals/pending           # Get pending approvals
POST /api/v1/approvals/{id}/respond      # Submit approval response

# Data Export
POST /api/v1/exports                     # Create export
GET  /api/v1/projects/{id}/exports       # Export history

# Health & Monitoring
GET  /health                             # Basic health check
GET  /health/detailed                    # Comprehensive health check
```

### WebSocket Real-time Updates

```javascript
// Connect to project updates
const ws = new WebSocket('ws://localhost:8000/ws/{project_id}');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Project update:', update);
};
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_HOST` | PostgreSQL hostname | `postgres` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |
| `MINIO_ENDPOINT` | MinIO server endpoint | `minio:9000` |
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |

## 🚨 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check Docker is running
docker info

# Check ports aren't in use
netstat -tlnp | grep -E ':(3000|8000|5432|6379|9000)'

# View specific service logs
./scripts/logs.sh postgres
```

**Database connection fails:**
```bash
# Check PostgreSQL is ready
docker-compose exec postgres pg_isready -U ai_video_user

# Reset database
docker-compose down postgres
docker volume rm ai-video-generator_postgres_data
./scripts/start.sh
```

**API keys not working:**
```bash
# Verify environment variables are loaded
docker-compose exec backend env | grep API_KEY

# Check API key validity
curl -H "Authorization: Bearer ${OPENAI_API_KEY}" https://api.openai.com/v1/models
```

## 💾 Backup & Recovery

### Automated Backups

```bash
# Database backup
docker-compose exec postgres pg_dump -U ai_video_user ai_video_generator > backup_$(date +%Y%m%d).sql

# MinIO backup
docker-compose exec minio mc mirror local/ai-video-generator /backup/minio_$(date +%Y%m%d)/

# Configuration backup
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env* docker-compose* nginx/ monitoring/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Made with ❤️ for the creator economy**

*Empowering storytellers worldwide with AI-powered video generation*
