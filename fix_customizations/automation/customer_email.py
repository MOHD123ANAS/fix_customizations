import frappe
from frappe.utils import formatdate, get_url, now_datetime


@frappe.whitelist()
def send_invoice_delivery_email(doc, method=None):
    """Send Swiggy-style email to customer after Sales Invoice is delivered"""
    try:
        
        if doc.workflow_state != "Delivered":
            return

        
        customer = frappe.get_doc("Customer", doc.customer)
        customer_name= customer.customer_name
        recipient = customer.custom_email
        if not recipient:
            frappe.log_error(f"No custom_email found for Customer {doc.customer}", "Delivery Email Skipped")
            return

        
        company_doc = frappe.get_doc("Company", doc.company)
        
        
        company_logo = ""
        if company_doc.logo_for_printing:
            logo_url = get_url(company_doc.logo_for_printing)
            company_logo = f"""
                <div style="text-align:center; margin: 20px 0;">
                    <img src="{logo_url}" alt="Company Logo" width="180" style="border-radius:8px;">
                </div>
            """


        
        pdf_data = frappe.attach_print(
            doctype="Sales Invoice",
            name=doc.name,
            print_format="GST Tax Invoice",
            print_letterhead=True
        )

        
        pdf_bytes = None
        if isinstance(pdf_data, dict):
            pdf_bytes = pdf_data.get("fcontent")
        elif isinstance(pdf_data, (bytes, bytearray)):
            pdf_bytes = pdf_data

        if not pdf_bytes:
            frappe.log_error(f"PDF content is empty for {doc.name} | attach_print output: {repr(pdf_data)}", "Delivery Email Error")
            return

        attachments = [{"fname": f"{doc.name}.pdf", "fcontent": pdf_bytes}]

        
        customer_address = doc.address_display or ""

        
        order_datetime = formatdate(doc.posting_date, "full")
        delivered_datetime = formatdate(doc.get("modified") or now_datetime(), "full")

        
        order_items_html = ""
        for item in doc.items:
            order_items_html += f"""
                <tr>
                    <td>{item.item_name}</td>
                    <td align="center">{item.qty}</td>
                    <td align="right">₹ {item.rate:.2f}</td>
                </tr>
            """


        email_html = f"""
        <div style="font-family:Arial, sans-serif; color:#333; background:#fafafa; padding:20px;">
            <div style="max-width:600px; margin:auto; background:#fff; border-radius:8px; padding:20px; box-shadow:0 2px 8px rgba(0,0,0,0.1);">

                <h2 style="text-align:center; color:#FC8019;">Fixlist</h2>
                <p style="text-align:center; font-size:16px;">Greetings from Fixlist!</p>
                <p style="text-align:center;">Your order was delivered successfully.<br></p>

                {company_logo}

                <hr style="border:none; border-top:1px solid #ddd; margin:20px 0;">

                <h3>Order Details</h3>
                <p>
                    <b>Invoice Number:</b> {doc.name}<br>
                    <b>Order placed at:</b> {order_datetime}<br>
                    <b>Order delivered at:</b> {delivered_datetime}<br>
                    <b>Status:</b> Delivered
                </p>

                <h3>Ordered from:</h3>
                <p>{doc.company}</p>

                <h3>Delivery To:</h3>
                <p>{customer_name}<br>{customer_address}</p>

                <h3>Your Order Summary:</h3>
                <table border="1" cellspacing="0" cellpadding="6" width="100%" style="border-collapse:collapse; font-size:14px;">
                    <tr style="background:#FC8019; color:white;">
                        <th align="left">Item Name</th>
                        <th>Qty</th>
                        <th align="right">Price</th>
                    </tr>
                    {order_items_html}
                    <tr><td colspan="2" align="right"><b>Item Total:</b></td><td align="right">₹ {doc.total:.2f}</td></tr>
                    <tr><td colspan="2" align="right"><b>Taxes:</b></td><td align="right">₹ {doc.total_taxes_and_charges:.2f}</td></tr>
                    <tr><td colspan="2" align="right"><b>Grand Total:</b></td><td align="right">₹ {doc.grand_total:.2f}</td></tr>
                </table>

                <p style="text-align:center; margin-top:30px; color:#888; font-size:12px;">
                    Thank you for ordering with Fixlist!
                </p>
            </div>
        </div>
        """

        
        frappe.sendmail(
            recipients=[recipient],
            subject=f"Your Order {doc.name} Delivered Successfully",
            message=email_html,
            attachments=attachments,
            reference_doctype=doc.doctype,
            reference_name=doc.name
        )

        frappe.logger().info(f"Delivery email sent to {recipient} for invoice {doc.name}")

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Sales Invoice Delivery Email Error")
