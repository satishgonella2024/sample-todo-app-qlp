"""
User Service Module

Handles all business logic related to User entity including:
- User registration and authentication
- User CRUD operations
- Password hashing and verification
- JWT token management
"""

from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID, uuid4
import logging

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from jose import JWTError, jwt

from models.user import User
from schemas.user import UserCreate, UserUpdate, UserResponse
from core.config import settings
from core.exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException,
    InvalidCredentialsException,
    UnauthorizedException
)

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """Service class for User entity operations"""

    def __init__(self, db: Session):
        """
        Initialize UserService with database session
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a plain text password
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain text password against hashed password
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password from database
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token
        
        Args:
            data: Data to encode in token
            expires_delta: Optional expiration time delta
            
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> dict:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            UnauthorizedException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.error(f"JWT verification failed: {str(e)}")
            raise UnauthorizedException("Invalid or expired token")

    def create(self, user_data: UserCreate) -> User:
        """
        Create a new user (registration)
        
        Args:
            user_data: User creation data
            
        Returns:
            Created User object
            
        Raises:
            UserAlreadyExistsException: If user with email already exists
        """
        try:
            # Check if user already exists
            existing_user = self.db.query(User).filter(
                User.email == user_data.email
            ).first()
            
            if existing_user:
                logger.warning(f"Attempt to register existing email: {user_data.email}")
                raise UserAlreadyExistsException(f"User with email {user_data.email} already exists")

            # Create new user with hashed password
            hashed_password = self.hash_password(user_data.password)
            
            db_user = User(
                id=uuid4(),
                email=user_data.email,
                name=user_data.name,
                password_hash=hashed_password,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            
            logger.info(f"User created successfully: {db_user.id}")
            return db_user
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error during user creation: {str(e)}")
            raise UserAlreadyExistsException(f"User with email {user_data.email} already exists")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise

    def read(self, user_id: UUID) -> User:
        """
        Read/retrieve a user by ID
        
        Args:
            user_id: UUID of the user
            
        Returns:
            User object
            
        Raises:
            UserNotFoundException: If user not found
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise UserNotFoundException(f"User with id {user_id} not found")
        
        return user

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address
        
        Args:
            email: User email address
            
        Returns:
            User object if found, None otherwise
        """
        user = self.db.query(User).filter(User.email == email).first()
        return user

    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all users with pagination
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of User objects
        """
        users = self.db.query(User).offset(skip).limit(limit).all()
        return users

    def update(self, user_id: UUID, user_data: UserUpdate) -> User:
        """
        Update user information
        
        Args:
            user_id: UUID of the user to update
            user_data: User update data
            
        Returns:
            Updated User object
            
        Raises:
            UserNotFoundException: If user not found
            UserAlreadyExistsException: If email already taken by another user
        """
        user = self.read(user_id)
        
        try:
            # Update fields if provided
            if user_data.email is not None:
                # Check if email is already taken by another user
                existing_user = self.db.query(User).filter(
                    User.email == user_data.email,
                    User.id != user_id
                ).first()
                
                if existing_user:
                    raise UserAlreadyExistsException(
                        f"Email {user_data.email} is already taken"
                    )
                user.email = user_data.email
            
            if user_data.name is not None:
                user.name = user_data.name
            
            if user_data.password is not None:
                user.password_hash = self.hash_password(user_data.password)
            
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"User updated successfully: {user_id}")
            return user
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error during user update: {str(e)}")
            raise UserAlreadyExistsException("Email already exists")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user: {str(e)}")
            raise

    def delete(self, user_id: UUID) -> bool:
        """
        Delete a user
        
        Args:
            user_id: UUID of the user to delete
            
        Returns:
            True if deletion successful
            
        Raises:
            UserNotFoundException: If user not found
        """
        user = self.read(user_id)
        
        try:
            self.db.delete(user)
            self.db.commit()
            
            logger.info(f"User deleted successfully: {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting user: {str(e)}")
            raise

    def register(self, user_data: UserCreate) -> tuple[User, str]:
        """
        Register a new user and generate access token
        
        Args:
            user_data: User registration data
            
        Returns:
            Tuple of (User object, access token)
        """
        user = self.create(user_data)
        
        # Generate access token
        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        logger.info(f"User registered successfully: {user.email}")
        return user, access_token

    def login(self, email: str, password: str) -> tuple[User, str]:
        """
        Authenticate user and generate access token
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Tuple of (User object, access token)
            
        Raises:
            InvalidCredentialsException: If credentials are invalid
        """
        user = self.get_by_email(email)
        
        if not user:
            logger.warning(f"Login attempt with non-existent email: {email}")
            raise InvalidCredentialsException("Invalid email or password")
        
        if not self.verify_password(password, user.password_hash):
            logger.warning(f"Invalid password attempt for user: {email}")
            raise InvalidCredentialsException("Invalid email or password")
        
        # Generate access token
        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        logger.info(f"User logged in successfully: {email}")
        return user, access_token

    def verify(self, token: str) -> User:
        """
        Verify JWT token and return associated user
        
        Args:
            token: JWT token string
            
        Returns:
            User object associated with token
            
        Raises:
            UnauthorizedException: If token is invalid
            UserNotFoundException: If user not found
        """
        payload = self.verify_token(token)
        
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise UnauthorizedException("Invalid token payload")
        
        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise UnauthorizedException("Invalid user ID in token")
        
        user = self.read(user_id)
        return user

    def logout(self, user_id: UUID) -> bool:
        """
        Logout user (token invalidation handled client-side or via token blacklist)
        
        Args:
            user_id: UUID of the user logging out
            
        Returns:
            True if logout successful
        """
        # Verify user exists
        self.read(user_id)
        
        logger.info(f"User logged out: {user_id}")
        return True

    def get_user_by_token(self, token: str) -> User:
        """
        Get user from JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            User object
        """
        return self.verify(token)

    def change_password(self, user_id: UUID, old_password: str, new_password: str) -> User:
        """
        Change user password
        
        Args:
            user_id: UUID of the user
            old_password: Current password
            new_password: New password
            
        Returns:
            Updated User object
            
        Raises:
            InvalidCredentialsException: If old password is incorrect
        """
        user = self.read(user_id)
        
        if not self.verify_password(old_password, user.password_hash):
            logger.warning(f"Invalid old password for user: {user_id}")
            raise InvalidCredentialsException("Current password is incorrect")
        
        user.password_hash = self.hash_password(new_password)
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"Password changed for user: {user_id}")
        return user

    def count(self) -> int:
        """
        Get total count of users
        
        Returns:
            Total number of users
        """
        return self.db.query(User).count()

    def exists(self, user_id: UUID) -> bool:
        """
        Check if user exists
        
        Args:
            user_id: UUID of the user
            
        Returns:
            True if user exists, False otherwise
        """
        return self.db.query(User).filter(User.id == user_id).first() is not None

    def email_exists(self, email: str) -> bool:
        """
        Check if email already exists
        
        Args:
            email: Email address to check
            
        Returns:
            True if email exists, False otherwise
        """
        return self.db.query(User).filter(User.email == email).first() is not None
