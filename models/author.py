from odoo import fields, models

class Property(models.Model):
    _name = "library.author"
    _description = "A book author"

    name = fields.Char(required=True, string="Name")
    birthdate = fields.Date()
    biography = fields.Text()
    book_ids = fields.One2many("library.book", "author_id", string="Books Written")# book_ids = One2many to library.book
