#!/bin/bash

# AI Marketing Campaign Generator - Complete Infrastructure Deployment Script
# This script deploys the complete infrastructure including Bedrock agents and knowledge base

set -e

# Default values
STACK_NAME="marketing-agent-app-complete"
REGION="us-east-1"
ENVIRONMENT="dev"
PROJECT_NAME="marketing-agent-app"
BUCKET_NAME=""
KB_DATA_BUCKET=""
ENABLE_LOGS="true"
VALIDATE_ONLY=false
DELETE_STACK=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_help() {
    cat << EOF
AI Marketing Campaign Generator - Complete Infrastructure Deployment

Usage: $0 [OPTIONS]

Options:
    -s, --stack-name NAME       CloudFormation stack name (default: marketing-agent-app-complete)
    -r, --region REGION         AWS region (default: us-east-1)
    -e, --environment ENV       Environment (dev/staging/prod) (default: dev)
    -p, --project-name NAME     Project name prefix (default: marketing-agent-app)
    -b, --bucket-name NAME      Custom S3 bucket name (optional)
    -k, --kb-bucket NAME        Knowledge base data source bucket (optional)
    --no-logs                   Disable CloudWatch logging
    --validate-only             Only validate the template
    --delete                    Delete the stack
    -h, --help                  Show this help message

Examples:
    # Basic deployment
    $0

    # Production deployment in us-west-2
    $0 -e prod -r us-west-2

    # Custom configuration
    $0 -s my-marketing-stack -b my-custom-bucket -k my-kb-bucket

    # Validate template only
    $0 --validate-only

    # Delete stack
    $0 --delete

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -p|--project-name)
            PROJECT_NAME="$2"
            shift 2
            ;;
        -b|--bucket-name)
            BUCKET_NAME="$2"
            shift 2
            ;;
        -k|--kb-bucket)
            KB_DATA_BUCKET="$2"
            shift 2
            ;;
        --no-logs)
            ENABLE_LOGS="false"
            shift
            ;;
        --validate-only)
            VALIDATE_ONLY=true
            shift
            ;;
        --delete)
            DELETE_STACK=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    print_error "Environment must be one of: dev, staging, prod"
    exit 1
fi

# Check if AWS CLI is installed and configured
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity --region "$REGION" &> /dev/null; then
    print_error "AWS credentials not configured or invalid for region $REGION"
    exit 1
fi

# Get current AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --region "$REGION")
print_status "Using AWS Account: $ACCOUNT_ID in region: $REGION"

# Template file
TEMPLATE_FILE="infrastructure.yaml"

# Check if template file exists
if [[ ! -f "$TEMPLATE_FILE" ]]; then
    print_error "Template file $TEMPLATE_FILE not found!"
    exit 1
fi

# Function to delete stack
delete_stack() {
    print_status "Deleting CloudFormation stack: $STACK_NAME"
    
    if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &> /dev/null; then
        aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$REGION"
        print_status "Waiting for stack deletion to complete..."
        aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" --region "$REGION"
        print_success "Stack $STACK_NAME deleted successfully!"
    else
        print_warning "Stack $STACK_NAME does not exist"
    fi
}

# Function to validate template
validate_template() {
    print_status "Validating CloudFormation template..."
    if aws cloudformation validate-template --template-body file://"$TEMPLATE_FILE" --region "$REGION" > /dev/null; then
        print_success "Template validation successful!"
        return 0
    else
        print_error "Template validation failed!"
        return 1
    fi
}

# Function to check if Bedrock models are available
check_bedrock_models() {
    print_status "Checking Bedrock model availability in region $REGION..."
    
    # Check for required models
    local models=("anthropic.claude-3-haiku-20240307-v1:0" "amazon.titan-embed-text-v2:0")
    local nova_models=("amazon.nova-premier-v1:0" "amazon.nova-canvas-v1:0")
    
    for model in "${models[@]}"; do
        if aws bedrock list-foundation-models --region "$REGION" --query "modelSummaries[?modelId=='$model']" --output text | grep -q "$model"; then
            print_success "Model $model is available"
        else
            print_warning "Model $model may not be available in $REGION"
        fi
    done
    
    # Check Nova models (may require special access)
    for model in "${nova_models[@]}"; do
        print_status "Note: $model requires Amazon Nova access in $REGION"
    done
}

# Function to deploy stack
deploy_stack() {
    print_status "Deploying CloudFormation stack: $STACK_NAME"
    
    # Build parameters
    local params=""
    params+="ParameterKey=ProjectName,ParameterValue=$PROJECT_NAME "
    params+="ParameterKey=Environment,ParameterValue=$ENVIRONMENT "
    params+="ParameterKey=EnableCloudWatchLogs,ParameterValue=$ENABLE_LOGS "
    
    if [[ -n "$BUCKET_NAME" ]]; then
        params+="ParameterKey=BucketName,ParameterValue=$BUCKET_NAME "
    fi
    
    if [[ -n "$KB_DATA_BUCKET" ]]; then
        params+="ParameterKey=KnowledgeBaseDataSourceBucket,ParameterValue=$KB_DATA_BUCKET "
    fi
    
    # Check if stack exists
    if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &> /dev/null; then
        print_status "Stack exists, updating..."
        aws cloudformation update-stack \
            --stack-name "$STACK_NAME" \
            --template-body file://"$TEMPLATE_FILE" \
            --parameters $params \
            --capabilities CAPABILITY_NAMED_IAM \
            --region "$REGION" || {
                if [[ $? -eq 255 ]]; then
                    print_warning "No updates to be performed"
                    return 0
                else
                    print_error "Stack update failed"
                    return 1
                fi
            }
        
        print_status "Waiting for stack update to complete..."
        aws cloudformation wait stack-update-complete --stack-name "$STACK_NAME" --region "$REGION"
    else
        print_status "Creating new stack..."
        aws cloudformation create-stack \
            --stack-name "$STACK_NAME" \
            --template-body file://"$TEMPLATE_FILE" \
            --parameters $params \
            --capabilities CAPABILITY_NAMED_IAM \
            --region "$REGION"
        
        print_status "Waiting for stack creation to complete..."
        aws cloudformation wait stack-create-complete --stack-name "$STACK_NAME" --region "$REGION"
    fi
    
    print_success "Stack deployment completed successfully!"
}

# Function to show stack outputs
show_outputs() {
    print_status "Retrieving stack outputs..."
    
    local outputs
    outputs=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs' \
        --output table)
    
    if [[ -n "$outputs" ]]; then
        echo "$outputs"
        
        # Generate configuration file
        print_status "Generating configuration file..."
        generate_config_file
    else
        print_warning "No outputs found for stack $STACK_NAME"
    fi
}

# Function to generate configuration file
generate_config_file() {
    local config_file=".env"
    local temp_config="marketing-app-config-complete.env.template"
    
    if [[ -f "$temp_config" ]]; then
        cp "$temp_config" "$config_file"
        
        # Get stack outputs and replace placeholders
        local bucket_name
        bucket_name=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' \
            --output text 2>/dev/null || echo "")
        
        local supervisor_agent_id
        supervisor_agent_id=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`SupervisorAgentId`].OutputValue' \
            --output text 2>/dev/null || echo "")
        
        local content_agent_id
        content_agent_id=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`ContentAgentId`].OutputValue' \
            --output text 2>/dev/null || echo "")
        
        local visual_agent_id
        visual_agent_id=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`VisualAgentId`].OutputValue' \
            --output text 2>/dev/null || echo "")
        
        local kb_id
        kb_id=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`KnowledgeBaseId`].OutputValue' \
            --output text 2>/dev/null || echo "")
        
        local log_group
        log_group=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`LogGroupName`].OutputValue' \
            --output text 2>/dev/null || echo "")
        
        # Replace placeholders
        sed -i.bak \
            -e "s|AWS_REGION=us-east-1|AWS_REGION=$REGION|g" \
            -e "s|<GET_FROM_STACK_OUTPUT_S3BucketName>|$bucket_name|g" \
            -e "s|<GET_FROM_STACK_OUTPUT_SupervisorAgentId>|$supervisor_agent_id|g" \
            -e "s|<GET_FROM_STACK_OUTPUT_ContentAgentId>|$content_agent_id|g" \
            -e "s|<GET_FROM_STACK_OUTPUT_VisualAgentId>|$visual_agent_id|g" \
            -e "s|<GET_FROM_STACK_OUTPUT_KnowledgeBaseId>|$kb_id|g" \
            -e "s|<GET_FROM_STACK_OUTPUT_LogGroupName>|$log_group|g" \
            "$config_file"
        
        rm -f "$config_file.bak"
        print_success "Configuration file generated: $config_file"
        
        # Show important values
        echo ""
        print_status "Important Configuration Values:"
        echo "S3 Bucket: $bucket_name"
        echo "Supervisor Agent ID: $supervisor_agent_id"
        echo "Content Agent ID: $content_agent_id"
        echo "Visual Agent ID: $visual_agent_id"
        echo "Knowledge Base ID: $kb_id"
        echo "Region: $REGION"
    else
        print_warning "Configuration template not found: $temp_config"
    fi
}

# Main execution
main() {
    print_status "AI Marketing Campaign Generator - Complete Infrastructure Deployment"
    print_status "Stack: $STACK_NAME | Region: $REGION | Environment: $ENVIRONMENT"
    
    # Handle delete operation
    if [[ "$DELETE_STACK" == true ]]; then
        delete_stack
        exit 0
    fi
    
    # Validate template
    if ! validate_template; then
        exit 1
    fi
    
    # Check Bedrock models
    check_bedrock_models
    
    # Handle validate-only operation
    if [[ "$VALIDATE_ONLY" == true ]]; then
        print_success "Template validation completed successfully!"
        exit 0
    fi
    
    # Deploy stack
    if deploy_stack; then
        show_outputs
        
        echo ""
        print_success "Deployment completed successfully!"
        print_status "Next steps:"
        echo "1. Review the generated .env file"
        echo "2. Upload knowledge base documents to S3 bucket under 'knowledge-base/' prefix"
        echo "3. Sync the knowledge base data source"
        echo "4. Run your marketing application: streamlit run marketing_agent_app_v2.py"
        
        # Show knowledge base sync command
        local kb_id
        kb_id=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`KnowledgeBaseId`].OutputValue' \
            --output text 2>/dev/null || echo "")
        
        if [[ -n "$kb_id" ]]; then
            echo ""
            print_status "To sync knowledge base data:"
            echo "aws bedrock-agent start-ingestion-job --knowledge-base-id $kb_id --data-source-id <data-source-id> --region $REGION"
        fi
    else
        print_error "Deployment failed!"
        exit 1
    fi
}

# Run main function
main
