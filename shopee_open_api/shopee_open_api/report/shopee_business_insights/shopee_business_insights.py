# Copyright (c) 2013, Dap Official and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    # frappe.msgprint("<pre>{}</pre>".format(filters))

    default_filters = {
        "date_start": None,
        "date_end": None,
        "order_status": None,
    }

    default_filters.update(filters)

    if default_filters.get("date_start") and default_filters.get("date_end"):
        if default_filters["date_end"] < default_filters["date_start"]:
            frappe.throw("The end date cannot be earlier than the start date")

    sales_data = frappe.db.sql(
        """
        SELECT
            DATE(shopee_order.create_time) AS date_order,
            COUNT(shopee_order.name) AS number_of_orders,
            SUM(shopee_order.total_amount) AS total_revenue
        FROM
            `tabShopee Order` AS shopee_order
        WHERE
            (%(date_start)s IS NULL OR DATE(shopee_order.create_time) >= %(date_start)s) AND
            (%(date_end)s IS NULL OR DATE(shopee_order.create_time) <= %(date_end)s) AND
            (%(order_status)s IS NULL OR shopee_order.order_status = %(order_status)s) AND
            shopee_order.order_status != 'CANCELLED'
        GROUP BY
            DATE(shopee_order.create_time)
        """,
        values=default_filters,
    )

    top_products_data = frappe.db.sql(
        """
        SELECT 
            product.item_name AS item_name,
            SUM(order_item.qty) AS qty,
            SUM(order_item.qty * order_item.model_discounted_price) AS total_revenue
        FROM
            `tabShopee Order Item` AS order_item INNER JOIN
            `tabShopee Product` AS product ON order_item.shopee_product = product.name INNER JOIN
            `tabShopee Order` AS shopee_order ON shopee_order.name = order_item.parent
        WHERE
            (%(date_start)s IS NULL OR DATE(shopee_order.create_time) >= %(date_start)s) AND
            (%(date_end)s IS NULL OR DATE(shopee_order.create_time) <= %(date_end)s) AND
            (%(order_status)s IS NULL OR shopee_order.order_status = %(order_status)s) AND
            shopee_order.order_status != 'CANCELLED'
        GROUP BY
            product.item_name
        ORDER BY
            total_revenue DESC
        """,
        values=default_filters,
    )

    columns = [
        {"fieldname": "item_name", "label": "Item Name", "fieldtype": "Data"},
        {"fieldname": "qty", "label": "QTY", "fieldtype": "Int"},
        {"fieldname": "total_venue", "label": "Total Revenue", "fieldtype": "Currency"},
    ]

    data = top_products_data

    total_revenue = sum([row[2] for row in sales_data])
    number_of_orders = sum([row[1] for row in sales_data])

    average_order_value_result = frappe.db.sql(
        """
        SELECT AVG(total_amount) AS average_order_value FROM `tabShopee Order`
        WHERE
            (%(date_start)s IS NULL OR DATE(create_time) >= %(date_start)s) AND
            (%(date_end)s IS NULL OR DATE(create_time) <= %(date_end)s) AND
            (%(order_status)s IS NULL OR order_status = %(order_status)s) AND
            order_status != 'CANCELLED'
        """,
        values=default_filters,
        as_dict=True,
    )
    average_order_value = (
        0
        if not average_order_value_result
        else average_order_value_result[0].get("average_order_value")
    )

    report_summary = [
        {
            "label": "Total Revenue",
            "value": f"{frappe.db.get_default('Currency')} {total_revenue:,}",
        },
        {"label": "No. of Orders", "value": f"{number_of_orders:,}"},
        {
            "label": "Avg. Order Value",
            "value": f"{frappe.db.get_default('Currency')} {average_order_value:,.2f}",
        },
    ]

    return columns, data, None, None, report_summary
