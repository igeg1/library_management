import requests
from odoo import models
from odoo.exceptions import UserError


class LibraryApiService(models.AbstractModel):
    _name = 'library.api.service'
    _description = 'Library External API Service'

    def search_books(self, title_query=None, author_query=None, limit=10):
        """Search Open Library by title, author, or both"""
        if not title_query and not author_query:
            raise UserError('Please provide at least a title or author to search.')

        if title_query and author_query:
            url = f"https://openlibrary.org/search.json?q=title:{title_query}&author={author_query}&fields=title,author_name,first_publish_year,isbn&limit={limit}"
        elif title_query:
            url = f"https://openlibrary.org/search.json?q=title:{title_query}&fields=title,author_name,first_publish_year,isbn&limit={limit}"
        else:
            url = f"https://openlibrary.org/search.json?author={author_query}&fields=title,author_name,first_publish_year,isbn&limit={limit}"

        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            raise UserError('Failed to reach Open Library API.')

        results = []
        for doc in response.json().get('docs', [])[:limit]:
            author_names = doc.get('author_name', [])
            isbn_list = doc.get('isbn', [])
            results.append({
                'title': doc.get('title', 'Unknown'),
                'display_author': author_names[0] if author_names else 'Unknown',
                'author_names': author_names,        # full list, stored in wizard
                'isbn': isbn_list[0] if isbn_list else None,
                'first_publish_year': doc.get('first_publish_year'),
            })

        return results

    def search_author(self, author_name):
        """Search Open Library for author details, returns first result with a valid birthdate"""
        url = f"https://openlibrary.org/search/authors.json?q={author_name}&fields=key,birth_date,death_date&limit=10"

        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return None

        for author in response.json().get('docs', []):
            birth_date = author.get('birth_date')
            if birth_date:
                return {
                    'birth_date': birth_date,
                    'death_date': author.get('death_date'),
                }

        # Exhausted all results with no valid birthdate
        return None