"""
Integration tests for product management endpoints.

Tests product CRUD operations, image upload, analysis, and tenant isolation.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 24.3
"""

import pytest
import io
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from shared.models.domain import Product, ImageAnalysis
from shared.services.jwt_service import generate_access_token


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user ID."""
    return "test-user-123"


@pytest.fixture
def auth_headers(mock_auth_user):
    """Generate authentication headers with valid JWT."""
    token = generate_access_token(mock_auth_user)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_product(mock_auth_user):
    """Create a sample product for testing."""
    return Product(
        product_id="product-123",
        user_id=mock_auth_user,
        name="Test Product",
        description="A test product description",
        image_url="https://s3.amazonaws.com/bucket/test.jpg",
        image_s3_key="test-user-123/products/product-123.jpg",
        image_analysis=ImageAnalysis(
            labels=["Product", "Item", "Object"],
            confidence_scores={"Product": 95.5, "Item": 90.2, "Object": 85.7},
            has_faces=False,
            dominant_colors=["Blue", "White"],
            detected_text=[],
            is_safe=True
        ),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_image_bytes():
    """Create sample image bytes for testing."""
    # Create a minimal valid JPEG header
    return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00' + b'\x00' * 100


@pytest.mark.integration
class TestProductCreation:
    """Test product creation endpoint."""
    
    @patch('dev_api.routes.products.ProductRepository')
    @patch('dev_api.routes.products.S3Client')
    @patch('dev_api.routes.products.ImageAnalysisService')
    async def test_create_product_success(
        self,
        mock_image_service_class,
        mock_s3_class,
        mock_repo_class,
        client: AsyncClient,
        auth_headers,
        mock_auth_user,
        sample_image_bytes
    ):
        """Test successful product creation with image upload and analysis."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        
        # Mock S3 client
        mock_s3 = AsyncMock()
        mock_s3_class.return_value = mock_s3
        mock_s3.upload_file.return_value = f"{mock_auth_user}/products/test.jpg"
        mock_s3.generate_presigned_url.return_value = "https://s3.amazonaws.com/bucket/test.jpg"
        
        # Mock image analysis service
        mock_image_service = AsyncMock()
        mock_image_service_class.return_value = mock_image_service
        mock_image_service.analyze_image.return_value = ImageAnalysis(
            labels=["Product", "Item"],
            confidence_scores={"Product": 95.5, "Item": 90.2},
            has_faces=False,
            dominant_colors=["Blue"],
            detected_text=[],
            is_safe=True
        )
        
        # Mock create to return product
        async def mock_create(product):
            return product
        mock_repo.create.side_effect = mock_create
        
        # Create multipart form data
        files = {
            'image': ('test.jpg', io.BytesIO(sample_image_bytes), 'image/jpeg')
        }
        data = {
            'name': 'Test Product',
            'description': 'A test product description'
        }
        
        # Make request
        response = await client.post(
            "/api/v1/products",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 201
        result = response.json()
        
        assert result["name"] == "Test Product"
        assert result["description"] == "A test product description"
        assert result["user_id"] == mock_auth_user
        assert result["image_url"] == "https://s3.amazonaws.com/bucket/test.jpg"
        assert result["image_analysis"] is not None
        assert result["image_analysis"]["labels"] == ["Product", "Item"]
        assert result["image_analysis"]["is_safe"] is True
        
        # Verify S3 upload was called
        mock_s3.upload_file.assert_called_once()
        
        # Verify image analysis was called
        mock_image_service.analyze_image.assert_called_once()
        
        # Verify product was created in database
        mock_repo.create.assert_called_once()
    
    async def test_create_product_unauthorized(self, client: AsyncClient, sample_image_bytes):
        """Test product creation without authentication."""
        files = {
            'image': ('test.jpg', io.BytesIO(sample_image_bytes), 'image/jpeg')
        }
        data = {
            'name': 'Test Product',
            'description': 'A test product description'
        }
        
        response = await client.post(
            "/api/v1/products",
            files=files,
            data=data
        )
        
        assert response.status_code == 403  # No auth header
    
    async def test_create_product_invalid_image_format(
        self,
        client: AsyncClient,
        auth_headers
    ):
        """Test product creation with invalid image format."""
        files = {
            'image': ('test.txt', io.BytesIO(b'not an image'), 'text/plain')
        }
        data = {
            'name': 'Test Product',
            'description': 'A test product description'
        }
        
        response = await client.post(
            "/api/v1/products",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "invalid image format" in response.json()["detail"].lower()
    
    async def test_create_product_image_too_large(
        self,
        client: AsyncClient,
        auth_headers
    ):
        """Test product creation with image exceeding 10MB limit."""
        # Create 11MB of data
        large_image = b'\xff\xd8\xff\xe0' + b'\x00' * (11 * 1024 * 1024)
        
        files = {
            'image': ('large.jpg', io.BytesIO(large_image), 'image/jpeg')
        }
        data = {
            'name': 'Test Product',
            'description': 'A test product description'
        }
        
        response = await client.post(
            "/api/v1/products",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()
    
    async def test_create_product_empty_name(
        self,
        client: AsyncClient,
        auth_headers,
        sample_image_bytes
    ):
        """Test product creation with empty name."""
        files = {
            'image': ('test.jpg', io.BytesIO(sample_image_bytes), 'image/jpeg')
        }
        data = {
            'name': '   ',  # Whitespace only
            'description': 'A test product description'
        }
        
        response = await client.post(
            "/api/v1/products",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    @patch('dev_api.routes.products.ProductRepository')
    @patch('dev_api.routes.products.S3Client')
    @patch('dev_api.routes.products.ImageAnalysisService')
    async def test_create_product_image_analysis_failure(
        self,
        mock_image_service_class,
        mock_s3_class,
        mock_repo_class,
        client: AsyncClient,
        auth_headers,
        mock_auth_user,
        sample_image_bytes
    ):
        """Test product creation continues even if image analysis fails."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        
        # Mock S3 client
        mock_s3 = AsyncMock()
        mock_s3_class.return_value = mock_s3
        mock_s3.upload_file.return_value = f"{mock_auth_user}/products/test.jpg"
        mock_s3.generate_presigned_url.return_value = "https://s3.amazonaws.com/bucket/test.jpg"
        
        # Mock image analysis service to fail
        mock_image_service = AsyncMock()
        mock_image_service_class.return_value = mock_image_service
        mock_image_service.analyze_image.side_effect = Exception("Rekognition error")
        
        # Mock create
        async def mock_create(product):
            return product
        mock_repo.create.side_effect = mock_create
        
        # Create request
        files = {
            'image': ('test.jpg', io.BytesIO(sample_image_bytes), 'image/jpeg')
        }
        data = {
            'name': 'Test Product',
            'description': 'A test product description'
        }
        
        # Make request
        response = await client.post(
            "/api/v1/products",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        # Should still succeed without image analysis
        assert response.status_code == 201
        result = response.json()
        assert result["image_analysis"] is None


@pytest.mark.integration
class TestProductListing:
    """Test product listing endpoint."""
    
    @patch('dev_api.routes.products.ProductRepository')
    async def test_list_products_success(
        self,
        mock_repo_class,
        client: AsyncClient,
        auth_headers,
        mock_auth_user
    ):
        """Test successful product listing with pagination."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        
        # Create sample products
        products = [
            Product(
                product_id=f"product-{i}",
                user_id=mock_auth_user,
                name=f"Product {i}",
                description=f"Description {i}",
                image_url=f"https://s3.amazonaws.com/bucket/product-{i}.jpg",
                image_s3_key=f"{mock_auth_user}/products/product-{i}.jpg",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            for i in range(5)
        ]
        
        mock_repo.get_by_user.return_value = products
        
        # Make request
        response = await client.get(
            "/api/v1/products",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        result = response.json()
        
        assert result["total"] == 5
        assert len(result["products"]) == 5
        assert result["page"] == 1
        assert result["page_size"] == 20
        assert result["has_more"] is False
        
        # Verify tenant isolation
        mock_repo.get_by_user.assert_called_once_with(mock_auth_user, include_deleted=False)
    
    @patch('dev_api.routes.products.ProductRepository')
    async def test_list_products_pagination(
        self,
        mock_repo_class,
        client: AsyncClient,
        auth_headers,
        mock_auth_user
    ):
        """Test product listing with pagination."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        
        # Create 25 products
        products = [
            Product(
                product_id=f"product-{i}",
                user_id=mock_auth_user,
                name=f"Product {i}",
                description=f"Description {i}",
                image_url=f"https://s3.amazonaws.com/bucket/product-{i}.jpg",
                image_s3_key=f"{mock_auth_user}/products/product-{i}.jpg",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            for i in range(25)
        ]
        
        mock_repo.get_by_user.return_value = products
        
        # Request page 1 with page_size 10
        response = await client.get(
            "/api/v1/products?page=1&page_size=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["total"] == 25
        assert len(result["products"]) == 10
        assert result["page"] == 1
        assert result["page_size"] == 10
        assert result["has_more"] is True
        
        # Request page 2
        response = await client.get(
            "/api/v1/products?page=2&page_size=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert len(result["products"]) == 10
        assert result["page"] == 2
        assert result["has_more"] is True
        
        # Request page 3 (last page)
        response = await client.get(
            "/api/v1/products?page=3&page_size=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert len(result["products"]) == 5
        assert result["page"] == 3
        assert result["has_more"] is False
    
    async def test_list_products_unauthorized(self, client: AsyncClient):
        """Test product listing without authentication."""
        response = await client.get("/api/v1/products")
        
        assert response.status_code == 403
    
    async def test_list_products_invalid_pagination(
        self,
        client: AsyncClient,
        auth_headers
    ):
        """Test product listing with invalid pagination parameters."""
        # Invalid page number
        response = await client.get(
            "/api/v1/products?page=0",
            headers=auth_headers
        )
        assert response.status_code == 400
        
        # Invalid page size
        response = await client.get(
            "/api/v1/products?page_size=0",
            headers=auth_headers
        )
        assert response.status_code == 400
        
        # Page size too large
        response = await client.get(
            "/api/v1/products?page_size=101",
            headers=auth_headers
        )
        assert response.status_code == 400


@pytest.mark.integration
class TestProductUpdate:
    """Test product update endpoint."""
    
    @patch('dev_api.routes.products.ProductRepository')
    async def test_update_product_success(
        self,
        mock_repo_class,
        client: AsyncClient,
        auth_headers,
        sample_product
    ):
        """Test successful product update."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        
        mock_repo.get_by_id.return_value = sample_product
        
        async def mock_update(product):
            return product
        mock_repo.update.side_effect = mock_update
        
        # Make request
        response = await client.put(
            f"/api/v1/products/{sample_product.product_id}",
            json={
                "name": "Updated Product Name",
                "description": "Updated description"
            },
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        result = response.json()
        
        assert result["name"] == "Updated Product Name"
        assert result["description"] == "Updated description"
        assert result["product_id"] == sample_product.product_id
        
        # Verify ownership check
        mock_repo.get_by_id.assert_called_once()
        mock_repo.update.assert_called_once()
    
    @patch('dev_api.routes.products.ProductRepository')
    async def test_update_product_partial(
        self,
        mock_repo_class,
        client: AsyncClient,
        auth_headers,
        sample_product
    ):
        """Test partial product update (only name)."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        
        mock_repo.get_by_id.return_value = sample_product
        
        async def mock_update(product):
            return product
        mock_repo.update.side_effect = mock_update
        
        # Make request with only name
        response = await client.put(
            f"/api/v1/products/{sample_product.product_id}",
            json={"name": "New Name Only"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["name"] == "New Name Only"
        assert result["description"] == sample_product.description  # Unchanged
    
    @patch('dev_api.routes.products.ProductRepository')
    async def test_update_product_not_found(
        self,
        mock_repo_class,
        client: AsyncClient,
        auth_headers
    ):
        """Test update of non-existent product."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        
        mock_repo.get_by_id.return_value = None
        
        # Make request
        response = await client.put(
            "/api/v1/products/nonexistent-id",
            json={"name": "Updated Name"},
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    async def test_update_product_unauthorized(self, client: AsyncClient):
        """Test product update without authentication."""
        response = await client.put(
            "/api/v1/products/product-123",
            json={"name": "Updated Name"}
        )
        
        assert response.status_code == 403


@pytest.mark.integration
class TestProductDeletion:
    """Test product deletion endpoint."""
    
    @patch('dev_api.routes.products.ProductRepository')
    async def test_delete_product_success(
        self,
        mock_repo_class,
        client: AsyncClient,
        auth_headers,
        sample_product
    ):
        """Test successful product soft deletion."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        
        mock_repo.soft_delete.return_value = True
        
        # Make request
        response = await client.delete(
            f"/api/v1/products/{sample_product.product_id}",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 204
        
        # Verify soft delete was called with tenant isolation
        mock_repo.soft_delete.assert_called_once()
    
    @patch('dev_api.routes.products.ProductRepository')
    async def test_delete_product_not_found(
        self,
        mock_repo_class,
        client: AsyncClient,
        auth_headers
    ):
        """Test deletion of non-existent product."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        
        mock_repo.soft_delete.return_value = False
        
        # Make request
        response = await client.delete(
            "/api/v1/products/nonexistent-id",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    async def test_delete_product_unauthorized(self, client: AsyncClient):
        """Test product deletion without authentication."""
        response = await client.delete("/api/v1/products/product-123")
        
        assert response.status_code == 403


@pytest.mark.integration
class TestTenantIsolation:
    """Test tenant isolation across product operations."""
    
    @patch('dev_api.routes.products.ProductRepository')
    async def test_cannot_access_other_user_product(
        self,
        mock_repo_class,
        client: AsyncClient,
        mock_auth_user
    ):
        """Test that users cannot access products from other users."""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        
        # Product belongs to different user
        other_user_product = Product(
            product_id="product-123",
            user_id="other-user-456",
            name="Other User Product",
            description="Description",
            image_url="https://s3.amazonaws.com/bucket/test.jpg",
            image_s3_key="other-user-456/products/product-123.jpg",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Repository returns None for tenant isolation
        mock_repo.get_by_id.return_value = None
        
        # Generate auth headers for current user
        token = generate_access_token(mock_auth_user)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to get other user's product
        response = await client.get(
            f"/api/v1/products/{other_user_product.product_id}",
            headers=headers
        )
        
        assert response.status_code == 404
        
        # Verify repository was called with correct user_id
        mock_repo.get_by_id.assert_called_once_with(mock_auth_user, other_user_product.product_id)
