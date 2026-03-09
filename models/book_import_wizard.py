from odoo import fields, models, api
from odoo.exceptions import UserError
from datetime import datetime


def parse_open_library_date(date_str):
    """Parse Open Library date strings like '15 March 1947' to a Date object"""
    if not date_str:
        return None
    for fmt in ('%d %B %Y', '%B %d, %Y', '%Y'):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


class LibraryBookImportWizard(models.TransientModel):
    _name = 'library.book.import.wizard'
    _description = 'Import Books from Open Library'

    title_query = fields.Char(string='Title')
    author_query = fields.Char(string='Author')
    search_type = fields.Selection([
        ('title', 'By Title'),
        ('author', 'By Author'),
        ('both', 'By Title and Author'),
    ], default='title', required=True, string='Search By')

    result_ids = fields.One2many(
        'library.book.import.result',
        'wizard_id',
        string='Results'
    )

    def action_search(self):
        """Trigger API search based on search_type"""
        title = self.title_query if self.search_type in ('title', 'both') else None
        author = self.author_query if self.search_type in ('author', 'both') else None

        if not title and not author:
            raise UserError('Please fill in the required search field(s).')

        results = self.env['library.api.service'].search_books(
            title_query=title,
            author_query=author,
        )

        # Clear previous results
        self.result_ids.unlink()

        self.result_ids = [(0, 0, {
            'wizard_id': self.id,
            'title': r['title'],
            'display_author': r['display_author'],
            'author_names': ','.join(r['author_names']),   # store as comma-separated string
            'isbn': r['isbn'],
            'first_publish_year': r['first_publish_year'],
            'selected': False,
        }) for r in results]

        # Reopen wizard to show results
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Books to Import',
            'res_model': 'library.book.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('library_management.library_book_import_wizard_view_results').id,
            'target': 'new',
        }

    def action_back_to_search(self):
        """Go back to the search view"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Import from Open Library',
            'res_model': 'library.book.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('library_management.library_book_import_wizard_view_search').id,
            'target': 'new',
        }

    def action_import_selected(self):
        """Import selected books, resolving authors against local DB or API"""
        selected = self.result_ids.filtered(lambda r: r.selected)

        if not selected:
            raise UserError('Please select at least one book to import.')

        AuthorModel = self.env['library.author']
        BookModel = self.env['library.book']
        ApiService = self.env['library.api.service']
        imported = 0

        for result in selected:
            # Skip duplicates
            if result.isbn and BookModel.search([('isbn', '=', result.isbn)], limit=1):
                continue

            # Resolve author — check all author_names against local DB
            author_names = [n.strip() for n in result.author_names.split(',') if n.strip()]
            matched_author = None

            for name in author_names:
                matched_author = AuthorModel.search([('name', '=', name)], limit=1)
                if matched_author:
                    break

            # No local match — fetch from API using first author name
            if not matched_author and author_names:
                primary_name = author_names[0]
                author_data = ApiService.search_author(primary_name)

                author_vals = {'name': primary_name}
                if author_data:
                    author_vals['birthdate'] = parse_open_library_date(author_data.get('birth_date'))

                matched_author = AuthorModel.create(author_vals)

            # Create the book
            BookModel.create({
                'name': result.title,
                'author_id': matched_author.id if matched_author else False,
                'isbn': result.isbn,
                'published_year': result.first_publish_year or 0,
                'copies_available': 1,
                'is_available': True,
            })
            imported += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Import Complete',
                'message': f'{imported} book(s) imported successfully.',
                'type': 'success',
            }
        }


class LibraryBookImportResult(models.TransientModel):
    _name = 'library.book.import.result'
    _description = 'Book Import Search Result'

    wizard_id = fields.Many2one('library.book.import.wizard', ondelete='cascade')
    selected = fields.Boolean(default=False)
    title = fields.Char()
    display_author = fields.Char(string='Author')       # only first author, for display
    author_names = fields.Char()                         # full comma-separated list, for import logic
    isbn = fields.Char(string='ISBN')
    first_publish_year = fields.Integer(string='Year')