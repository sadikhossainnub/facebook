import frappe
from frappe.model.document import Document

class MessengerSettings(Document):
    def on_update(self):
        self.set_webhook_url()

    def set_webhook_url(self):
        if not self.webhook_url:
            self.webhook_url = frappe.utils.get_url("/api/method/facebook.api.messenger_webhook")
            self.save()
