# Copyright (c) 2021, Dap Official and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class ShopeeProductDimension(Document):
	def get_wlh(self):
		'''get weihght x lenght x height'''
		return "{0} x {1} x {2}".format(self.package_width, self.package_length ,self.package_height)

