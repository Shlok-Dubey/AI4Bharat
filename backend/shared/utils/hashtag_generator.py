"""
Hashtag generation utility for campaign content.

Generates hashtags from suggested tags, product labels, and fixed brand hashtags.
"""

from typing import List, Optional


def generate_hashtags(
    suggested_hashtags: List[str],
    product_labels: Optional[List[str]] = None,
    max_hashtags: int = 10
) -> List[str]:
    """
    Generate hashtags for a campaign.
    
    Algorithm:
    1. Convert suggested hashtags to lowercase, remove spaces, prefix with #
    2. Add label-based hashtags from top 3 product labels
    3. Add fixed brand hashtags (#smallbusiness, #shoponline, #supportlocal)
    4. Remove duplicates (case-insensitive)
    5. Limit to max_hashtags total
    
    Args:
        suggested_hashtags: List of hashtag suggestions (with or without #)
        product_labels: Optional list of product labels from image analysis
        max_hashtags: Maximum number of hashtags to return (default 10)
    
    Returns:
        List of formatted hashtags (with # prefix)
    
    Examples:
        >>> generate_hashtags(["fashion", "style"], ["Clothing", "Dress"])
        ['#fashion', '#style', '#clothing', '#dress', '#smallbusiness', '#shoponline', '#supportlocal']
        
        >>> generate_hashtags(["#tech", "gadgets"], ["Electronics"])
        ['#tech', '#gadgets', '#electronics', '#smallbusiness', '#shoponline', '#supportlocal']
    """
    hashtags = []
    seen = set()  # Track lowercase versions for case-insensitive deduplication
    
    # Fixed brand hashtags
    brand_hashtags = ["#smallbusiness", "#shoponline", "#supportlocal"]
    
    # Process suggested hashtags
    for tag in suggested_hashtags:
        # Remove # if present, strip whitespace, convert to lowercase
        clean_tag = tag.strip().lstrip('#').replace(' ', '').lower()
        
        if clean_tag and clean_tag not in seen:
            hashtags.append(f"#{clean_tag}")
            seen.add(clean_tag)
    
    # Add label-based hashtags from top 3 product labels
    if product_labels:
        for label in product_labels[:3]:
            clean_label = label.strip().replace(' ', '').lower()
            
            if clean_label and clean_label not in seen:
                hashtags.append(f"#{clean_label}")
                seen.add(clean_label)
    
    # Add fixed brand hashtags
    for brand_tag in brand_hashtags:
        clean_brand = brand_tag.lstrip('#').lower()
        
        if clean_brand not in seen:
            hashtags.append(brand_tag)
            seen.add(clean_brand)
    
    # Limit to max_hashtags
    return hashtags[:max_hashtags]
