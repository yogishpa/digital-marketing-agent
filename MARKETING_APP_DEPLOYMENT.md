# AI Marketing Campaign Generator - Infrastructure Deployment Guide

This guide provides step-by-step instructions to deploy the complete AWS infrastructure required for the AI Marketing Campaign Generator application.

## 📋 Prerequisites

Before deploying, ensure you have:

1. **AWS CLI installed and configured**
   ```bash
   aws --version
   aws configure list
   ```

2. **Appropriate AWS permissions** for:
   - CloudFormation (full access)
   - IAM (create roles, policies, users)
   - S3 (create and manage buckets)
   - Amazon Bedrock (invoke models and agents)
   - CloudWatch (create log groups and dashboards)

3. **Python 3.9+ and required packages**
   ```bash
   pip install -r requirements.txt
   ```

## 🏗️ Infrastructure Components

The CloudFormation template creates:

### Core Resources
- **S3 Bucket**: Stores marketing assets and generated content
- **IAM Role**: Execution role for EC2/ECS/Lambda with Bedrock permissions
- **IAM User**: Developer user for local testing
- **Security Group**: Network access rules for the application

### Monitoring & Logging
- **CloudWatch Log Group**: Application logging
- **CloudWatch Dashboard**: Monitoring and metrics
- **Log Streams**: Organized log collection

### Security Features
- **Encrypted S3 bucket** with versioning
- **Least privilege IAM policies**
- **Public access blocked** on S3
- **Secure access keys** for development

## 🚀 Quick Deployment

### Step 1: Deploy Infrastructure

```bash
# Basic deployment with defaults
./deploy-marketing-infrastructure.sh

# Production deployment
./deploy-marketing-infrastructure.sh -e prod -r us-west-2

# Custom bucket name
./deploy-marketing-infrastructure.sh -b my-marketing-assets-bucket
```

### Step 2: Configure Application

1. **Copy the configuration template:**
   ```bash
   cp marketing-app-config.env.template .env
   ```

2. **Update the `.env` file** with values from CloudFormation outputs:
   ```bash
   # Get the S3 bucket name from stack outputs
   aws cloudformation describe-stacks \
     --stack-name marketing-agent-app-infrastructure \
     --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' \
     --output text
   ```

### Step 3: Run the Application

```bash
# Load environment variables
source .env

# Start the Streamlit app
streamlit run marketing_agent_app_v2.py
```

## 📖 Detailed Deployment Options

### Command Line Options

```bash
./deploy-marketing-infrastructure.sh [OPTIONS]

Options:
  -s, --stack-name NAME     CloudFormation stack name
  -r, --region REGION       AWS region (default: us-east-1)
  -e, --environment ENV     Environment (dev/staging/prod)
  -p, --project-name NAME   Project name prefix
  -b, --bucket-name NAME    Custom S3 bucket name
  --no-logs                 Disable CloudWatch logging
  --validate-only           Only validate the template
  --delete                  Delete the stack
  -h, --help                Show help message
```

### Environment-Specific Deployments

#### Development Environment
```bash
./deploy-marketing-infrastructure.sh -e dev
```

#### Staging Environment
```bash
./deploy-marketing-infrastructure.sh -e staging -r us-west-2
```

#### Production Environment
```bash
./deploy-marketing-infrastructure.sh -e prod -r us-west-2 --project-name marketing-prod
```

## 🔧 Configuration Management

### Environment Variables

After deployment, configure these key variables:

```bash
# AWS Configuration
export AWS_REGION=us-east-1
export S3_BUCKET_NAME=your-bucket-name-from-outputs

# Bedrock Agents (from your app configuration)
export SUPERVISOR_AGENT_ID=E4NLVBHEHI
export CONTENT_AGENT_ID=BSESL8XMSK
export VISUAL_AGENT_ID=EMHWFO0REL

# CloudWatch Logging
export LOG_GROUP_NAME=/aws/marketing-app/marketing-agent-app-dev
```

### AWS Credentials Setup

#### For Local Development
Use the developer user credentials from CloudFormation outputs:

```bash
# Get credentials from stack outputs
aws cloudformation describe-stacks \
  --stack-name marketing-agent-app-infrastructure \
  --query 'Stacks[0].Outputs[?OutputKey==`DeveloperAccessKeyId`].OutputValue' \
  --output text

# Configure AWS CLI profile
aws configure --profile marketing-app
```

#### For EC2/ECS Deployment
Use the IAM role created by the stack:

```bash
# Get the role ARN
aws cloudformation describe-stacks \
  --stack-name marketing-agent-app-infrastructure \
  --query 'Stacks[0].Outputs[?OutputKey==`ExecutionRoleArn`].OutputValue' \
  --output text
```

## 🖥️ Application Deployment Options

### Option 1: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
source .env

# Run locally
streamlit run marketing_agent_app_v2.py --server.port 8501
```

### Option 2: EC2 Deployment

```bash
# Launch EC2 instance with the created IAM role
aws ec2 run-instances \
  --image-id ami-0abcdef1234567890 \
  --instance-type t3.medium \
  --iam-instance-profile Name=marketing-agent-app-dev-instance-profile \
  --security-group-ids sg-xxxxxxxxx \
  --user-data file://user-data-script.sh
```

### Option 3: ECS Deployment

Create an ECS task definition using the execution role:

```json
{
  "family": "marketing-agent-app",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/marketing-agent-app-dev-execution-role",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/marketing-agent-app-dev-execution-role",
  "containerDefinitions": [
    {
      "name": "marketing-app",
      "image": "your-marketing-app-image",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "AWS_REGION",
          "value": "us-east-1"
        },
        {
          "name": "S3_BUCKET_NAME",
          "value": "your-bucket-name"
        }
      ]
    }
  ]
}
```

## 📊 Monitoring and Logging

### CloudWatch Dashboard

Access your monitoring dashboard:
```bash
# Get dashboard URL from stack outputs
aws cloudformation describe-stacks \
  --stack-name marketing-agent-app-infrastructure \
  --query 'Stacks[0].Outputs[?OutputKey==`DashboardURL`].OutputValue' \
  --output text
```

### Log Monitoring

```bash
# View recent logs
aws logs tail /aws/marketing-app/marketing-agent-app-dev --follow

# Search logs
aws logs filter-log-events \
  --log-group-name /aws/marketing-app/marketing-agent-app-dev \
  --filter-pattern "ERROR"
```

## 🔒 Security Best Practices

### 1. Secure Credentials Management

```bash
# Store sensitive credentials in AWS Secrets Manager
aws secretsmanager create-secret \
  --name marketing-app/dev/credentials \
  --description "Marketing app credentials" \
  --secret-string '{"access_key":"xxx","secret_key":"xxx"}'
```

### 2. Network Security

- Use the created security group for controlled access
- Consider VPC deployment for production
- Enable VPC Flow Logs for network monitoring

### 3. S3 Security

- Bucket encryption is enabled by default
- Public access is blocked
- Versioning is enabled for data protection

## 🧹 Cleanup and Maintenance

### Delete Infrastructure

```bash
# Delete the entire stack
./deploy-marketing-infrastructure.sh --delete

# Or manually delete
aws cloudformation delete-stack --stack-name marketing-agent-app-infrastructure
```

### Cost Optimization

1. **S3 Lifecycle Policies**: Automatically configured to delete old versions
2. **CloudWatch Log Retention**: Set to 14 days by default
3. **Resource Tagging**: All resources are tagged for cost tracking

### Backup Strategy

```bash
# Backup S3 bucket
aws s3 sync s3://your-marketing-bucket s3://your-backup-bucket

# Export CloudFormation template
aws cloudformation get-template \
  --stack-name marketing-agent-app-infrastructure \
  --template-stage Processed > backup-template.json
```

## 🐛 Troubleshooting

### Common Issues

1. **Permission Denied Errors**
   ```bash
   # Check IAM permissions
   aws iam simulate-principal-policy \
     --policy-source-arn arn:aws:iam::ACCOUNT:role/marketing-agent-app-dev-execution-role \
     --action-names bedrock:InvokeModel \
     --resource-arns "*"
   ```

2. **Bedrock Access Issues**
   ```bash
   # Verify Bedrock model access
   aws bedrock list-foundation-models --region us-east-1
   ```

3. **S3 Access Issues**
   ```bash
   # Test S3 access
   aws s3 ls s3://your-bucket-name
   ```

### Stack Deployment Failures

```bash
# Check stack events for errors
aws cloudformation describe-stack-events \
  --stack-name marketing-agent-app-infrastructure

# Validate template before deployment
./deploy-marketing-infrastructure.sh --validate-only
```

## 📞 Support

For issues with:
- **AWS Infrastructure**: Check CloudFormation events and AWS documentation
- **Application Code**: Review application logs in CloudWatch
- **Bedrock Agents**: Verify agent IDs and aliases in the AWS console

## 🔄 Updates and Maintenance

### Updating the Stack

```bash
# Update with new parameters
./deploy-marketing-infrastructure.sh -e prod --bucket-name new-bucket-name
```

### Monitoring Costs

```bash
# Check current month costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE
```

This infrastructure setup provides a robust, scalable, and secure foundation for your AI Marketing Campaign Generator application.
