from datetime import datetime
from app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
import secrets


# Family model - represents a family unit with surname
class Family(db.Model):
    __tablename__ = 'families'
    id = db.Column(db.Integer, primary_key=True)
    surname = db.Column(db.String(100), nullable=False)
    invite_code = db.Column(db.String(20), unique=True, nullable=False)
    created_by = db.Column(db.String, nullable=True)
    description = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    members = db.relationship('User', back_populates='family', foreign_keys='User.family_id')
    
    @staticmethod
    def generate_invite_code():
        """Generate a unique 8-character invite code"""
        return secrets.token_urlsafe(6).upper()[:8]


# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    nickname = db.Column(db.String(100), nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)
    family_id = db.Column(db.Integer, db.ForeignKey('families.id'), nullable=True)
    is_family_admin = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    family = db.relationship('Family', back_populates='members', foreign_keys=[family_id])
    profile = db.relationship('FamilyProfile', back_populates='user', uselist=False, cascade='all, delete-orphan')
    events = db.relationship('Event', back_populates='creator', cascade='all, delete-orphan')
    chores = db.relationship('Chore', back_populates='assigned_to_user', foreign_keys='Chore.assigned_to')
    memories = db.relationship('Memory', back_populates='author', cascade='all, delete-orphan')
    photos = db.relationship('Photo', back_populates='uploader', cascade='all, delete-orphan')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', back_populates='sender', cascade='all, delete-orphan')
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', back_populates='receiver', cascade='all, delete-orphan')
    posts = db.relationship('Post', back_populates='author', cascade='all, delete-orphan')
    post_likes = db.relationship('PostLike', back_populates='user', cascade='all, delete-orphan')
    post_comments = db.relationship('PostComment', back_populates='author', cascade='all, delete-orphan')


# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)


class FamilyProfile(db.Model):
    __tablename__ = 'family_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), unique=True, nullable=False)
    age = db.Column(db.Integer)
    role = db.Column(db.String(100))  # Mom, Dad, Sister, Brother, Grandma, etc.
    interests = db.Column(db.Text)  # Comma-separated interests
    favorite_things = db.Column(db.Text)
    bio = db.Column(db.Text)
    
    # Legacy Section
    legacy_hope_remembered_for = db.Column(db.Text)
    legacy_impact_on_family = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    user = db.relationship('User', back_populates='profile')


class RemembranceMember(db.Model):
    __tablename__ = 'remembrance_members'
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey('families.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    birth_date = db.Column(db.Date)
    passing_date = db.Column(db.Date)
    role = db.Column(db.String(100))
    photo_url = db.Column(db.String(500))
    life_story = db.Column(db.Text)
    favorite_quote = db.Column(db.String(500))
    legacy = db.Column(db.Text)
    
    # Personal Connection & Memories (from submitter)
    relationship_to_submitter = db.Column(db.String(200))  # e.g., "My grandmother", "My father"
    favorite_memories = db.Column(db.Text)  # Cherished memories with them
    legacy_in_effect = db.Column(db.Text)  # How their legacy lives on without them
    
    # Genealogy & Heritage Information
    place_of_birth = db.Column(db.String(200))
    place_of_passing = db.Column(db.String(200))
    occupation = db.Column(db.String(200))
    achievements = db.Column(db.Text)  # Life accomplishments
    hobbies_interests = db.Column(db.Text)  # What they loved to do
    personality_traits = db.Column(db.Text)  # What made them unique
    special_traditions = db.Column(db.Text)  # Family traditions they started
    maiden_name = db.Column(db.String(100))  # For genealogy
    parents_names = db.Column(db.String(300))  # Mother and father's names
    siblings_names = db.Column(db.Text)  # Brothers and sisters
    children_names = db.Column(db.Text)  # Their children
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    memories = db.relationship('Memory', back_populates='remembrance_member', cascade='all, delete-orphan')


class Memory(db.Model):
    __tablename__ = 'memories'
    id = db.Column(db.Integer, primary_key=True)
    remembrance_member_id = db.Column(db.Integer, db.ForeignKey('remembrance_members.id'), nullable=False)
    author_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    memory_date = db.Column(db.Date)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    remembrance_member = db.relationship('RemembranceMember', back_populates='memories')
    author = db.relationship('User', back_populates='memories')


class Photo(db.Model):
    __tablename__ = 'photos'
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey('families.id'), nullable=False)
    uploader_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    album_name = db.Column(db.String(100), default='General')
    photo_url = db.Column(db.String(500), nullable=False)
    media_type = db.Column(db.String(20), default='photo')  # photo or video
    caption = db.Column(db.Text)
    photo_date = db.Column(db.Date)
    file_size = db.Column(db.Integer)  # Size in bytes
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    uploader = db.relationship('User', back_populates='photos')


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    family_id = db.Column(db.Integer, db.ForeignKey('families.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_type = db.Column(db.String(50))  # birthday, anniversary, gathering, etc.
    event_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    is_recurring = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    creator = db.relationship('User', back_populates='events')


class Chore(db.Model):
    __tablename__ = 'chores'
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey('families.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    assigned_to = db.Column(db.String, db.ForeignKey('users.id'))
    due_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    assigned_to_user = db.relationship('User', back_populates='chores', foreign_keys=[assigned_to])


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], back_populates='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], back_populates='received_messages')


# Data Marketplace & Crypto Token Models
class UserWallet(db.Model):
    __tablename__ = 'user_wallets'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), unique=True, nullable=False)
    ilah_hugh_balance = db.Column(db.Float, default=0.0)  # Ilah Hugh token balance
    wallet_address = db.Column(db.String(200))  # Optional blockchain wallet address
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    user = db.relationship('User', backref='wallet')
    transactions = db.relationship('TokenTransaction', back_populates='wallet', cascade='all, delete-orphan')


class DataConsent(db.Model):
    __tablename__ = 'data_consents'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), unique=True, nullable=False)
    consent_given = db.Column(db.Boolean, default=False)  # User opted in to sell data
    
    # Granular consent options
    share_profile_data = db.Column(db.Boolean, default=False)
    share_activity_data = db.Column(db.Boolean, default=False)
    share_interaction_data = db.Column(db.Boolean, default=False)
    
    consent_date = db.Column(db.DateTime)
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    user = db.relationship('User', backref='data_consent')


class TokenTransaction(db.Model):
    __tablename__ = 'token_transactions'
    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('user_wallets.id'), nullable=False)
    
    amount = db.Column(db.Float, nullable=False)  # Ilah Hugh tokens earned/transferred
    transaction_type = db.Column(db.String(50), default='data_earning')  # data_earning, bonus, withdrawal, transfer
    description = db.Column(db.String(500))
    data_category = db.Column(db.String(100))  # profile, activity, interaction, etc.
    
    external_address = db.Column(db.String(200))  # For withdrawals/transfers to external wallets
    status = db.Column(db.String(50), default='completed')  # completed, pending, failed
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    wallet = db.relationship('UserWallet', back_populates='transactions')


class Exchange(db.Model):
    __tablename__ = 'exchanges'
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(db.String(100), nullable=False)  # e.g., "Binance", "Coinbase", "Raydium"
    trading_pair = db.Column(db.String(50), nullable=False)  # e.g., "ILAH/USDT", "ILAH/SOL"
    exchange_url = db.Column(db.String(500))  # Direct link to trading page
    logo_url = db.Column(db.String(500))  # Exchange logo
    
    current_price = db.Column(db.Float, default=0.0)  # Current ILAH price on exchange
    volume_24h = db.Column(db.Float, default=0.0)  # 24h trading volume
    liquidity = db.Column(db.Float, default=0.0)  # Available liquidity
    
    is_active = db.Column(db.Boolean, default=True)  # Exchange is active/live
    listing_date = db.Column(db.DateTime)  # When ILAH was listed
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


# Social Feed Models
class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    family_id = db.Column(db.Integer, db.ForeignKey('families.id'), nullable=False)
    
    content = db.Column(db.Text, nullable=False)
    media_url = db.Column(db.String(500))  # Optional photo/video URL
    media_type = db.Column(db.String(20))  # photo or video
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    author = db.relationship('User', back_populates='posts')
    likes = db.relationship('PostLike', back_populates='post', cascade='all, delete-orphan')
    comments = db.relationship('PostComment', back_populates='post', cascade='all, delete-orphan')


class PostLike(db.Model):
    __tablename__ = 'post_likes'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    post = db.relationship('Post', back_populates='likes')
    user = db.relationship('User', back_populates='post_likes')
    
    # Ensure a user can only like a post once
    __table_args__ = (UniqueConstraint('post_id', 'user_id', name='unique_post_like'),)


class PostComment(db.Model):
    __tablename__ = 'post_comments'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    author_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    content = db.Column(db.Text, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    post = db.relationship('Post', back_populates='comments')
    author = db.relationship('User', back_populates='post_comments')


# Digital Family Scrapbook
class ScrapbookPage(db.Model):
    __tablename__ = 'scrapbook_pages'
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey('families.id'), nullable=False)
    creator_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.Date)  # Date of the event/memory
    
    # Content sections
    story = db.Column(db.Text)  # The narrative of the memory
    people_involved = db.Column(db.Text)  # Family members who were part of this moment
    location = db.Column(db.String(200))  # Where it happened
    
    # Media
    cover_photo_url = db.Column(db.String(500))
    
    # Tags and categorization
    tags = db.Column(db.Text)  # Comma-separated tags like "birthday, celebration, vacation"
    mood = db.Column(db.String(50))  # joy, nostalgia, adventure, etc.
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    creator = db.relationship('User', backref='scrapbook_pages')
    photos = db.relationship('ScrapbookPhoto', back_populates='scrapbook_page', cascade='all, delete-orphan')


class ScrapbookPhoto(db.Model):
    __tablename__ = 'scrapbook_photos'
    id = db.Column(db.Integer, primary_key=True)
    scrapbook_page_id = db.Column(db.Integer, db.ForeignKey('scrapbook_pages.id'), nullable=False)
    
    photo_url = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)  # For ordering photos in the scrapbook
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    scrapbook_page = db.relationship('ScrapbookPage', back_populates='photos')
