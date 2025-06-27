from flask import Flask, render_template, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

# Configuração da API do TMDB
TMDB_API_KEY = '25c1c9e872aa78a8f573381f3918fd8a'  # Substitua pela sua chave da API
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/w500'


class TMDBService:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = TMDB_BASE_URL

    def _make_request(self, endpoint, params=None):
        """Faz requisição para a API do TMDB"""
        if params is None:
            params = {}
        params['api_key'] = self.api_key
        params['language'] = 'pt-BR'

        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição: {e}")
            return None

    def get_popular_movies(self, page=1):
        """Busca filmes populares"""
        return self._make_request('/movie/popular', {'page': page})

    def search_movies(self, query, page=1):
        """Busca filmes por termo"""
        return self._make_request('/search/movie', {'query': query, 'page': page})

    def get_movie_details(self, movie_id):
        """Busca detalhes de um filme específico"""
        return self._make_request(f'/movie/{movie_id}')

    def get_movie_credits(self, movie_id):
        """Busca elenco e equipe de um filme"""
        return self._make_request(f'/movie/{movie_id}/credits')

    def get_trending_movies(self, time_window='week'):
        """Busca filmes em alta (day ou week)"""
        return self._make_request(f'/trending/movie/{time_window}')

    def get_genres(self):
        """Busca lista de gêneros"""
        return self._make_request('/genre/movie/list')


# Instância do serviço TMDB
tmdb = TMDBService(TMDB_API_KEY)


@app.route('/')
def index():
    """Página inicial com filmes populares"""
    popular_movies = tmdb.get_popular_movies()
    trending_movies = tmdb.get_trending_movies()

    return render_template('index.html',
                           popular_movies=popular_movies,
                           trending_movies=trending_movies,
                           image_base_url=TMDB_IMAGE_BASE_URL)


@app.route('/search')
def search():
    """Página de busca de filmes"""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    results = None
    if query:
        results = tmdb.search_movies(query, page)

    return render_template('search.html',
                           results=results,
                           query=query,
                           image_base_url=TMDB_IMAGE_BASE_URL)


@app.route('/movie/<int:movie_id>')
def movie_details(movie_id):
    """Página de detalhes do filme"""
    movie = tmdb.get_movie_details(movie_id)
    credits = tmdb.get_movie_credits(movie_id)

    if not movie:
        return render_template('404.html'), 404

    return render_template('movie_details.html',
                           movie=movie,
                           credits=credits,
                           image_base_url=TMDB_IMAGE_BASE_URL)


@app.route('/api/movies/popular')
def api_popular_movies():
    """API endpoint para filmes populares"""
    page = request.args.get('page', 1, type=int)
    movies = tmdb.get_popular_movies(page)
    return jsonify(movies)


@app.route('/api/search')
def api_search():
    """API endpoint para busca"""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400

    results = tmdb.search_movies(query, page)
    return jsonify(results)


@app.template_filter('format_date')
def format_date(date_string):
    """Filtro para formatar datas"""
    if not date_string:
        return 'Data não disponível'
    try:
        date = datetime.strptime(date_string, '%Y-%m-%d')
        return date.strftime('%d/%m/%Y')
    except ValueError:
        return date_string


@app.template_filter('format_runtime')
def format_runtime(minutes):
    """Filtro para formatar duração em horas e minutos"""
    if not minutes:
        return 'Duração não disponível'
    hours = minutes // 60
    mins = minutes % 60
    if hours:
        return f"{hours}h {mins}min"
    return f"{mins}min"


@app.template_filter('format_currency')
def format_currency(amount):
    """Filtro para formatar valores monetários"""
    if not amount:
        return 'Não informado'
    return f"${amount:,.0f}"


if __name__ == '__main__':
    app.run(debug=True)