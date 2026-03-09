from odoo import fields, models, api

class Property(models.Model):
    _name = "library.book"
    _description = "A library book"

    name = fields.Char(required=True, string="Title")
    isbn = fields.Char(string="ISBN")
    description = fields.Text()
    author_id = fields.Many2one("library.author", string="Author") # author_id = Many2one to library.author
    copies_available = fields.Integer()
    price = fields.Float()
    is_available = fields.Boolean()
    genre = fields.Selection(
        selection=[
                    ('fiction', 'Fiction'),
                    ('non_fiction', 'Non-Fiction'),
                    ('mystery', 'Mystery'),
                    ('science_fiction', 'Science Fiction'),
                    ('fantasy', 'Fantasy'),
                    ('biography', 'Biography'),
                    ('self_help', 'Self-Help'),
                    ('thriller', 'Thriller'),
                ]
    )
    published_year = fields.Integer(string="Published Year")
    loan_ids = fields.One2many("library.loan", "book_id", string="Loans")
    # optional - tags = Many2many to a tag model
    tag_ids = fields.Many2many("library.tag", string="Tags")

    loan_count = fields.Integer(compute='_compute_loan_count')

    @api.depends('loan_ids')
    def _compute_loan_count(self):
        for record in self:
            record.loan_count = len(record.loan_ids)

    def action_view_loans(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Loans',
            'res_model': 'library.loan',
            'view_mode': 'list,form',
            'domain': [('book_id', '=', self.id)],
        }

