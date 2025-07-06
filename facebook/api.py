import frappe
from werkzeug.wrappers import Response
import json
import requests

@frappe.whitelist(allow_guest=True)
def messenger_webhook():
    if frappe.request.method == 'GET':
        # Facebook verification
        if frappe.form_dict.get('hub.verify_token') == frappe.db.get_single_value('Messenger Settings', 'verify_token'):
            return Response(frappe.form_dict['hub.challenge'])
        else:
            return Response("Invalid verification token", status=403)

    elif frappe.request.method == 'POST':
        data = json.loads(frappe.request.data)
        for entry in data.get('entry', []):
            for message in entry.get('messaging', []):
                if message.get('message'):
                    handle_incoming_message(message)
        return Response("success", status=200)

def handle_incoming_message(message):
    sender_id = message['sender']['id']
    message_text = message['message']['text']

    conversation = frappe.get_doc('Messenger Conversation', {'fb_psid': sender_id})
    if not conversation:
        conversation = frappe.new_doc('Messenger Conversation')
        conversation.fb_psid = sender_id
        conversation.status = 'Open'
        # You might want to create a new Lead or Contact here
        conversation.insert(ignore_permissions=True)

    new_message = frappe.new_doc('Messenger Message')
    new_message.parent = conversation.name
    new_message.parenttype = 'Messenger Conversation'
    new_message.parentfield = 'messages'
    new_message.content = message_text
    new_message.direction = 'Inbound'
    new_message.sender = sender_id
    new_message.timestamp = frappe.utils.now_datetime()
    new_message.insert(ignore_permissions=True)

    conversation.last_message_time = frappe.utils.now_datetime()
    conversation.save(ignore_permissions=True)

    frappe.publish_realtime('messenger_message', data={'conversation': conversation.name, 'text': message_text}, user=frappe.session.user)


@frappe.whitelist()
def send_message(conversation_name, message_text):
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
        new_message.parenttype = 'Messenger Conversation'
        new_message.parentfield = 'messages'
        new_message.content = message_text
        new_message.direction = 'Outbound'
        new_message.sender = 'Me'
        new_message.timestamp = frappe.utils.now_datetime()
        new_message.insert(ignore_permissions=True)

        conversation.last_message_time = frappe.utils.now_datetime()
        conversation.save(ignore_permissions=True)

        frappe.publish_realtime('messenger_message', data={'conversation': conversation.name, 'text': message_text}, user=frappe.session.user)
    else:
        frappe.throw(f"Failed to send message: {response.text}")
