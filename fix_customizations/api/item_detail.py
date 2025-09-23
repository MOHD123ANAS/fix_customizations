import frappe

@frappe.whitelist()
def get_item_details():
    debug_logs = []
    try:
        debug_logs.append("Step 1: API called successfully.")

        debug_logs.append("Step 2: Running SQL query...")
        data = frappe.db.sql("""
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
                i.item_group,
                itd.context AS tech_context,
                itd.value   AS tech_value,
                pd.context  AS prod_context,
                pd.value    AS prod_value
            FROM
                `tabItem Price` ip
            INNER JOIN
                `tabItem` i ON ip.item_code = i.name
            LEFT JOIN
                `tabTechnical Details` itd ON itd.parent = i.name
            LEFT JOIN
                `tabProduct Details` pd ON pd.parent = i.name
            WHERE
                ip.price_list = 'Standard Selling'
                AND IFNULL(i.custom_is_this_a_website_item, 0) = 1
        """, as_dict=1)

        debug_logs.append(f"Step 3: Query executed. Records fetched = {len(data)}")

        # Fetch all attachments in one go
        attachments = frappe.get_all(
            "File",
            filters={"attached_to_doctype": "Item"},
            fields=["attached_to_name", "file_url", "file_name", "is_private"]
        )
        attachment_map = {}
        for att in attachments:
            attachment_map.setdefault(att["attached_to_name"], []).append(att)

        # Merge attachments into result
        for row in data:
            row["attachments"] = attachment_map.get(row["item_code"], [])

        debug_logs.append("Step 4: Response prepared successfully.")

        return {"status": "success", "data": data}

    except Exception as e:
        frappe.log_error(f"Error in get_website_items_with_price: {str(e)}", "Custom API Error")
        debug_logs.append(f"Step X: Error occurred -> {str(e)}")
        return {"status": "error", "error": str(e)}

    finally:
        frappe.log_error("\n".join(debug_logs), "DEBUG LOGS - get_website_items_with_price")
