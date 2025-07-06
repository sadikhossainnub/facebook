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

    def set_webhook_url(self):
        if not self.webhook_url:
            self.webhook_url = frappe.utils.get_url("/api/method/facebook.api.messenger_webhook")
            self.save()
