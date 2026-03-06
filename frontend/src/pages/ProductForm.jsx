import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { productAPI } from '../services/api';

const ProductForm = () => {
  const { id } = useParams();
  const isEdit = !!id;
  
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const navigate = useNavigate();

  useEffect(() => {
    if (isEdit) {
      loadProduct();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const loadProduct = async () => {
    try {
      const response = await productAPI.get(id);
      const product = response.data;
      setName(product.name);
      setDescription(product.description);
      setImagePreview(product.image_url);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load product');
    }
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type
    if (!['image/jpeg', 'image/png'].includes(file.type)) {
      setError('Only JPEG and PNG images are supported');
      return;
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('Image must be less than 10MB');
      return;
    }

    setImage(file);
    setImagePreview(URL.createObjectURL(file));
    setError('');
  };

  const validateForm = () => {
    if (!name.trim()) {
      setError('Product name is required');
      return false;
    }
    if (!description.trim()) {
      setError('Product description is required');
      return false;
    }
    if (!isEdit && !image) {
      setError('Product image is required');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      if (isEdit) {
        // Update existing product
        await productAPI.update(id, { name, description });
        navigate('/products');
      } else {
        // Create new product
        const formData = new FormData();
        formData.append('name', name);
        formData.append('description', description);
        formData.append('image', image);

        await productAPI.create(formData);
        navigate('/products');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save product');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>{isEdit ? 'Edit Product' : 'Add Product'}</h1>

      <form onSubmit={handleSubmit} style={styles.form}>
        {error && <div style={styles.error}>{error}</div>}

        <div style={styles.formGroup}>
          <label htmlFor="name" style={styles.label}>Product Name</label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            style={styles.input}
            disabled={loading}
          />
        </div>

        <div style={styles.formGroup}>
          <label htmlFor="description" style={styles.label}>Description</label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            style={styles.textarea}
            rows="4"
            disabled={loading}
          />
        </div>

        {!isEdit && (
          <div style={styles.formGroup}>
            <label htmlFor="image" style={styles.label}>Product Image</label>
            <input
              id="image"
              type="file"
              accept="image/jpeg,image/png"
              onChange={handleImageChange}
              style={styles.fileInput}
              disabled={loading}
            />
            <p style={styles.hint}>JPEG or PNG, max 10MB</p>
          </div>
        )}

        {imagePreview && (
          <div style={styles.preview}>
            <img src={imagePreview} alt="Preview" style={styles.previewImage} />
          </div>
        )}

        <div style={styles.actions}>
          <button
            type="submit"
            style={styles.submitButton}
            disabled={loading}
          >
            {loading ? 'Saving...' : isEdit ? 'Update Product' : 'Create Product'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/products')}
            style={styles.cancelButton}
            disabled={loading}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

const styles = {
  container: {
    maxWidth: '600px',
    margin: '0 auto',
    padding: '1rem',
  },
  title: {
    fontSize: '2rem',
    color: '#333',
    marginBottom: '2rem',
  },
  form: {
    backgroundColor: 'white',
    padding: '2rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  formGroup: {
    marginBottom: '1.5rem',
  },
  label: {
    display: 'block',
    fontWeight: '500',
    color: '#333',
    marginBottom: '0.5rem',
  },
  input: {
    width: '100%',
    padding: '0.75rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
  },
  textarea: {
    width: '100%',
    padding: '0.75rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
    fontFamily: 'inherit',
    resize: 'vertical',
  },
  fileInput: {
    width: '100%',
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
  },
  hint: {
    fontSize: '0.85rem',
    color: '#666',
    marginTop: '0.25rem',
  },
  preview: {
    marginBottom: '1.5rem',
  },
  previewImage: {
    maxWidth: '100%',
    maxHeight: '300px',
    borderRadius: '4px',
  },
  error: {
    padding: '0.75rem',
    backgroundColor: '#fee',
    color: '#c33',
    borderRadius: '4px',
    marginBottom: '1rem',
  },
  actions: {
    display: 'flex',
    gap: '1rem',
  },
  submitButton: {
    flex: 1,
    padding: '0.75rem',
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '1rem',
    cursor: 'pointer',
    fontWeight: '500',
  },
  cancelButton: {
    flex: 1,
    padding: '0.75rem',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '1rem',
    cursor: 'pointer',
    fontWeight: '500',
  },
};

export default ProductForm;
