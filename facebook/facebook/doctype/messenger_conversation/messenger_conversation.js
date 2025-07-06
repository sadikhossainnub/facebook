frappe.ui.form.on('Messenger Conversation', {
    refresh: function(frm) {
        if (frm.doc.status === 'Open') {
            frm.add_custom_button(__('Send Reply'), function() {
                frappe.prompt({
                    fieldname: 'reply_text',
                    label: 'Your Reply',
                    fieldtype: 'Text',
                    reqd: 1
                }, function(values) {
                    frappe.call({
                        method: 'facebook.api.send_message',
                        args: {
                            conversation_name: frm.doc.name,
                            message_text: values.reply_text
                        },
                        callback: function(r) {
                            frm.reload_doc();
                        }
                    });
                });
            });
        }

        frappe.realtime.on('messenger_message', function(data) {
            if (data.conversation === frm.doc.name) {
                frm.reload_doc();
            }
        });
    }
});
