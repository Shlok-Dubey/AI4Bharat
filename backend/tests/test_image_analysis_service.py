"""Unit tests for image analysis service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.shared.services.image_analysis_service import ImageAnalysisService
from backend.shared.models.domain import ImageAnalysis


@pytest.fixture
def image_analysis_service():
    """Create an ImageAnalysisService instance for testing."""
    return ImageAnalysisService()


@pytest.fixture
def sample_image_bytes():
    """Sample image bytes for testing."""
    return b"fake_image_data"


@pytest.fixture
def mock_rekognition_labels():
    """Mock Rekognition DetectLabels response."""
    return [
        {
            'Name': 'Product',
            'Confidence': 99.5,
            'Instances': [
                {
                    'DominantColors': [
                        {'SimplifiedColor': 'Blue'},
                        {'SimplifiedColor': 'White'}
                    ]
                }
            ],
            'Parents': []
        },
        {
            'Name': 'Clothing',
            'Confidence': 95.2,
            'Instances': [],
            'Parents': []
        },
        {
            'Name': 'Apparel',
            'Confidence': 92.8,
            'Instances': [],
            'Parents': []
        },
        {
            'Name': 'Shirt',
            'Confidence': 88.3,
            'Instances': [
                {
                    'DominantColors': [
                        {'SimplifiedColor': 'Red'}
                    ]
                }
            ],
            'Parents': []
        },
        {
            'Name': 'Fashion',
            'Confidence': 85.7,
            'Instances': [],
            'Parents': []
        },
        {
            'Name': 'Accessory',
            'Confidence': 78.1,
            'Instances': [],
            'Parents': []
        }
    ]


@pytest.fixture
def mock_rekognition_faces():
    """Mock Rekognition DetectFaces response with faces."""
    return [
        {
            'BoundingBox': {
                'Width': 0.5,
                'Height': 0.5,
                'Left': 0.25,
                'Top': 0.25
            },
            'Confidence': 99.9
        }
    ]


@pytest.fixture
def mock_rekognition_no_faces():
    """Mock Rekognition DetectFaces response without faces."""
    return []


@pytest.fixture
def mock_rekognition_moderation_safe():
    """Mock Rekognition DetectModerationLabels response for safe content."""
    return []


@pytest.fixture
def mock_rekognition_moderation_unsafe():
    """Mock Rekognition DetectModerationLabels response for unsafe content."""
    return [
        {
            'Name': 'Explicit Nudity',
            'Confidence': 85.0,
            'ParentName': ''
        }
    ]


@pytest.mark.asyncio
async def test_analyze_image_success(
    image_analysis_service,
    sample_image_bytes,
    mock_rekognition_labels,
    mock_rekognition_no_faces,
    mock_rekognition_moderation_safe
):
    """Test successful image analysis with all components."""
    # Mock Rekognition client methods
    image_analysis_service.rekognition_client.detect_labels = AsyncMock(
        return_value=mock_rekognition_labels
    )
    image_analysis_service.rekognition_client.detect_faces = AsyncMock(
        return_value=mock_rekognition_no_faces
    )
    image_analysis_service.rekognition_client.detect_moderation_labels = AsyncMock(
        return_value=mock_rekognition_moderation_safe
    )
    
    # Analyze image
    result = await image_analysis_service.analyze_image(sample_image_bytes)
    
    # Verify result type
    assert isinstance(result, ImageAnalysis)
    
    # Verify top 5 labels are extracted and sorted by confidence
    assert len(result.labels) == 5
    assert result.labels == ['Product', 'Clothing', 'Apparel', 'Shirt', 'Fashion']
    
    # Verify confidence scores
    assert result.confidence_scores['Product'] == 99.5
    assert result.confidence_scores['Clothing'] == 95.2
    assert result.confidence_scores['Apparel'] == 92.8
    assert result.confidence_scores['Shirt'] == 88.3
    assert result.confidence_scores['Fashion'] == 85.7
    
    # Verify no faces detected
    assert result.has_faces is False
    
    # Verify content is safe
    assert result.is_safe is True
    
    # Verify dominant colors extracted
    assert 'Blue' in result.dominant_colors
    assert 'White' in result.dominant_colors
    assert 'Red' in result.dominant_colors
    
    # Verify all Rekognition methods were called
    image_analysis_service.rekognition_client.detect_labels.assert_called_once_with(sample_image_bytes)
    image_analysis_service.rekognition_client.detect_faces.assert_called_once_with(sample_image_bytes)
    image_analysis_service.rekognition_client.detect_moderation_labels.assert_called_once_with(sample_image_bytes)


@pytest.mark.asyncio
async def test_analyze_image_with_faces(
    image_analysis_service,
    sample_image_bytes,
    mock_rekognition_labels,
    mock_rekognition_faces,
    mock_rekognition_moderation_safe
):
    """Test image analysis detects human presence."""
    # Mock Rekognition client methods
    image_analysis_service.rekognition_client.detect_labels = AsyncMock(
        return_value=mock_rekognition_labels
    )
    image_analysis_service.rekognition_client.detect_faces = AsyncMock(
        return_value=mock_rekognition_faces
    )
    image_analysis_service.rekognition_client.detect_moderation_labels = AsyncMock(
        return_value=mock_rekognition_moderation_safe
    )
    
    # Analyze image
    result = await image_analysis_service.analyze_image(sample_image_bytes)
    
    # Verify faces detected
    assert result.has_faces is True


@pytest.mark.asyncio
async def test_analyze_image_unsafe_content(
    image_analysis_service,
    sample_image_bytes,
    mock_rekognition_labels,
    mock_rekognition_no_faces,
    mock_rekognition_moderation_unsafe
):
    """Test image analysis detects unsafe content."""
    # Mock Rekognition client methods
    image_analysis_service.rekognition_client.detect_labels = AsyncMock(
        return_value=mock_rekognition_labels
    )
    image_analysis_service.rekognition_client.detect_faces = AsyncMock(
        return_value=mock_rekognition_no_faces
    )
    image_analysis_service.rekognition_client.detect_moderation_labels = AsyncMock(
        return_value=mock_rekognition_moderation_unsafe
    )
    
    # Analyze image
    result = await image_analysis_service.analyze_image(sample_image_bytes)
    
    # Verify content is unsafe
    assert result.is_safe is False


@pytest.mark.asyncio
async def test_analyze_image_filters_by_confidence(
    image_analysis_service,
    sample_image_bytes,
    mock_rekognition_no_faces,
    mock_rekognition_moderation_safe
):
    """Test that labels are filtered by confidence >= 75."""
    # Create labels with varying confidence levels
    labels_with_low_confidence = [
        {'Name': 'HighConfidence', 'Confidence': 95.0, 'Instances': [], 'Parents': []},
        {'Name': 'MediumConfidence', 'Confidence': 80.0, 'Instances': [], 'Parents': []},
        {'Name': 'LowConfidence', 'Confidence': 60.0, 'Instances': [], 'Parents': []},  # Should be filtered by Rekognition
    ]
    
    # Mock Rekognition client (Rekognition already filters by MinConfidence=75)
    image_analysis_service.rekognition_client.detect_labels = AsyncMock(
        return_value=labels_with_low_confidence[:2]  # Only high and medium confidence
    )
    image_analysis_service.rekognition_client.detect_faces = AsyncMock(
        return_value=mock_rekognition_no_faces
    )
    image_analysis_service.rekognition_client.detect_moderation_labels = AsyncMock(
        return_value=mock_rekognition_moderation_safe
    )
    
    # Analyze image
    result = await image_analysis_service.analyze_image(sample_image_bytes)
    
    # Verify only labels with confidence >= 75 are included
    assert 'HighConfidence' in result.labels
    assert 'MediumConfidence' in result.labels
    assert 'LowConfidence' not in result.labels


@pytest.mark.asyncio
async def test_analyze_image_sorts_by_confidence(
    image_analysis_service,
    sample_image_bytes,
    mock_rekognition_no_faces,
    mock_rekognition_moderation_safe
):
    """Test that labels are sorted by confidence in descending order."""
    # Create labels in random order
    unsorted_labels = [
        {'Name': 'Medium', 'Confidence': 85.0, 'Instances': [], 'Parents': []},
        {'Name': 'Highest', 'Confidence': 99.0, 'Instances': [], 'Parents': []},
        {'Name': 'Low', 'Confidence': 76.0, 'Instances': [], 'Parents': []},
        {'Name': 'High', 'Confidence': 92.0, 'Instances': [], 'Parents': []},
    ]
    
    # Mock Rekognition client
    image_analysis_service.rekognition_client.detect_labels = AsyncMock(
        return_value=unsorted_labels
    )
    image_analysis_service.rekognition_client.detect_faces = AsyncMock(
        return_value=mock_rekognition_no_faces
    )
    image_analysis_service.rekognition_client.detect_moderation_labels = AsyncMock(
        return_value=mock_rekognition_moderation_safe
    )
    
    # Analyze image
    result = await image_analysis_service.analyze_image(sample_image_bytes)
    
    # Verify labels are sorted by confidence (descending)
    assert result.labels == ['Highest', 'High', 'Medium', 'Low']
    assert result.confidence_scores['Highest'] == 99.0
    assert result.confidence_scores['High'] == 92.0
    assert result.confidence_scores['Medium'] == 85.0
    assert result.confidence_scores['Low'] == 76.0


@pytest.mark.asyncio
async def test_analyze_image_takes_top_5_labels(
    image_analysis_service,
    sample_image_bytes,
    mock_rekognition_no_faces,
    mock_rekognition_moderation_safe
):
    """Test that only top 5 labels are returned."""
    # Create more than 5 labels
    many_labels = [
        {'Name': f'Label{i}', 'Confidence': 90.0 - i, 'Instances': [], 'Parents': []}
        for i in range(10)
    ]
    
    # Mock Rekognition client
    image_analysis_service.rekognition_client.detect_labels = AsyncMock(
        return_value=many_labels
    )
    image_analysis_service.rekognition_client.detect_faces = AsyncMock(
        return_value=mock_rekognition_no_faces
    )
    image_analysis_service.rekognition_client.detect_moderation_labels = AsyncMock(
        return_value=mock_rekognition_moderation_safe
    )
    
    # Analyze image
    result = await image_analysis_service.analyze_image(sample_image_bytes)
    
    # Verify only top 5 labels are returned
    assert len(result.labels) == 5
    assert result.labels == ['Label0', 'Label1', 'Label2', 'Label3', 'Label4']


@pytest.mark.asyncio
async def test_analyze_image_handles_rekognition_error(
    image_analysis_service,
    sample_image_bytes
):
    """Test error handling when Rekognition fails."""
    # Mock Rekognition client to raise an exception
    image_analysis_service.rekognition_client.detect_labels = AsyncMock(
        side_effect=Exception("Rekognition API error")
    )
    
    # Verify exception is propagated
    with pytest.raises(Exception, match="Rekognition API error"):
        await image_analysis_service.analyze_image(sample_image_bytes)


@pytest.mark.asyncio
async def test_extract_dominant_colors_from_instances(
    image_analysis_service
):
    """Test dominant color extraction from label instances."""
    labels = [
        {
            'Name': 'Product',
            'Confidence': 99.0,
            'Instances': [
                {
                    'DominantColors': [
                        {'SimplifiedColor': 'Blue'},
                        {'SimplifiedColor': 'White'}
                    ]
                }
            ],
            'Parents': []
        }
    ]
    
    colors = image_analysis_service._extract_dominant_colors(labels)
    
    assert 'Blue' in colors
    assert 'White' in colors


@pytest.mark.asyncio
async def test_extract_dominant_colors_deduplication(
    image_analysis_service
):
    """Test that duplicate colors are removed."""
    labels = [
        {
            'Name': 'Product1',
            'Confidence': 99.0,
            'Instances': [
                {
                    'DominantColors': [
                        {'SimplifiedColor': 'Blue'},
                        {'SimplifiedColor': 'Blue'}  # Duplicate
                    ]
                }
            ],
            'Parents': []
        },
        {
            'Name': 'Product2',
            'Confidence': 95.0,
            'Instances': [
                {
                    'DominantColors': [
                        {'SimplifiedColor': 'Blue'}  # Duplicate
                    ]
                }
            ],
            'Parents': []
        }
    ]
    
    colors = image_analysis_service._extract_dominant_colors(labels)
    
    # Should only have one 'Blue'
    assert colors.count('Blue') == 1


@pytest.mark.asyncio
async def test_is_color_label(
    image_analysis_service
):
    """Test color label detection."""
    # Test common colors
    assert image_analysis_service._is_color_label('Red') is True
    assert image_analysis_service._is_color_label('Blue') is True
    assert image_analysis_service._is_color_label('Green') is True
    assert image_analysis_service._is_color_label('Yellow') is True
    
    # Test case insensitivity
    assert image_analysis_service._is_color_label('RED') is True
    assert image_analysis_service._is_color_label('blue') is True
    
    # Test non-color labels
    assert image_analysis_service._is_color_label('Product') is False
    assert image_analysis_service._is_color_label('Clothing') is False
    assert image_analysis_service._is_color_label('Person') is False


@pytest.mark.asyncio
async def test_analyze_image_empty_labels(
    image_analysis_service,
    sample_image_bytes,
    mock_rekognition_no_faces,
    mock_rekognition_moderation_safe
):
    """Test image analysis with no labels detected."""
    # Mock Rekognition client with empty labels
    image_analysis_service.rekognition_client.detect_labels = AsyncMock(
        return_value=[]
    )
    image_analysis_service.rekognition_client.detect_faces = AsyncMock(
        return_value=mock_rekognition_no_faces
    )
    image_analysis_service.rekognition_client.detect_moderation_labels = AsyncMock(
        return_value=mock_rekognition_moderation_safe
    )
    
    # Analyze image
    result = await image_analysis_service.analyze_image(sample_image_bytes)
    
    # Verify empty results
    assert result.labels == []
    assert result.confidence_scores == {}
    assert result.has_faces is False
    assert result.is_safe is True
