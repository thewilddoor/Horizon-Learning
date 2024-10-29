from app import create_app, db
from app.models import User

# Create the Flask application context
app = create_app()

with app.app_context():
    # Check if admin already exists
    admin = User.query.filter_by(email='admin@example.com').first()
    
    if not admin:
        # Create the first admin user
        admin_user = User(
            name='Theodore',
            email='thewilddoor@qq.com',
            role='admin'
        )
        admin_user.set_password('20080609')  # Change to a secure password
        db.session.add(admin_user)

    # Check if teacher already exists
    teacher = User.query.filter_by(email='teacher@example.com').first()
    
    if not teacher:
        # Create the first teacher user
        teacher_user = User(
            name='Teacher',
            email='teacher@example.com',
            role='teacher',
            school_name='Default School'  # Modify as needed
        )
        teacher_user.set_password('teacherpassword')  # Change to a secure password
        db.session.add(teacher_user)

    # Check if student already exists
    student = User.query.filter_by(email='student@example.com').first()
    
    if not student:
        # Create the first student user
        student_user = User(
            name='Student',
            email='student@example.com',
            role='student',
            class_code=''  # Modify with a proper class code if needed
        )
        student_user.set_password('studentpassword')  # Change to a secure password
        db.session.add(student_user)

    # Commit the users to the database
    db.session.commit()

    print("Admin, Teacher, and Student accounts initialized successfully.")
