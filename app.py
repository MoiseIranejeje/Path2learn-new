from sqlalchemy import or_, and_
from sqlalchemy import func, inspect, text
from sqlalchemy.orm import aliased
from flask_mail import Mail, Message
from dotenv import load_dotenv
from models import db, User, School, SchoolSuggestion, Review
import os
import csv
import io
from flask import (Flask, render_template, request, redirect, url_for, flash,
                   jsonify, send_from_directory)
from flask_login import (LoginManager, UserMixin, login_user, login_required,
                         logout_user, current_user)
from werkzeug.utils import secure_filename
from functools import wraps

load_dotenv() # Loads the .env file


# --- App Initialization and Config ---
app = Flask(__name__)

# ★★★ ADD THIS SINGLE LINE HERE ★★★
app.jinja_env.globals['min'] = min
app.config['SECRET_KEY'] = 'a-very-secret-key-that-you-should-change'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///schools.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['STATIC_TEMPLATE_DIR'] = os.path.join(app.root_path, 'static', 'templates')
# ★★★ START: NEW MAIL CONFIGURATION ★★★
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
mail = Mail(app)
# ★★★ END: NEW MAIL CONFIGURATION ★★★

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['STATIC_TEMPLATE_DIR'], exist_ok=True)

# --- Database, Login, and Forms Initialization ---
# ★ IMPORTANT: Added SchoolSuggestion to model imports
from models import db, User, School, SchoolSuggestion
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# ★ IMPORTANT: Added SuggestSchoolForm to form imports
from forms import CsvUploadForm, AddAdminForm, SuggestSchoolForm, ReviewForm, ContactForm, ChangePasswordForm, RegistrationForm, LinkFamilyForm, CompareSchoolsForm
from models import Shortlist # Add Shortlist here

# --- Location Data (Unchanged) ---
RWANDA_PROVINCES = ['Kigali City', 'Southern Province', 'Northern Province', 'Eastern Province', 'Western Province']
RWANDA_DATA = {
    "Eastern Province": {
        "Nyagatare": ["Rwimiyaga", "Karangazi", "Nyagatare", "Katabagemu", "Rukomo", "Tabagwe", "Musheli", "Gatunda", "Mimuli", "Karama", "Matimba", "Mukama", "Rwempasha", "Kiyombe"],
        "Bugesera": ["Gashora", "Juru", "Kamabuye", "Karembo", "Ntarama", "Mareba", "Mayange", "Musenyi", "Mwogo", "Ngeruka", "Nyamata", "Nyarugenge", "Rilima", "Ruhuha", "Rweru"],
        "Ngoma": ["Gashanda", "Jarama", "Karembo", "Kazo", "Kibungo", "Mugesera", "Murama", "Mutenderi", "Remera", "Rukira", "Rukumberi", "Sake", "Zaza"],
        "Rwamagana": ["Fumbwe", "Gahengeri", "Gishari", "Karenge", "Kigabiro", "Muhazi", "Munyaga", "Munyiginya", "Musha", "Muyumbu", "Mwulire", "Nyakariro", "Nzige", "Rubona"],
        "Gatsibo": ["Gasange", "Gatsibo", "Gitoki", "Kabarore", "Kageyo", "Kiramuruzi", "Kiziguro", "Muhura", "Murambi", "Ngarama", "Nyagihanga", "Remera", "Rugarama", "Rwimbogo"],
        "Kayonza": ["Gahini", "Kabarondo", "Mukarange", "Murama", "Murundi", "Mwiri", "Ndego", "Nyamirama", "Rukara", "Ruramira", "Rwinkwavu"],
        "Kirehe": ["Gahara", "Gatore", "Kigarama", "Kigina", "Kirehe", "Mahama", "Mpanga", "Musaza", "Mushikiri", "Nasho", "Nyamugari", "Nyarubuye"]
    },
    "Northern Province": {
        "Burera": ["Bungwe", "Butaro", "Cyanika", "Cyeru", "Gahunga", "Gatebe", "Gitovu", "Kagogo", "Kinoni", "Kinyababa", "Kivuye", "Nemba", "Rugarama", "Rugendabari", "Ruhunde", "Rusarabuge", "Rwerere"],
        "Gicumbi": ["Bukure", "Bwisige", "Byumba", "Cyumba", "Giti", "Kaniga", "Manyagiro", "Miyove", "Kageyo", "Mukarange", "Muko", "Mutete", "Nyamiyaga", "Nyankenke II", "Rubaya", "Rukomo", "Rushaki", "Rutare", "Ruvune", "Rwamiko", "Shangasha"],
        "Rulindo": ["Base", "Burega", "Bushoki", "Buyoga", "Cyinzuzi", "Cyungo", "Kinihira", "Kisaro", "Masoro", "Mbogo", "Murambi", "Ngoma", "Ntarabana", "Rukozo", "Rusiga", "Shyorongi", "Tumba"]
    },
    "Western Province": {
        "Karongi": ["Bwishyura", "Gishyita", "Gishari", "Gitesi", "Mubuga", "Murambi", "Murundi", "Mutuntu", "Rubengera", "Rugabano", "Ruganda", "Rwankuba", "Twumba"],
        "Nyabihu": ["Bigogwe", "Jenda", "Jomba", "Kabatwa", "Karago", "Kintobo", "Mukamira", "Muringa", "Rambura", "Rugera", "Rurembo", "Shyira"],
        "Rubavu": ["Bugeshi", "Busasamana", "Cyanzarwe", "Gisenyi", "Kanama", "Kanzenze", "Nyakiliba", "Nyamyumba", "Nyundo", "Rubavu", "Rugerero"],
        "Rutsiro": ["Boneza", "Gihango", "Kigeyo", "Kivumu", "Manihira", "Mukura", "Murunda", "Musasa", "Mushonyi", "Mushubati", "Nyabirasi", "Ruhango", "Rusebeya"],
        "Ngororero": ["Bwira", "Gatumba", "Hindiro", "Kabaya", "Kageyo", "Kavumu", "Matyazo", "Muhanda", "Muhororo", "Ndaro", "Ngororero", "Nyange", "Sovu"],
        "Nyamasheke": ["Ruharambuga", "Bushekeri", "Bushenge", "Cyato", "Gihombo", "Kagano", "Kanjongo", "Karambi", "Karengera", "Kirimbi", "Macuba", "Mahembe", "Nyakabuye", "Nyakarenzo", "Nzahaha", "Rwimbogo"],
        "Rusizi": ["Bugarama", "Butare", "Bweyeye", "Gikundamvura", "Gihundwe", "Giheke", "Gitambi", "Kamembe", "Muganza", "Nkanka", "Nkombo", "Nkungu", "Rwimbogo"]
    },
    "Southern Province": {
        "Gisagara": ["Gikonko", "Gishubi", "Kansi", "Kibilizi", "Kigembe", "Mamba", "Muganza", "Mugombwa", "Mukindo", "Musha", "Ndora", "Nyanza", "Save"],
        "Kamonyi": ["Gacurabwenge", "Karama", "Kayenzi", "Kayumbu", "Mugina", "Musambira", "Ngamba", "Nyamiyaga", "Rugalika", "Rukoma", "Runda"],
        "Nyamagabe": ["Buruhukiro", "Cyanika", "Gatare", "Kaduha", "Kamegeli", "Kibirizi", "Kibumbwe", "Kitabi", "Mbazi", "Mugano", "Musange", "Musebeya", "Mushubi", "Nkomane", "Tare", "Uwinkingi"],
        "Nyaruguru": ["Busanze", "Cyahinda", "Kibeho", "Mata", "Munini", "Kivu", "Ngoma", "Nyabimata", "Nyagisozi", "Muganza", "Ruheru", "Ruramba", "Rusenge"],
        "Huye": ["Gishamvu", "Karama", "Kigoma", "Kinazi", "Maraba", "Mbazi", "Mukura", "Ngoma", "Ruhashya", "Huye", "Rusatira", "Rwaniro", "Simbi", "Tumba"],
        "Muhanga": ["Cyeza", "Kibangu", "Kiyumba", "Muhanga", "Mushishiro", "Nyabinoni", "Nyamabuye", "Nyarusange", "Rongi", "Kabacuzi", "Shyogwe", "Rugendabari"],
        "Nyanza": ["Busasamana", "Busoro", "Cyabakamyi", "Kibirizi", "Kigoma", "Mukingo", "Muyira", "Ntyazo", "Nyagisozi", "Rwabicuma"],
        "Ruhango": ["Kinazi", "Byimana", "Bweramana", "Mbuye", "Ruhango", "Mwendo", "Kinihira", "Ntongwe", "Kabagari"]
    },
    "Kigali City": {
        "Gasabo": ["Bumbogo", "Gatsata", "Jali", "Gikomero", "Gisozi", "Jabana", "Kinyinya", "Ndera", "Nduba", "Rusororo", "Rutunga", "Kacyiru", "Kimihurura", "Kimironko", "Remera"],
        "Kicukiro": ["Gahanga", "Gatenga", "Gikondo", "Kagarama", "Kanombe", "Kicukiro", "Kigarama", "Masaka", "Niboye", "Nyarugunga"],
        "Nyarugenge": ["Gitega", "Kanyinya", "Kigali", "Kimisagara", "Mageragere", "Muhima", "Nyakabanda", "Nyamirambo", "Nyarugenge", "Rwezamenyo"]
    }
}

SMART_TAG_OPTIONS = [
    'STEM',
    'Arts',
    'Sports',
    'Leadership',
    'Faith-Based',
    'International',
    'Sciences',
    'Humanities',
    'Inclusive Support',
]

FEE_BAND_OPTIONS = ['Affordable', 'Moderate', 'Premium', 'Not Published']
LANGUAGE_OF_INSTRUCTION_OPTIONS = ['English', 'French', 'Bilingual', 'Other / Not Published']
DEFAULT_EXTRACURRICULAR_OPTIONS = [
    'Football',
    'Basketball',
    'Volleyball',
    'Chess Club',
    'Debate Club',
    'Robotics Club',
    'Music and Choir',
    'STEM Fair',
    'Art Club',
]
DEFAULT_COMBINATION_OPTIONS = ['PCM', 'PCB', 'MCB', 'MEG', 'MPC', 'HEG']


def split_csv_values(value):
    return [item.strip() for item in (value or '').split(',') if item.strip()]


def normalize_token(value):
    return ' '.join((value or '').strip().lower().split())


def normalize_choice(value, allowed_values, default=''):
    normalized = normalize_token(value)
    for allowed in allowed_values:
        if normalize_token(allowed) == normalized:
            return allowed
    return default or (value.strip() if isinstance(value, str) else value)


def normalize_smart_tags(tags):
    normalized_tags = []
    seen = set()
    for tag in split_csv_values(tags):
        canonical = normalize_choice(tag, SMART_TAG_OPTIONS)
        if canonical in SMART_TAG_OPTIONS and canonical not in seen:
            normalized_tags.append(canonical)
            seen.add(canonical)
    return ', '.join(normalized_tags)


def school_primary_image(school):
    photos = split_csv_values(school.photos)
    if photos:
        return photos[0]
    return url_for('static', filename='images/default_school.png')


def search_rank_key(name, query):
    school_name = normalize_token(name)
    search_query = normalize_token(query)
    if school_name == search_query:
        return (0, len(name), school_name)
    if school_name.startswith(search_query):
        return (1, len(name), school_name)
    return (2, school_name.find(search_query), len(name), school_name)


def serialize_school_search_result(school):
    return {
        'id': school.id,
        'name': school.name,
        'district': school.district,
        'province': school.province,
        'education_program': school.education_program,
        'image_url': school_primary_image(school),
        'url': url_for('school_detail', school_id=school.id),
    }


def collect_distinct_csv_values(attribute_name, seed_values=None):
    collected = list(seed_values or [])
    seen = {normalize_token(item) for item in collected}
    values = db.session.query(getattr(School, attribute_name)).all()
    for (raw_value,) in values:
        for item in split_csv_values(raw_value):
            token = normalize_token(item)
            if token and token not in seen:
                collected.append(item)
                seen.add(token)
    return collected


def collect_distinct_field_values(attribute_name, seed_values=None):
    collected = list(seed_values or [])
    seen = {normalize_token(item) for item in collected}
    values = db.session.query(getattr(School, attribute_name)).all()
    for (raw_value,) in values:
        if not raw_value:
            continue
        token = normalize_token(raw_value)
        if token not in seen:
            collected.append(raw_value)
            seen.add(token)
    return collected


def school_profile_completeness(school):
    profile_fields = [
        school.description,
        school.photos,
        school.phone,
        school.email,
        school.website,
        school.extracurriculars,
        school.tags,
        school.combinations,
        school.fees_breakdown,
        school.performance_history,
        school.boarding_policy,
        school.fee_band,
        school.language_of_instruction,
    ]
    return sum(1 for field in profile_fields if field and str(field).strip())


def ensure_school_schema():
    inspector = inspect(db.engine)
    if not inspector.has_table('school'):
        return

    existing_columns = {column['name'] for column in inspector.get_columns('school')}
    alter_statements = []

    schema_updates = {
        'tags': "ALTER TABLE school ADD COLUMN tags TEXT",
        'min_aggregate': "ALTER TABLE school ADD COLUMN min_aggregate INTEGER DEFAULT 0",
        'combinations': "ALTER TABLE school ADD COLUMN combinations TEXT",
        'fees_breakdown': "ALTER TABLE school ADD COLUMN fees_breakdown TEXT",
        'performance_history': "ALTER TABLE school ADD COLUMN performance_history TEXT",
        'fee_band': "ALTER TABLE school ADD COLUMN fee_band VARCHAR(50) DEFAULT 'Not Published'",
        'language_of_instruction': "ALTER TABLE school ADD COLUMN language_of_instruction VARCHAR(50) DEFAULT 'Other / Not Published'",
    }

    for column_name, statement in schema_updates.items():
        if column_name not in existing_columns:
            alter_statements.append(statement)

    if alter_statements:
        with db.engine.begin() as connection:
            for statement in alter_statements:
                connection.execute(text(statement))

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- Admin Decorators ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_superadmin:
            flash('This action requires super-administrator privileges.', 'danger')
            return redirect(url_for('admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- Public Routes ---
# In app.py
@app.route('/search')
def advanced_search():
    # Get all filter values from the URL
    search_term = request.args.get('q', '').strip()
    province = request.args.get('province', '')
    district = request.args.get('district', '')
    ownership = request.args.get('ownership', '')
    gender = request.args.get('gender', '')
    program = request.args.get('program', '')
    
    query = School.query
    
    if search_term:
        query = query.filter(School.name.ilike(f'%{search_term}%'))
    if province: query = query.filter_by(province=province)
    if district: query = query.filter_by(district=district)
    if ownership: query = query.filter_by(ownership=ownership)
    if gender: query = query.filter_by(gender_policy=gender)
    if program: query = query.filter_by(education_program=program)
    
    if search_term:
        results = sorted(query.all(), key=lambda school: search_rank_key(school.name, search_term))
    else:
        results = query.order_by(School.name).all()
    
    return render_template('advanced_search.html',
                           title="Advanced Search",
                           results=results,
                           provinces=RWANDA_PROVINCES,
                           search_term=search_term,
                           # Pass selections back to the template
                           s_province=province, s_district=district, s_ownership=ownership,
                           s_gender=gender, s_program=program)

@app.route('/')
def index():
    school_count = School.query.count()
    approved_review_count = Review.query.filter_by(status='approved').count()

    # Original featured schools (latest additions)
    featured_schools = School.query.order_by(School.id.desc()).limit(6).all()
    
    # ★★★ NEW: Highest Rated Schools Query ★★★
    highest_rated_schools_query = db.session.query(
        School, 
        func.avg(Review.rating).label('average_rating')
    ).join(Review).filter(Review.status == 'approved').group_by(School.id).order_by(func.avg(Review.rating).desc()).limit(3).all()
    # Extract just the school objects
    highest_rated_schools = [school for school, avg_rating in highest_rated_schools_query]

    # ★★★ NEW: Most Popular Schools Query ★★★
    most_popular_schools_query = db.session.query(
        School,
        func.count(Review.id).label('review_count')
    ).join(Review).filter(Review.status == 'approved').group_by(School.id).order_by(func.count(Review.id).desc()).limit(3).all()
    most_popular_schools = [school for school, review_count in most_popular_schools_query]

    return render_template('index.html', 
                           featured_schools=featured_schools,
                           highest_rated_schools=highest_rated_schools,
                           most_popular_schools=most_popular_schools,
                           school_count=school_count,
                           approved_review_count=approved_review_count,
                           provinces=RWANDA_PROVINCES)

# ★★★ START: REPLACED school_detail ROUTE WITH DEBUGGING ★★★
@app.route('/school/<int:school_id>', methods=['GET', 'POST'])
def school_detail(school_id):
    school = db.session.get(School, school_id)
    if not school:
        flash('School not found!', 'danger')
        return redirect(url_for('index'))

    form = ReviewForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                new_review = Review(
                    rating=int(form.rating.data),
                    comment=form.comment.data,
                    reviewer_name=form.reviewer_name.data,
                    school_id=school.id
                )
                db.session.add(new_review)
                db.session.commit()
                flash('Thank you! Your review has been submitted and is pending approval.', 'success')
                return redirect(url_for('school_detail', school_id=school.id))
            except Exception as e:
                db.session.rollback()
                flash('A database error occurred while submitting your review. Please try again later.', 'danger')

        else:
            flash('There was an error with your submission. Please check the fields and try again.', 'danger')


    photos = [p.strip() for p in school.photos.split(',')] if school.photos else []
    approved_reviews = Review.query.filter_by(school_id=school.id, status='approved').order_by(Review.submitted_at.desc()).all()
    activities = [item.strip() for item in school.extracurriculars.split(',')] if school.extracurriculars else []
    combinations = [item.strip() for item in school.combinations.split(',')] if school.combinations else []
    tags = [item.strip() for item in school.tags.split(',')] if school.tags else []
    review_count = len(approved_reviews)
    has_contact_info = any([school.phone, school.email, school.website])
    has_academic_info = any([school.combinations, school.min_aggregate, school.performance_history, school.education_program])

    return render_template('school_detail.html', 
                           school=school, 
                           photos=photos,
                           reviews=approved_reviews,
                           form=form,
                           activities=activities,
                           combinations=combinations,
                           tags=tags,
                           review_count=review_count,
                           has_contact_info=has_contact_info,
                           has_academic_info=has_academic_info)
# ★★★ END: REPLACED school_detail ROUTE ★★★

# ★★★ START: NEW ROUTE FOR SCHOOL SUGGESTIONS ★★★
@app.route('/suggest-school', methods=['GET', 'POST'])
def suggest_school():
    form = SuggestSchoolForm()
    # Populate province choices dynamically
    form.province.choices = [('', 'Select Province')] + [(p, p) for p in RWANDA_PROVINCES]

    # Populate district and sector choices if a province/district is selected (for GET or failed POST)
    if request.method == 'GET' or not form.province.data: # For initial load or if province not yet selected
        form.district.choices = [('', 'Select District')]
        form.sector.choices = [('', 'Select Sector')]
    elif form.province.data in RWANDA_DATA:
        districts = RWANDA_DATA[form.province.data]
        form.district.choices = [('', 'Select District')] + [(d, d) for d in districts.keys()]
        if form.district.data and form.district.data in districts:
            sectors = districts[form.district.data]
            form.sector.choices = [('', 'Select Sector')] + [(s, s) for s in sectors]
        else:
            form.sector.choices = [('', 'Select Sector')]

    if form.validate_on_submit():
        # Create a new suggestion object from the form data
        suggestion = SchoolSuggestion(
            name=form.name.data,
            description=form.description.data,
            province=form.province.data,
            district=form.district.data,
            sector=form.sector.data,
            education_program=form.education_program.data,
            gender_policy=form.gender_policy.data,
            ownership=form.ownership.data,
            religious_affiliation=form.religious_affiliation.data,
            phone=form.phone.data,
            email=None, # Admin will add this - keeping your original comment/intent
            website=form.website.data,
            photos=form.photos.data,
            boarding_policy=form.boarding_policy.data,
            extracurriculars=form.extracurriculars.data,
            suggester_name=form.suggester_name.data,
            suggester_email=form.suggester_email.data,
        )
        db.session.add(suggestion)
        db.session.commit()
        flash('Thank you! Your school suggestion has been received and is pending review by our team.', 'success')
        return redirect(url_for('index'))

    return render_template('suggest_school.html', title='Suggest a School', form=form)
# ★★★ END: NEW ROUTE ★★★


# --- Authentication Routes ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    # Reusing admin_login.html logic but perhaps we should rename it or check fields
    # Assuming the form in admin_login.html just sends username and password via POST
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('admin_login.html', title='Login') # Reusing existing template for now

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'student':
        return redirect(url_for('student_dashboard'))
    elif current_user.role == 'parent':
        return redirect(url_for('parent_dashboard'))
    elif current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    else:
        # Fallback
        return redirect(url_for('index'))

# --- Admin Dashboard ---
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    schools_count = db.session.query(School).count()
    public_count = School.query.filter_by(ownership='Public').count()
    private_count = School.query.filter_by(ownership='Private').count()
    recent_schools = School.query.order_by(School.id.desc()).limit(5).all()
        
    # ★★★ ADD THIS LINE ★★★
    suggestions_count = SchoolSuggestion.query.filter_by(status='pending').count()
    # ★ ADD THIS LINE ★
    reviews_count = Review.query.filter_by(status='pending').count()

    return render_template('admin_dashboard.html',
                           schools_count=schools_count,
                           public_count=public_count,
                           private_count=private_count,
                           recent_schools=recent_schools,
                           suggestions_count=suggestions_count,
                           reviews_count=reviews_count) # ★ And pass it here
   
   
# --- School Management (CRUD) ---



# ★★★ START: UPGRADED admin_schools ROUTE WITH PAGINATION ★★★
@app.route('/admin/schools')
@login_required
@admin_required
def admin_schools():
    # Get page number, default to 1
    page = request.args.get('page', 1, type=int)
    
    # Get search and filter parameters from the URL
    search_query = request.args.get('q', '')
    province_filter = request.args.get('province', '')
    
    # Start with a base query
    schools_query = School.query
    
    # Apply search filter if a query exists
    if search_query:
        schools_query = schools_query.filter(School.name.ilike(f'%{search_query}%'))
        
    # Apply province filter if selected
    if province_filter:
        schools_query = schools_query.filter_by(province=province_filter)
        
    # Execute the query with pagination instead of .all()
    # We will show 10 schools per page
    schools_pagination = schools_query.order_by(School.name).paginate(page=page, per_page=10, error_out=False)
    
    return render_template('admin_schools.html', 
                           schools=schools_pagination,  # Pass the entire pagination object
                           provinces=RWANDA_PROVINCES,
                           search_query=search_query,
                           selected_province=province_filter)
# ★★★ END: UPGRADED admin_schools ROUTE ★★★


@app.route('/admin/schools/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_school():
    # You might want to use a SchoolForm here too for consistency and validation
    if request.method == 'POST':
        try:
            min_agg = int(request.form.get('min_aggregate')) if request.form.get('min_aggregate') else 0
        except ValueError:
            min_agg = 0

        selected_tags = normalize_smart_tags(', '.join(request.form.getlist('tags')) or request.form.get('tags', ''))

        new_school = School(
            name=request.form.get('name'),
            description=request.form.get('description'),
            province=request.form.get('province'),
            district=request.form.get('district'),
            sector=request.form.get('sector'),
            education_program=request.form.get('education_program'),
            gender_policy=request.form.get('gender_policy'),
            ownership=request.form.get('ownership'),
            religious_affiliation=request.form.get('religious_affiliation'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            website=request.form.get('website'),
            photos=request.form.get('image_urls'),
            tags=selected_tags,
            min_aggregate=min_agg,
            boarding_policy=request.form.get('boarding_policy'),
            extracurriculars=request.form.get('extracurriculars'),
            combinations=request.form.get('combinations'),
            fees_breakdown=request.form.get('fees_breakdown'),
            performance_history=request.form.get('performance_history'),
            fee_band=normalize_choice(request.form.get('fee_band'), FEE_BAND_OPTIONS, 'Not Published'),
            language_of_instruction=normalize_choice(request.form.get('language_of_instruction'), LANGUAGE_OF_INSTRUCTION_OPTIONS, 'Other / Not Published')
        )
        if 'fees_file' in request.files:
            file = request.files['fees_file']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                new_school.fees_file = f"uploads/{filename}"
        db.session.add(new_school)
        db.session.commit()
        flash(f'School "{new_school.name}" added successfully!', 'success')
        return redirect(url_for('admin_schools'))
    return render_template(
        'add_school.html',
        provinces=RWANDA_PROVINCES,
        smart_tag_options=SMART_TAG_OPTIONS,
        fee_band_options=FEE_BAND_OPTIONS,
        language_options=LANGUAGE_OF_INSTRUCTION_OPTIONS,
        title="Add School"
    )

@app.route('/admin/schools/edit/<int:school_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_school(school_id):
    school = db.session.get(School, school_id)
    if not school: return redirect(url_for('admin_schools'))
    if request.method == 'POST':
        selected_tags = normalize_smart_tags(', '.join(request.form.getlist('tags')) or request.form.get('tags', ''))
        school.name=request.form.get('name')
        school.description=request.form.get('description')
        school.province=request.form.get('province')
        # ... update all other fields ...
        school.district=request.form.get('district') # Example of updating more fields
        school.sector=request.form.get('sector')
        school.education_program=request.form.get('education_program')
        school.gender_policy=request.form.get('gender_policy')
        school.ownership=request.form.get('ownership')
        school.boarding_policy=request.form.get('boarding_policy')
        school.extracurriculars=request.form.get('extracurriculars')
        school.religious_affiliation=request.form.get('religious_affiliation')
        school.phone=request.form.get('phone')
        school.email=request.form.get('email')
        school.website=request.form.get('website')
        school.photos=request.form.get('image_urls') # Assuming this is still image_urls for edit
        school.tags=selected_tags
        school.combinations=request.form.get('combinations')
        school.fees_breakdown=request.form.get('fees_breakdown')
        school.performance_history=request.form.get('performance_history')
        school.fee_band=normalize_choice(request.form.get('fee_band'), FEE_BAND_OPTIONS, 'Not Published')
        school.language_of_instruction=normalize_choice(request.form.get('language_of_instruction'), LANGUAGE_OF_INSTRUCTION_OPTIONS, 'Other / Not Published')
        
        try:
            school.min_aggregate = int(request.form.get('min_aggregate')) if request.form.get('min_aggregate') else 0
        except ValueError:
            school.min_aggregate = 0

        if 'fees_file' in request.files and request.files['fees_file'].filename != '':
            file = request.files['fees_file']
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            school.fees_file = f"uploads/{filename}"

        db.session.commit()
        flash(f'School "{school.name}" updated successfully!', 'success')
        return redirect(url_for('admin_schools'))
     # Re-use the add_school template for editing for consistency
    return render_template(
        'add_school.html',
        school=school,
        provinces=RWANDA_PROVINCES,
        smart_tag_options=SMART_TAG_OPTIONS,
        fee_band_options=FEE_BAND_OPTIONS,
        language_options=LANGUAGE_OF_INSTRUCTION_OPTIONS,
        title="Edit School"
    )

@app.route('/admin/schools/delete/<int:school_id>', methods=['POST'])
@login_required
@admin_required
def delete_school(school_id):
    school = db.session.get(School, school_id)
    if school:
        db.session.delete(school)
        db.session.commit()
        flash(f'School "{school.name}" has been deleted.', 'success')
    return redirect(url_for('admin_schools'))

# --- ★★★ FULLY REBUILT IMPORT FUNCTION ★★★ ---
@app.route('/admin/import', methods=['GET', 'POST'])
@login_required
@admin_required
def import_schools():
    form = CsvUploadForm()
    if form.validate_on_submit():
        print("Form validated. Starting file processing...") # DEBUG PRINT
        
        # This dictionary maps the exact CSV header to your database model field name.
        HEADER_MAP = {
            'Name of  the school .': 'name',
            'Add atleast one school photo (For visual reference) (Please Right click on the image and then copy image address)': 'photos',
            'Gender Inclusivity Policy': 'gender_policy',
            'Ownership policy': 'ownership',
            'Education program ': 'education_program',
            'Province': 'province',
            'District': 'district',
            'Sector': 'sector',
            'Phone number': 'phone',
            'School Website (If any )': 'website',
            'Religious denominations (Optional)': 'religious_affiliation',
            'Email Address': 'email',
            '1.Descibe the school its life style and others in not more than 100 words.': 'description', 
            'Boarding Policy': 'boarding_policy',
            'Extracurriculars': 'extracurriculars',
            'Smart Tags': 'tags',
            'Minimum Aggregate Cutoff': 'min_aggregate',
            'Subject Combinations': 'combinations',
            'Fees Breakdown': 'fees_breakdown',
            'Performance History': 'performance_history',
            'Fee Band': 'fee_band',
            'Language of Instruction': 'language_of_instruction'
        }

        file = form.csv_file.data
        stream = io.TextIOWrapper(file.stream, encoding='utf-8-sig', newline='')
        reader = csv.DictReader(stream)

        schools_to_add = []
        errors = []
        
        # Check if headers are valid before looping
        csv_headers = reader.fieldnames
        if not csv_headers or not any(h in HEADER_MAP for h in csv_headers):
            flash('Import failed: The CSV file does not contain any recognizable headers.', 'danger')
            return render_template('import_schools.html', form=form)

        for row_num, row in enumerate(reader, 2):
            print(f"--- Processing row {row_num} ---") # DEBUG PRINT
            
            # This logic correctly builds a dictionary with clean keys (name, province, etc.)
            school_data = {}
            for csv_header, db_field in HEADER_MAP.items():
                if csv_header in row:
                    school_data[db_field] = row[csv_header].strip()

            name = school_data.get('name')
            province = school_data.get('province')

            if not name or not province:
                errors.append(f"Row {row_num}: Skipped. 'Name of the school' and 'Province' are required fields.")
                print(f"Row {row_num}: SKIPPED due to missing name or province.") # DEBUG PRINT
                continue

            existing_school = School.query.filter_by(name=name, province=province).first()
            if existing_school:
                errors.append(f"Row {row_num}: Skipped. School '{name}' in '{province}' already exists.")
                print(f"Row {row_num}: SKIPPED because school '{name}' already exists.") # DEBUG PRINT
                continue
            
            photo_urls = school_data.get('photos', '')
            valid_photos = [url.strip() for url in photo_urls.split(',') if url.strip().startswith('http')]
            school_data['photos'] = ', '.join(valid_photos)
            school_data['min_aggregate'] = int(school_data['min_aggregate']) if school_data.get('min_aggregate', '').isdigit() else 0
            school_data['tags'] = normalize_smart_tags(school_data.get('tags', ''))
            school_data['fee_band'] = normalize_choice(school_data.get('fee_band'), FEE_BAND_OPTIONS, 'Not Published')
            school_data['language_of_instruction'] = normalize_choice(
                school_data.get('language_of_instruction'),
                LANGUAGE_OF_INSTRUCTION_OPTIONS,
                'Other / Not Published'
            )
            
            # We can now create the School object easily
            new_school = School(**school_data)
            schools_to_add.append(new_school)
            print(f"Row {row_num}: Staged '{name}' for addition.") # DEBUG PRINT

        # Now, we try to commit everything at once
        if schools_to_add:
            try:
                db.session.add_all(schools_to_add)
                db.session.commit()
                flash(f'Success! {len(schools_to_add)} new schools have been imported.', 'success')
                
            except Exception as e:
                db.session.rollback()
                flash(f'A database error occurred during import. No schools were added. Error: {e}', 'danger')
                
        else:
            flash('No new schools were imported. They may already exist in the database or there were issues with the data.', 'warning')
            

        if errors:
            flash('Please note the following issues with some rows:', 'info')
            for error in errors[:5]: # Show first 5 errors
                flash(error, 'secondary')

        return redirect(url_for('admin_schools'))
    
    # This part runs if the form is just being displayed (GET request) or if validation fails
    return render_template('import_schools.html', form=form)


@app.route('/admin/download-template')
@login_required
@admin_required
def download_template():
    headers = [
        'Name of  the school .','Add atleast one school photo (For visual reference) (Please Right click on the image and then copy image address)','Gender Inclusivity Policy',
        'Ownership policy','Education program ','Province','District','Sector','Phone number','School Website (If any )',
        'Religious denominations (Optional)','Email Address','1.Descibe the school its life style and others in not more than 100 words.',
        'Boarding Policy','Extracurriculars','Smart Tags','Minimum Aggregate Cutoff','Subject Combinations','Fees Breakdown','Performance History','Fee Band','Language of Instruction'
    ]
    example_row = [
        "Example Green Hills Academy","https://example.com/photo1.jpg","Mixed","Private","Cambridge International Education (CIE)",
        "Kigali City","Gasabo","Remera","+250 788 123 456","https://www.greenhillsacademy.rw","Protestants","info@greenhills.ac.rw",
        "A top-rated international school.", "Day and Boarding","Football, Basketball, Chess Club, STEM Fair","STEM, International, Boarding","15",
        "PCM, MEG, MCB","Moderate fees with separate boarding and transport costs.","Strong exam performance over the last three years.","Premium","English"
    ]
    template_file = 'path2learn_import_template.csv'
    template_filepath = os.path.join(app.config['STATIC_TEMPLATE_DIR'], template_file)
    with open(template_filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerow(example_row)
    return send_from_directory(app.config['STATIC_TEMPLATE_DIR'], template_file, as_attachment=True)

# --- User Management & API Routes ---
# ... (all other routes like manage_users, add_admin, api/districts, etc., are unchanged) ...
@app.route('/admin/users')
@login_required
@superadmin_required
def manage_users():
    users = User.query.order_by(User.role.desc(), User.username).all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
@superadmin_required
def add_admin():
    form = AddAdminForm()
    if form.validate_on_submit():
        new_admin = User(username=form.username.data, email=form.email.data, role='admin')
        new_admin.set_password(form.password.data)
        db.session.add(new_admin)
        db.session.commit()
        flash(f'New admin "{new_admin.username}" created successfully!', 'success')
        return redirect(url_for('manage_users'))
    return render_template('add_admin.html', form=form, title='Add New Admin')
# ★★★ NEW: DELETE ADMIN ROUTE ★★★
@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
@superadmin_required
def delete_admin(user_id):
    user_to_delete = db.session.get(User, user_id)
    if not user_to_delete:
        flash('User not found.', 'danger')
        return redirect(url_for('manage_users'))

    # Safety Check 1: Superadmin cannot delete themselves.
    if user_to_delete.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('manage_users'))

    # Safety Check 2: A superadmin cannot delete another superadmin.
    if user_to_delete.is_superadmin:
        flash('Superadmin accounts cannot be deleted.', 'danger')
        return redirect(url_for('manage_users'))

    db.session.delete(user_to_delete)
    db.session.commit()
    flash(f"Admin '{user_to_delete.username}' has been deleted.", 'success')
    return redirect(url_for('manage_users'))
# In app.py, near your other API routes

# ★★★ NEW: API ROUTE FOR THE MAP ★★★


# ★★★ START: CORRECTED AND ROBUST API ROUTE ★★★
'''@app.route('/api/schools-by-province')
def schools_by_province():
    province = request.args.get('province', '')
    if not province:
        return jsonify([])
    
    # Use .ilike() for a case-insensitive search. This is much more robust.
    # For example, it will match "Kigali City" even if the request is for "kigali city".
    schools_query = School.query.filter(School.province.ilike(f'%{province}%')).order_by(School.name)
    
    schools = schools_query.all()
    
    # This part is correct and remains the same
    return jsonify([{'id': s.id, 'name': s.name, 'district': s.district} for s in schools])
# ★★★ END: CORRECTED AND ROBUST API ROUTE ★★★'''

@app.route('/api/districts')
def get_districts():
    province = request.args.get('province')
    if province in RWANDA_DATA: return jsonify(list(RWANDA_DATA[province].keys()))
    return jsonify([])

@app.route('/api/sectors')
def get_sectors():
    province = request.args.get('province')
    district = request.args.get('district')
    if province in RWANDA_DATA and district in RWANDA_DATA[province]: return jsonify(RWANDA_DATA[province][district])
    return jsonify([])

@app.route('/api/search')
def search():
    query = (request.args.get('q') or request.args.get('query') or '').strip()
    if not query:
        return jsonify([])
    search_term = f"%{query}%"
    results = School.query.filter(School.name.ilike(search_term)).all()
    ranked_results = sorted(results, key=lambda school: search_rank_key(school.name, query))
    return jsonify([serialize_school_search_result(school) for school in ranked_results[:8]])


@app.route('/api/recommend')
def recommend():
    filters = {}
    if request.args.get('province'):
        filters['province'] = request.args.get('province')
    if request.args.get('program'):
        filters['education_program'] = request.args.get('program')
    if request.args.get('gender_policy'):
        filters['gender_policy'] = request.args.get('gender_policy')

    if not filters:
        return jsonify([])

    results = School.query.filter_by(**filters).all()
    return jsonify([school.to_dict() for school in results])
# --- ★★★ NEW STATIC PAGE ROUTES ★★★ ---

@app.route('/about')
def about():
    return render_template('about.html', title='About Us')

@app.route('/how-to-use')
def how_to_use():
    return redirect(url_for('about') + '#guide')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        try:
            msg = Message(
                subject=f"New Contact Form Message from {form.name.data}",
                sender=app.config['MAIL_USERNAME'],
                recipients=[app.config['MAIL_USERNAME']] # Send the email to yourself
            )
            msg.body = f"""
            You have received a new message from the Path2Learn contact form.

            From: {form.name.data}
            Email: {form.email.data}

            Message:
            {form.message.data}
            """
            mail.send(msg)
            flash('Your message has been sent successfully! We will get back to you soon.', 'success')
            return redirect(url_for('contact'))
        except Exception as e:
            flash(f'An error occurred while sending your message: {e}', 'danger')

    return render_template('contact.html', title='Contact Us', form=form)
# ★★★ START: NEW ROUTES FOR MANAGING SUGGESTIONS ★★★

@app.route('/admin/suggestions')
@login_required
@admin_required
def manage_suggestions():
    # Fetch all suggestions that are still pending
    suggestions = SchoolSuggestion.query.filter_by(status='pending').order_by(SchoolSuggestion.submitted_at.asc()).all()
    return render_template('admin_suggestions.html', suggestions=suggestions, title="Manage Suggestions")

@app.route('/admin/suggestions/approve/<int:suggestion_id>', methods=['POST'])
@login_required
@admin_required
def approve_suggestion(suggestion_id):
    suggestion = db.session.get(SchoolSuggestion, suggestion_id)
    if not suggestion:
        flash('Suggestion not found.', 'danger')
        return redirect(url_for('manage_suggestions'))

    # Check if a school with the same name and province already exists
    existing_school = School.query.filter_by(name=suggestion.name, province=suggestion.province).first()
    if existing_school:
        flash(f"A school named '{suggestion.name}' already exists in {suggestion.province}. Please review before adding.", 'warning')
        # You might want to delete the suggestion even if it's a duplicate
        db.session.delete(suggestion)
        db.session.commit()
        return redirect(url_for('manage_suggestions'))

    # Create a new official school from the suggestion data
    new_school = School(
        name=suggestion.name,
        description=suggestion.description,
        province=suggestion.province,
        district=suggestion.district,
        sector=suggestion.sector,
        education_program=suggestion.education_program,
        gender_policy=suggestion.gender_policy,
        ownership=suggestion.ownership,
        religious_affiliation=suggestion.religious_affiliation,
        phone=suggestion.phone,
        boarding_policy=suggestion.boarding_policy,
        extracurriculars=suggestion.extracurriculars,
        website=suggestion.website,
        photos=suggestion.photos,
        # Admin should verify and add email and fees file later
    )
    db.session.add(new_school)
    
    # Remove the suggestion from the queue
    db.session.delete(suggestion)
    
    db.session.commit()
    flash(f"School '{new_school.name}' has been approved and added to the database!", 'success')
    return redirect(url_for('manage_suggestions'))

@app.route('/admin/suggestions/reject/<int:suggestion_id>', methods=['POST'])
@login_required
@admin_required
def reject_suggestion(suggestion_id):
    suggestion = db.session.get(SchoolSuggestion, suggestion_id)
    if suggestion:
        db.session.delete(suggestion)
        db.session.commit()
        flash(f"Suggestion for '{suggestion.name}' has been rejected and removed.", 'info')
    else:
        flash('Suggestion not found.', 'danger')
    return redirect(url_for('manage_suggestions'))

# ★★★ END: NEW SUGGESTION ROUTES ★★★
# ★★★ START: NEW ADMIN ROUTES FOR REVIEWS ★★★
@app.route('/admin/reviews')
@login_required
@admin_required
def manage_reviews():
    pending_reviews = Review.query.filter_by(status='pending').order_by(Review.submitted_at.asc()).all()
    return render_template('admin_reviews.html', reviews=pending_reviews, title="Manage Reviews")

@app.route('/admin/reviews/approve/<int:review_id>', methods=['POST'])
@login_required
@admin_required
def approve_review(review_id):
    review = db.session.get(Review, review_id)
    if review:
        review.status = 'approved'
        db.session.commit()
        flash(f"Review for '{review.school.name}' has been approved.", 'success')
    return redirect(url_for('manage_reviews'))

# ★★★ START: CORRECTED delete_review ROUTE ★★★
@app.route('/admin/reviews/delete/<int:review_id>', methods=['POST'])
@login_required
@admin_required
def delete_review(review_id):
    review = db.session.get(Review, review_id)
    if review:
        # Get the school name BEFORE deleting the review
        school_name = review.school.name
        
        # Now, delete and commit
        db.session.delete(review)
        db.session.commit()
        
        # Use the stored name in the flash message
        flash(f"Review for '{school_name}' has been deleted.", 'info')
    else:
        flash('Review not found.', 'danger')
        
    return redirect(url_for('manage_reviews'))
# ★★★ END: CORRECTED delete_review ROUTE ★★★
# ★★★ START: NEW DESTRUCTIVE ACTION ROUTE ★★★
@app.route('/admin/empty-database', methods=['POST'])
@login_required
@superadmin_required
def empty_database():
    # A final check to ensure the user is a superadmin
    if not current_user.is_superadmin:
        flash("You do not have permission for this action.", "danger")
        return redirect(url_for('admin_dashboard'))

    # Delete data from tables in the correct order to respect relationships
    db.session.query(Review).delete()
    db.session.query(SchoolSuggestion).delete()
    db.session.query(School).delete()
    
    db.session.commit()
    
    flash("Database Emptied! All schools, suggestions, and reviews have been deleted.", "warning")
    return redirect(url_for('admin_dashboard'))
# ★★★ END: NEW DESTRUCTIVE ACTION ROUTE ★★★
# ★★★ NEW: ROUTE FOR THE MAP PAGE ★★★
@app.route('/map')
def school_map():
    return render_template('map.html', title="School Map of Rwanda")

# ★★★ NEW: ROUTE FOR THE TEAM PAGE ★★★
@app.route('/team')
def team():
    return render_template('team.html', title="Our Team")
# In app.py
# --- Update your imports at the top ---
# ★★★ NEW: CHANGE PASSWORD ROUTE ★★★
@app.route('/admin/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    # Allow any logged-in user to change password, or restrict to admin?
    # For now, keeping it consistent with the previous instruction, but if students/parents need it:
    # We should probably duplicate or make a generic change-password route.
    # Given the previous instruction was specific to ADMIN dashboard, I'll leave this as is
    # but remove @admin_required if regular users need it.
    # However, for safety, I will keep @admin_required here and assume students/parents might need a different route later
    # or I will refactor. Let's make a generic one.

    form = ChangePasswordForm()
    if form.validate_on_submit():
        # Check if the current password is correct
        if current_user.check_password(form.old_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Your password has been updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Incorrect current password. Please try again.', 'danger')
    return render_template('admin_change_password.html', title="Change Password", form=form)

@app.route('/smart-search', methods=['GET', 'POST'])
def smart_search():
    available_programs = collect_distinct_field_values(
        'education_program',
        seed_values=[
            'Rwandan General Education (REB Curriculum)',
            'Cambridge International Education (CIE)',
            'Technical and Vocational Education and Training (TVET)',
        ],
    )
    available_extracurriculars = collect_distinct_csv_values('extracurriculars', seed_values=DEFAULT_EXTRACURRICULAR_OPTIONS)
    available_combinations = collect_distinct_csv_values('combinations', seed_values=DEFAULT_COMBINATION_OPTIONS)

    if request.method == 'POST':
        student_answers = {
            'province': request.form.get('province', '').strip(),
            'education_program': request.form.get('education_program', '').strip(),
            'aggregate_score': request.form.get('aggregate_score', '').strip(),
            'gender_policy': request.form.get('gender_policy', '').strip(),
            'boarding_policy': request.form.get('boarding_policy', '').strip(),
            'ownership': request.form.get('ownership', '').strip(),
            'religious_affiliation': request.form.get('religious_affiliation', '').strip(),
            'fee_band': normalize_choice(request.form.get('fee_band', '').strip(), FEE_BAND_OPTIONS),
            'language_of_instruction': normalize_choice(
                request.form.get('language_of_instruction', '').strip(),
                LANGUAGE_OF_INSTRUCTION_OPTIONS
            ),
            'extracurriculars': request.form.getlist('extracurriculars'),
            'preferred_combinations': request.form.getlist('preferred_combinations'),
            'focus_tags': [tag for tag in request.form.getlist('focus_tags') if tag in SMART_TAG_OPTIONS],
        }

        candidate_query = School.query
        if student_answers['education_program']:
            candidate_query = candidate_query.filter(School.education_program == student_answers['education_program'])
        if student_answers['gender_policy']:
            candidate_query = candidate_query.filter(School.gender_policy == student_answers['gender_policy'])

        aggregate_score = None
        if student_answers['aggregate_score']:
            try:
                aggregate_score = int(student_answers['aggregate_score'])
                candidate_query = candidate_query.filter(
                    or_(School.min_aggregate >= aggregate_score, School.min_aggregate == None, School.min_aggregate == 0)
                )
            except ValueError:
                aggregate_score = None

        candidates = candidate_query.all()

        if not candidates:
            active_gates = []
            if student_answers['education_program']:
                active_gates.append(f"program: {student_answers['education_program']}")
            if student_answers['gender_policy']:
                active_gates.append(f"gender policy: {student_answers['gender_policy']}")
            if aggregate_score is not None:
                active_gates.append(f"aggregate score: {aggregate_score}")

            return render_template(
                'results.html',
                title="Your School Choice Matches",
                best_match=None,
                alternative_matches=[],
                advisor_answers=student_answers,
                empty_state={
                    'headline': 'No schools matched your core requirements yet',
                    'message': 'Try widening one or two strict answers, especially your academic program, gender policy, or aggregate score.',
                    'active_gates': active_gates,
                },
            )

        scoring_weights = {
            'province': 15,
            'boarding_policy': 10,
            'ownership': 5,
            'religious_affiliation': 5,
            'fee_band': 10,
            'language_of_instruction': 5,
            'extracurriculars': 15,
            'focus_tags': 15,
            'preferred_combinations': 10,
        }

        ranked_results = []

        for school in candidates:
            school_activities = split_csv_values(school.extracurriculars)
            school_tags = split_csv_values(school.tags)
            school_combinations = split_csv_values(school.combinations)
            review_count = Review.query.filter_by(school_id=school.id, status='approved').count()

            score = 0.0
            max_score = 0
            reasons = []
            watchouts = []
            answered_fields = 0
            available_fields = 0

            def track_simple(answer_key, school_value, label, weight, comparison_value=None):
                nonlocal score, max_score, answered_fields, available_fields
                answer_value = student_answers[answer_key]
                if not answer_value:
                    return
                answered_fields += 1
                max_score += weight
                if school_value:
                    available_fields += 1
                target_value = comparison_value if comparison_value is not None else school_value
                if school_value and normalize_token(target_value) == normalize_token(answer_value):
                    score += weight
                    reasons.append(f"{label} matches your preference")
                elif school_value:
                    watchouts.append(f"{label} differs from your preferred choice")
                else:
                    watchouts.append(f"{label} is not published for this school")

            track_simple('province', school.province, 'Location', scoring_weights['province'])
            track_simple('boarding_policy', school.boarding_policy, 'Boarding setup', scoring_weights['boarding_policy'])
            track_simple('ownership', school.ownership, 'Ownership', scoring_weights['ownership'])
            track_simple('fee_band', school.fee_band, 'Fee band', scoring_weights['fee_band'])
            track_simple(
                'language_of_instruction',
                school.language_of_instruction,
                'Language of instruction',
                scoring_weights['language_of_instruction']
            )

            if student_answers['religious_affiliation']:
                answered_fields += 1
                max_score += scoring_weights['religious_affiliation']
                if school.religious_affiliation:
                    available_fields += 1
                    if normalize_token(student_answers['religious_affiliation']) in normalize_token(school.religious_affiliation):
                        score += scoring_weights['religious_affiliation']
                        reasons.append('Religious affiliation aligns with your preference')
                    else:
                        watchouts.append('Religious affiliation does not match your preferred tradition')
                else:
                    watchouts.append('Religious affiliation is not published for this school')

            def score_overlap(answer_key, school_values, label, weight):
                nonlocal score, max_score, answered_fields, available_fields
                selected_values = student_answers[answer_key]
                if not selected_values:
                    return
                answered_fields += 1
                max_score += weight
                if school_values:
                    available_fields += 1
                    school_tokens = {normalize_token(item): item for item in school_values}
                    overlap = [school_tokens[token] for token in {normalize_token(item) for item in selected_values} if token in school_tokens]
                    if overlap:
                        overlap_ratio = len(overlap) / len(selected_values)
                        overlap_points = round(weight * overlap_ratio, 2)
                        score += overlap_points
                        reasons.append(f"{label}: {', '.join(overlap[:3])}")
                        if overlap_ratio < 1:
                            watchouts.append(f"{label} only partially overlaps with your interests")
                    else:
                        watchouts.append(f"No listed {label.lower()} match your selected options")
                else:
                    watchouts.append(f"{label} are not published for this school")

            score_overlap('extracurriculars', school_activities, 'Activities', scoring_weights['extracurriculars'])
            score_overlap('focus_tags', school_tags, 'Focus tags', scoring_weights['focus_tags'])
            score_overlap('preferred_combinations', school_combinations, 'Subject combinations', scoring_weights['preferred_combinations'])

            if aggregate_score is not None and school.min_aggregate:
                reasons.append(f"Aggregate score {aggregate_score} is eligible for the listed cutoff")
            elif aggregate_score is not None and not school.min_aggregate:
                watchouts.append('This school has no published cutoff, so eligibility is less certain')

            fit_score = 100 if max_score == 0 else round((score / max_score) * 100)
            confidence_ratio = 1 if answered_fields == 0 else available_fields / answered_fields
            if confidence_ratio >= 0.8:
                confidence_label = 'High confidence'
            elif confidence_ratio >= 0.55:
                confidence_label = 'Medium confidence'
            else:
                confidence_label = 'Developing confidence'

            if not reasons:
                reasons.append('This school clears your core requirements and is ranked using published profile quality and review tie-breakers')

            ranked_results.append({
                'school': school,
                'photo': school_primary_image(school),
                'score': round(score, 2),
                'max_score': max_score,
                'fit_score': fit_score,
                'confidence_label': confidence_label,
                'reasons': reasons[:4],
                'watchouts': watchouts[:3],
                'review_count': review_count,
                'average_rating': school.average_rating,
                'profile_completeness': school_profile_completeness(school),
                'matched_program': school.education_program,
            })

        ranked_results.sort(
            key=lambda item: (
                -item['fit_score'],
                -item['average_rating'],
                -item['review_count'],
                -item['profile_completeness'],
                item['school'].name.lower(),
            )
        )

        top_matches = ranked_results[:3]
        best_match = top_matches[0] if top_matches else None
        alternative_matches = top_matches[1:] if len(top_matches) > 1 else []

        return render_template(
            'results.html',
            title="Your School Choice Matches",
            best_match=best_match,
            alternative_matches=alternative_matches,
            advisor_answers=student_answers,
            empty_state=None,
        )

    return render_template(
        'smart_search.html',
        title="School Choice Assistant",
        provinces=RWANDA_PROVINCES,
        education_programs=available_programs,
        extracurriculars=available_extracurriculars,
        combinations=available_combinations,
        smart_tags=SMART_TAG_OPTIONS,
        fee_band_options=FEE_BAND_OPTIONS,
        language_options=LANGUAGE_OF_INSTRUCTION_OPTIONS,
    )
# ★★★ END: UPGRADED smart_search ROUTE ★★★

# --- ★★★ NEW: PARENT/STUDENT PORTALS ★★★ ---

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('dashboard'))

    # Get shortlist
    shortlist = Shortlist.query.filter_by(student_id=current_user.id).all()

    # Check parent link
    parent = current_user.parent

    return render_template('student_dashboard.html',
                           title="Student Dashboard",
                           shortlist=shortlist,
                           parent=parent)

@app.route('/parent/dashboard')
@login_required
def parent_dashboard():
    if current_user.role != 'parent':
        return redirect(url_for('dashboard'))

    children = User.query.filter_by(parent_id=current_user.id).all()

    # Gather all shortlists from all children
    # Structure: [ { 'child': child_obj, 'shortlists': [list_of_shortlists] } ]
    children_data = []
    for child in children:
        s_lists = Shortlist.query.filter_by(student_id=child.id).all()
        children_data.append({'child': child, 'shortlists': s_lists})

    return render_template('parent_dashboard.html',
                           title="Parent Dashboard",
                           children_data=children_data)

@app.route('/profile/link', methods=['GET', 'POST'])
@login_required
def link_account():
    form = LinkFamilyForm()
    if form.validate_on_submit():
        target_user = User.query.filter_by(email=form.target_email.data).first()
        if not target_user:
            flash('User with that email not found.', 'danger')
        elif target_user.id == current_user.id:
             flash('You cannot link to yourself.', 'warning')
        else:
            # Logic:
            # If current is Parent, target must be Student.
            # If current is Student, target must be Parent.

            if current_user.role == 'parent':
                if target_user.role == 'student':
                    # Parent "claims" student? Or invites?
                    # For simplicity: Direct Link
                    target_user.parent_id = current_user.id
                    db.session.commit()
                    flash(f'Successfully linked to student {target_user.username}.', 'success')
                    return redirect(url_for('parent_dashboard'))
                else:
                    flash('A Parent account can only link to a Student account.', 'warning')

            elif current_user.role == 'student':
                if target_user.role == 'parent':
                    current_user.parent_id = target_user.id
                    db.session.commit()
                    flash(f'Successfully linked to parent {target_user.username}.', 'success')
                    return redirect(url_for('student_dashboard'))
                else:
                    flash('A Student account can only link to a Parent account.', 'warning')
            else:
                 flash('Only Students and Parents can link accounts.', 'warning')

    return render_template('link_account.html', title="Link Family Account", form=form)

@app.route('/student/shortlist/add/<int:school_id>', methods=['POST'])
@login_required
def add_to_shortlist(school_id):
    if current_user.role != 'student':
        flash('Only students can shortlist schools.', 'danger')
        return redirect(url_for('index'))

    existing = Shortlist.query.filter_by(student_id=current_user.id, school_id=school_id).first()
    if existing:
        flash('This school is already in your shortlist.', 'info')
    else:
        new_item = Shortlist(student_id=current_user.id, school_id=school_id)
        db.session.add(new_item)
        db.session.commit()
        flash('School added to your shortlist!', 'success')

    return redirect(url_for('student_dashboard'))

@app.route('/parent/shortlist/update/<int:shortlist_id>', methods=['POST'])
@login_required
def update_shortlist_status(shortlist_id):
    print(f"DEBUG: Hit update route for shortlist {shortlist_id}")
    print(f"DEBUG: Current User: {current_user}")
    if current_user.role != 'parent':
        print(f"DEBUG: Not a parent, role is {current_user.role}")
        return redirect(url_for('dashboard'))

    shortlist_item = Shortlist.query.get_or_404(shortlist_id)

    # Security check: Ensure this shortlist belongs to one of the parent's children
    print(f"DEBUG: Student Parent ID: {shortlist_item.student.parent_id}, Current User ID: {current_user.id}")
    if shortlist_item.student.parent_id != current_user.id:
        print("DEBUG: Unauthorized action")
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('parent_dashboard'))

    action = request.form.get('action') # 'approve' or 'reject'
    print(f"DEBUG: Action received: {action}")
    comment = request.form.get('comment')

    if action in ['approved', 'rejected']:
        shortlist_item.parent_status = action
        if comment:
            shortlist_item.parent_comment = comment
        db.session.commit()
        flash(f'Shortlist item marked as {action}.', 'success')

    return redirect(url_for('parent_dashboard'))

@app.route('/compare', methods=['GET', 'POST'])
def compare_schools():
    def split_items(value):
        return [item.strip() for item in value.split(',') if item.strip()] if value else []

    def primary_photo(school):
        photos = split_items(school.photos)
        return photos[0] if photos else url_for('static', filename='images/default_school.png')

    def approved_review_count(school_id):
        return Review.query.filter_by(school_id=school_id, status='approved').count()

    def availability_text(value, empty_text='Unavailable'):
        if value is None:
            return empty_text
        if isinstance(value, str):
            return value if value.strip() else empty_text
        if isinstance(value, list):
            return ', '.join(value) if value else empty_text
        if value == 0:
            return empty_text
        return str(value)

    def compare_numeric_higher_more_accessible(v1, v2):
        if not v1 or not v2:
            return None
        if v1 == v2:
            return 'tie'
        return 'left' if v1 > v2 else 'right'

    def compare_numeric_higher_better(v1, v2):
        if v1 is None or v2 is None:
            return None
        if v1 == v2:
            return 'tie'
        return 'left' if v1 > v2 else 'right'

    def compare_presence(v1, v2):
        left_has = bool(v1)
        right_has = bool(v2)
        if left_has and right_has:
            return 'tie'
        if left_has:
            return 'left'
        if right_has:
            return 'right'
        return None

    def build_profile(school):
        return {
            'school': school,
            'photo': primary_photo(school),
            'review_count': approved_review_count(school.id),
            'combinations': split_items(school.combinations),
            'activities': split_items(school.extracurriculars),
            'tags': split_items(school.tags),
            'fees_text': availability_text(school.fees_breakdown, 'Not published'),
            'cutoff_text': availability_text(school.min_aggregate, 'Not specified'),
        }

    def criterion(label, left, right, helper=None, comparison=None, left_display=None, right_display=None):
        return {
            'label': label,
            'left': availability_text(left),
            'right': availability_text(right),
            'left_display': left_display or availability_text(left),
            'right_display': right_display or availability_text(right),
            'helper': helper,
            'comparison': comparison,
        }

    def build_overall_summary(left_school, right_school, sections):
        scoring_rules = {
            'Minimum aggregate cutoff': {'left': 3, 'right': 3},
            'Average rating': {'left': 2, 'right': 2},
            'Approved review count': {'left': 1, 'right': 1},
            'Subject combinations': {'left': 1, 'right': 1},
            'Performance history': {'left': 1, 'right': 1},
            'Activities and clubs': {'left': 1, 'right': 1},
            'Tags': {'left': 1, 'right': 1},
            'Website': {'left': 1, 'right': 1},
            'Contact phone': {'left': 1, 'right': 1},
            'Fees breakdown': {'left': 1, 'right': 1},
            'Fees document': {'left': 1, 'right': 1},
        }

        left_score = 0
        right_score = 0
        left_reasons = []
        right_reasons = []

        for section in sections:
            for item in section['criteria']:
                weights = scoring_rules.get(item['label'])
                if not weights:
                    continue
                if item['comparison'] == 'left':
                    left_score += weights['left']
                    left_reasons.append(item['label'])
                elif item['comparison'] == 'right':
                    right_score += weights['right']
                    right_reasons.append(item['label'])

        if left_score == 0 and right_score == 0:
            return {
                'winner': None,
                'left_score': left_score,
                'right_score': right_score,
                'headline': 'No overall suggestion yet',
                'summary': 'There is not enough comparable published data to recommend one school over the other yet.',
                'reasons': [],
            }

        if left_score == right_score:
            return {
                'winner': None,
                'left_score': left_score,
                'right_score': right_score,
                'headline': 'These schools are closely matched',
                'summary': 'The available comparison data is balanced, so the better choice depends on your personal preferences and priorities.',
                'reasons': left_reasons[:3] if left_reasons else right_reasons[:3],
            }

        winner = 'left' if left_score > right_score else 'right'
        winning_school = left_school if winner == 'left' else right_school
        winning_score = left_score if winner == 'left' else right_score
        losing_score = right_score if winner == 'left' else left_score
        reasons = left_reasons if winner == 'left' else right_reasons

        return {
            'winner': winner,
            'left_score': left_score,
            'right_score': right_score,
            'headline': f'Best overall choice: {winning_school.name}',
            'summary': f'This school leads on more published student-fit signals ({winning_score} vs {losing_score}) based on real comparison data only.',
            'reasons': reasons[:4],
        }

    form = CompareSchoolsForm()
    # Populate choices
    schools = School.query.order_by(School.name).all()
    choices = [(s.id, s.name) for s in schools]
    form.school1.choices = choices
    form.school2.choices = choices

    s1_obj = None
    s2_obj = None
    compare_sections = []
    s1_profile = None
    s2_profile = None
    overall_summary = None

    if form.validate_on_submit():
        s1_obj = db.session.get(School, form.school1.data)
        s2_obj = db.session.get(School, form.school2.data)
    elif request.args.get('s1') and request.args.get('s2'):
        # Allow GET params for sharing links
        s1_obj = db.session.get(School, request.args.get('s1'))
        s2_obj = db.session.get(School, request.args.get('s2'))
        # Set form data for display
        form.school1.data = int(request.args.get('s1'))
        form.school2.data = int(request.args.get('s2'))

    if s1_obj and s2_obj:
        s1_profile = build_profile(s1_obj)
        s2_profile = build_profile(s2_obj)

        compare_sections = [
            {
                'title': 'Admissions & Fit',
                'description': 'Best for quick student decision-making and access planning.',
                'criteria': [
                    criterion(
                        'Minimum aggregate cutoff',
                        s1_obj.min_aggregate,
                        s2_obj.min_aggregate,
                        helper='A higher listed cutoff can mean the school is accessible to more students. If a value is missing or zero, the cutoff is not specified.',
                        comparison=compare_numeric_higher_more_accessible(s1_obj.min_aggregate, s2_obj.min_aggregate),
                        left_display=s1_profile['cutoff_text'],
                        right_display=s2_profile['cutoff_text'],
                    ),
                    criterion('Boarding policy', s1_obj.boarding_policy, s2_obj.boarding_policy),
                    criterion('Education program', s1_obj.education_program, s2_obj.education_program),
                    criterion('Gender policy', s1_obj.gender_policy, s2_obj.gender_policy),
                    criterion('Location', f'{s1_obj.district}, {s1_obj.province}', f'{s2_obj.district}, {s2_obj.province}'),
                ],
            },
            {
                'title': 'Academic Profile',
                'description': 'Real academic details published on each school profile.',
                'criteria': [
                    criterion(
                        'Subject combinations',
                        s1_profile['combinations'],
                        s2_profile['combinations'],
                        comparison=compare_presence(s1_profile['combinations'], s2_profile['combinations']),
                    ),
                    criterion(
                        'Performance history',
                        s1_obj.performance_history,
                        s2_obj.performance_history,
                        comparison=compare_presence(s1_obj.performance_history, s2_obj.performance_history),
                    ),
                ],
            },
            {
                'title': 'Student Life',
                'description': 'Signals about school activities and identity from profile data.',
                'criteria': [
                    criterion(
                        'Activities and clubs',
                        s1_profile['activities'],
                        s2_profile['activities'],
                        comparison=compare_presence(s1_profile['activities'], s2_profile['activities']),
                    ),
                    criterion(
                        'Tags',
                        s1_profile['tags'],
                        s2_profile['tags'],
                        comparison=compare_presence(s1_profile['tags'], s2_profile['tags']),
                    ),
                ],
            },
            {
                'title': 'Practical Details',
                'description': 'Useful contact and fee information without guessing.',
                'criteria': [
                    criterion(
                        'Website',
                        s1_obj.website,
                        s2_obj.website,
                        comparison=compare_presence(s1_obj.website, s2_obj.website),
                    ),
                    criterion(
                        'Contact phone',
                        s1_obj.phone,
                        s2_obj.phone,
                        comparison=compare_presence(s1_obj.phone, s2_obj.phone),
                    ),
                    criterion(
                        'Fees breakdown',
                        s1_obj.fees_breakdown,
                        s2_obj.fees_breakdown,
                        comparison=compare_presence(s1_obj.fees_breakdown, s2_obj.fees_breakdown),
                        left_display=s1_profile['fees_text'],
                        right_display=s2_profile['fees_text'],
                    ),
                    criterion(
                        'Fees document',
                        'Available' if s1_obj.fees_file else None,
                        'Available' if s2_obj.fees_file else None,
                        comparison=compare_presence(s1_obj.fees_file, s2_obj.fees_file),
                    ),
                ],
            },
            {
                'title': 'Community Signals',
                'description': 'Based only on approved public reviews.',
                'criteria': [
                    criterion(
                        'Average rating',
                        s1_obj.average_rating,
                        s2_obj.average_rating,
                        helper='Ratings are calculated from approved reviews only.',
                        comparison=compare_numeric_higher_better(s1_obj.average_rating, s2_obj.average_rating),
                        left_display=f"{s1_obj.average_rating:.1f} / 5" if s1_profile['review_count'] else 'Unavailable',
                        right_display=f"{s2_obj.average_rating:.1f} / 5" if s2_profile['review_count'] else 'Unavailable',
                    ),
                    criterion(
                        'Approved review count',
                        s1_profile['review_count'],
                        s2_profile['review_count'],
                        comparison=compare_numeric_higher_better(s1_profile['review_count'], s2_profile['review_count']),
                        left_display=str(s1_profile['review_count']) if s1_profile['review_count'] else 'Unavailable',
                        right_display=str(s2_profile['review_count']) if s2_profile['review_count'] else 'Unavailable',
                    ),
                ],
            },
        ]

        overall_summary = build_overall_summary(s1_obj, s2_obj, compare_sections)

    return render_template(
        'compare.html',
        title="Compare Schools",
        form=form,
        s1=s1_obj,
        s2=s2_obj,
        s1_profile=s1_profile,
        s2_profile=s2_profile,
        compare_sections=compare_sections,
        overall_summary=overall_summary,
    )
# --- Main execution ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', email='admin@path2learn.rw', role='superadmin')
            admin_user.set_password('password')
            db.session.add(admin_user)
            db.session.commit()
            print("Default SUPERADMIN user created with username 'admin' and password 'password'")
    app.run(debug=True)
