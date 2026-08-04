frappe.ui.form.on("Contract Version", {
    refresh(frm) {
        if (frm.states) {
            frm.states.show_actions = () => {};
        }
        frm.set_df_property("status", "read_only", 1);

        if (frm.doc.status === "Draft") {
            frm.add_custom_button(__("Submit for Review"), () => {
                frm.call("submit_for_review").then((r) => {
                    frappe.show_alert({
                        message: __("Submitted for review"),
                        indicator: "green",
                    });
                    frm.refresh();
                });
            });
        }
    },
});