import React, { useState, useEffect } from 'react';

interface UserEntity {
  id: string;
  email: string;
  name: string;
  password_hash: string;
  created_at: string;
  updated_at: string;
}

interface UserProps {
  userId?: string;
  onUserUpdate?: (user: UserEntity) => void;
  onUserDelete?: (userId: string) => void;
}

interface UserFormData {
  email: string;
  name: string;
  password: string;
}

export const User: React.FC<UserProps> = ({ userId, onUserUpdate, onUserDelete }) => {
  const [user, setUser] = useState<UserEntity | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<UserFormData>({
    email: '',
    name: '',
    password: '',
  });

  useEffect(() => {
    if (userId) {
      fetchUser(userId);
    }
  }, [userId]);

  const fetchUser = async (id: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/users/${id}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch user: ${response.statusText}`);
      }
      const data: UserEntity = await response.json();
      setUser(data);
      setFormData({
        email: data.email,
        name: data.name,
        password: '',
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      console.error('Error fetching user:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const endpoint = user ? `/api/users/${user.id}` : '/api/users';
      const method = user ? 'PUT' : 'POST';

      const payload: any = {
        email: formData.email,
        name: formData.name,
      };

      if (formData.password) {
        payload.password = formData.password;
      }

      const response = await fetch(endpoint, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Failed to save user: ${response.statusText}`);
      }

      const savedUser: UserEntity = await response.json();
      setUser(savedUser);
      setIsEditing(false);
      setFormData(prev => ({ ...prev, password: '' }));

      if (onUserUpdate) {
        onUserUpdate(savedUser);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      console.error('Error saving user:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!user) return;

    if (!window.confirm(`Are you sure you want to delete user ${user.name}?`)) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/users/${user.id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`Failed to delete user: ${response.statusText}`);
      }

      if (onUserDelete) {
        onUserDelete(user.id);
      }

      setUser(null);
      setFormData({ email: '', name: '', password: '' });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      console.error('Error deleting user:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    if (user) {
      setFormData({
        email: user.email,
        name: user.name,
        password: '',
      });
    } else {
      setFormData({ email: '', name: '', password: '' });
    }
    setIsEditing(false);
    setError(null);
  };

  const formatDate = (dateString: string): string => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  if (isLoading && !user) {
    return (
      <div className="user-component loading">
        <p>Loading user...</p>
      </div>
    );
  }

  return (
    <div className="user-component">
      {error && (
        <div className="error-message" role="alert">
          <strong>Error:</strong> {error}
        </div>
      )}

      {!isEditing && user ? (
        <div className="user-details">
          <h2>User Details</h2>
          <div className="user-field">
            <label>ID:</label>
            <span>{user.id}</span>
          </div>
          <div className="user-field">
            <label>Email:</label>
            <span>{user.email}</span>
          </div>
          <div className="user-field">
            <label>Name:</label>
            <span>{user.name}</span>
          </div>
          <div className="user-field">
            <label>Created At:</label>
            <span>{formatDate(user.created_at)}</span>
          </div>
          <div className="user-field">
            <label>Updated At:</label>
            <span>{formatDate(user.updated_at)}</span>
          </div>
          <div className="user-actions">
            <button
              onClick={() => setIsEditing(true)}
              disabled={isLoading}
              className="btn btn-primary"
            >
              Edit
            </button>
            <button
              onClick={handleDelete}
              disabled={isLoading}
              className="btn btn-danger"
            >
              {isLoading ? 'Deleting...' : 'Delete'}
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="user-form">
          <h2>{user ? 'Edit User' : 'Create User'}</h2>
          
          <div className="form-group">
            <label htmlFor="email">
              Email: <span className="required">*</span>
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              required
              disabled={isLoading}
              placeholder="user@example.com"
            />
          </div>

          <div className="form-group">
            <label htmlFor="name">
              Name: <span className="required">*</span>
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              required
              disabled={isLoading}
              placeholder="John Doe"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">
              Password: {!user && <span className="required">*</span>}
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              required={!user}
              disabled={isLoading}
              placeholder={user ? 'Leave blank to keep current password' : 'Enter password'}
            />
            {user && (
              <small className="form-hint">
                Leave blank to keep the current password
              </small>
            )}
          </div>

          <div className="form-actions">
            <button
              type="submit"
              disabled={isLoading}
              className="btn btn-primary"
            >
              {isLoading ? 'Saving...' : user ? 'Update' : 'Create'}
            </button>
            {user && (
              <button
                type="button"
                onClick={handleCancel}
                disabled={isLoading}
                className="btn btn-secondary"
              >
                Cancel
              </button>
            )}
          </div>
        </form>
      )}

      <style>{`
        .user-component {
          max-width: 600px;
          margin: 0 auto;
          padding: 20px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }

        .loading {
          text-align: center;
          padding: 40px;
          color: #666;
        }

        .error-message {
          background-color: #fee;
          border: 1px solid #fcc;
          border-radius: 4px;
          padding: 12px 16px;
          margin-bottom: 20px;
          color: #c33;
        }

        .user-details {
          background: #fff;
          border: 1px solid #ddd;
          border-radius: 8px;
          padding: 24px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .user-details h2 {
          margin-top: 0;
          margin-bottom: 20px;
          color: #333;
          font-size: 24px;
        }

        .user-field {
          display: flex;
          margin-bottom: 16px;
          padding-bottom: 16px;
          border-bottom: 1px solid #eee;
        }

        .user-field:last-of-type {
          border-bottom: none;
        }

        .user-field label {
          font-weight: 600;
          color: #555;
          min-width: 120px;
          margin-right: 16px;
        }

        .user-field span {
          color: #333;
          word-break: break-all;
        }

        .user-form {
          background: #fff;
          border: 1px solid #ddd;
          border-radius: 8px;
          padding: 24px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .user-form h2 {
          margin-top: 0;
          margin-bottom: 24px;
          color: #333;
          font-size: 24px;
        }

        .form-group {
          margin-bottom: 20px;
        }

        .form-group label {
          display: block;
          margin-bottom: 6px;
          font-weight: 600;
          color: #333;
        }

        .required {
          color: #e53e3e;
        }

        .form-group input {
          width: 100%;
          padding: 10px 12px;
          border: 1px solid #ccc;
          border-radius: 4px;
          font-size: 14px;
          box-sizing: border-box;
          transition: border-color 0.2s;
        }

        .form-group input:focus {
          outline: none;
          border-color: #4299e1;
          box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
        }

        .form-group input:disabled {
          background-color: #f5f5f5;
          cursor: not-allowed;
        }

        .form-hint {
          display: block;
          margin-top: 4px;
          font-size: 12px;
          color: #666;
        }

        .form-actions,
        .user-actions {
          display: flex;
          gap: 12px;
          margin-top: 24px;
        }

        .btn {
          padding: 10px 20px;
          border: none;
          border-radius: 4px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .btn-primary {
          background-color: #4299e1;
          color: white;
        }

        .btn-primary:hover:not(:disabled) {
          background-color: #3182ce;
        }

        .btn-secondary {
          background-color: #718096;
          color: white;
        }

        .btn-secondary:hover:not(:disabled) {
          background-color: #4a5568;
        }

        .btn-danger {
          background-color: #e53e3e;
          color: white;
        }

        .btn-danger:hover:not(:disabled) {
          background-color: #c53030;
        }
      `}</style>
    </div>
  );
};

export default User;
