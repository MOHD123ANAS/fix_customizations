# Copyright (c) 2025, Winspire Tech PVT LTD and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Parameters(Document):
	def autoname(self):
		self.name=self.parameter_label
