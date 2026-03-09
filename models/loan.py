from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import timedelta


class Property(models.Model):
    _name = "library.loan"
    _description = "A library loan"

    name = fields.Char(compute='_compute_name')
    # book_id = Many2one to library.book
    book_id = fields.Many2one("library.book", string="Book")
    borrower_name = fields.Char()
    borrow_date = fields.Date(required=True, default=fields.Date.today())
    return_date = fields.Date()
    is_returned = fields.Boolean(compute='_compute_is_returned', store=True)
    late_return = fields.Boolean(compute='_compute_late_return') # computed field (based on return date)


    @api.depends('return_date')
    def _compute_is_returned(self):
        for record in self:
            record.is_returned = bool(record.return_date)

    @api.depends('borrow_date', 'return_date')
    def _compute_late_return(self):
        for record in self:
            if record.borrow_date and record.return_date:
                allowed_date = record.borrow_date + timedelta(days=14)
                record.late_return = record.return_date > allowed_date
            else:
                record.late_return = False
    
    @api.depends('book_id', 'borrower_name')
    def _compute_name(self):
        for record in self:
            book = record.book_id.name or ''
            borrower = record.borrower_name or ''
            if book or borrower:
                record.name = f"{book} - {borrower}"
            else:
                record.name = "New Loan"

    @api.onchange('book_id')
    def _onchange_book_id(self):
        if self.book_id:
            return {
                'warning': {
                    'title': 'Available Copies',
                    'message': f'This book has {self.book_id.copies_available} copies available.'
                }
            }
    
    @api.constrains('borrow_date', 'return_date')
    def _check_dates(self):
        for record in self:
            if record.borrow_date and record.return_date:
                if record.return_date < record.borrow_date:
                    raise ValidationError("Return date must be after borrow date.")