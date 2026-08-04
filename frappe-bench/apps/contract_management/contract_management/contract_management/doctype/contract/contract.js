// Copyright (c) 2026, Ayush Kumar Kashyap and contributors
// For license information, please see license.txt

frappe.ui.form.on("Contract", {
    refresh(frm) {
        if (frm.doc.docstatus !== 1) {
            return;
        }

        frm.page.set_primary_action(__("Create Version"), () => {
            frm.call("create_version").then((r) => {
                frappe.new_doc("Contract Version", r.message);
            });
        });
    },
});