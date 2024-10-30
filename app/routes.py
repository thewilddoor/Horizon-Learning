# app/routes.py

from flask import (
    render_template, redirect, send_from_directory, session, url_for, flash, request, Response, stream_with_context, jsonify
)
from flask_login import (
    login_required, current_user, login_user, logout_user
)
from app import db, login  # Relative import
from .models import User, Bot, LearningCompanion, Material, Report, Message
from .forms import (
    EditLearningCompanionForm,
    RegistrationForm,
    LoginForm,
    BotForm,
    LearningCompanionForm,
    MaterialUploadForm,
    AssignMaterialForm,
    LinkCompanionForm,
    ChatForm
)
from .utils import (
    check_message_limit, allowed_file, Coze, convert_file_to_text,
    generate_conversation_id
)
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from flask import Blueprint
import os
import json

auth = Blueprint('auth', __name__)

# ------------------------
# User Loader Callback
# ------------------------

@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------------
# Home Route
# ------------------------

@auth.route('/')
def home():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('auth.admin_dashboard'))
        elif current_user.is_teacher():
            return redirect(url_for('auth.teacher_dashboard'))
        elif current_user.is_student():
            return redirect(url_for('auth.student_dashboard'))
    return render_template('home.html')

# ------------------------
# Authentication Routes
# ------------------------

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        role = form.role.data
        name = form.name.data
        email = form.email.data
        password = form.password.data

        if role == 'teacher':
            school_name = form.school_name.data
            new_user = User(name=name, email=email, role=role, school_name=school_name)
        elif role == 'student':
            class_code = form.class_code.data  # For student registration, class_code might be optional or auto-generated
            new_user = User(name=name, email=email, role=role, class_code=class_code)
        else:
            flash('Invalid role selected.', 'danger')
            return redirect(url_for('auth.register'))

        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            if user.is_admin():
                return redirect(next_page or url_for('auth.admin_dashboard'))
            elif user.is_teacher():
                return redirect(next_page or url_for('auth.teacher_dashboard'))
            elif user.is_student():
                return redirect(next_page or url_for('auth.student_dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

# ------------------------
# Admin Routes
# ------------------------

@auth.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    users = User.query.all()
    bots = Bot.query.all()
    return render_template('admin_dashboard.html', users=users, bots=bots)


@auth.route('/admin/bots/add', methods=['GET', 'POST'])
@login_required
def add_bot():
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    form = BotForm()
    if form.validate_on_submit():
        name = form.name.data
        bot_id = form.bot_id.data
        api_token = form.api_token.data

        # Check for unique name and bot_id
        existing_bot = Bot.query.filter((Bot.name == name) | (Bot.bot_id == bot_id)).first()
        if existing_bot:
            flash('Bot with this name or Bot ID already exists.', 'danger')
            return render_template('add_bot.html', form=form)

        new_bot = Bot(name=name, bot_id=bot_id, api_token=api_token)
        db.session.add(new_bot)
        db.session.commit()
        flash('Bot added successfully.', 'success')
        return redirect(url_for('auth.admin_dashboard'))
    return render_template('add_bot.html', form=form)


@auth.route('/admin/bots/edit/<int:bot_id>', methods=['GET', 'POST'])
@login_required
def edit_bot(bot_id):
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    bot = Bot.query.get_or_404(bot_id)
    form = BotForm(obj=bot)
    if form.validate_on_submit():
        # Check for unique name and bot_id
        if form.name.data != bot.name:
            existing_bot = Bot.query.filter_by(name=form.name.data).first()
            if existing_bot:
                form.name.errors.append('Bot name already exists.')
                return render_template('edit_bot.html', form=form, bot=bot)
        if form.bot_id.data != bot.bot_id:
            existing_bot = Bot.query.filter_by(bot_id=form.bot_id.data).first()
            if existing_bot:
                form.bot_id.errors.append('Bot ID already exists.')
                return render_template('edit_bot.html', form=form, bot=bot)
        
        bot.name = form.name.data
        bot.bot_id = form.bot_id.data
        bot.api_token = form.api_token.data
        db.session.commit()
        flash('Bot updated successfully.', 'success')
        return redirect(url_for('auth.admin_dashboard'))
    return render_template('edit_bot.html', form=form, bot=bot)


@auth.route('/admin/bots/delete/<int:bot_id>', methods=['POST'])
@login_required
def delete_bot(bot_id):
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    bot = Bot.query.get_or_404(bot_id)
    db.session.delete(bot)
    db.session.commit()
    flash('Bot deleted successfully.', 'success')
    return redirect(url_for('auth.admin_dashboard'))

@auth.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    
    user = User.query.get_or_404(user_id)

    # Prevent deletion of admin users
    if user.is_admin():
        flash('Cannot delete admin users.', 'danger')
        return redirect(url_for('auth.admin_dashboard'))

    # Delete the user
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('auth.admin_dashboard'))

# ------------------------
# Teacher Routes
# ------------------------

@auth.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    # Fetch teacher's learning companions
    companions = LearningCompanion.query.options(joinedload(LearningCompanion.students)).filter_by(teacher_id=current_user.id).all()
    return render_template('teacher_dashboard.html', companions=companions)


@auth.route('/teacher/create_companion', methods=['GET', 'POST'])
@login_required
def create_learning_companion():
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    form = LearningCompanionForm()
    # Populate bot choices
    form.bot.choices = [(bot.id, bot.name) for bot in Bot.query.all()]
    if form.validate_on_submit():
        class_name = form.class_name.data
        subject = form.subject.data
        instructions = form.instructions.data
        bot_id = form.bot.data

        new_companion = LearningCompanion(
            class_name=class_name,
            subject=subject,
            instructions=instructions,
            teacher_id=current_user.id,
            bot_id=bot_id
        )
        db.session.add(new_companion)
        db.session.commit()
        flash(f'Learning Companion created successfully. Class Code: {new_companion.class_code}', 'success')
        return redirect(url_for('auth.teacher_dashboard'))
    return render_template('create_learning_companion.html', form=form)


@auth.route('/teacher/upload_material', methods=['GET', 'POST'])
@login_required
def upload_material():
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    
    form = MaterialUploadForm()
    companions = LearningCompanion.query.filter_by(teacher_id=current_user.id).all()
    form.companion.choices = [(comp.id, f"{comp.class_name} - {comp.subject}") for comp in companions]
    
    if form.validate_on_submit():
        companion_id = form.companion.data
        file = form.file.data

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = os.path.join('app', 'static', 'uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            filepath = os.path.join(upload_folder, filename)
            try:
                file.save(filepath)
            except Exception as e:
                flash(f'Failed to save file: {e}', 'danger')
                return redirect(url_for('auth.upload_material'))

            # Convert file to plaintext
            plaintext_content = convert_file_to_text(filepath, filename)

            # Save material to the database
            new_material = Material(
                filename=filename,
                content=plaintext_content
            )
            db.session.add(new_material)
            db.session.commit()

            # Save plaintext content to a .txt file
            text_filename = f"{new_material.id}.txt"
            text_folder = os.path.join('app', 'static', 'materials')
            if not os.path.exists(text_folder):
                os.makedirs(text_folder)
            text_filepath = os.path.join(text_folder, text_filename)
            with open(text_filepath, 'w', encoding='utf-8') as text_file:
                text_file.write(plaintext_content)

            # Delete the original uploaded file after conversion
            os.remove(filepath)

            # Assign material to the companion (many-to-many relationship)
            companion = LearningCompanion.query.get(companion_id)
            if new_material not in companion.materials:
                companion.materials.append(new_material)
                db.session.commit()

            flash('Material uploaded and processed successfully.', 'success')
            return redirect(url_for('auth.teacher_dashboard'))
        else:
            flash('Invalid file type. Allowed types: PDF, DOCX, PPT, PPTX.', 'danger')
    
    return render_template('upload_material.html', form=form)


@auth.route('/teacher/assign_material', methods=['GET', 'POST'])
@login_required
def assign_material():
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    form = AssignMaterialForm()
    # Populate learning companion choices
    companions = LearningCompanion.query.filter_by(teacher_id=current_user.id).all()
    form.companion.choices = [(comp.id, f"{comp.class_name} - {comp.subject}") for comp in companions]

    # Populate material choices
    form.material.choices = [(mat.id, mat.filename) for mat in Material.query.all()]

    if form.validate_on_submit():
        companion_id = form.companion.data
        material_id = form.material.data

        companion = LearningCompanion.query.get(companion_id)
        material = Material.query.get(material_id)

        if material not in companion.materials:
            companion.materials.append(material)
            db.session.commit()
            flash('Material assigned successfully.', 'success')
        else:
            flash('Material is already assigned to this companion.', 'info')

        return redirect(url_for('auth.teacher_dashboard'))
    return render_template('assign_material.html', form=form)


@auth.route('/teacher/edit_companion/<int:companion_id>', methods=['GET', 'POST'])
@login_required
def edit_learning_companion(companion_id):
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    
    companion = LearningCompanion.query.get_or_404(companion_id)
    
    # Ensure that the current teacher owns this companion
    if companion.teacher_id != current_user.id:
        flash('You do not have permission to edit this learning companion.', 'danger')
        return redirect(url_for('auth.teacher_dashboard'))
    
    form = EditLearningCompanionForm(obj=companion)
    # Populate bot choices
    form.bot.choices = [(bot.id, bot.name) for bot in Bot.query.all()]
    
    if form.validate_on_submit():
        companion.class_name = form.class_name.data
        companion.subject = form.subject.data
        companion.instructions = form.instructions.data
        companion.bot_id = form.bot.data
        
        db.session.commit()
        flash('Learning Companion updated successfully.', 'success')
        return redirect(url_for('auth.teacher_dashboard'))
    
    return render_template('edit_learning_companion.html', form=form, companion=companion)


@auth.route('/teacher/delete_companion/<int:companion_id>', methods=['POST'])
@login_required
def delete_learning_companion(companion_id):
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    
    companion = LearningCompanion.query.get_or_404(companion_id)
    
    # Ensure the companion belongs to the current teacher
    if companion.teacher_id != current_user.id:
        flash('You do not have permission to delete this companion.', 'danger')
        return redirect(url_for('auth.teacher_dashboard'))

    # Delete the companion
    db.session.delete(companion)
    db.session.commit()
    flash('Learning Companion deleted successfully.', 'success')
    
    return redirect(url_for('auth.teacher_dashboard'))

# ------------------------
# Student Routes
# ------------------------

@auth.route('/student/dashboard')
@login_required
def student_dashboard():
    if not current_user.is_student():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    companions = current_user.learning_companions
    return render_template('student_dashboard.html', companions=companions)


@auth.route('/student/link_companion', methods=['GET', 'POST'])
@login_required
def link_companion():
    if not current_user.is_student():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    form = LinkCompanionForm()
    if form.validate_on_submit():
        class_code = form.class_code.data
        # Assuming class_code corresponds to LearningCompanion's class_code
        companion = LearningCompanion.query.filter_by(class_code=class_code).first()

        if companion:
            if companion not in current_user.learning_companions:
                current_user.learning_companions.append(companion)
                db.session.commit()
                flash('Successfully linked to the learning companion!', 'success')
            else:
                flash('Already linked to this learning companion.', 'info')
            return redirect(url_for('auth.student_dashboard'))
        else:
            flash('Invalid class code.', 'danger')
    return render_template('link_companion.html', form=form)


@auth.route('/student/chat/<int:companion_id>', methods=['GET'])
@login_required
def chat(companion_id):
    """
    Route to render the chat interface for students.
    """
    if not current_user.is_student():
        flash('Access denied. Only students can access the chat.', 'danger')
        return redirect(url_for('auth.login'))

    # Fetch the LearningCompanion instance
    companion = LearningCompanion.query.get_or_404(companion_id)

    # Verify that the student is linked to this learning companion
    if companion not in current_user.learning_companions:
        flash('You are not linked to this learning companion.', 'danger')
        return redirect(url_for('auth.student_dashboard'))

    # Initialize the chat form
    form = ChatForm()

    # Retrieve or generate a unique conversation ID for this student-companion pair
    session_key = f'conversation_id_{companion_id}'
    conversation_id = session.get(session_key)
    if not conversation_id:
        conversation_id = generate_conversation_id()
        session[session_key] = conversation_id

    # Fetch all messages for this conversation
    messages = Message.query.filter_by(
        companion_id=companion_id,
        conversation_id=conversation_id
    ).order_by(Message.timestamp.asc()).all()

    # Fetch all materials assigned to this learning companion
    materials = companion.materials

    return render_template('chat.html', form=form, messages=messages, companion=companion, materials=materials)


@auth.route('/student/chat/<int:companion_id>/send', methods=['POST'])
@login_required
def chat_send(companion_id):
    """
    Route to handle chat messages and stream AI responses.
    Expects a JSON payload with 'message' and optionally 'materials'.
    Returns a streaming response with the complete AI message.
    """
    if not current_user.is_student():
        return jsonify({'error': 'Access denied.'}), 403

    companion = LearningCompanion.query.get_or_404(companion_id)

    if companion not in current_user.learning_companions:
        return jsonify({'error': 'You are not linked to this learning companion.'}), 403

    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided.'}), 400

    user_message = data['message'].strip()

    if not user_message:
        return jsonify({'error': 'Empty message.'}), 400

    # Check message limit
    if not check_message_limit(current_user.id, companion_id):
        return jsonify({'error': 'Message limit reached. You can only send 45 messages per hour.'}), 429

    # Handle selected materials (if any)
    selected_material_ids = data.get('materials', [])
    materials_text = ''
    if selected_material_ids:
        materials_content = []
        for material_id in selected_material_ids:
            try:
                material = Material.query.get(int(material_id))
                if material:
                    text_filename = f"{material.id}.txt"
                    text_filepath = os.path.join('app', 'static', 'materials', text_filename)
                    if os.path.exists(text_filepath):
                        with open(text_filepath, 'r', encoding='utf-8') as text_file:
                            content = text_file.read().strip()
                            materials_content.append(content)
                    else:
                        # File not found
                        continue
            except ValueError:
                continue  # skip invalid material ids

        if materials_content:
            # Combine all materials content into a single string with proper formatting
            materials_text = "\n\n".join(materials_content)

    # Construct the full query
    if materials_text:
        # Instruct the AI to use Markdown formatting and consider the context materials
        full_query = (
            f"### User Query\n\n"
            f"{user_message}\n\n"
            f"### Context Material\n\n"
            f"{materials_text}\n\n"
            f"**Please provide a well-structured response using Markdown formatting.**"
        )
    else:
        # Instruct the AI to use Markdown formatting even without context
        full_query = (
            f"### User Query\n\n"
            f"{user_message}\n\n"
            f"**Please provide a well-structured response using Markdown formatting.**"
        )

    # Save the student's message to the database with the conversation_id
    session_key = f'conversation_id_{companion_id}'
    conversation_id = session.get(session_key)
    if not conversation_id:
        # Generate a new conversation ID
        conversation_id = generate_conversation_id()
        session[session_key] = conversation_id

    new_message = Message(
        user_id=current_user.id,
        companion_id=companion_id,
        content=user_message,
        conversation_id=conversation_id,
        sender_type='student'
    )
    db.session.add(new_message)
    db.session.commit()

    # Retrieve the chat history for this conversation
    messages = Message.query.filter_by(
        companion_id=companion_id,
        conversation_id=conversation_id
    ).order_by(Message.timestamp.asc()).all()

    history = []
    for msg in messages:
        is_user = msg.sender_type == 'student'
        history.append((msg.content, is_user))

    # Initialize Coze with stream=True
    coze = Coze(
        bot_id=companion.bot.bot_id,
        api_token=companion.bot.api_token,
        user_id=str(current_user.id),
        conversation_id=conversation_id,
        stream=True
    )

    # Get the response generator
    ai_response_generator = coze(full_query, history=history)

    # Define generator to yield response chunks
    def generate_response():
        response_text = ''
        try:
            for chunk in ai_response_generator:
                if chunk == "[DONE]":
                    break
                response_text += chunk
                # Yield the chunk without rendering
                yield chunk
            # After streaming, save the full AI message
            ai_message = Message(
                user_id=None,
                companion_id=companion_id,
                content=response_text,
                conversation_id=conversation_id,
                sender_type='AI'
            )
            db.session.add(ai_message)
            db.session.commit()
        except Exception as e:
            yield "An error occurred while processing your request."

    return Response(stream_with_context(generate_response()), mimetype='text/plain')


@auth.route('/student/reset_conversation/<int:companion_id>', methods=['POST'])
@login_required
def reset_conversation(companion_id):
    if not current_user.is_student():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    companion = LearningCompanion.query.get_or_404(companion_id)

    # Ensure the student is linked to this companion
    if companion not in current_user.learning_companions:
        flash('You are not linked to this learning companion.', 'danger')
        return redirect(url_for('auth.student_dashboard'))

    # Generate a new conversation ID for this student-companion pair
    from .utils import generate_conversation_id

    # Store the new conversation ID in the session
    session_key = f'conversation_id_{companion_id}'
    session[session_key] = generate_conversation_id()

    flash('Conversation has been reset.', 'success')
    return redirect(url_for('auth.chat', companion_id=companion_id))

# ------------------------
# Common Routes
# ------------------------

@auth.route('/materials/<int:material_id>')
@login_required
def view_material(material_id):
    material = Material.query.get_or_404(material_id)
    # Ensure that the user has access to this material
    if current_user.is_teacher():
        # Check if the material belongs to the teacher's companions
        if not any(material in companion.materials for companion in current_user.learning_companions):
            flash('You do not have access to this material.', 'danger')
            return redirect(url_for('auth.teacher_dashboard'))
    elif current_user.is_student():
        # Check if the material is assigned to the student's companions
        if not any(material in companion.materials for companion in current_user.learning_companions):
            flash('You do not have access to this material.', 'danger')
            return redirect(url_for('auth.student_dashboard'))
    else:
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    html_filename = f"{material.id}.html"
    html_folder = os.path.join('app', 'static', 'materials')
    html_filepath = os.path.join(html_folder, html_filename)

    if not os.path.exists(html_filepath):
        flash('Material file not found.', 'danger')
        return redirect(url_for('auth.teacher_dashboard'))

    return send_from_directory(html_folder, html_filename)

# ------------------------
# Report Routes
# ------------------------

@auth.route('/teacher/reports')
@login_required
def view_reports():
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    # Fetch messages from the last 24 hours
    time_threshold = datetime.utcnow() - timedelta(hours=24)

    # Get companions belonging to the teacher
    companions = LearningCompanion.query.filter_by(teacher_id=current_user.id).all()
    companion_ids = [companion.id for companion in companions]

    # Get selected companion_id from query parameters
    selected_companion_id = request.args.get('companion_id', type=int)

    # Build the base query
    messages_query = Message.query.filter(
        Message.companion_id.in_(companion_ids),
        Message.timestamp >= time_threshold
    )

    # If a specific companion is selected, filter messages accordingly
    if selected_companion_id:
        messages_query = messages_query.filter(Message.companion_id == selected_companion_id)

    # Fetch all relevant messages
    messages = messages_query.order_by(Message.timestamp.asc()).all()

    return render_template('reports.html', messages=messages, companions=companions, selected_companion_id=selected_companion_id)

# ------------------------
# Helper Functions
# ------------------------

def get_ai_response(companion, user_message):
    """
    Integrate the Coze class to generate AI responses based on user messages and companion materials.
    """
    materials = "\n".join([mat.content for mat in companion.materials])  # Combine all materials
    coze = Coze(
        bot_id=companion.bot.bot_id,
        api_token=companion.bot.api_token,
        user_id=current_user.id,
        history=[(
            msg.user_id == current_user.id and msg.content or "Assistant: " + msg.content
        ) for msg in Message.query.filter_by(companion_id=companion.id).order_by(Message.timestamp.asc()).all()]
    )
    ai_response = coze(
        user_message.content,
        history=[(
            msg.user_id == current_user.id and msg.content or "Assistant: " + msg.content
        ) for msg in Message.query.filter_by(companion_id=companion.id).order_by(Message.timestamp.asc()).all()],
        materials=materials
    )
    return ai_response

# ------------------------
# Clear Messages Route
# ------------------------

@auth.route('/teacher/clear_messages', methods=['POST'])
@login_required
def clear_messages():
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    # Get the companion_id from the form
    companion_id = request.form.get('companion_id', type=int)

    # Get companions belonging to the teacher
    companions = LearningCompanion.query.filter_by(teacher_id=current_user.id).all()
    companion_ids = [companion.id for companion in companions]

    if companion_id:
        # Ensure the companion belongs to the teacher
        if companion_id not in companion_ids:
            flash('Invalid companion selected.', 'danger')
            return redirect(url_for('auth.view_reports'))

        # Delete messages for the selected companion
        Message.query.filter_by(companion_id=companion_id).delete()
        db.session.commit()
        flash('Messages for the selected companion have been cleared.', 'success')
    else:
        # Delete messages for all companions belonging to the teacher
        Message.query.filter(Message.companion_id.in_(companion_ids)).delete()
        db.session.commit()
        flash('All messages for your companions have been cleared.', 'success')

    return redirect(url_for('auth.view_reports'))

