from . import __version__ as app_version

app_name = "shopee_open_api"
app_title = "Shopee Open API"
app_publisher = "Dap Official"
app_description = "Connect to your Shopee Open API and manage your multi-branch shops from your erpnext"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "siwatjames@gmail.com"
app_license = "MIT"
required_apps = ["erpnext"]
# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/shopee_open_api/css/shopee_open_api.css"

# << include customize doctype js to desk>>
# app_include_js = "/assets/shopee_open_api/js/branch_modification.js"

# include js, css files in header of web template
# web_include_css = "/assets/shopee_open_api/css/shopee_open_api.css"
# web_include_js = "/assets/shopee_open_api/js/shopee_open_api.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "shopee_open_api/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"branch" : "public/js/branch_modification.js"}
doctype_list_js = {"Branch": "public/js/branch_modification.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Fixture
# ------------
fixtures = [
    "Shopee Logistic Status",
    "Shopee Order Status",
    "Shopee Return Status",
    "Shopee Cancel Reason",
    "Role Profile",
    {"dt": "Accounting Dimension", "filters": [["name", "=", "Shopee Shop"]]},
    "Customer Group",
    {"dt": "User", "filters": [["first_name", "=", "Shopee"]]},
    {"dt": "Sales Partner", "filters": [["name", "=", "Shopee"]]},
    {"dt": "Notification Settings", "filters": [["name", "=", "shopee@example.com"]]},
]

# Installation
# ------------

# before_install = "shopee_open_api.install.before_install"
# after_install = "shopee_open_api.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "shopee_open_api.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
    "Item Price": "shopee_open_api.overrides.item_price.CustomItemPrice"
}

# Document Events
# ---------------
# Hook on document methods and events

# << custom tricker event in form for doctype (overide/extend)>>
doc_events = {
    # "*": {
    #     "on_update": "shopee_open_api.controllers.test.on_all_events",
    #     "after_insert": "shopee_open_api.controllers.test.on_all_events",
    # },
    "Shopee Shop": {
        "before_save": "shopee_open_api.controllers.shopee_shop.update_profile",
    },
}
# << Events for running tasks periodically in the background >>
# Scheduled Tasks
# ---------------

scheduler_events = {
    "cron": {
        "0 */4 * * *": [
            "shopee_open_api.scheduled_tasks.tasks.update_products",
            "shopee_open_api.scheduled_tasks.tasks.process_order_queue",
        ]
    },
    # "all": [
    # 	"shopee_open_api.tasks.all"
    # ],
    "daily": [
        "shopee_open_api.scheduled_tasks.tasks.update_wallet_transactions",
    ],
    # "hourly": [
    # 	"shopee_open_api.tasks.hourly"
    # ],
    # "weekly": [
    # 	"shopee_open_api.tasks.weekly"
    # ]
    # "monthly": [
    # 	"shopee_open_api.tasks.monthly"
    # ],
}

# Testing
# -------

before_tests = "erpnext.setup.utils.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "shopee_open_api.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "shopee_open_api.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
    {
        "doctype": "{doctype_1}",
        "filter_by": "{filter_by}",
        "redact_fields": ["{field_1}", "{field_2}"],
        "partial": 1,
    },
    {
        "doctype": "{doctype_2}",
        "filter_by": "{filter_by}",
        "partial": 1,
    },
    {
        "doctype": "{doctype_3}",
        "strict": False,
    },
    {"doctype": "{doctype_4}"},
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"shopee_open_api.auth.validate"
# ]
