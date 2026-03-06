import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { productAPI } from '../services/api';

const Products = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);

  useEffect(() => {
    loadProducts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const loadProducts = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await productAPI.list(page, 20);
      setProducts(response.data.products);
      setHasMore(response.data.has_more);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load products');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (productId) => {
    if (!confirm('Are you sure you want to delete this product?')) {
      return;
    }

    try {
      await productAPI.delete(productId);
      loadProducts();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete product');
    }
  };

  if (loading) {
    return <div style={styles.loading}>Loading products...</div>;
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>Products</h1>
        <Link to="/products/new" style={styles.addButton}>
          Add Product
        </Link>
      </div>

      {error && <div style={styles.error}>{error}</div>}

      {products.length === 0 ? (
        <div style={styles.empty}>
          <p>No products yet. Add your first product to get started!</p>
          <Link to="/products/new" style={styles.addButton}>
            Add Product
          </Link>
        </div>
      ) : (
        <>
          <div style={styles.grid}>
            {products.map((product) => (
              <div key={product.product_id} style={styles.card}>
                {product.image_url && (
                  <img
                    src={product.image_url}
                    alt={product.name}
                    style={styles.image}
                  />
                )}
                <div style={styles.cardContent}>
                  <h3 style={styles.productName}>{product.name}</h3>
                  <p style={styles.productDescription}>{product.description}</p>
                  
                  <div style={styles.actions}>
                    <Link
                      to={`/products/${product.product_id}/edit`}
                      style={styles.editButton}
                    >
                      Edit
                    </Link>
                    <button
                      onClick={() => handleDelete(product.product_id)}
                      style={styles.deleteButton}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div style={styles.pagination}>
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              style={styles.pageButton}
            >
              Previous
            </button>
            <span style={styles.pageInfo}>Page {page}</span>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={!hasMore}
              style={styles.pageButton}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
};

const styles = {
  container: {
    padding: '1rem',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '2rem',
  },
  title: {
    fontSize: '2rem',
    color: '#333',
  },
  addButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#28a745',
    color: 'white',
    textDecoration: 'none',
    borderRadius: '4px',
    fontWeight: '500',
  },
  loading: {
    textAlign: 'center',
    padding: '2rem',
    color: '#666',
  },
  error: {
    padding: '1rem',
    backgroundColor: '#fee',
    color: '#c33',
    borderRadius: '4px',
    marginBottom: '1rem',
  },
  empty: {
    textAlign: 'center',
    padding: '3rem',
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
    gap: '1.5rem',
    marginBottom: '2rem',
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    overflow: 'hidden',
  },
  image: {
    width: '100%',
    height: '200px',
    objectFit: 'cover',
  },
  cardContent: {
    padding: '1rem',
  },
  productName: {
    fontSize: '1.25rem',
    color: '#333',
    marginBottom: '0.5rem',
  },
  productDescription: {
    color: '#666',
    marginBottom: '1rem',
    lineHeight: '1.5',
  },
  actions: {
    display: 'flex',
    gap: '0.5rem',
  },
  editButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#007bff',
    color: 'white',
    textDecoration: 'none',
    borderRadius: '4px',
    fontSize: '0.9rem',
  },
  deleteButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.9rem',
  },
  pagination: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    gap: '1rem',
  },
  pageButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  pageInfo: {
    color: '#666',
  },
};

export default Products;
