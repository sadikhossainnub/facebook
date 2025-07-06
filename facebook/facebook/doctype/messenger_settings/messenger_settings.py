import frappe
from frappe.model.document import Document

class MessengerSettings(Document):
    def on_update(self):
        self.set_webhook_url()
        self.validate_tokens()

    def set_webhook_url(self):
        if not self.webhook_url:
            self.webhook_url = frappe.utils.get_url("/api/method/facebook.api.messenger_webhook")
            self.save()

    def validate_tokens(self):
        # if not self.page_access_token:
        #     frappe.throw("Page Access Token must be set in Messenger Settings")
        if not self.verify_token:
            frappe.throw("Verify Token must be set in Messenger Settings")
        # Optionally validate app_secret presence
        # if not self.app_secret:
        #     frappe.throw("App Secret must be set in Messenger Settings")

    def validate_integration(self):
        # Adapt validation to new fields from waba_settings reference
        if self.integration_enabled:
            if not self.access_token:
                frappe.throw("Access Token must be set if integration is enabled")
            if not self.phone_number_id:
                frappe.throw("Phone Number ID must be set if integration is enabled")
            if not self.business_account_id:
                frappe.throw("Business Account ID must be set if integration is enabled")
            if not self.webhook_verify_token:
                frappe.throw("Webhook Verify Token must be set if integration is enabled")

    def set_webhook_url(self):
        if not self.webhook_url:
            self.webhook_url = frappe.utils.get_url("/api/method/facebook.api.messenger_webhook")
            self.save()
