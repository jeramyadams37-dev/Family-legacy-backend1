from flask import session, render_template, request, redirect, url_for, jsonify, flash
from app import app, db
from replit_auth import require_login, make_replit_blueprint
from flask_login import current_user
from models import User, FamilyProfile, Event, Chore, Photo, Memory, RemembranceMember, Message, Family, UserWallet, DataConsent, TokenTransaction, Post, PostLike, PostComment, ScrapbookPage, ScrapbookPhoto
from ai_helper import get_family_ai_response, generate_family_tree_insights, suggest_family_activities
from email_helper import send_family_invite_email
from data_marketplace import get_or_create_wallet, get_or_create_consent, award_tokens, simulate_data_earnings
from upload_helper import save_uploaded_file, delete_uploaded_file
from datetime import datetime, timedelta
from sqlalchemy import or_
import os
import math

app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True


# Alternative simple logout route
@app.route('/logout')
def simple_logout():
    """Simple logout that just clears session and redirects home"""
    from flask_login import logout_user
    logout_user()
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))


@app.route('/')
def index():
    """Landing page for logged out users, home for logged in users"""
    if not current_user.is_authenticated:
        return render_template('landing.html')
    
    # Refresh user from database to ensure we have latest family_id
    db.session.refresh(current_user)
    
    # Check if user needs to setup their family
    if not current_user.family_id:
        return redirect(url_for('family_setup'))
    
    # Get user's profile or create one if it doesn't exist
    profile = FamilyProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = FamilyProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
    
    # Get upcoming events (next 30 days) for this family only
    upcoming_events = Event.query.filter(
        Event.family_id == current_user.family_id,
        Event.event_date >= datetime.now(),
        Event.event_date <= datetime.now() + timedelta(days=30)
    ).order_by(Event.event_date).limit(5).all()
    
    # Get pending chores for this family
    pending_chores = Chore.query.filter_by(
        family_id=current_user.family_id,
        assigned_to=current_user.id,
        status='pending'
    ).order_by(Chore.due_date).limit(5).all()
    
    # Get unread messages count
    unread_count = Message.query.filter_by(
        receiver_id=current_user.id,
        is_read=False
    ).count()
    
    # Get recent memories for this family only
    recent_memories = Memory.query.join(RemembranceMember).filter(
        RemembranceMember.family_id == current_user.family_id
    ).order_by(Memory.created_at.desc()).limit(3).all()
    
    return render_template('home.html',
                         profile=profile,
                         upcoming_events=upcoming_events,
                         pending_chores=pending_chores,
                         unread_count=unread_count,
                         recent_memories=recent_memories)


@app.route('/family/setup', methods=['GET', 'POST'])
@require_login
def family_setup():
    """Setup or join a family"""
    if current_user.family_id:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create':
            surname = request.form.get('surname')
            description = request.form.get('description')
            
            if not surname:
                flash('Family surname is required!', 'error')
                return redirect(url_for('family_setup'))
            
            # Generate unique invite code
            invite_code = Family.generate_invite_code()
            while Family.query.filter_by(invite_code=invite_code).first():
                invite_code = Family.generate_invite_code()
            
            # Create new family
            family = Family(
                surname=surname,
                invite_code=invite_code,
                created_by=current_user.id,
                description=description
            )
            db.session.add(family)
            db.session.flush()
            
            # Assign user to family and make them admin
            current_user.family_id = family.id
            current_user.is_family_admin = True
            db.session.commit()
            
            flash(f'Welcome to the {surname} family! Share your invite code: {invite_code}', 'success')
            return redirect(url_for('index'))
        
        elif action == 'join':
            invite_code = request.form.get('invite_code', '').strip().upper()
            
            if not invite_code:
                flash('Invite code is required!', 'error')
                return redirect(url_for('family_setup'))
            
            family = Family.query.filter_by(invite_code=invite_code).first()
            
            if not family:
                flash('Invalid invite code!', 'error')
                return redirect(url_for('family_setup'))
            
            # Join the family
            current_user.family_id = family.id
            db.session.commit()
            
            flash(f'Welcome to the {family.surname} family!', 'success')
            return redirect(url_for('index'))
    
    return render_template('family_setup.html')


@app.route('/family/manage')
@require_login
def manage_family():
    """Manage family settings and view invite code"""
    if not current_user.family_id:
        return redirect(url_for('family_setup'))
    
    family = Family.query.get(current_user.family_id)
    members = User.query.filter_by(family_id=family.id).all()
    
    return render_template('manage_family.html', family=family, members=members)


@app.route('/family/regenerate-invite', methods=['POST'])
@require_login
def regenerate_invite():
    """Regenerate family invite code (admin only)"""
    if not current_user.is_family_admin:
        flash('Only family administrators can regenerate invite codes.', 'error')
        return redirect(url_for('manage_family'))
    
    family = Family.query.get(current_user.family_id)
    
    # Generate new unique invite code
    new_code = Family.generate_invite_code()
    while Family.query.filter_by(invite_code=new_code).first():
        new_code = Family.generate_invite_code()
    
    family.invite_code = new_code
    db.session.commit()
    
    flash(f'New invite code generated: {new_code}', 'success')
    return redirect(url_for('manage_family'))


@app.route('/family/send-invite', methods=['POST'])
@require_login
def send_invite():
    """Send family invite via email"""
    if not current_user.family_id:
        flash('You must be part of a family to send invites.', 'error')
        return redirect(url_for('family_setup'))
    
    family = Family.query.get(current_user.family_id)
    recipient_email = request.form.get('recipient_email', '').strip()
    
    if not recipient_email:
        flash('Please provide a recipient email address.', 'error')
        return redirect(url_for('manage_family'))
    
    try:
        # Get the app URL
        app_url = request.url_root.rstrip('/')
        
        # Get inviter name
        inviter_name = current_user.first_name or 'A family member'
        
        # Send the invite email
        send_family_invite_email(
            recipient_email=recipient_email,
            family_name=family.surname,
            invite_code=family.invite_code,
            inviter_name=inviter_name,
            app_url=app_url
        )
        
        flash(f'Invite sent to {recipient_email}!', 'success')
    except Exception as e:
        flash(f'Failed to send invite: {str(e)}', 'error')
    
    return redirect(url_for('manage_family'))


@app.route('/profile/<user_id>')
@require_login
def view_profile(user_id):
    """View any family member's profile (within same family only)"""
    if not current_user.family_id:
        return redirect(url_for('family_setup'))
    
    user = User.query.get_or_404(user_id)
    
    # Security: Only allow viewing profiles within the same family
    if user.family_id != current_user.family_id:
        flash('You can only view profiles within your own family.', 'error')
        return redirect(url_for('family_members'))
    
    profile = FamilyProfile.query.filter_by(user_id=user_id).first()
    
    if not profile:
        profile = FamilyProfile(user_id=user_id)
        db.session.add(profile)
        db.session.commit()
    
    can_edit = (current_user.id == user_id)
    
    return render_template('profile.html', 
                         user=user, 
                         profile=profile, 
                         can_edit=can_edit)


@app.route('/profile/edit', methods=['GET', 'POST'])
@require_login
def edit_profile():
    """Edit own profile (users can only edit their own)"""
    profile = FamilyProfile.query.filter_by(user_id=current_user.id).first()
    
    if not profile:
        profile = FamilyProfile(user_id=current_user.id)
        db.session.add(profile)
    
    if request.method == 'POST':
        # Update user basic info
        current_user.first_name = request.form.get('first_name', '').strip()
        current_user.last_name = request.form.get('last_name', '').strip()
        current_user.nickname = request.form.get('nickname', '').strip()
        
        # Update profile fields
        profile.age = request.form.get('age', type=int)
        profile.role = request.form.get('role')
        profile.interests = request.form.get('interests')
        profile.favorite_things = request.form.get('favorite_things')
        profile.bio = request.form.get('bio')
        profile.legacy_hope_remembered_for = request.form.get('legacy_hope_remembered_for')
        profile.legacy_impact_on_family = request.form.get('legacy_impact_on_family')
        
        db.session.commit()
        flash('✅ Profile updated successfully!', 'success')
        return redirect(url_for('view_profile', user_id=current_user.id))
    
    return render_template('edit_profile.html', profile=profile)


@app.route('/family')
@require_login
def family_members():
    """View all family members"""
    if not current_user.family_id:
        return redirect(url_for('family_setup'))
    
    members = User.query.filter_by(family_id=current_user.family_id).all()
    family = Family.query.get(current_user.family_id)
    return render_template('family_members.html', members=members, family=family)


@app.route('/calendar')
@require_login
def calendar():
    """Shared family calendar with events and chores"""
    if not current_user.family_id:
        return redirect(url_for('family_setup'))
    
    events = Event.query.filter_by(family_id=current_user.family_id).order_by(Event.event_date).all()
    chores = Chore.query.filter_by(family_id=current_user.family_id).order_by(Chore.due_date).all()
    
    return render_template('calendar.html', events=events, chores=chores)


@app.route('/event/create', methods=['GET', 'POST'])
@require_login
def create_event():
    """Create a new family event"""
    if not current_user.family_id:
        return redirect(url_for('family_setup'))
    
    if request.method == 'POST':
        event_date_str = request.form.get('event_date')
        if not event_date_str:
            flash('Event date is required!', 'error')
            return redirect(url_for('create_event'))
        
        event = Event(
            creator_id=current_user.id,
            family_id=current_user.family_id,
            title=request.form.get('title'),
            description=request.form.get('description'),
            event_type=request.form.get('event_type'),
            event_date=datetime.fromisoformat(event_date_str),
            location=request.form.get('location'),
            is_recurring=request.form.get('is_recurring') == 'on'
        )
        db.session.add(event)
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('calendar'))
    
    return render_template('create_event.html')


@app.route('/chore/create', methods=['GET', 'POST'])
@require_login
def create_chore():
    """Create a new chore"""
    if not current_user.family_id:
        return redirect(url_for('family_setup'))
    
    if request.method == 'POST':
        chore = Chore(
            family_id=current_user.family_id,
            title=request.form.get('title'),
            description=request.form.get('description'),
            assigned_to=request.form.get('assigned_to'),
            due_date=datetime.fromisoformat(request.form.get('due_date')) if request.form.get('due_date') else None,
            priority=request.form.get('priority', 'medium')
        )
        db.session.add(chore)
        db.session.commit()
        flash('Chore created successfully!', 'success')
        return redirect(url_for('calendar'))
    
    family_members = User.query.filter_by(family_id=current_user.family_id).all()
    return render_template('create_chore.html', family_members=family_members)


@app.route('/chore/<int:chore_id>/update', methods=['POST'])
@require_login
def update_chore_status(chore_id):
    """Update chore status"""
    chore = Chore.query.get_or_404(chore_id)
    
    # Security: Only allow updating chores within the same family
    if chore.family_id != current_user.family_id:
        return jsonify({'success': False, 'error': 'Not authorized'}), 403
    
    if chore.assigned_to == current_user.id:
        chore.status = request.form.get('status', 'pending')
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Not authorized'}), 403


@app.route('/remembrance')
@require_login
def remembrance():
    """Memorial page for beloved family members who have passed"""
    if not current_user.family_id:
        return redirect(url_for('family_setup'))
    
    remembered_members = RemembranceMember.query.filter_by(family_id=current_user.family_id).all()
    return render_template('remembrance.html', remembered_members=remembered_members)


@app.route('/remembrance/<int:member_id>')
@require_login
def remembrance_detail(member_id):
    """Detailed memorial page with memories"""
    member = RemembranceMember.query.get_or_404(member_id)
    
    # Security: Only allow viewing remembrance members within the same family
    if member.family_id != current_user.family_id:
        flash('You can only view remembrance pages within your own family.', 'error')
        return redirect(url_for('remembrance'))
    
    tributes = Memory.query.filter_by(remembrance_member_id=member_id).order_by(Memory.created_at.desc()).all()
    return render_template('remembrance_detail.html', member=member, tributes=tributes)


@app.route('/remembrance/add', methods=['POST'])
@require_login
def add_remembrance_member():
    """Add a new member to the remembrance wall"""
    if not current_user.family_id:
        flash('❌ Please join a family first', 'error')
        return redirect(url_for('family_setup'))
    
    name = request.form.get('name', '').strip()
    if not name:
        flash('❌ Name is required', 'error')
        return redirect(url_for('remembrance'))
    
    # Parse dates
    birth_date = None
    passing_date = None
    
    try:
        if request.form.get('birth_date') and request.form.get('birth_date').strip():
            birth_date = datetime.strptime(request.form.get('birth_date').strip(), '%Y-%m-%d').date()
        if request.form.get('passing_date') and request.form.get('passing_date').strip():
            passing_date = datetime.strptime(request.form.get('passing_date').strip(), '%Y-%m-%d').date()
    except ValueError as e:
        flash('❌ Invalid date format. Please use the date picker or format dates as YYYY-MM-DD', 'error')
        return redirect(url_for('remembrance'))
    
    # Handle photo upload
    photo_url = None
    if 'photo' in request.files:
        file = request.files['photo']
        if file and file.filename:
            photo_url, _, _ = save_uploaded_file(file)
    
    member = RemembranceMember(
        family_id=current_user.family_id,
        name=name,
        birth_date=birth_date,
        passing_date=passing_date,
        role=request.form.get('role', '').strip(),
        photo_url=photo_url,
        life_story=request.form.get('life_story', '').strip(),
        favorite_quote=request.form.get('favorite_quote', '').strip(),
        legacy=request.form.get('legacy', '').strip(),
        
        # Personal Connection & Memories
        relationship_to_submitter=request.form.get('relationship_to_submitter', '').strip(),
        favorite_memories=request.form.get('favorite_memories', '').strip(),
        legacy_in_effect=request.form.get('legacy_in_effect', '').strip(),
        
        # Genealogy & Heritage
        place_of_birth=request.form.get('place_of_birth', '').strip(),
        place_of_passing=request.form.get('place_of_passing', '').strip(),
        occupation=request.form.get('occupation', '').strip(),
        achievements=request.form.get('achievements', '').strip(),
        hobbies_interests=request.form.get('hobbies_interests', '').strip(),
        personality_traits=request.form.get('personality_traits', '').strip(),
        special_traditions=request.form.get('special_traditions', '').strip(),
        maiden_name=request.form.get('maiden_name', '').strip(),
        parents_names=request.form.get('parents_names', '').strip(),
        siblings_names=request.form.get('siblings_names', '').strip(),
        children_names=request.form.get('children_names', '').strip()
    )
    
    db.session.add(member)
    db.session.commit()
    
    flash(f'✅ {name} has been added to the remembrance wall', 'success')
    return redirect(url_for('remembrance'))


@app.route('/remembrance/<int:member_id>/edit', methods=['GET', 'POST'])
@require_login
def edit_remembrance_member(member_id):
    """Edit a remembrance member"""
    member = RemembranceMember.query.get_or_404(member_id)
    
    # Security: Only allow editing remembrance members within the same family
    if member.family_id != current_user.family_id:
        flash('❌ You can only edit remembrance members within your own family.', 'error')
        return redirect(url_for('remembrance'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('❌ Name is required', 'error')
            return redirect(url_for('edit_remembrance_member', member_id=member_id))
        
        # Parse dates
        birth_date = None
        passing_date = None
        
        try:
            if request.form.get('birth_date') and request.form.get('birth_date').strip():
                birth_date = datetime.strptime(request.form.get('birth_date').strip(), '%Y-%m-%d').date()
            if request.form.get('passing_date') and request.form.get('passing_date').strip():
                passing_date = datetime.strptime(request.form.get('passing_date').strip(), '%Y-%m-%d').date()
        except ValueError as e:
            flash('❌ Invalid date format. Please use the date picker or format dates as YYYY-MM-DD', 'error')
            return redirect(url_for('edit_remembrance_member', member_id=member_id))
        
        # Handle photo upload
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename:
                photo_url, _, _ = save_uploaded_file(file)
                member.photo_url = photo_url
        
        # Update member fields
        member.name = name
        member.birth_date = birth_date
        member.passing_date = passing_date
        member.role = request.form.get('role', '').strip()
        member.life_story = request.form.get('life_story', '').strip()
        member.favorite_quote = request.form.get('favorite_quote', '').strip()
        member.legacy = request.form.get('legacy', '').strip()
        
        # Personal Connection & Memories
        member.relationship_to_submitter = request.form.get('relationship_to_submitter', '').strip()
        member.favorite_memories = request.form.get('favorite_memories', '').strip()
        member.legacy_in_effect = request.form.get('legacy_in_effect', '').strip()
        
        # Genealogy & Heritage
        member.place_of_birth = request.form.get('place_of_birth', '').strip()
        member.place_of_passing = request.form.get('place_of_passing', '').strip()
        member.occupation = request.form.get('occupation', '').strip()
        member.achievements = request.form.get('achievements', '').strip()
        member.hobbies_interests = request.form.get('hobbies_interests', '').strip()
        member.personality_traits = request.form.get('personality_traits', '').strip()
        member.special_traditions = request.form.get('special_traditions', '').strip()
        member.maiden_name = request.form.get('maiden_name', '').strip()
        member.parents_names = request.form.get('parents_names', '').strip()
        member.siblings_names = request.form.get('siblings_names', '').strip()
        member.children_names = request.form.get('children_names', '').strip()
        
        db.session.commit()
        flash(f'✅ {name}\'s remembrance has been updated', 'success')
        return redirect(url_for('remembrance_detail', member_id=member_id))
    
    return render_template('edit_remembrance.html', member=member)


@app.route('/remembrance/<int:member_id>/memory', methods=['POST'])
@require_login
def add_memory(member_id):
    """Add a memory/comment about a beloved family member"""
    member = RemembranceMember.query.get_or_404(member_id)
    
    # Security: Only allow adding memories for remembrance members within the same family
    if member.family_id != current_user.family_id:
        flash('You can only add memories for remembrance members within your own family.', 'error')
        return redirect(url_for('remembrance'))
    
    memory = Memory(
        remembrance_member_id=member_id,
        author_id=current_user.id,
        title=request.form.get('title'),
        content=request.form.get('content'),
        memory_date=datetime.fromisoformat(request.form.get('memory_date')) if request.form.get('memory_date') else None
    )
    db.session.add(memory)
    db.session.commit()
    flash('Memory shared successfully!', 'success')
    return redirect(url_for('remembrance_detail', member_id=member_id))


@app.route('/remembrance/<int:member_id>/tribute', methods=['POST'])
@require_login
def add_remembrance_tribute(member_id):
    """Add a tribute to a beloved family member"""
    member = RemembranceMember.query.get_or_404(member_id)
    
    # Security: Only allow adding tributes for remembrance members within the same family
    if member.family_id != current_user.family_id:
        flash('You can only add tributes for remembrance members within your own family.', 'error')
        return redirect(url_for('remembrance'))
    
    tribute_content = request.form.get('tribute_content', '').strip()
    if not tribute_content:
        flash('Please write a tribute message.', 'error')
        return redirect(url_for('remembrance_detail', member_id=member_id))
    
    memory = Memory(
        remembrance_member_id=member_id,
        author_id=current_user.id,
        title=None,
        content=tribute_content,
        memory_date=None
    )
    db.session.add(memory)
    db.session.commit()
    flash('🕊️ Tribute shared successfully!', 'success')
    return redirect(url_for('remembrance_detail', member_id=member_id))


@app.route('/photos')
@require_login
def photos():
    """Photo gallery"""
    if not current_user.family_id:
        return redirect(url_for('family_setup'))
    
    all_photos = Photo.query.filter_by(family_id=current_user.family_id).order_by(Photo.created_at.desc()).all()
    
    # Group photos by album
    albums = {}
    for photo in all_photos:
        album_name = photo.album_name or 'General'
        if album_name not in albums:
            albums[album_name] = []
        albums[album_name].append(photo)
    
    return render_template('photos.html', albums=albums)


@app.route('/messages')
@require_login
def messages():
    """View messages"""
    if not current_user.family_id:
        return redirect(url_for('family_setup'))
    
    received = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.created_at.desc()).all()
    sent = Message.query.filter_by(sender_id=current_user.id).order_by(Message.created_at.desc()).all()
    
    # Mark received messages as read
    for msg in received:
        if not msg.is_read:
            msg.is_read = True
    db.session.commit()
    
    # Only show family members from the same family
    family_members = User.query.filter(
        User.id != current_user.id,
        User.family_id == current_user.family_id
    ).all()
    
    return render_template('messages.html', 
                         received_messages=received, 
                         sent_messages=sent,
                         family_members=family_members)


@app.route('/messages/send', methods=['POST'])
@require_login
def send_message():
    """Send a message to another family member"""
    receiver_id = request.form.get('receiver_id')
    receiver = User.query.get(receiver_id)
    
    # Security: Only allow sending messages within the same family
    if not receiver or receiver.family_id != current_user.family_id:
        flash('You can only send messages to members of your own family.', 'error')
        return redirect(url_for('messages'))
    
    message = Message(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=request.form.get('content')
    )
    db.session.add(message)
    db.session.commit()
    flash('Message sent!', 'success')
    return redirect(url_for('messages'))


@app.route('/video-call')
@require_login
def video_call():
    """Video calling page with Jitsi Meet integration"""
    if not current_user.family_id:
        return redirect(url_for('family_setup'))
    
    family = Family.query.get(current_user.family_id)
    family_members = User.query.filter(
        User.family_id == current_user.family_id
    ).all()
    
    # Check if joining a specific room
    with_user_id = request.args.get('with_user')
    family_room = request.args.get('family_room')
    
    room_name = None
    caller_name = None
    
    if family_room:
        # Create a family group room
        room_name = f"FamilyHub_{family.surname}_{family.id}"
        caller_name = f"{family.surname} Family"
    elif with_user_id:
        # Create a one-on-one room
        other_user = User.query.get(with_user_id)
        if other_user and other_user.family_id == current_user.family_id:
            # Create consistent room name regardless of who initiates
            user_ids = sorted([current_user.id, other_user.id])
            room_name = f"FamilyHub_Private_{user_ids[0]}_{user_ids[1]}"
            caller_name = f"{other_user.first_name} {other_user.last_name}"
    
    return render_template('video_call.html', 
                         family_members=family_members,
                         family=family,
                         room_name=room_name,
                         caller_name=caller_name)


@app.route('/ai-helper', methods=['GET', 'POST'])
@require_login
def ai_helper():
    """AI Family Helper chat interface with rich context"""
    if not current_user.family_id:
        return redirect(url_for('family_setup'))
    
    response_text = None
    
    if request.method == 'POST':
        user_question = request.form.get('question')
        
        # Gather comprehensive family context for AI
        family = Family.query.get(current_user.family_id)
        members = User.query.filter_by(family_id=current_user.family_id).all()
        profiles = FamilyProfile.query.join(User).filter(User.family_id == current_user.family_id).all()
        
        # Build detailed family context
        family_context = f"The {family.surname} Family\n"
        family_context += f"Total Members: {len(members)}\n\n"
        
        # Member details
        family_context += "Family Members:\n"
        for user in members:
            profile = next((p for p in profiles if p.user_id == user.id), None)
            if profile and profile.age:
                family_context += f"- {user.first_name} {user.last_name}: Age {profile.age}"
                if profile.role:
                    family_context += f", Role: {profile.role}"
                if profile.interests:
                    family_context += f", Interests: {profile.interests}"
                family_context += "\n"
            else:
                family_context += f"- {user.first_name} {user.last_name}\n"
        
        # Upcoming events
        upcoming_events = Event.query.filter(
            Event.family_id == current_user.family_id,
            Event.event_date >= datetime.now()
        ).order_by(Event.event_date).limit(5).all()
        
        if upcoming_events:
            family_context += f"\nUpcoming Events ({len(upcoming_events)}):\n"
            for event in upcoming_events:
                family_context += f"- {event.title} on {event.event_date.strftime('%B %d, %Y')}"
                if event.location:
                    family_context += f" at {event.location}"
                family_context += "\n"
        
        # Recent memories/activities
        recent_memories_count = Memory.query.join(RemembranceMember).filter(
            RemembranceMember.family_id == current_user.family_id
        ).count()
        
        if recent_memories_count > 0:
            family_context += f"\nShared Memories: {recent_memories_count} memories preserved\n"
        
        # Pending chores
        pending_chores_count = Chore.query.filter_by(
            family_id=current_user.family_id,
            status='pending'
        ).count()
        
        if pending_chores_count > 0:
            family_context += f"Active Chores: {pending_chores_count} tasks\n"
        
        family_context += f"\nCurrent User: {current_user.first_name} {current_user.last_name}"
        
        response_text = get_family_ai_response(user_question, family_context)
    
    return render_template('ai_helper.html', response=response_text)


@app.route('/ai-helper/insights')
@require_login
def ai_insights():
    """Get AI-generated family insights with comprehensive data"""
    if not current_user.family_id:
        return redirect(url_for('family_setup'))
    
    # Gather comprehensive family data
    family = Family.query.get(current_user.family_id)
    members = User.query.filter_by(family_id=current_user.family_id).all()
    profiles = FamilyProfile.query.join(User).filter(User.family_id == current_user.family_id).all()
    
    family_data = f"The {family.surname} Family Analysis\n\n"
    family_data += f"Total Family Members: {len(members)}\n\n"
    
    family_data += "Detailed Member Profiles:\n"
    for user in members:
        profile = next((p for p in profiles if p.user_id == user.id), None)
        family_data += f"\n{user.first_name} {user.last_name}:\n"
        if profile:
            if profile.age:
                family_data += f"  - Age: {profile.age}\n"
            if profile.role:
                family_data += f"  - Role: {profile.role}\n"
            if profile.interests:
                family_data += f"  - Interests: {profile.interests}\n"
            if profile.bio:
                family_data += f"  - Bio: {profile.bio[:100]}...\n" if len(profile.bio) > 100 else f"  - Bio: {profile.bio}\n"
            if profile.legacy_hope_remembered_for:
                family_data += f"  - Hopes to be Remembered For: {profile.legacy_hope_remembered_for[:100]}...\n" if len(profile.legacy_hope_remembered_for) > 100 else f"  - Hopes to be Remembered For: {profile.legacy_hope_remembered_for}\n"
            if profile.legacy_impact_on_family:
                family_data += f"  - Legacy Impact: {profile.legacy_impact_on_family[:100]}...\n" if len(profile.legacy_impact_on_family) > 100 else f"  - Legacy Impact: {profile.legacy_impact_on_family}\n"
        else:
            family_data += "  - Profile incomplete\n"
    
    # Add event data
    total_events = Event.query.filter_by(family_id=current_user.family_id).count()
    family_data += f"\n\nFamily Activities:\n"
    family_data += f"- Total Events Created: {total_events}\n"
    
    # Add memory data
    remembrance_count = RemembranceMember.query.filter_by(family_id=current_user.family_id).count()
    if remembrance_count > 0:
        family_data += f"- Remembrance Pages: {remembrance_count} beloved members honored\n"
    
    insights = generate_family_tree_insights(family_data)
    
    return render_template('ai_insights.html', insights=insights)


@app.route('/ai-helper/activity-suggestions')
@require_login
def ai_activity_suggestions():
    """Get AI-generated activity suggestions with rich context"""
    if not current_user.family_id:
        return redirect(url_for('family_setup'))
    
    # Gather comprehensive family info
    family = Family.query.get(current_user.family_id)
    profiles = FamilyProfile.query.join(User).filter(User.family_id == current_user.family_id).all()
    events = Event.query.filter(
        Event.family_id == current_user.family_id,
        Event.event_date >= datetime.now()
    ).order_by(Event.event_date).limit(5).all()
    
    family_info = f"The {family.surname} Family\n\n"
    family_info += "Family Members:\n"
    for profile in profiles:
        user = User.query.get(profile.user_id)
        if user:
            family_info += f"- {user.first_name} {user.last_name}"
            if profile.age:
                family_info += f" (Age {profile.age})"
            if profile.role:
                family_info += f" - {profile.role}"
            if profile.interests:
                family_info += f"\n  Interests: {profile.interests}"
            if profile.favorite_things:
                family_info += f"\n  Favorites: {profile.favorite_things}"
            family_info += "\n"
    
    events_info = ""
    if events:
        events_info = "Upcoming Events:\n"
        for event in events:
            events_info += f"- {event.title} on {event.event_date.strftime('%B %d, %Y')}"
            if event.location:
                events_info += f" at {event.location}"
            events_info += "\n"
    
    # Get current season
    month = datetime.now().month
    if month in [3, 4, 5]:
        season = "Spring"
    elif month in [6, 7, 8]:
        season = "Summer"
    elif month in [9, 10, 11]:
        season = "Fall"
    else:
        season = "Winter"
    
    suggestions = suggest_family_activities(family_info, events_info, season)
    
    return render_template('ai_activity_suggestions.html', suggestions=suggestions)


# API endpoints
@app.route('/api/messages/unread-count')
@require_login
def unread_count():
    """Get count of unread messages"""
    count = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})


# Data Marketplace & Ilah Hughs Token Routes
@app.route('/data-marketplace')
@require_login
def data_marketplace():
    """Data marketplace dashboard showing token balance and earnings"""
    if not current_user.family_id:
        return redirect(url_for('family_setup'))
    
    wallet = get_or_create_wallet(current_user.id)
    consent = get_or_create_consent(current_user.id)
    
    # Get recent transactions
    transactions = TokenTransaction.query.filter_by(wallet_id=wallet.id).order_by(
        TokenTransaction.created_at.desc()
    ).limit(20).all()
    
    # Calculate earnings summary
    total_earned = sum(t.amount for t in TokenTransaction.query.filter_by(
        wallet_id=wallet.id,
        transaction_type='data_earning'
    ).all())
    
    # Get earnings by category
    earnings_by_category = db.session.query(
        TokenTransaction.data_category,
        db.func.sum(TokenTransaction.amount).label('total')
    ).filter_by(wallet_id=wallet.id).group_by(TokenTransaction.data_category).all()
    
    return render_template('data_marketplace.html',
                         wallet=wallet,
                         consent=consent,
                         transactions=transactions,
                         total_earned=total_earned,
                         earnings_by_category=earnings_by_category)


@app.route('/data-marketplace/consent', methods=['POST'])
@require_login
def update_data_consent():
    """Update user's data sharing consent preferences"""
    consent = get_or_create_consent(current_user.id)
    
    consent.consent_given = request.form.get('consent_given') == 'on'
    consent.share_profile_data = request.form.get('share_profile_data') == 'on'
    consent.share_activity_data = request.form.get('share_activity_data') == 'on'
    consent.share_interaction_data = request.form.get('share_interaction_data') == 'on'
    
    if consent.consent_given:
        consent.consent_date = datetime.now()
    
    db.session.commit()
    
    # Award welcome bonus if first time opting in
    if consent.consent_given and not TokenTransaction.query.filter_by(
        wallet_id=get_or_create_wallet(current_user.id).id
    ).first():
        award_tokens(current_user.id, 10.0, "Welcome bonus for joining data marketplace!", "bonus")
        flash('🎉 Congratulations! You earned 10 ILAH tokens as a welcome bonus!', 'success')
    
    flash('✅ Data sharing preferences updated successfully!', 'success')
    return redirect(url_for('data_marketplace'))


@app.route('/data-marketplace/simulate-earnings', methods=['POST'])
@require_login
def simulate_earnings():
    """Simulate daily earnings (for demonstration)"""
    earned = simulate_data_earnings(current_user.id)
    
    if earned > 0:
        flash(f'✨ You earned {earned:.2f} ILAH tokens from your data contributions!', 'success')
    else:
        flash('⚠️ Enable data sharing in your privacy settings to start earning ILAH tokens!', 'warning')
    
    return redirect(url_for('data_marketplace'))


@app.route('/exchanges')
@require_login
def exchange_listings():
    """View cryptocurrency exchanges where ILAH is listed"""
    if not current_user.family_id:
        return redirect(url_for('family_setup'))
    
    from data_marketplace import get_all_exchanges, initialize_exchanges
    
    initialize_exchanges()
    exchanges = get_all_exchanges()
    
    wallet = get_or_create_wallet(current_user.id)
    
    avg_price = sum(e.current_price for e in exchanges) / len(exchanges) if exchanges else 0
    total_volume = sum(e.volume_24h for e in exchanges)
    
    return render_template('exchange_listings.html',
                         exchanges=exchanges,
                         wallet=wallet,
                         avg_price=avg_price,
                         total_volume=total_volume)


@app.route('/withdraw-tokens', methods=['POST'])
@require_login
def withdraw_tokens_route():
    """Withdraw ILAH tokens to external Solana wallet"""
    from data_marketplace import withdraw_tokens
    
    amount_str = str(request.form.get('amount', '0')).strip()
    external_address = request.form.get('external_address', '').strip()
    
    if not external_address:
        flash('❌ Please provide a valid Solana wallet address', 'error')
        return redirect(url_for('exchange_listings'))
    
    if amount_str.lower() in ('nan', 'inf', '-inf', 'infinity', '-infinity'):
        flash('❌ Please enter a valid withdrawal amount', 'error')
        return redirect(url_for('exchange_listings'))
    
    try:
        amount = float(amount_str)
    except (ValueError, TypeError):
        flash('❌ Please enter a valid withdrawal amount', 'error')
        return redirect(url_for('exchange_listings'))
    
    if math.isnan(amount) or math.isinf(amount) or amount <= 0:
        flash('❌ Please enter a valid withdrawal amount', 'error')
        return redirect(url_for('exchange_listings'))
    
    success, message = withdraw_tokens(current_user.id, amount, external_address)
    
    if success:
        flash(f'✅ Withdrawal initiated! {amount} ILAH will be sent to {external_address[:10]}...', 'success')
    else:
        flash(f'❌ Withdrawal failed: {message}', 'error')
    
    return redirect(url_for('exchange_listings'))


@app.route('/photo/upload', methods=['POST'])
@require_login
def upload_photo():
    """Handle photo/video upload to gallery"""
    if 'file' not in request.files:
        flash('❌ No file selected', 'error')
        return redirect(url_for('photos'))
    
    file = request.files['file']
    file_url, media_type, file_size = save_uploaded_file(file)
    
    if not file_url:
        flash('❌ Invalid file or file too large (max 50MB)', 'error')
        return redirect(url_for('photos'))
    
    # Create photo/video record
    photo = Photo(
        family_id=current_user.family_id,
        uploader_id=current_user.id,
        album_name=request.form.get('album_name', 'General'),
        photo_url=file_url,
        media_type=media_type,
        caption=request.form.get('caption', ''),
        file_size=file_size
    )
    
    db.session.add(photo)
    db.session.commit()
    
    media_name = 'Video' if media_type == 'video' else 'Photo'
    flash(f'✅ {media_name} uploaded successfully!', 'success')
    return redirect(url_for('photos'))


@app.route('/feed/<user_id>')
@require_login
def personal_feed(user_id):
    """View a family member's personal wall/feed"""
    # Get user
    user = User.query.get_or_404(user_id)
    
    # Ensure user is in same family
    if user.family_id != current_user.family_id:
        flash('❌ Access denied', 'error')
        return redirect(url_for('index'))
    
    # Get user's posts (newest first)
    posts = Post.query.filter_by(
        author_id=user_id
    ).order_by(Post.created_at.desc()).all()
    
    # Get user profile
    profile = FamilyProfile.query.filter_by(user_id=user_id).first()
    
    return render_template('personal_feed.html', 
                          feed_user=user, 
                          profile=profile,
                          posts=posts)


@app.route('/post/create', methods=['POST'])
@require_login
def create_post():
    """Create a new post on personal wall"""
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('❌ Post content cannot be empty', 'error')
        return redirect(url_for('personal_feed', user_id=current_user.id))
    
    # Handle optional media upload
    media_url = None
    media_type = None
    
    if 'media' in request.files:
        file = request.files['media']
        if file and file.filename:
            media_url, media_type, _ = save_uploaded_file(file)
    
    # Create post
    post = Post(
        author_id=current_user.id,
        family_id=current_user.family_id,
        content=content,
        media_url=media_url,
        media_type=media_type
    )
    
    db.session.add(post)
    db.session.commit()
    
    # AI-powered scrapbook suggestion
    scrapbook_suggestion = None
    try:
        # Analyze if this moment might be worth scrapbooking
        prompt = f"""Analyze this family post and determine if it's a special moment worth preserving in a scrapbook.

Post content: "{content}"
Has media: {media_url is not None}

If this seems like a meaningful family moment (celebration, milestone, special memory, achievement, gathering, tradition, etc.), 
respond with a brief, warm suggestion to create a scrapbook page (1-2 sentences max).
If it's just a casual update, respond with only "NO_SUGGESTION".

Be selective - only suggest scrapbooking for truly special moments."""

        ai_response = get_family_ai_response(current_user.family_id, prompt)
        
        if ai_response and "NO_SUGGESTION" not in ai_response:
            scrapbook_suggestion = ai_response.strip()
    except Exception as e:
        pass
    
    flash('✅ Post created successfully!', 'success')
    
    # Show scrapbook suggestion if AI detected a special moment
    if scrapbook_suggestion:
        flash(f'✨ {scrapbook_suggestion} <a href="/scrapbook/create" style="color: white; text-decoration: underline; font-weight: bold;">Create Scrapbook Page →</a>', 'success')
    
    return redirect(url_for('personal_feed', user_id=current_user.id))


@app.route('/post/<int:post_id>/like', methods=['POST'])
@require_login
def like_post(post_id):
    """Like or unlike a post"""
    post = Post.query.get_or_404(post_id)
    
    # Ensure post is from same family
    if post.family_id != current_user.family_id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Check if already liked
    existing_like = PostLike.query.filter_by(
        post_id=post_id,
        user_id=current_user.id
    ).first()
    
    if existing_like:
        # Unlike
        db.session.delete(existing_like)
        db.session.commit()
        liked = False
    else:
        # Like
        like = PostLike(post_id=post_id, user_id=current_user.id)
        db.session.add(like)
        db.session.commit()
        liked = True
    
    # Return updated like count
    like_count = PostLike.query.filter_by(post_id=post_id).count()
    
    return jsonify({
        'liked': liked,
        'like_count': like_count
    })


@app.route('/post/<int:post_id>/comment', methods=['POST'])
@require_login
def comment_on_post(post_id):
    """Add a comment to a post"""
    post = Post.query.get_or_404(post_id)
    
    # Ensure post is from same family
    if post.family_id != current_user.family_id:
        flash('❌ Access denied', 'error')
        return redirect(url_for('index'))
    
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('❌ Comment cannot be empty', 'error')
        return redirect(url_for('personal_feed', user_id=post.author_id))
    
    # Create comment
    comment = PostComment(
        post_id=post_id,
        author_id=current_user.id,
        content=content
    )
    
    db.session.add(comment)
    db.session.commit()
    
    flash('✅ Comment added!', 'success')
    return redirect(url_for('personal_feed', user_id=post.author_id))


@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@require_login
def edit_post(post_id):
    """Edit a post (owner only)"""
    post = Post.query.get_or_404(post_id)
    
    # Only author can edit their post
    if post.author_id != current_user.id:
        flash('❌ You can only edit your own posts', 'error')
        return redirect(url_for('personal_feed', user_id=post.author_id))
    
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        
        if not content:
            flash('❌ Post content cannot be empty', 'error')
            return redirect(url_for('edit_post', post_id=post_id))
        
        post.content = content
        post.updated_at = datetime.now()
        db.session.commit()
        
        flash('✅ Post updated successfully!', 'success')
        return redirect(url_for('personal_feed', user_id=current_user.id))
    
    return render_template('edit_post.html', post=post)


@app.route('/post/<int:post_id>/delete', methods=['POST'])
@require_login
def delete_post(post_id):
    """Delete a post (owner only)"""
    post = Post.query.get_or_404(post_id)
    
    # Only author can delete their post
    if post.author_id != current_user.id:
        flash('❌ You can only delete your own posts', 'error')
        return redirect(url_for('personal_feed', user_id=post.author_id))
    
    # Delete media file if exists
    if post.media_url:
        delete_uploaded_file(post.media_url)
    
    # Delete post (cascade deletes likes and comments)
    db.session.delete(post)
    db.session.commit()
    
    flash('✅ Post deleted successfully', 'success')
    return redirect(url_for('personal_feed', user_id=current_user.id))


@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@require_login
def delete_comment(comment_id):
    """Delete a comment (owner only)"""
    comment = PostComment.query.get_or_404(comment_id)
    post = Post.query.get(comment.post_id)
    
    # Only author can delete their comment
    if comment.author_id != current_user.id:
        flash('❌ You can only delete your own comments', 'error')
        return redirect(url_for('personal_feed', user_id=post.author_id))
    
    db.session.delete(comment)
    db.session.commit()
    
    flash('✅ Comment deleted successfully', 'success')
    return redirect(url_for('personal_feed', user_id=post.author_id))


# ================ SCRAPBOOK ROUTES ================

@app.route('/scrapbook')
@require_login
def scrapbook_list():
    """View all family scrapbook pages"""
    if not current_user.family_id:
        flash('❌ Please join a family first', 'error')
        return redirect(url_for('family_setup'))
    
    # Get all scrapbook pages for this family
    pages = ScrapbookPage.query.filter_by(
        family_id=current_user.family_id
    ).order_by(ScrapbookPage.event_date.desc().nullslast(), ScrapbookPage.created_at.desc()).all()
    
    return render_template('scrapbook_list.html', pages=pages)


@app.route('/scrapbook/<int:page_id>')
@require_login
def scrapbook_view(page_id):
    """View a specific scrapbook page"""
    page = ScrapbookPage.query.get_or_404(page_id)
    
    # Ensure page belongs to user's family
    if page.family_id != current_user.family_id:
        flash('❌ Access denied', 'error')
        return redirect(url_for('scrapbook_list'))
    
    # Get all photos for this page
    photos = ScrapbookPhoto.query.filter_by(
        scrapbook_page_id=page_id
    ).order_by(ScrapbookPhoto.order).all()
    
    return render_template('scrapbook_view.html', page=page, photos=photos)


@app.route('/scrapbook/create', methods=['GET', 'POST'])
@require_login
def scrapbook_create():
    """Create a new scrapbook page"""
    if not current_user.family_id:
        flash('❌ Please join a family first', 'error')
        return redirect(url_for('family_setup'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        story = request.form.get('story', '').strip()
        people_involved = request.form.get('people_involved', '').strip()
        location = request.form.get('location', '').strip()
        tags = request.form.get('tags', '').strip()
        mood = request.form.get('mood', '').strip()
        event_date_str = request.form.get('event_date', '').strip()
        
        if not title:
            flash('❌ Title is required', 'error')
            return redirect(url_for('scrapbook_create'))
        
        # Parse event date
        event_date = None
        if event_date_str:
            try:
                event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('❌ Invalid date format. Please use YYYY-MM-DD', 'error')
                return redirect(url_for('scrapbook_create'))
        
        # Handle cover photo upload
        cover_photo_url = None
        if 'cover_photo' in request.files:
            file = request.files['cover_photo']
            if file and file.filename:
                cover_photo_url, _, _ = save_uploaded_file(file)
        
        # Create scrapbook page
        page = ScrapbookPage(
            family_id=current_user.family_id,
            creator_id=current_user.id,
            title=title,
            description=description,
            story=story,
            people_involved=people_involved,
            location=location,
            tags=tags,
            mood=mood,
            event_date=event_date,
            cover_photo_url=cover_photo_url
        )
        
        db.session.add(page)
        db.session.commit()
        
        flash('✅ Scrapbook page created successfully!', 'success')
        return redirect(url_for('scrapbook_view', page_id=page.id))
    
    return render_template('scrapbook_create.html')


@app.route('/scrapbook/<int:page_id>/edit', methods=['GET', 'POST'])
@require_login
def scrapbook_edit(page_id):
    """Edit a scrapbook page"""
    page = ScrapbookPage.query.get_or_404(page_id)
    
    # Ensure page belongs to user's family
    if page.family_id != current_user.family_id:
        flash('❌ Access denied', 'error')
        return redirect(url_for('scrapbook_list'))
    
    if request.method == 'POST':
        page.title = request.form.get('title', '').strip()
        page.description = request.form.get('description', '').strip()
        page.story = request.form.get('story', '').strip()
        page.people_involved = request.form.get('people_involved', '').strip()
        page.location = request.form.get('location', '').strip()
        page.tags = request.form.get('tags', '').strip()
        page.mood = request.form.get('mood', '').strip()
        event_date_str = request.form.get('event_date', '').strip()
        
        if not page.title:
            flash('❌ Title is required', 'error')
            return render_template('scrapbook_edit.html', page=page)
        
        # Parse event date
        if event_date_str:
            try:
                page.event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('❌ Invalid date format. Please use YYYY-MM-DD', 'error')
                return render_template('scrapbook_edit.html', page=page)
        else:
            page.event_date = None
        
        # Handle cover photo upload
        if 'cover_photo' in request.files:
            file = request.files['cover_photo']
            if file and file.filename:
                # Delete old cover photo if exists
                if page.cover_photo_url:
                    delete_uploaded_file(page.cover_photo_url)
                page.cover_photo_url, _, _ = save_uploaded_file(file)
        
        db.session.commit()
        
        flash('✅ Scrapbook page updated successfully!', 'success')
        return redirect(url_for('scrapbook_view', page_id=page.id))
    
    return render_template('scrapbook_edit.html', page=page)


@app.route('/scrapbook/<int:page_id>/delete', methods=['POST'])
@require_login
def scrapbook_delete(page_id):
    """Delete a scrapbook page"""
    page = ScrapbookPage.query.get_or_404(page_id)
    
    # Ensure page belongs to user's family
    if page.family_id != current_user.family_id:
        flash('❌ Access denied', 'error')
        return redirect(url_for('scrapbook_list'))
    
    # Delete cover photo if exists
    if page.cover_photo_url:
        delete_uploaded_file(page.cover_photo_url)
    
    # Delete all photos in this page
    for photo in page.photos:
        delete_uploaded_file(photo.photo_url)
    
    db.session.delete(page)
    db.session.commit()
    
    flash('✅ Scrapbook page deleted successfully', 'success')
    return redirect(url_for('scrapbook_list'))
