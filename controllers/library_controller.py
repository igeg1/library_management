from odoo import http
from odoo.http import request


class LibraryController(http.Controller):

    @http.route('/library/search-books', type='json', auth='user', methods=['POST'])
    def search_books(self, title_query=None, author_query=None, limit=10, **kwargs):
        results = request.env['library.api.service'].search_books(
            title_query=title_query,
            author_query=author_query,
            limit=limit,
        )
        return {'results': results}

    @http.route('/library/import-books', type='json', auth='user', methods=['POST'])
    def import_books(self, books, **kwargs):
        """
        Accepts a list of book dicts (each with title, author_names, isbn,
        first_publish_year) and imports them, resolving authors along the way.
        """
        AuthorModel = request.env['library.author']
        BookModel = request.env['library.book']
        ApiService = request.env['library.api.service']
        imported = 0

        for book in books:
            # Skip duplicates
            isbn = book.get('isbn')
            if isbn and BookModel.search([('isbn', '=', isbn)], limit=1):
                continue

            # Resolve author against local DB first
            author_names = book.get('author_names', [])
            matched_author = None

            for name in author_names:
                matched_author = AuthorModel.search([('name', '=', name)], limit=1)
                if matched_author:
                    break

            # No local match — fetch from API
            if not matched_author and author_names:
                primary_name = author_names[0]
                author_data = ApiService.search_author(primary_name)

                author_vals = {'name': primary_name}
                if author_data:
                    from models.book_import_wizard import parse_open_library_date
                    author_vals['birthdate'] = parse_open_library_date(author_data.get('birth_date'))

                matched_author = AuthorModel.create(author_vals)

            BookModel.create({
                'name': book.get('title'),
                'author_id': matched_author.id if matched_author else False,
                'isbn': isbn,
                'published_year': book.get('first_publish_year') or 0,
                'copies_available': 1,
                'is_available': True,
            })
            imported += 1

        return {'imported': imported}