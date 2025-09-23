import frappe

@frappe.whitelist()
def get_item_details():
    try:
        # Step 1: Fetch main item + price
        items = frappe.db.sql("""
            SELECT DISTINCT
                ip.item_code,
                i.item_name,
                ip.price_list,
                ip.price_list_rate,
                i.custom_is_this_a_website_item,
                i.disabled,
                i.description,
                i.stock_uom,
                i.brand,
                i.custom_min_qty,
                i.item_group
            FROM
                `tabItem Price` ip
            INNER JOIN
                `tabItem` i ON ip.item_code = i.name
            WHERE
                ip.price_list = 'Standard Selling'
                AND IFNULL(i.custom_is_this_a_website_item, 0) = 1
        """, as_dict=1)

        if not items:
            return {"status": "success", "data": []}

        item_codes = [x["item_code"] for x in items]

        # Step 2: Fetch technical details
        tech_details = frappe.get_all(
            "Technical Details",
            filters={"parent": ["in", item_codes]},
            fields=["parent", "context", "value"]
        )

        tech_map = {}
        for td in tech_details:
            tech_map.setdefault(td["parent"], []).append({
                "context": td["context"],
                "value": td["value"]
            })

        # Step 3: Fetch product details
        prod_details = frappe.get_all(
            "Product Details",
            filters={"parent": ["in", item_codes]},
            fields=["parent", "context", "value"]
        )

        prod_map = {}
        for pd in prod_details:
            prod_map.setdefault(pd["parent"], []).append({
                "context": pd["context"],
                "value": pd["value"]
            })

        # Step 4: Fetch attachments
        attachments = frappe.get_all(
            "File",
            filters={"attached_to_doctype": "Item", "attached_to_name": ["in", item_codes]},
            fields=["attached_to_name", "file_url", "file_name", "is_private"]
        )
        attachment_map = {}
        for att in attachments:
            attachment_map.setdefault(att["attached_to_name"], []).append(att)

        # Step 5: Merge everything
        for row in items:
            row["technical_details"] = tech_map.get(row["item_code"], [])
            row["product_details"] = prod_map.get(row["item_code"], [])
            row["attachments"] = attachment_map.get(row["item_code"], [])

        return {"status": "success", "data": items}

    except Exception as e:
        frappe.log_error(f"Error in get_item_details: {str(e)}", "Custom API Error")
        return {"status": "error", "error": str(e)}