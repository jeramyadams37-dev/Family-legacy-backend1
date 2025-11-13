from flask import render_template, request, redirect, url_for, jsonify, flash
from flask_login import current_user
from app import db
from models import UserWallet, DataConsent, TokenTransaction, Exchange
from datetime import datetime
import random

def get_or_create_wallet(user_id):
    """Get existing wallet or create new one for user"""
    wallet = UserWallet.query.filter_by(user_id=user_id).first()
    if not wallet:
        wallet = UserWallet(user_id=user_id, ilah_hugh_balance=0.0)
        db.session.add(wallet)
        db.session.commit()
    return wallet

def get_or_create_consent(user_id):
    """Get existing consent record or create new one"""
    consent = DataConsent.query.filter_by(user_id=user_id).first()
    if not consent:
        consent = DataConsent(user_id=user_id, consent_given=False)
        db.session.add(consent)
        db.session.commit()
    return consent

def award_tokens(user_id, amount, description, data_category='general'):
    """Award Ilah Hugh tokens to a user"""
    wallet = get_or_create_wallet(user_id)
    wallet.ilah_hugh_balance += amount
    
    transaction = TokenTransaction(
        wallet_id=wallet.id,
        amount=amount,
        transaction_type='data_earning',
        description=description,
        data_category=data_category
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    return wallet.ilah_hugh_balance

def simulate_data_earnings(user_id):
    """Simulate daily data earnings based on user activity"""
    consent = get_or_create_consent(user_id)
    
    if not consent.consent_given:
        return 0
    
    total_earned = 0
    
    # Simulate earnings based on what data they're sharing
    if consent.share_profile_data:
        amount = round(random.uniform(0.5, 2.0), 2)
        award_tokens(user_id, amount, "Profile data contribution", "profile")
        total_earned += amount
    
    if consent.share_activity_data:
        amount = round(random.uniform(1.0, 3.0), 2)
        award_tokens(user_id, amount, "Activity data contribution", "activity")
        total_earned += amount
    
    if consent.share_interaction_data:
        amount = round(random.uniform(0.8, 2.5), 2)
        award_tokens(user_id, amount, "Interaction data contribution", "interaction")
        total_earned += amount
    
    return total_earned

def withdraw_tokens(user_id, amount, external_address, description="Token withdrawal to external wallet"):
    """Withdraw ILAH tokens to external wallet"""
    wallet = get_or_create_wallet(user_id)
    
    if wallet.ilah_hugh_balance < amount:
        return False, "Insufficient balance"
    
    if amount < 1.0:
        return False, "Minimum withdrawal is 1.0 ILAH"
    
    wallet.ilah_hugh_balance -= amount
    
    transaction = TokenTransaction(
        wallet_id=wallet.id,
        amount=-amount,
        transaction_type='withdrawal',
        description=description,
        external_address=external_address,
        status='pending'
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    return True, transaction.id

def get_all_exchanges():
    """Get all active exchange listings"""
    return Exchange.query.filter_by(is_active=True).order_by(Exchange.volume_24h.desc()).all()

def initialize_exchanges():
    """Initialize default exchange listings if none exist"""
    if Exchange.query.count() > 0:
        return
    
    default_exchanges = [
        {
            'name': 'Raydium (Solana DEX)',
            'trading_pair': 'ILAH/SOL',
            'exchange_url': 'https://raydium.io/swap/?inputCurrency=sol&outputCurrency=ILAH',
            'logo_url': 'https://raydium.io/logo.png',
            'current_price': 0.045,
            'volume_24h': 125000.0,
            'liquidity': 50000.0,
            'listing_date': datetime(2025, 10, 1)
        },
        {
            'name': 'Jupiter (Solana Aggregator)',
            'trading_pair': 'ILAH/USDC',
            'exchange_url': 'https://jup.ag/swap/USDC-ILAH',
            'logo_url': 'https://jup.ag/logo.png',
            'current_price': 0.044,
            'volume_24h': 89000.0,
            'liquidity': 35000.0,
            'listing_date': datetime(2025, 10, 5)
        },
        {
            'name': 'Orca (Solana DEX)',
            'trading_pair': 'ILAH/USDT',
            'exchange_url': 'https://www.orca.so/pools?tokens=ILAH',
            'logo_url': 'https://www.orca.so/logo.png',
            'current_price': 0.043,
            'volume_24h': 67000.0,
            'liquidity': 28000.0,
            'listing_date': datetime(2025, 10, 10)
        },
        {
            'name': 'Gate.io (CEX)',
            'trading_pair': 'ILAH/USDT',
            'exchange_url': 'https://www.gate.io/trade/ILAH_USDT',
            'logo_url': 'https://www.gate.io/logo.png',
            'current_price': 0.046,
            'volume_24h': 210000.0,
            'liquidity': 75000.0,
            'listing_date': datetime(2025, 10, 15)
        },
        {
            'name': 'MEXC (CEX)',
            'trading_pair': 'ILAH/USDT',
            'exchange_url': 'https://www.mexc.com/exchange/ILAH_USDT',
            'logo_url': 'https://www.mexc.com/logo.png',
            'current_price': 0.045,
            'volume_24h': 156000.0,
            'liquidity': 62000.0,
            'listing_date': datetime(2025, 10, 20)
        }
    ]
    
    for exchange_data in default_exchanges:
        exchange = Exchange(**exchange_data)
        db.session.add(exchange)
    
    db.session.commit()
