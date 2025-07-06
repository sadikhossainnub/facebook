import frappe
from werkzeug.wrappers import Response

@frappe.whitelist(allow_guest=True)
def messenger_webhook():
    if frappe.request.method == "GET":
        return verify_token_and_fulfill_challenge()

    try:
        form_dict = frappe.local.form_dict
        messages = form_dict["entry"][0]["changes"][0]["value"].get("messages", [])
        statuses = form_dict["entry"][0]["changes"][0]["value"].get("statuses", [])

        # TODO: Implement message processing logic here
        # For now, just log the messages and statuses
        frappe.logger().info(f"Received Messenger messages: {messages}")
        frappe.logger().info(f"Received Messenger statuses: {statuses}")

        frappe.get_doc(
            {"doctype": "Messenger Webhook Log", "payload": frappe.as_json(form_dict)}
        ).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error("Messenger Webhook Log Error", frappe.get_traceback())
        frappe.throw("Something went wrong")

    return Response("EVENT_RECEIVED", status=200)

def verify_token_and_fulfill_challenge():
    meta_challenge = frappe.form_dict.get("hub.challenge")
    expected_token = frappe.db.get_single_value("Messenger Settings", "verify_token")

    if frappe.form_dict.get("hub.verify_token") != expected_token:
        frappe.throw("Verify token does not match")

    return Response(meta_challenge, status=200)
