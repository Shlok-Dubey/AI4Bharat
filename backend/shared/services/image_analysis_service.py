"""Image analysis service for product images using Amazon Rekognition."""

from typing import List, Dict, Any
from shared.utils.rekognition_client import RekognitionClient
from shared.models.domain import ImageAnalysis


class ImageAnalysisService:
    """Service for analyzing product images using Amazon Rekognition."""
    
    def __init__(self):
        """Initialize the image analysis service."""
        self.rekognition_client = RekognitionClient()
    
    async def analyze_image(self, image_bytes: bytes) -> ImageAnalysis:
        """
        Perform comprehensive image analysis on product images.
        
        This method implements the image analysis algorithm:
        1. Call Rekognition DetectLabels and filter by confidence >= 75
        2. Sort labels by confidence and take top 5
        3. Call DetectFaces to check for human presence
        4. Call DetectModerationLabels to check content safety
        5. Extract dominant colors from label metadata
        6. Return ImageAnalysis object with all fields
        
        Args:
            image_bytes: Image content as bytes
        
        Returns:
            ImageAnalysis object containing:
                - labels: Top 5 label names
                - confidence_scores: Dict mapping label names to confidence scores
                - has_faces: Boolean indicating human presence
                - dominant_colors: List of dominant color names
                - detected_text: List of detected text (empty for now)
                - is_safe: Boolean indicating content safety
        
        Raises:
            Exception: If Rekognition API calls fail after retries
        
        Requirements: 4.1, 4.2, 4.4
        """
        # Call Rekognition DetectLabels with MinConfidence=75
        labels_response = await self.rekognition_client.detect_labels(image_bytes)
        
        # Sort labels by confidence (descending) and take top 5
        sorted_labels = sorted(
            labels_response,
            key=lambda x: x.get('Confidence', 0),
            reverse=True
        )[:5]
        
        # Extract label names and confidence scores
        label_names = [label['Name'] for label in sorted_labels]
        confidence_scores = {
            label['Name']: label['Confidence']
            for label in sorted_labels
        }
        
        # Extract dominant colors from label metadata
        dominant_colors = self._extract_dominant_colors(sorted_labels)
        
        # Call DetectFaces to check for human presence
        faces_response = await self.rekognition_client.detect_faces(image_bytes)
        has_faces = len(faces_response) > 0
        
        # Call DetectModerationLabels to check content safety
        moderation_response = await self.rekognition_client.detect_moderation_labels(image_bytes)
        is_safe = len(moderation_response) == 0
        
        # Return ImageAnalysis object
        return ImageAnalysis(
            labels=label_names,
            confidence_scores=confidence_scores,
            has_faces=has_faces,
            dominant_colors=dominant_colors,
            detected_text=[],  # Can be extended later with text detection
            is_safe=is_safe
        )
    
    def _extract_dominant_colors(self, labels: List[Dict[str, Any]]) -> List[str]:
        """
        Extract dominant colors from Rekognition label metadata.
        
        Rekognition labels may include color information in the label instances.
        This method extracts unique color names from the label data.
        
        Args:
            labels: List of label dictionaries from Rekognition
        
        Returns:
            List of unique dominant color names
        """
        colors = []
        
        for label in labels:
            # Check if label has instances with dominant colors
            instances = label.get('Instances', [])
            for instance in instances:
                dominant_colors = instance.get('DominantColors', [])
                for color_info in dominant_colors:
                    # Extract color name if available
                    color_name = color_info.get('SimplifiedColor')
                    if color_name and color_name not in colors:
                        colors.append(color_name)
            
            # Also check parent-level color information if available
            parents = label.get('Parents', [])
            for parent in parents:
                parent_name = parent.get('Name', '')
                # Check if parent is a color-related label
                if self._is_color_label(parent_name) and parent_name not in colors:
                    colors.append(parent_name)
        
        return colors[:5]  # Return top 5 colors
    
    def _is_color_label(self, label_name: str) -> bool:
        """
        Check if a label name represents a color.
        
        Args:
            label_name: Label name to check
        
        Returns:
            True if the label represents a color
        """
        color_keywords = [
            'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink',
            'black', 'white', 'gray', 'grey', 'brown', 'beige', 'tan',
            'cyan', 'magenta', 'turquoise', 'violet', 'indigo', 'maroon',
            'navy', 'teal', 'olive', 'lime', 'aqua', 'silver', 'gold'
        ]
        
        label_lower = label_name.lower()
        return any(color in label_lower for color in color_keywords)
