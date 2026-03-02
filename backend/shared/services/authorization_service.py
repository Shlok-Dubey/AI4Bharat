"""
Authorization service for resource ownership verification.

This module provides authorization helpers to verify users can only access
their own resources as specified in requirements 1.5 and 26.3.
"""

from fastapi import HTTPException, status


def check_resource_ownership(
    resource_user_id: str,
    authenticated_user_id: str,
    resource_type: str = "resource"
) -> None:
    """
    Verify that the authenticated user owns the requested resource.
    
    This function checks if the user_id associated with a resource matches
    the authenticated user's ID. Raises 403 Forbidden if they don't match.
    
    Args:
        resource_user_id: User ID associated with the resource
        authenticated_user_id: User ID from the authenticated JWT token
        resource_type: Type of resource for error message (e.g., "product", "campaign")
        
    Raises:
        HTTPException: 403 Forbidden if user doesn't own the resource
        
    Requirements: 1.5, 26.3
    
    Usage:
        # In an endpoint handler
        product = await product_repository.get_by_id(product_id)
        check_resource_ownership(
            resource_user_id=product.user_id,
            authenticated_user_id=current_user_id,
            resource_type="product"
        )
    """
    if resource_user_id != authenticated_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have permission to access this {resource_type}"
        )


def verify_user_access(
    requested_user_id: str,
    authenticated_user_id: str
) -> None:
    """
    Verify that the authenticated user is accessing their own data.
    
    This is used for endpoints where the user_id is in the path or query params.
    
    Args:
        requested_user_id: User ID being requested
        authenticated_user_id: User ID from the authenticated JWT token
        
    Raises:
        HTTPException: 403 Forbidden if user is trying to access another user's data
        
    Requirements: 1.5, 26.3
    """
    if requested_user_id != authenticated_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own data"
        )
