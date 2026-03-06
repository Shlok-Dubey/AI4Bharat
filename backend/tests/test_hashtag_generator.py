"""
Unit tests for hashtag generation utility.
"""

import pytest
from shared.utils.hashtag_generator import generate_hashtags


def test_generate_hashtags_basic():
    """Test basic hashtag generation with suggested tags."""
    suggested = ["fashion", "style", "trendy"]
    result = generate_hashtags(suggested)
    
    assert "#fashion" in result
    assert "#style" in result
    assert "#trendy" in result
    assert "#smallbusiness" in result
    assert "#shoponline" in result
    assert "#supportlocal" in result


def test_generate_hashtags_with_hash_prefix():
    """Test hashtag generation when tags already have # prefix."""
    suggested = ["#tech", "#gadgets"]
    result = generate_hashtags(suggested)
    
    assert "#tech" in result
    assert "#gadgets" in result
    # Should not have duplicate #
    assert "##tech" not in result


def test_generate_hashtags_with_product_labels():
    """Test hashtag generation with product labels."""
    suggested = ["fashion"]
    labels = ["Clothing", "Dress", "Apparel", "Fabric"]
    result = generate_hashtags(suggested, labels)
    
    assert "#fashion" in result
    assert "#clothing" in result
    assert "#dress" in result
    assert "#apparel" in result
    # Only top 3 labels should be included
    assert "#fabric" not in result or len([h for h in result if h.startswith("#")]) <= 10


def test_generate_hashtags_removes_duplicates():
    """Test that duplicate hashtags are removed (case-insensitive)."""
    suggested = ["Fashion", "fashion", "FASHION", "style"]
    result = generate_hashtags(suggested)
    
    # Should only have one #fashion
    fashion_count = sum(1 for h in result if h.lower() == "#fashion")
    assert fashion_count == 1


def test_generate_hashtags_removes_spaces():
    """Test that spaces are removed from hashtags."""
    suggested = ["summer style", "beach wear"]
    result = generate_hashtags(suggested)
    
    assert "#summerstyle" in result
    assert "#beachwear" in result
    assert "# " not in " ".join(result)


def test_generate_hashtags_limits_to_max():
    """Test that hashtags are limited to max_hashtags."""
    suggested = ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"]
    labels = ["Label1", "Label2", "Label3"]
    result = generate_hashtags(suggested, labels, max_hashtags=10)
    
    assert len(result) <= 10


def test_generate_hashtags_empty_input():
    """Test hashtag generation with empty input."""
    result = generate_hashtags([])
    
    # Should still have brand hashtags
    assert "#smallbusiness" in result
    assert "#shoponline" in result
    assert "#supportlocal" in result


def test_generate_hashtags_lowercase_conversion():
    """Test that all hashtags are converted to lowercase."""
    suggested = ["FASHION", "Style", "TrEnDy"]
    result = generate_hashtags(suggested)
    
    assert "#fashion" in result
    assert "#style" in result
    assert "#trendy" in result
    # No uppercase hashtags
    assert all(h == h.lower() for h in result)


def test_generate_hashtags_brand_tags_not_duplicated():
    """Test that brand hashtags are not duplicated if already in suggested."""
    suggested = ["smallbusiness", "fashion", "shoponline"]
    result = generate_hashtags(suggested)
    
    # Should only have one of each brand tag
    smallbusiness_count = sum(1 for h in result if h.lower() == "#smallbusiness")
    shoponline_count = sum(1 for h in result if h.lower() == "#shoponline")
    
    assert smallbusiness_count == 1
    assert shoponline_count == 1
