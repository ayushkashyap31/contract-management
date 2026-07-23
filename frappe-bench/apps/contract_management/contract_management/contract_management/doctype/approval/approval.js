frappe.ui.form.on("Approval", {
    refresh(frm) {
        // Status should only change via workflow actions
        frm.set_df_property("status", "read_only", 1);

        if (frm.is_new()) {
            return;
        }

        if (frm.doc.status === "Pending") {
            frm.add_custom_button(__("Approve"), () => {
                frappe.confirm(
                    __("Are you sure you want to approve this approval?"),
                    () => {
                        frm.call("approve").then(() => {
                            frappe.show_alert({
                                message: __("Approved"),
                                indicator: "green",
                            });

                            frm.reload_doc();
                        });
                    }
                );
            });

            frm.add_custom_button(__("Reject"), () => {
                frappe.confirm(
                    __("Are you sure you want to reject this approval?"),
                    () => {
                        frm.call("reject").then(() => {
                            frappe.show_alert({
                                message: __("Rejected"),
                                indicator: "red",
                            });

                            frm.reload_doc();
                        });
                    }
                );
            });
        }
    },
});