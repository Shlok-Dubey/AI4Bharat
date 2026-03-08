"""
AI Content Generator Agent

This module provides AI-powered content generation for social media campaigns.
Now using AWS Bedrock (Claude) for real AI generation!
"""

import random
from typing import Dict, List, Optional
from datetime import datetime
import os

# Import AWS Bedrock client
try:
    from utils.bedrock_client import generate_social_content_with_bedrock, test_bedrock_connection
    BEDROCK_AVAILABLE = test_bedrock_connection()
except Exception as e:
    print(f"Bedrock not available: {e}")
    BEDROCK_AVAILABLE = False

class ContentGeneratorAgent:
    """
    AI agent for generating social media content.
    
    This agent generates platform-specific content including:
    - Instagram captions and hashtags
    - Reel scripts with timing
    - Thumbnail text overlays
    - Platform-optimized messaging
    
    For AWS Bedrock deployment:
    - Use boto3 to invoke Bedrock models
    - Supported models: Claude, Llama, Titan
    - Implement streaming for long-form content
    """
    
    def __init__(self, model_name: str = "template-v1"):
        """
        Initialize the content generator agent.
        
        Args:
            model_name: Name of the AI model to use
            
        For production:
            model_name options:
            - "gpt-4" for OpenAI
            - "claude-3-sonnet" for Anthropic
            - "anthropic.claude-v2" for AWS Bedrock
            - "meta.llama2-70b" for AWS Bedrock
        """
        self.model_name = model_name
        self.temperature = 0.7
        self.max_tokens = 500
        
        # Initialize AWS Bedrock client (commented for local development)
        # self._init_bedrock_client()
    
    def _init_bedrock_client(self):
        """
        Initialize AWS Bedrock client for production deployment.
        
        Prerequisites:
            pip install boto3
            
        Environment Variables:
            AWS_ACCESS_KEY_ID
            AWS_SECRET_ACCESS_KEY
            AWS_REGION (default: us-east-1)
        
        Example:
            import boto3
            
            self.bedrock_client = boto3.client(
                service_name='bedrock-runtime',
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
        """
        pass
    
    def generate_social_content(
        self,
        product_name: str,
        product_description: str,
        platform: str = "instagram",
        content_type: str = "post",
        tone: str = "engaging",
        target_audience: str = "general"
    ) -> Dict[str, str]:
        """
        Generate social media content for a product.
        
        Now using AWS Bedrock (Claude) for real AI generation!
        Falls back to templates if Bedrock is unavailable.
        
        Args:
            product_name: Name of the product
            product_description: Detailed product description
            platform: Target platform (instagram, facebook, twitter, linkedin)
            content_type: Type of content (post, story, reel, tweet)
            tone: Content tone (engaging, professional, casual, enthusiastic)
            target_audience: Target audience description
            
        Returns:
            Dictionary containing:
            - instagram_caption: Main caption text
            - hashtags: Relevant hashtags
            - reel_script: Video script with timing (for reels)
            - thumbnail_text: Text overlay for thumbnails
        """
        # Try AWS Bedrock first
        if BEDROCK_AVAILABLE:
            try:
                print(f"🤖 Generating content with AWS Bedrock (Claude)...")
                bedrock_content = generate_social_content_with_bedrock(
                    product_name=product_name,
                    product_description=product_description,
                    platform=platform,
                    content_type=content_type,
                    tone=tone
                )
                
                # Map Bedrock response to expected format
                return {
                    "instagram_caption": bedrock_content.get("caption", ""),
                    "hashtags": bedrock_content.get("hashtags", ""),
                    "reel_script": bedrock_content.get("reel_script", ""),
                    "thumbnail_text": bedrock_content.get("thumbnail_text", "")
                }
            except Exception as e:
                print(f"⚠️  Bedrock generation failed, falling back to templates: {e}")
        
        # Fallback to template-based generation
        print(f"📝 Using template-based generation...")
        return self._generate_with_template(
            product_name=product_name,
            product_description=product_description,
            platform=platform,
            content_type=content_type,
            tone=tone
        )
    
    def _generate_with_template(
        self,
        product_name: str,
        product_description: str,
        platform: str,
        content_type: str,
        tone: str
    ) -> Dict[str, str]:
        """
        Generate content using templates (for local development).
        
        This is a placeholder implementation that will be replaced
        with actual AI generation in production.
        """
        # Extract key features from description
        features = self._extract_features(product_description)
        
        # Generate caption based on platform and tone
        caption = self._generate_caption(
            product_name=product_name,
            features=features,
            platform=platform,
            content_type=content_type,
            tone=tone
        )
        
        # Generate hashtags
        hashtags = self._generate_hashtags(
            product_name=product_name,
            platform=platform
        )
        
        # Generate reel script if needed
        reel_script = None
        if content_type == "reel":
            reel_script = self._generate_reel_script(
                product_name=product_name,
                features=features
            )
        
        # Generate thumbnail text
        thumbnail_text = self._generate_thumbnail_text(
            product_name=product_name,
            content_type=content_type
        )
        
        return {
            "instagram_caption": caption,
            "hashtags": hashtags,
            "reel_script": reel_script,
            "thumbnail_text": thumbnail_text
        }
    
    def _generate_with_bedrock(
        self,
        product_name: str,
        product_description: str,
        platform: str,
        content_type: str,
        tone: str
    ) -> Dict[str, str]:
        """
        Generate content using AWS Bedrock (for production).
        
        AWS Bedrock Models:
        - anthropic.claude-v2: Best for creative content
        - anthropic.claude-instant-v1: Faster, good for simple content
        - meta.llama2-70b-chat-v1: Open source alternative
        - amazon.titan-text-express-v1: AWS native model
        
        Example Implementation:
        
        import json
        
        # Construct prompt
        prompt = f'''
        Generate engaging social media content for {platform}.
        
        Product: {product_name}
        Description: {product_description}
        Content Type: {content_type}
        Tone: {tone}
        
        Generate:
        1. A compelling caption (max 2200 characters for Instagram)
        2. 10-15 relevant hashtags
        3. Video script with timing (if reel/video)
        4. Thumbnail text overlay (short, punchy)
        
        Format as JSON:
        {{
            "caption": "...",
            "hashtags": "#tag1 #tag2 ...",
            "script": "...",
            "thumbnail_text": "..."
        }}
        '''
        
        # For Claude models
        body = json.dumps({
            "prompt": f"\\n\\nHuman: {prompt}\\n\\nAssistant:",
            "max_tokens_to_sample": self.max_tokens,
            "temperature": self.temperature,
            "top_p": 0.9,
        })
        
        # Invoke Bedrock model
        response = self.bedrock_client.invoke_model(
            modelId="anthropic.claude-v2",
            contentType="application/json",
            accept="application/json",
            body=body
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        completion = response_body.get('completion', '')
        
        # Extract JSON from completion
        try:
            content_json = json.loads(completion)
            return {
                "instagram_caption": content_json.get("caption", ""),
                "hashtags": content_json.get("hashtags", ""),
                "reel_script": content_json.get("script"),
                "thumbnail_text": content_json.get("thumbnail_text")
            }
        except json.JSONDecodeError:
            # Fallback to template if parsing fails
            return self._generate_with_template(
                product_name, product_description, platform, content_type, tone
            )
        """
        pass
    
    def _extract_features(self, description: str) -> List[str]:
        """Extract key features from product description."""
        # Simple keyword extraction (replace with NLP in production)
        keywords = [
            "sustainable", "eco-friendly", "innovative", "premium",
            "durable", "lightweight", "powerful", "efficient",
            "smart", "advanced", "professional", "quality"
        ]
        
        features = []
        description_lower = description.lower()
        
        for keyword in keywords:
            if keyword in description_lower:
                features.append(keyword)
        
        # Extract first sentence as main feature
        first_sentence = description.split('.')[0] if '.' in description else description
        if len(first_sentence) < 100:
            features.insert(0, first_sentence)
        
        return features[:3]  # Return top 3 features
    
    def _generate_caption(
        self,
        product_name: str,
        features: List[str],
        platform: str,
        content_type: str,
        tone: str
    ) -> str:
        """Generate caption based on platform and tone."""
        # Tone-specific openers
        openers = {
            "engaging": ["✨", "🌟", "💫", "🎉", "🔥"],
            "professional": ["Introducing", "Discover", "Experience", "Elevate"],
            "casual": ["Hey!", "Check this out!", "OMG!", "Guess what?"],
            "enthusiastic": ["Exciting news!", "We're thrilled!", "Amazing!", "Incredible!"]
        }
        
        # Platform-specific templates
        if platform == "instagram":
            if content_type == "post":
                opener = random.choice(openers.get(tone, openers["engaging"]))
                if isinstance(opener, str) and not opener.startswith("✨"):
                    caption = f"{opener} {product_name}! "
                else:
                    caption = f"{opener} Discover {product_name}! "
                
                if features:
                    caption += f"{features[0]}. "
                
                caption += f"Perfect for your lifestyle! 💫\n\n"
                caption += f"Tap the link in bio to learn more! 👆"
                
            elif content_type == "story":
                caption = f"🔥 New Alert! {product_name} is here!\n\nSwipe up to get yours! 👆"
                
            elif content_type == "reel":
                caption = f"Watch how {product_name} transforms your daily routine! 🎬\n\n"
                if features:
                    caption += f"✨ {features[0].capitalize()}\n"
                caption += f"\nSave this for later! 📌"
        
        elif platform == "facebook":
            caption = f"Introducing {product_name}! 🎉\n\n"
            if features:
                caption += f"{features[0].capitalize()}. "
            caption += f"\n\nLearn more and get yours today! Click the link below. 👇"
        
        elif platform == "twitter":
            caption = f"🚀 {product_name} is here! "
            if features:
                caption += f"{features[0]}. "
            caption += f"Learn more 👉"
        
        elif platform == "linkedin":
            caption = f"We're excited to announce {product_name}.\n\n"
            if features:
                caption += f"{features[0].capitalize()}. "
            caption += f"\n\nThis represents our commitment to innovation and quality."
        
        else:
            caption = f"Check out {product_name}! "
            if features:
                caption += f"{features[0]}."
        
        return caption
    
    def _generate_hashtags(self, product_name: str, platform: str) -> str:
        """Generate relevant hashtags."""
        # Base hashtags
        base_tags = ["#product", "#innovation", "#quality", "#lifestyle"]
        
        # Platform-specific hashtags
        platform_tags = {
            "instagram": ["#instagood", "#instadaily", "#trending", "#viral", "#explore"],
            "facebook": ["#newproduct", "#shopping", "#deals"],
            "twitter": ["#tech", "#innovation", "#newlaunch"],
            "linkedin": ["#business", "#innovation", "#productlaunch"]
        }
        
        # Product-specific hashtags (simplified)
        product_words = product_name.lower().split()
        product_tags = [f"#{word}" for word in product_words if len(word) > 3]
        
        # Combine hashtags
        all_tags = base_tags + platform_tags.get(platform, []) + product_tags
        
        # Return random selection
        selected_tags = random.sample(all_tags, min(10, len(all_tags)))
        return " ".join(selected_tags)
    
    def _generate_reel_script(self, product_name: str, features: List[str]) -> str:
        """Generate video script with timing for reels."""
        script = f"""[0-3s] HOOK: Show the problem or pain point
- Quick cut showing frustration or need
- Text overlay: "Struggling with [problem]?"

[3-7s] INTRODUCE: Present {product_name}
- Product reveal with dynamic transition
- Text overlay: "{product_name}"
- Voiceover: "Meet {product_name}"

[7-12s] DEMONSTRATE: Show key features
"""
        
        if features:
            for i, feature in enumerate(features[:2], 1):
                script += f"- Feature {i}: {feature}\n"
        
        script += f"""
[12-15s] CALL TO ACTION
- Show product in use
- Text overlay: "Get Yours Now!"
- End with logo/brand

Music: Upbeat, trending audio
Transitions: Quick cuts, zoom effects
Text: Bold, easy to read"""
        
        return script
    
    def _generate_thumbnail_text(self, product_name: str, content_type: str) -> str:
        """Generate thumbnail text overlay."""
        templates = [
            f"{product_name}\nNow Available",
            f"NEW!\n{product_name}",
            f"{product_name}\nGame Changer",
            f"Introducing\n{product_name}",
            f"{product_name}\nYou Need This"
        ]
        
        if content_type == "reel":
            templates.extend([
                f"Watch This!\n{product_name}",
                f"{product_name}\nReview",
                f"Why {product_name}?"
            ])
        
        return random.choice(templates)
    
    def generate_variations(
        self,
        product_name: str,
        product_description: str,
        platform: str,
        count: int = 3
    ) -> List[Dict[str, str]]:
        """
        Generate multiple content variations.
        
        Args:
            product_name: Name of the product
            product_description: Product description
            platform: Target platform
            count: Number of variations to generate
            
        Returns:
            List of content dictionaries
        """
        variations = []
        tones = ["engaging", "professional", "casual", "enthusiastic"]
        
        for i in range(count):
            tone = tones[i % len(tones)]
            content = self.generate_social_content(
                product_name=product_name,
                product_description=product_description,
                platform=platform,
                tone=tone
            )
            variations.append(content)
        
        return variations


# Singleton instance
_content_generator = None

def get_content_generator() -> ContentGeneratorAgent:
    """
    Get or create the content generator agent instance.
    
    Returns:
        ContentGeneratorAgent instance
    """
    global _content_generator
    if _content_generator is None:
        _content_generator = ContentGeneratorAgent()
    return _content_generator
