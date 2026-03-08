"""
Test script for AI Content Generator Agent.
Tests the agent's content generation capabilities.

Usage:
    python test_agent.py
"""

import sys
sys.path.append('backend')

from agents.content_generator import ContentGeneratorAgent

def test_instagram_post():
    """Test Instagram post generation"""
    print("\n=== Testing Instagram Post Generation ===")
    
    agent = ContentGeneratorAgent()
    
    content = agent.generate_social_content(
        product_name="EcoBottle Pro",
        product_description="A sustainable, insulated water bottle made from recycled materials. Keeps drinks cold for 24 hours and hot for 12 hours. Perfect for outdoor enthusiasts.",
        platform="instagram",
        content_type="post",
        tone="engaging"
    )
    
    print(f"\nCaption:\n{content['instagram_caption']}")
    print(f"\nHashtags:\n{content['hashtags']}")
    print(f"\nThumbnail Text:\n{content['thumbnail_text']}")

def test_instagram_reel():
    """Test Instagram reel generation"""
    print("\n=== Testing Instagram Reel Generation ===")
    
    agent = ContentGeneratorAgent()
    
    content = agent.generate_social_content(
        product_name="SmartWatch Pro",
        product_description="Advanced smartwatch with health tracking, GPS, and 7-day battery life. Features include heart rate monitoring, sleep tracking, and workout detection.",
        platform="instagram",
        content_type="reel",
        tone="enthusiastic"
    )
    
    print(f"\nCaption:\n{content['instagram_caption']}")
    print(f"\nHashtags:\n{content['hashtags']}")
    print(f"\nReel Script:\n{content['reel_script']}")
    print(f"\nThumbnail Text:\n{content['thumbnail_text']}")

def test_multiple_platforms():
    """Test content generation for multiple platforms"""
    print("\n=== Testing Multiple Platforms ===")
    
    agent = ContentGeneratorAgent()
    
    product_name = "Wireless Earbuds X"
    product_description = "Premium wireless earbuds with active noise cancellation, 30-hour battery life, and crystal-clear sound quality."
    
    platforms = ["instagram", "facebook", "twitter", "linkedin"]
    
    for platform in platforms:
        print(f"\n--- {platform.upper()} ---")
        content = agent.generate_social_content(
            product_name=product_name,
            product_description=product_description,
            platform=platform,
            content_type="post"
        )
        print(f"Caption: {content['instagram_caption'][:100]}...")
        print(f"Hashtags: {content['hashtags'][:50]}...")

def test_variations():
    """Test generating multiple variations"""
    print("\n=== Testing Content Variations ===")
    
    agent = ContentGeneratorAgent()
    
    variations = agent.generate_variations(
        product_name="Fitness Tracker",
        product_description="Track your fitness goals with precision. Monitor steps, calories, heart rate, and sleep patterns.",
        platform="instagram",
        count=3
    )
    
    for i, content in enumerate(variations, 1):
        print(f"\n--- Variation {i} ---")
        print(f"Caption: {content['instagram_caption'][:80]}...")
        print(f"Hashtags: {content['hashtags'][:40]}...")

def test_different_tones():
    """Test different content tones"""
    print("\n=== Testing Different Tones ===")
    
    agent = ContentGeneratorAgent()
    
    tones = ["engaging", "professional", "casual", "enthusiastic"]
    
    for tone in tones:
        print(f"\n--- {tone.upper()} Tone ---")
        content = agent.generate_social_content(
            product_name="Laptop Stand",
            product_description="Ergonomic laptop stand for better posture and productivity.",
            platform="instagram",
            content_type="post",
            tone=tone
        )
        print(f"Caption: {content['instagram_caption'][:100]}...")

def main():
    print("="*60)
    print("AI Content Generator Agent - Test Suite")
    print("="*60)
    
    # Run tests
    test_instagram_post()
    test_instagram_reel()
    test_multiple_platforms()
    test_variations()
    test_different_tones()
    
    print("\n" + "="*60)
    print("✅ All agent tests completed!")
    print("="*60)
    
    print("\nAgent Features Tested:")
    print("  ✓ Instagram post generation")
    print("  ✓ Instagram reel with script")
    print("  ✓ Multi-platform support")
    print("  ✓ Content variations")
    print("  ✓ Different tones")
    
    print("\nNext Steps:")
    print("  1. Integrate with OpenAI/Anthropic API")
    print("  2. Implement AWS Bedrock for production")
    print("  3. Add content moderation")
    print("  4. Implement caching")
    print("  5. Add A/B testing for variations")

if __name__ == "__main__":
    main()
