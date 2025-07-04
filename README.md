# Marketing App

A comprehensive marketing application built with AWS services, featuring AI-powered content generation and visual creation capabilities using Amazon Bedrock Agents and Nova Canvas.

## Features

- AI-powered marketing content generation using Amazon Bedrock Agents
- Visual content creation using Amazon Nova Canvas
- Cross-region AWS service integration
- Modern class-based architecture
- Streamlit-based web interface
- Complete campaign creation workflow

## Project Structure

```
├── marketing_app.py                    # Main marketing application
├── nova_canvas_integration.py          # Amazon Nova Canvas integration
├── infrastructure.yaml                 # Complete AWS infrastructure (CloudFormation)
├── deploy.sh                          # Infrastructure deployment script
├── marketing-app-config.env.template   # Configuration template
├── marketing-app-config-complete.env.template  # Complete config template
├── requirements.txt                     # Python dependencies
└── MARKETING_APP_DEPLOYMENT.md         # Deployment documentation
```

## Quick Start

1. **Clone this repository**
   ```bash
   git clone <your-repo-url>
   cd marketing_app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp marketing-app-config-complete.env.template .env
   # Edit .env with your AWS configuration
   ```

4. **Deploy AWS infrastructure**
   ```bash
   ./deploy.sh
   ```

5. **Run the application**
   ```bash
   streamlit run marketing_app.py
   ```

## Configuration

Use the provided template files to configure your environment:
- `marketing-app-config.env.template` - Basic configuration
- `marketing-app-config-complete.env.template` - Complete configuration with all options

## AWS Services Used

- **Amazon Bedrock Agents** - AI-powered content generation
- **Amazon Nova Canvas** - Visual content creation
- **Amazon S3** - Storage for generated assets
- **AWS IAM** - Access management

## Deployment

Refer to the deployment guide:
- `MARKETING_APP_DEPLOYMENT.md` - Complete deployment instructions

## Requirements

- Python 3.8+
- AWS CLI configured with appropriate permissions
- Access to Amazon Bedrock and Nova Canvas services

## Architecture

The application uses a modern class-based architecture with:
- `MarketingAppV2` - Main application class
- `NovaCanvasGenerator` - Cross-region image generation
- Streamlit interface with tabbed navigation
- Session state management for campaign history

## Usage

1. **Campaign Creator** - Create comprehensive marketing campaigns
2. **Content Generator** - Generate marketing content using AI
3. **Visual Generator** - Create visuals with Nova Canvas
4. **Campaign History** - View and manage past campaigns
