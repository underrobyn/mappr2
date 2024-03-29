from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_pymongo import PyMongo
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_admin import Admin
from flask_wtf import CSRFProtect
import mimetypes

mimetypes.add_type('text/css', '.css')
mimetypes.add_type('text/javascript', '.js')

# Initialise objects
db = SQLAlchemy()
mongo = PyMongo()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address, default_limits=["10000 per day", "1000 per hour", "100 per minute"])
flaskadmin = Admin(name='Mappr2', template_mode='bootstrap4')

# Define folders
static_folder = 'static'
template_folder = 'templates'


def create_app():
	app = Flask(__name__, template_folder=template_folder, instance_relative_config=False, static_folder=static_folder)
	app.config.from_object('config.Config')

	db.init_app(app)
	mongo.init_app(app)
	migrate.init_app(app, db, compare_type=True)
	limiter.init_app(app)
	login_manager.init_app(app)
	flaskadmin.init_app(app)
	csrf.init_app(app)

	with app.app_context():
		from . import routes
		from .admin import views as admin_views
		from .api import routes as api_routes
		from .auth import routes as auth_routes
		from .errors import routes as error_routes
		from .gallery import routes as gallery_routes
		from .gallery import threads as gallery_threads
		from .map import routes as map_routes
		from .map import threads as map_threads
		from .statistics import routes as statistics_routes
		from .user import routes as user_routes

		app.register_blueprint(routes.main_bp)
		app.register_blueprint(api_routes.api_bp)
		app.register_blueprint(auth_routes.auth_bp)
		app.register_blueprint(error_routes.error_bp)
		app.register_blueprint(gallery_routes.gallery_bp)
		app.register_blueprint(map_routes.map_bp)
		app.register_blueprint(statistics_routes.statistics_bp)
		app.register_blueprint(user_routes.user_bp)

		@app.before_first_request
		def activate_job_monitor():
			# Create the threads
			img_thread = gallery_threads.ImageProcessorThread()
			csv_thread = map_threads.FileProcessorThread()

			img_thread.set_app(app)

			# Tie them to the application
			app.imageprocessor = img_thread
			app.mapfileprocessor = csv_thread

			# Start the threads
			img_thread.start()
			csv_thread.start()

		db.create_all()

	login_manager.login_view = "auth_bp.auth"
	login_manager.refresh_view = "auth_bp.reauth"
	login_manager.needs_refresh_message = (
		u"To protect your account, please reauthenticate to access this page."
	)
	login_manager.needs_refresh_message_category = "warning"

	@app.after_request
	def apply_headers(response):
		response.headers["Server"] = "Mappr2"
		response.headers['Cross-Origin-Resource-Policy'] = 'same-site'

		if not request.path.startswith('/static/') and not request.path.startswith('/api/') and '192.168' not in request.host:
			response.headers["Feature-Policy"] = "camera 'self'; fullscreen 'self'; geolocation 'self';"
			response.headers["Permissions-Policy"] = "accelerometer=(), camera=(self), geolocation=(self), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=(), interest-cohort=()"
			response.headers["Referrer-Policy"] = "same-origin"
			response.headers["X-Frame-Options"] = "Deny"
			response.headers["X-XSS-Protection"] = "1; mode=block"

			csp_header_value = "script-src 'self' https://analytics.mappr.uk https://static.cloudflareinsights.com https://fonts.googleapis.com https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; img-src 'self' data: blob: https://cdnjs.cloudflare.com https://api.cellmapper.net https://www.three.co.uk/ https://mapserver.vodafone.co.uk https://68aa7b45-tiles.spatialbuzz.net https://coverage.ee.co.uk https://mt1.google.com https://tile.opentopomap.org https://*.tile.openstreetmap.org https://*.api.tomtom.com; font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; connect-src 'self' https://analytics.mappr.uk https://nominatim.openstreetmap.org https://mappr.report-uri.com; media-src 'none'; object-src 'none'; child-src 'none'; form-action 'self'; upgrade-insecure-requests; block-all-mixed-content; manifest-src 'self'; worker-src 'self'; report-uri https://mappr.report-uri.com/r/d/csp/reportOnly"

			# Production only headers
			if app.config['ENV'] == 'production':
				response.headers['Content-Security-Policy-Report-Only'] = csp_header_value
				response.headers['Cross-Origin-Embedder-Policy-Report-Only'] = 'require-corp; report-to="default"' # Change to require-corp in future
				response.headers['Cross-Origin-Opener-Policy-Report-Only'] = 'same-origin; report-to="default"'
				response.headers['Expect-CT'] = 'report-uri="https://mappr.report-uri.com/r/d/ct/reportOnly", max-age=30'
				response.headers['Report-To'] = '{"group":"default","max_age":3600,"endpoints":[{"url":"https://mappr.report-uri.com/a/d/g"}],"include_subdomains":true}'
				response.headers['NEL'] = '{"report_to":"default","max_age":3600,"include_subdomains":true}'

			# Testing headers
			if app.config['ENV'] == 'development':
				response.headers['Content-Security-Policy'] = csp_header_value
				response.headers['Cross-Origin-Embedder-Policy'] = 'unsafe-none; report-to="default"'
				response.headers['Cross-Origin-Opener-Policy'] = 'same-origin; report-to="default"'

		return response

	return app


app = create_app()
