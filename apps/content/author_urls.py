"""URL routing for author endpoints.
"""
from django.urls import path
from apps.content.author_views import (
    search_tags,
    create_tag,
    search_genres,
    create_genre,
    search_languages,
    create_language,
)

urlpatterns = [
    # Tags
    path('tags/search/', search_tags, name='search_tags'),
    path('tags/create/', create_tag, name='create_tag'),
    
    # Genres
    path('genres/search/', search_genres, name='search_genres'),
    path('genres/create/', create_genre, name='create_genre'),
    
    # Languages
    path('languages/search/', search_languages, name='search_languages'),
    path('languages/create/', create_language, name='create_language'),
]
