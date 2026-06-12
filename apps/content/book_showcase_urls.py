"""
URL routing for book showcase endpoints (featured, popular, recommended books).
"""
from django.urls import path
from apps.content.book_showcase_views import (
    get_featured_books,
    toggle_featured_book,
    get_popular_books,
    get_recommended_books,
    add_recommended_book,
)

urlpatterns = [
    # Featured Books
    path('featured/', get_featured_books, name='get_featured_books'),
    path('featured/toggle/', toggle_featured_book, name='toggle_featured_book'),
    
    # Popular Books
    path('popular/', get_popular_books, name='get_popular_books'),
    
    # Recommended Books
    path('recommended/', get_recommended_books, name='get_recommended_books'),
    path('recommended/add/', add_recommended_book, name='add_recommended_book'),
]
