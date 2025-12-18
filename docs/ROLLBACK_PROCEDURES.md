# Rollback Procedures

This document describes the rollback procedures for the Keiko platform.

## Table of Contents

1. [Service Rollback](#service-rollback)
2. [Database Rollback](#database-rollback)
3. [Frontend Rollback](#frontend-rollback)
4. [Emergency Procedures](#emergency-procedures)
5. [Post-Rollback Verification](#post-rollback-verification)

## Service Rollback

### Automated Rollback

Use the automated rollback script for Kubernetes deployments:

```bash
./tools/scripts/rollback.sh <service-name> <target-version> [environment]
```

**Example:**
```bash
./tools/scripts/rollback.sh chat-service v1.2.0 production
```

### Manual Rollback

If the automated script fails, perform manual rollback:

1. **Check deployment history:**
   ```bash
   kubectl rollout history deployment/<service-name> -n keiko-production
   ```

2. **Rollback to previous revision:**
   ```bash
   kubectl rollout undo deployment/<service-name> -n keiko-production
   ```

3. **Rollback to specific revision:**
   ```bash
   kubectl rollout undo deployment/<service-name> --to-revision=<revision-number> -n keiko-production
   ```

4. **Monitor rollback status:**
   ```bash
   kubectl rollout status deployment/<service-name> -n keiko-production
   ```

### Service-Specific Considerations

#### Chat Service
- Ensure OpenAI API connections are stable
- Verify conversation history is preserved
- Check Redis cache connectivity

#### Search Service
- Verify Azure AI Search connectivity
- Check cache invalidation
- Monitor search latency

#### Document Service
- Verify Azure Blob Storage access
- Check file upload/download functionality
- Monitor storage quotas

## Database Rollback

### Prerequisites

1. **Always create a backup before rollback:**
   ```bash
   ./tools/scripts/database-rollback.sh <target-migration> [environment]
   ```

2. **Verify backup integrity:**
   ```bash
   # Check backup file exists and is not empty
   ls -lh db-backup-*.sql
   ```

### Migration Rollback

#### Using Alembic (Python services)

1. **Check current migration:**
   ```bash
   alembic current
   ```

2. **Rollback to specific migration:**
   ```bash
   alembic downgrade <migration-id>
   ```

3. **Rollback one step:**
   ```bash
   alembic downgrade -1
   ```

#### Using Flyway (if applicable)

1. **Check migration status:**
   ```bash
   flyway info
   ```

2. **Undo last migration:**
   ```bash
   flyway undo
   ```

### Database Restore from Backup

If migration rollback fails, restore from backup:

```bash
# For PostgreSQL
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < db-backup-<timestamp>.sql

# For Azure SQL
sqlcmd -S $DB_SERVER -d $DB_NAME -i db-backup-<timestamp>.sql
```

## Frontend Rollback

### Vercel Deployment Rollback

1. **Via Vercel Dashboard:**
   - Go to Deployments
   - Find the previous stable deployment
   - Click "Promote to Production"

2. **Via Vercel CLI:**
   ```bash
   vercel rollback <deployment-url>
   ```

### Manual Frontend Rollback

1. **Checkout previous version:**
   ```bash
   git checkout <previous-tag>
   ```

2. **Rebuild and deploy:**
   ```bash
   cd apps/frontend
   pnpm build
   vercel --prod
   ```

## Emergency Procedures

### Complete System Rollback

In case of critical failure affecting multiple services:

1. **Activate incident response team**
2. **Notify stakeholders**
3. **Execute rollback plan:**

```bash
# Rollback all services
for service in chat-service search-service document-service auth-service; do
    ./tools/scripts/rollback.sh $service <stable-version> production
done
```

4. **Verify system health:**
   ```bash
   kubectl get pods -n keiko-production
   kubectl get services -n keiko-production
   ```

### Traffic Routing

If rollback is not immediate, route traffic to backup environment:

1. **Update ingress rules:**
   ```bash
   kubectl apply -f infra/kubernetes/emergency/backup-ingress.yaml
   ```

2. **Update DNS (if needed):**
   - Point to backup environment
   - Reduce TTL for faster propagation

### Circuit Breaker Activation

For gradual rollback:

1. **Enable circuit breaker in gateway:**
   ```bash
   kubectl set env deployment/gateway-bff CIRCUIT_BREAKER_ENABLED=true -n keiko-production
   ```

2. **Configure failure threshold:**
   ```bash
   kubectl set env deployment/gateway-bff FAILURE_THRESHOLD=5 -n keiko-production
   ```

## Post-Rollback Verification

### Health Checks

1. **Service health:**
   ```bash
   for service in chat-service search-service document-service; do
       curl https://api.keiko.com/$service/health
   done
   ```

2. **Database connectivity:**
   ```bash
   # Run health check queries
   psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1;"
   ```

3. **External dependencies:**
   - Azure AI Search
   - Azure Blob Storage
   - OpenAI API
   - Redis Cache

### Monitoring

1. **Check Grafana dashboards:**
   - Service health metrics
   - Error rates
   - Response times

2. **Review Application Insights:**
   - Exception rates
   - Failed requests
   - Performance metrics

3. **Check Prometheus alerts:**
   ```bash
   kubectl port-forward svc/prometheus 9090:9090 -n keiko-system
   # Open http://localhost:9090/alerts
   ```

### Smoke Tests

Run automated smoke tests:

```bash
# E2E tests
cd apps/frontend
pnpm test:e2e

# Integration tests
cd services/chat-service
pytest tests/integration/

# API tests
cd tests/api
./run-smoke-tests.sh
```

### User Communication

1. **Update status page**
2. **Send notification to users**
3. **Post incident report**

## Rollback Decision Matrix

| Severity | Impact | Action | Approval Required |
|----------|--------|--------|-------------------|
| Critical | All users | Immediate rollback | CTO/Lead Engineer |
| High | >50% users | Rollback within 15 min | Team Lead |
| Medium | <50% users | Rollback within 1 hour | On-call Engineer |
| Low | <10% users | Scheduled rollback | Team decision |

## Contact Information

- **On-call Engineer:** [Slack: #keiko-oncall]
- **Team Lead:** [Slack: #keiko-team]
- **CTO:** [Emergency contact]

## Related Documentation

- [Deployment Guide](./DEPLOYMENT.md)
- [Monitoring Guide](./MONITORING.md)
- [Incident Response](./INCIDENT_RESPONSE.md)

