import os
import click
from flask import Flask, render_template
from config import Config
from routes.public import public_bp
from routes.admin import admin_bp
from routes.api import api_bp
from services.auth_service import ensure_seed_admin
from services.scheduler_service import start_scheduler
from services.sync_service import perform_sync
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    """Application factory for SC&SS JNU Alumni Meet Platform."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register Blueprints
    admin_prefix = app.config.get("ADMIN_PATH_PREFIX", "/admin")
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix=admin_prefix)
    app.register_blueprint(api_bp)

    # Global Template Context Processor
    @app.context_processor
    def inject_globals():
        return {
            "google_form_url": app.config.get("GOOGLE_FORM_URL"),
            "admin_path_prefix": app.config.get("ADMIN_PATH_PREFIX", "/admin")
        }

    # Template Filters
    @app.template_filter("currency_inr")
    def currency_inr_filter(value):
        """Format number as Indian Rupee (e.g. ₹10,000.00)."""
        try:
            val = float(value or 0)
            return f"₹{val:,.2f}"
        except (ValueError, TypeError):
            return "₹0.00"

    @app.template_filter("format_date")
    def format_date_filter(value, fmt="%d %B %Y"):
        """Format datetime object."""
        if not value:
            return "TBD"
        if hasattr(value, "strftime"):
            return value.strftime(fmt)
        return str(value)

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("base.html", error_title="Page Not Found", error_message="The page you requested could not be found."), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("base.html", error_title="System Error", error_message="An internal error occurred. Please try again shortly."), 500

    # Custom Flask CLI commands
    @app.cli.command("sync-sheets")
    def sync_sheets_command():
        """CLI command to manually trigger Google Sheet sync."""
        logger.info("Executing manual Google Sheets sync via Flask CLI...")
        result = perform_sync(triggered_by="flask_cli")
        if result.get("success"):
            print(f"Sync Successful: {result.get('message')}")
        else:
            print(f"Sync Failed: {result.get('error')}")

    @app.cli.command("purge-alumni")
    def purge_alumni_command():
        """CLI command to purge all alumni records, contributions, and responses."""
        from services.alumni_service import purge_all_alumni_records
        logger.warning("Executing alumni data purge via Flask CLI...")
        try:
            metrics = purge_all_alumni_records()
            print(f"Successfully purged database: {metrics['alumni_deleted']} alumni, {metrics['contributions_deleted']} contributions, {metrics['responses_deleted']} responses deleted.")
        except Exception as e:
            print(f"Purge failed: {e}")

    @app.cli.command("delete-alumnus")
    @click.argument("alumni_id", type=int)
    def delete_alumnus_command(alumni_id):
        """CLI command to delete a single alumnus record and related responses/contributions."""
        from services.alumni_service import delete_single_alumnus
        logger.warning(f"Executing deletion for alumnus ID #{alumni_id} via Flask CLI...")
        try:
            metrics = delete_single_alumnus(alumni_id)
            if not metrics:
                print(f"Alumnus ID #{alumni_id} not found.")
            else:
                print(f"Successfully deleted alumnus '{metrics['full_name']}' (ID #{alumni_id}): {metrics['responses_deleted']} responses, {metrics['contributions_deleted']} contributions deleted.")
        except Exception as e:
            print(f"Deletion failed: {e}")

    @app.cli.command("delete-contribution")
    @click.argument("contrib_id", type=int)
    def delete_contribution_command(contrib_id):
        """CLI command to delete a single duplicate or invalid contribution record."""
        from services.contribution_service import delete_single_contribution
        logger.warning(f"Executing deletion for contribution #{contrib_id} via Flask CLI...")
        try:
            contrib = delete_single_contribution(contrib_id)
            if not contrib:
                print(f"Contribution #{contrib_id} not found.")
            else:
                print(f"Successfully deleted contribution #{contrib_id} ({contrib.get('amount')} INR).")
        except Exception as e:
            print(f"Deletion failed: {e}")

    @app.cli.command("deduplicate-contributions")
    def deduplicate_contributions_command():
        """CLI command to scan and prune duplicate contribution records."""
        from services.contribution_service import clean_duplicate_contributions
        logger.info("Scanning for duplicate contributions via Flask CLI...")
        try:
            metrics = clean_duplicate_contributions()
            print(f"Cleanup finished: {metrics.get('duplicates_removed', 0)} duplicate contribution(s) removed.")
        except Exception as e:
            print(f"Deduplication failed: {e}")



    # Initialize Seed Admin and 24-Hour Sync Scheduler
    with app.app_context():
        try:
            ensure_seed_admin()
        except Exception as e:
            logger.warning(f"Could not connect to database on startup (will connect on requests): {e}")

        try:
            start_scheduler(app)
        except Exception as e:
            logger.warning(f"Could not start background sync scheduler: {e}")

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
