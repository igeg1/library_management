from odoo import fields, models

class Property(models.Model):
    _name = "library.tag"
    _description = "A library book tag"

    name = fields.Char(required=True, string="Tag")
    book_ids = fields.Many2many("library.book", string="Books")

