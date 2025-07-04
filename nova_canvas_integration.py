#!/usr/bin/env python3
"""
Nova Canvas Integration for Marketing App v2
Cross-region image generation using Nova Canvas from us-east-1
"""

import json
import boto3
import base64
import uuid
import os
from datetime import datetime
from typing import Dict, Optional

class NovaCanvasGenerator:
    """Nova Canvas image generator with cross-region support"""
    
    def __init__(self, s3_bucket: Optional[str] = None):
        """
        Initialize Nova Canvas generator
        
        Args:
            s3_bucket: Optional S3 bucket for storing images
        """
        self.bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.s3_client = boto3.client('s3') if s3_bucket else None
        self.s3_bucket = s3_bucket
        
    def generate_marketing_image(
        self, 
        prompt: str, 
        width: int = 1024, 
        height: int = 1024,
        quality: str = "standard",
        save_to_s3: bool = True,
        save_locally: bool = True
    ) -> Dict:
        """
        Generate marketing image using Nova Canvas
        
        Args:
            prompt: Text description of the image to generate
            width: Image width (default: 1024)
            height: Image height (default: 1024)
            quality: Image quality ("standard" or "premium")
            save_to_s3: Whether to save to S3 bucket
            save_locally: Whether to save locally
            
        Returns:
            Dict with generation results
        """
        
        try:
            # Prepare request
            request_body = {
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {
                    "text": prompt
                },
                "imageGenerationConfig": {
                    "numberOfImages": 1,
                    "quality": quality,
                    "width": width,
                    "height": height
                }
            }
            
            print(f"🎨 Generating image with Nova Canvas...")
            print(f"   Prompt: {prompt[:60]}{'...' if len(prompt) > 60 else ''}")
            print(f"   Dimensions: {width}x{height}")
            
            # Call Nova Canvas in us-east-1
            response = self.bedrock_client.invoke_model(
                modelId='amazon.nova-canvas-v1:0',
                body=json.dumps(request_body),
                contentType='application/json'
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            if 'images' not in response_body or len(response_body['images']) == 0:
                return {'success': False, 'error': 'No image generated'}
            
            # Get image data
            image_data = response_body['images'][0]
            image_bytes = base64.b64decode(image_data)
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"marketing_visual_{timestamp}_{uuid.uuid4().hex[:8]}.png"
            
            results = {
                'success': True,
                'filename': filename,
                'size_bytes': len(image_bytes),
                'dimensions': f"{width}x{height}",
                'prompt': prompt,
                'local_path': None,
                's3_url': None
            }
            
            # Save locally
            if save_locally:
                with open(filename, 'wb') as f:
                    f.write(image_bytes)
                results['local_path'] = os.path.abspath(filename)
                print(f"💾 Saved locally: {filename}")
            
            # Save to S3
            if save_to_s3 and self.s3_client and self.s3_bucket:
                s3_key = f"nova-canvas/{filename}"
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=s3_key,
                    Body=image_bytes,
                    ContentType='image/png'
                )
                results['s3_url'] = f"s3://{self.s3_bucket}/{s3_key}"
                print(f"☁️  Saved to S3: {results['s3_url']}")
            
            print(f"✅ Image generated successfully!")
            print(f"   Size: {len(image_bytes):,} bytes ({len(image_bytes)/(1024*1024):.2f} MB)")
            
            return results
            
        except Exception as e:
            print(f"❌ Error generating image: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def generate_social_media_post(self, prompt: str, format_type: str = "square") -> Dict:
        """Generate social media optimized images"""
        
        formats = {
            "square": (1024, 1024),      # Instagram post
            "story": (1080, 1920),       # Instagram/Facebook story  
            "banner": (1200, 630),       # Facebook cover (will use closest supported)
            "wide": (1024, 512)          # Twitter header (will use closest supported)
        }
        
        if format_type not in formats:
            return {'success': False, 'error': f'Unsupported format: {format_type}'}
        
        width, height = formats[format_type]
        
        # For unsupported dimensions, use closest supported
        if format_type in ["banner", "wide"]:
            width, height = 1024, 1024  # Use square for now
            print(f"⚠️  Using 1024x1024 instead of {formats[format_type]} (closest supported)")
        
        enhanced_prompt = f"Social media {format_type} format: {prompt}"
        
        return self.generate_marketing_image(
            prompt=enhanced_prompt,
            width=width,
            height=height
        )
    
    def generate_marketing_campaign_visuals(self, campaign_info: Dict) -> Dict:
        """Generate a complete set of marketing visuals for a campaign"""
        
        brand = campaign_info.get('brand', 'Brand')
        product = campaign_info.get('product', 'Product')
        style = campaign_info.get('style', 'modern and professional')
        colors = campaign_info.get('colors', 'blue and white')
        
        base_prompt = f"Marketing visual for {brand} {product}, {style} style, {colors} color scheme"
        
        results = {
            'campaign': campaign_info,
            'visuals': {},
            'success': True,
            'errors': []
        }
        
        # Generate different formats
        formats = {
            'social_post': f"{base_prompt}, social media post format",
            'story': f"{base_prompt}, Instagram story format", 
            'banner': f"{base_prompt}, marketing banner format"
        }
        
        for format_name, prompt in formats.items():
            print(f"\n📸 Generating {format_name}...")
            result = self.generate_social_media_post(prompt, "square")  # Use square for all for now
            
            if result['success']:
                results['visuals'][format_name] = result
            else:
                results['errors'].append(f"{format_name}: {result['error']}")
                results['success'] = False
        
        return results

# Example usage
if __name__ == "__main__":
    print("🚀 Nova Canvas Marketing Integration Test")
    print("=" * 50)
    
    # Initialize generator
    generator = NovaCanvasGenerator()
    
    # Test 1: Single image generation
    print("\n📸 Test 1: Single Marketing Image")
    result = generator.generate_marketing_image(
        prompt="Professional tech startup logo, modern minimalist design, blue gradient background",
        width=1024,
        height=1024
    )
    
    if result['success']:
        print(f"✅ Generated: {result['filename']}")
    
    # Test 2: Social media post
    print("\n📱 Test 2: Social Media Post")
    social_result = generator.generate_social_media_post(
        prompt="Exciting product launch announcement, vibrant colors, call-to-action",
        format_type="square"
    )
    
    if social_result['success']:
        print(f"✅ Generated: {social_result['filename']}")
    
    # Test 3: Complete campaign
    print("\n🎯 Test 3: Marketing Campaign Visuals")
    campaign_info = {
        'brand': 'TechCorp',
        'product': 'AI Assistant',
        'style': 'modern and sleek',
        'colors': 'blue and silver'
    }
    
    campaign_result = generator.generate_marketing_campaign_visuals(campaign_info)
    
    if campaign_result['success']:
        print(f"✅ Generated {len(campaign_result['visuals'])} campaign visuals")
        for format_name, visual in campaign_result['visuals'].items():
            print(f"   - {format_name}: {visual['filename']}")
    
    print("\n🎉 Nova Canvas integration test completed!")
    print("💡 You can now integrate this into your marketing app v2")
