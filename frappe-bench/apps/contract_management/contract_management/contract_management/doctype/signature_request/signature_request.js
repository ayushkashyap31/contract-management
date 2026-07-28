// Copyright (c) 2026, Ayush Kumar Kashyap and contributors
// For license information, please see license.txt

frappe.ui.form.on("Signature Request", {
    refresh(frm) {
        if (
            !frm.is_new() &&
            frm.doc.status === "Draft" &&
            !frm.doc.envelope_id
        ) {
            frm.add_custom_button(__("Send for Signature"), () => {
                frappe.confirm(
                    __("Are you sure you want to send this signature request?"),
                    () => {
                        frm.call({
                            method: "send_for_signature",
                            doc: frm.doc,
                            freeze: true,
                            freeze_message: __("Sending for signature..."),
                            callback() {
                                frappe.show_alert({
                                    message: __("Signature request sent"),
                                    indicator: "green",
                                });

                                frm.reload_doc();
                            },
                        });
                    }
                );
            });
        }
    },
});