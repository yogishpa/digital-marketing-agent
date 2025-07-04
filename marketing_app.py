#!/usr/bin/env python3
"""
Marketing App v2 - Complete Integration
Combines existing Bedrock agents with Nova Canvas cross-region functionality
"""

import streamlit as st
import boto3
import json
import base64
import uuid
import os
from datetime import datetime
from typing import Dict, List, Optional
from nova_canvas_integration import NovaCanvasGenerator

# Configuration
SUPERVISOR_AGENT_ID = "E4NLVBHEHI"  # Your existing supervisor agent
CONTENT_AGENT_ID = "BSESL8XMSK"    # Your existing content agent
VISUAL_AGENT_ID = "EMHWFO0REL"     # Your existing visual agent

# AWS Configuration
AWS_REGION = "us-east-1"  # Where your agents are located
NOVA_CANVAS_REGION = "us-east-1"  # Where Nova Canvas is available

class MarketingAppV2:
    """Complete Marketing App v2 with Nova Canvas integration"""
    
    def __init__(self):
        """Initialize the marketing app with all components"""
        self.bedrock_agent_client = boto3.client('bedrock-agent-runtime', region_name=AWS_REGION)
        self.nova_generator = NovaCanvasGenerator()
        
        # Session state initialization
        if 'campaign_history' not in st.session_state:
            st.session_state.campaign_history = []
        if 'generated_visuals' not in st.session_state:
            st.session_state.generated_visuals = []
    
    def invoke_agent(self, agent_id: str, message: str, session_id: str = None) -> Dict:
        """Invoke a Bedrock agent and return the response"""
        
        if not session_id:
            session_id = f"session_{uuid.uuid4().hex[:8]}"
        
        try:
            response = self.bedrock_agent_client.invoke_agent(
                agentId=agent_id,
                agentAliasId='TSTALIASID',  # Using test alias
                sessionId=session_id,
                inputText=message
            )
            
            # Parse the response
            response_text = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        response_text += chunk['bytes'].decode('utf-8')
            
            return {
                'success': True,
                'response': response_text,
                'session_id': session_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id
            }
    
    def generate_marketing_strategy(self, campaign_brief: Dict) -> Dict:
        """Generate comprehensive marketing strategy using supervisor agent"""
        
        strategy_prompt = f"""
        Create a comprehensive marketing strategy for the following campaign:
        
        Brand: {campaign_brief.get('brand', 'N/A')}
        Product/Service: {campaign_brief.get('product', 'N/A')}
        Target Audience: {campaign_brief.get('audience', 'N/A')}
        Campaign Goals: {campaign_brief.get('goals', 'N/A')}
        Budget Range: {campaign_brief.get('budget', 'N/A')}
        Timeline: {campaign_brief.get('timeline', 'N/A')}
        
        Please provide:
        1. Overall marketing strategy
        2. Content recommendations
        3. Visual content suggestions
        4. Channel recommendations
        5. Success metrics
        """
        
        return self.invoke_agent(SUPERVISOR_AGENT_ID, strategy_prompt)
    
    def generate_content(self, content_brief: str) -> Dict:
        """Generate marketing content using content agent"""
        
        content_prompt = f"""
        Generate marketing content for the following brief:
        {content_brief}
        
        Please provide:
        1. Social media posts (Facebook, Instagram, Twitter)
        2. Email marketing content
        3. Blog post outline
        4. Call-to-action suggestions
        """
        
        return self.invoke_agent(CONTENT_AGENT_ID, content_prompt)
    
    def generate_visual_concepts(self, visual_brief: str) -> Dict:
        """Generate visual concepts using visual agent"""
        
        visual_prompt = f"""
        Create visual content concepts for:
        {visual_brief}
        
        Please provide:
        1. Visual style recommendations
        2. Color palette suggestions
        3. Layout concepts
        4. Image composition ideas
        5. Specific prompts for image generation
        """
        
        return self.invoke_agent(VISUAL_AGENT_ID, visual_prompt)
    
    def generate_campaign_visuals(self, visual_prompts: List[str]) -> List[Dict]:
        """Generate actual images using Nova Canvas"""
        
        results = []
        
        for i, prompt in enumerate(visual_prompts):
            st.write(f"🎨 Generating visual {i+1}/{len(visual_prompts)}...")
            
            # Generate image with Nova Canvas
            result = self.nova_generator.generate_marketing_image(
                prompt=prompt,
                width=1024,
                height=1024,
                save_locally=True,
                save_to_s3=False  # Set to True if you have S3 bucket configured
            )
            
            if result['success']:
                results.append({
                    'prompt': prompt,
                    'filename': result['filename'],
                    'local_path': result['local_path'],
                    'size_mb': result['size_bytes'] / (1024 * 1024)
                })
                
                # Add to session state
                st.session_state.generated_visuals.append(result)
            
        return results
    
    def create_complete_campaign(self, campaign_brief: Dict) -> Dict:
        """Create a complete marketing campaign with strategy, content, and visuals"""
        
        campaign_results = {
            'brief': campaign_brief,
            'strategy': None,
            'content': None,
            'visual_concepts': None,
            'generated_visuals': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Step 1: Generate strategy
        st.write("🎯 Generating marketing strategy...")
        strategy_result = self.generate_marketing_strategy(campaign_brief)
        campaign_results['strategy'] = strategy_result
        
        if not strategy_result['success']:
            st.error(f"Strategy generation failed: {strategy_result['error']}")
            return campaign_results
        
        # Step 2: Generate content
        st.write("📝 Generating marketing content...")
        content_brief = f"Based on this strategy: {strategy_result['response'][:500]}... Create content for {campaign_brief.get('brand')} {campaign_brief.get('product')}"
        content_result = self.generate_content(content_brief)
        campaign_results['content'] = content_result
        
        # Step 3: Generate visual concepts
        st.write("🎨 Generating visual concepts...")
        visual_brief = f"Create visual concepts for {campaign_brief.get('brand')} {campaign_brief.get('product')} targeting {campaign_brief.get('audience')}"
        visual_concepts_result = self.generate_visual_concepts(visual_brief)
        campaign_results['visual_concepts'] = visual_concepts_result
        
        # Step 4: Generate actual visuals (if visual concepts were successful)
        if visual_concepts_result['success']:
            st.write("🖼️ Generating campaign visuals with Nova Canvas...")
            
            # Extract visual prompts from the response (simplified approach)
            sample_prompts = [
                f"Professional marketing banner for {campaign_brief.get('brand')} {campaign_brief.get('product')}, modern design, high quality",
                f"Social media post visual for {campaign_brief.get('brand')}, engaging and vibrant, call-to-action style",
                f"Product showcase image for {campaign_brief.get('product')}, clean background, professional lighting"
            ]
            
            generated_visuals = self.generate_campaign_visuals(sample_prompts)
            campaign_results['generated_visuals'] = generated_visuals
        
        # Save to session state
        st.session_state.campaign_history.append(campaign_results)
        
        return campaign_results

def main():
    """Main Streamlit application"""
    
    st.set_page_config(
        page_title="Marketing App v2 - Complete",
        page_icon="🚀",
        layout="wide"
    )
    
    st.title("🚀 Marketing App v2 - Complete Integration")
    st.markdown("**Powered by Amazon Bedrock Agents + Nova Canvas Cross-Region**")
    
    # Initialize app
    app = MarketingAppV2()
    
    # Sidebar configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        st.write(f"**Supervisor Agent:** {SUPERVISOR_AGENT_ID}")
        st.write(f"**Content Agent:** {CONTENT_AGENT_ID}")
        st.write(f"**Visual Agent:** {VISUAL_AGENT_ID}")
        st.write(f"**Nova Canvas Region:** {NOVA_CANVAS_REGION}")
        
        st.header("📊 Session Stats")
        st.metric("Campaigns Created", len(st.session_state.campaign_history))
        st.metric("Visuals Generated", len(st.session_state.generated_visuals))
    
    # Main interface
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Campaign Creator", "📝 Content Generator", "🎨 Visual Generator", "📈 Campaign History"])
    
    with tab1:
        st.header("🎯 Complete Campaign Creator")
        st.markdown("Create a comprehensive marketing campaign with strategy, content, and visuals")
        
        with st.form("campaign_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                brand = st.text_input("Brand Name", placeholder="e.g., TechCorp")
                product = st.text_input("Product/Service", placeholder="e.g., AI Assistant")
                audience = st.text_input("Target Audience", placeholder="e.g., Tech professionals, 25-45")
            
            with col2:
                goals = st.text_area("Campaign Goals", placeholder="e.g., Increase brand awareness, Generate leads")
                budget = st.text_input("Budget Range", placeholder="e.g., $10K - $50K")
                timeline = st.text_input("Timeline", placeholder="e.g., 3 months")
            
            submitted = st.form_submit_button("🚀 Create Complete Campaign")
            
            if submitted and brand and product:
                campaign_brief = {
                    'brand': brand,
                    'product': product,
                    'audience': audience,
                    'goals': goals,
                    'budget': budget,
                    'timeline': timeline
                }
                
                with st.spinner("Creating your complete marketing campaign..."):
                    results = app.create_complete_campaign(campaign_brief)
                
                # Display results
                st.success("🎉 Campaign created successfully!")
                
                # Strategy
                if results['strategy'] and results['strategy']['success']:
                    st.subheader("🎯 Marketing Strategy")
                    st.write(results['strategy']['response'])
                
                # Content
                if results['content'] and results['content']['success']:
                    st.subheader("📝 Marketing Content")
                    st.write(results['content']['response'])
                
                # Visual Concepts
                if results['visual_concepts'] and results['visual_concepts']['success']:
                    st.subheader("🎨 Visual Concepts")
                    st.write(results['visual_concepts']['response'])
                
                # Generated Visuals
                if results['generated_visuals']:
                    st.subheader("🖼️ Generated Visuals")
                    cols = st.columns(min(3, len(results['generated_visuals'])))
                    
                    for i, visual in enumerate(results['generated_visuals']):
                        with cols[i % 3]:
                            if os.path.exists(visual['filename']):
                                st.image(visual['filename'], caption=f"Visual {i+1}")
                                st.caption(f"Size: {visual['size_mb']:.2f} MB")
                                st.caption(f"Prompt: {visual['prompt'][:50]}...")
    
    with tab2:
        st.header("📝 Content Generator")
        st.markdown("Generate marketing content using your content agent")
        
        content_brief = st.text_area(
            "Content Brief",
            placeholder="Describe what type of content you need...",
            height=100
        )
        
        if st.button("📝 Generate Content"):
            if content_brief:
                with st.spinner("Generating content..."):
                    result = app.generate_content(content_brief)
                
                if result['success']:
                    st.success("Content generated successfully!")
                    st.write(result['response'])
                else:
                    st.error(f"Content generation failed: {result['error']}")
    
    with tab3:
        st.header("🎨 Visual Generator")
        st.markdown("Generate visual concepts and actual images")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Visual Concepts")
            visual_brief = st.text_area(
                "Visual Brief",
                placeholder="Describe the visual style and requirements...",
                height=100
            )
            
            if st.button("🎨 Generate Visual Concepts"):
                if visual_brief:
                    with st.spinner("Generating visual concepts..."):
                        result = app.generate_visual_concepts(visual_brief)
                    
                    if result['success']:
                        st.success("Visual concepts generated!")
                        st.write(result['response'])
                    else:
                        st.error(f"Visual concept generation failed: {result['error']}")
        
        with col2:
            st.subheader("Nova Canvas Image Generation")
            image_prompt = st.text_area(
                "Image Prompt",
                placeholder="Describe the image you want to generate...",
                height=100
            )
            
            if st.button("🖼️ Generate Image with Nova Canvas"):
                if image_prompt:
                    with st.spinner("Generating image with Nova Canvas..."):
                        result = app.nova_generator.generate_marketing_image(
                            prompt=image_prompt,
                            width=1024,
                            height=1024
                        )
                    
                    if result['success']:
                        st.success("Image generated successfully!")
                        if os.path.exists(result['filename']):
                            st.image(result['filename'], caption="Generated Image")
                            st.write(f"**File:** {result['filename']}")
                            st.write(f"**Size:** {result['size_bytes'] / (1024*1024):.2f} MB")
                    else:
                        st.error(f"Image generation failed: {result['error']}")
    
    with tab4:
        st.header("📈 Campaign History")
        
        if st.session_state.campaign_history:
            for i, campaign in enumerate(reversed(st.session_state.campaign_history)):
                with st.expander(f"Campaign {len(st.session_state.campaign_history) - i}: {campaign['brief'].get('brand', 'Unknown')} - {campaign['brief'].get('product', 'Unknown')}"):
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Campaign Brief:**")
                        st.json(campaign['brief'])
                    
                    with col2:
                        st.write("**Generated Visuals:**")
                        if campaign['generated_visuals']:
                            for visual in campaign['generated_visuals']:
                                if os.path.exists(visual['filename']):
                                    st.image(visual['filename'], width=200)
                        else:
                            st.write("No visuals generated")
        else:
            st.info("No campaigns created yet. Use the Campaign Creator tab to get started!")

if __name__ == "__main__":
    main()
