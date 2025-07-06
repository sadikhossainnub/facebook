import frappe
from werkzeug.wrappers import Response
import json
import requests
import logging
import hmac
import hashlib

logger = logging.getLogger(__name__)

@frappe.whitelist(allow_guest=True)
def messenger_webhook():
    try:
        if frappe.request.method == 'GET':
            # Facebook verification
            verify_token = frappe.db.get_single_value('Messenger Settings', 'verify_token')
            if frappe.form_dict.get('hub.verify_token') == verify_token:
                return Response(frappe.form_dict['hub.challenge'])
            else:
                logger.warning("Invalid verification token received in webhook GET")
                return Response("Invalid verification token", status=403)

        elif frappe.request.method == 'POST':
            # Optional: Verify X-Hub-Signature-256 header for security
            app_secret = frappe.db.get_single_value('Messenger Settings', 'app_secret')
            signature = frappe.request.headers.get('X-Hub-Signature-256')
            if signature and app_secret:
                if not verify_signature(frappe.request.data, signature, app_secret):
                    logger.warning("Invalid webhook signature")
                    return Response("Invalid signature", status=403)

            data = json.loads(frappe.request.data)
            for entry in data.get('entry', []):
                for message in entry.get('messaging', []):
                    if message.get('message'):
                        handle_incoming_message(message)
            return Response("success", status=200)
        else:
            logger.warning(f"Unsupported HTTP method {frappe.request.method} on messenger_webhook")
            return Response("Method not allowed", status=405)
    except Exception as e:
        logger.error(f"Error in messenger_webhook: {str(e)}", exc_info=True)
        return Response("Internal Server Error", status=500)

def verify_signature(payload, signature, app_secret):
    try:
        sha_name, signature_hash = signature.split('=')
        if sha_name != 'sha256':
            return False
        mac = hmac.new(app_secret.encode('utf-8'), msg=payload, digestmod=hashlib.sha256)
        expected_hash = mac.hexdigest()
        return hmac.compare_digest(expected_hash, signature_hash)
    except Exception as e:
        logger.error(f"Error verifying signature: {str(e)}", exc_info=True)
        return False

def handle_incoming_message(message):
    try:
        sender_id = message.get('sender', {}).get('id')
        message_text = message.get('message', {}).get('text')
        if not sender_id or not message_text:
            logger.error('Missing sender_id or message_text in incoming message')
            return

        conversation_name = frappe.db.get_value('Messenger Conversation', {'fb_psid': sender_id})
        if conversation_name:
            conversation = frappe.get_doc('Messenger Conversation', conversation_name)
        else:
            conversation = frappe.new_doc('Messenger Conversation')
            conversation.fb_psid = sender_id
            conversation.status = 'Open'
            # You might want to create a new Lead or Contact here
            conversation.insert(ignore_permissions=True)

        new_message = frappe.new_doc('Messenger Message')
        new_message.parent = conversation.name
        new_message.content = message_text
        new_message.direction = 'Inbound'
        new_message.sender = sender_id
        new_message.timestamp = frappe.utils.now_datetime()
        new_message.insert(ignore_permissions=True)

        conversation.last_message_time = frappe.utils.now_datetime()
        conversation.save(ignore_permissions=True)

        frappe.publish_realtime('messenger_message', data={'conversation': conversation.name, 'text': message_text}, user=frappe.session.user)
    except Exception as e:
        logger.error(f"Error handling incoming message: {str(e)}", exc_info=True)

@frappe.whitelist()
def send_message(conversation_name, message_text):
    try:
        conversation = frappe.get_doc('Messenger Conversation', conversation_name)
        page_access_token = frappe.db.get_single_value('Messenger Settings', 'page_access_token')

        if not page_access_token:
            frappe.throw("Please set the Page Access Token in Messenger Settings")

        url = f"https://graph.facebook.com/v13.0/me/messages?access_token={page_access_token}"
        payload = {
            "recipient": {"id": conversation.fb_psid},
            "message": {"text": message_text}
        }
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            new_message = frappe.new_doc('Messenger Message')
            new_message.parent = conversation.name
            new_message.content = message_text
            new_message.direction = 'Outbound'
            new_message.sender = 'Me'
            new_message.timestamp = frappe.utils.now_datetime()
            new_message.insert(ignore_permissions=True)

            conversation.last_message_time = frappe.utils.now_datetime()
            conversation.save(ignore_permissions=True)

            frappe.publish_realtime('messenger_message', data={'conversation': conversation.name, 'text': message_text}, user=frappe.session.user)
        else:
            logger.error(f"Failed to send message: {response.status_code} {response.text}")
            frappe.throw(f"Failed to send message: {response.text}")
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}", exc_info=True)
        frappe.throw("An error occurred while sending the message")
