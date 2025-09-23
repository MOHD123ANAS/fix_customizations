import frappe
from collections import defaultdict

@frappe.whitelist()
def get_item_details():
    try:
        # URL filters
        filters = {}
        if frappe.form_dict.get("item_code"):
            filters["name"] = frappe.form_dict.get("item_code")
        if frappe.form_dict.get("brand"):
            filters["brand"] = frappe.form_dict.get("brand")
        if frappe.form_dict.get("item_group"):
            filters["item_group"] = frappe.form_dict.get("item_group")

        filters["custom_is_this_a_website_item"] = 1

        # Fetch items
        items = frappe.get_all(
            "Item",
            filters=filters,
            fields=[
                "name as item_code",
                "item_name",
                "brand",
                "item_group",
                "description",
                "stock_uom",
                "custom_min_qty",
                "disabled",
                "custom_is_this_a_website_item"
            ]
        )

        if not items:
            return {"status": "success", "data": []}

        item_codes = [x["item_code"] for x in items]

        # Product Details
        prod_details = frappe.get_all(
            "Product Details",
            filters={"parent": ["in", item_codes]},
            fields=["parent", "parameter", "value", "category"]
        )

        # Group product details by category
        prod_map = {}
        for pd in prod_details:
            parent = pd["parent"]
            prod_map.setdefault(parent, defaultdict(list))
            prod_map[parent][pd.get("category", "Other")].append({
                "parameter": pd.get("parameter"),
                "value": pd.get("value")
            })

        # Attachments
        attachments = frappe.get_all(
            "File",
            filters={"attached_to_doctype": "Item", "attached_to_name": ["in", item_codes]},
            fields=["attached_to_name", "file_url", "file_name", "is_private"]
        )
        attachment_map = {}
        for att in attachments:
            attachment_map.setdefault(att["attached_to_name"], []).append(att)

        # Merge product details and attachments
        for row in items:
            row["product_details"] = prod_map.get(row["item_code"], {})
            row["attachments"] = attachment_map.get(row["item_code"], [])

        return {"status": "success", "data": items}

    except Exception as e:
        frappe.log_error(f"Error in get_item_details: {str(e)}", "Custom API Error")
        return {"status": "error", "error": str(e)}
