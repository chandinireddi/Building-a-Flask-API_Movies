import requests
from flask import Flask, request, jsonify
from functools import wraps

app = Flask(__name__)

# API key configuration
API_KEY = 'd9ecee123ee7252dcb0edde02390a84d'

def require_api_key(view_func):
    @wraps(view_func)
    def decorated_func(*args, **kwargs):
        provided_key = request.headers.get('X-API-Key')

        if not provided_key or provided_key != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401

        return view_func(*args, **kwargs)

    return decorated_func

@app.route('/movies/<movie_name>', methods=['GET'])
@require_api_key
def get_movie_details(movie_name):
    # Make a request to the TMDb API to search for the movie
    api_url = f'https://api.themoviedb.org/3/search/movie'
    params = {'api_key': API_KEY, 'query': movie_name}
    response = requests.get(api_url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        # Extract the movie details from the response
        data = response.json()

        # Check if any movie matches the search query
        if data['total_results'] > 0:
            # Get the first movie from the search results
            movie = data['results'][0]

            # Extract the relevant details from the movie
            movie_id = movie['id']
            cast_api_url = f'https://api.themoviedb.org/3/movie/{movie_id}/credits'
            cast_params = {'api_key': API_KEY}
            cast_response = requests.get(cast_api_url, params=cast_params)
            cast_data = cast_response.json()
            cast = [actor['name'] for actor in cast_data['cast']]

            movie_details = {
                'title': movie['title'],
                'release_year': movie['release_date'][:4],
                'plot': movie['overview'],
                'cast': cast,
                'rating': movie['vote_average']
            }

            return jsonify(movie_details)

    # If no movie found or there was an error, return an error message
    return jsonify({'error': 'Movie not found'}), 404

@app.route('/movies', methods=['GET'])
@require_api_key
def get_movie_list():
    # Get query parameters from the request
    year = request.args.get('year')
    genre = request.args.get('genre')
    rating = request.args.get('rating')

    # Build the query parameters for the API request
    query_params = {
        'api_key': API_KEY,
        'year': year,
        'with_genres': genre,
        'vote_average.gte': rating
    }

    # Make a request to the TMDb API to retrieve the movie list
    api_url = 'https://api.themoviedb.org/3/discover/movie'
    response = requests.get(api_url, params=query_params)

    # Check if the request was successful
    if response.status_code == 200:
        # Extract the movie list from the response
        data = response.json()

        # Extract the relevant details from each movie
        movie_list = []
        for movie in data.get('results', []):
            # Fetch cast details for each movie
            cast_api_url = f'https://api.themoviedb.org/3/movie/{movie["id"]}/credits'
            cast_params = {'api_key': API_KEY}
            cast_response = requests.get(cast_api_url, params=cast_params)
            cast_data = cast_response.json()
            cast = [actor['name'] for actor in cast_data['cast']]

            # Check if the release_date key exists in the movie data
            release_year = movie.get('release_date', '')[:4]

            movie_details = {
                'title': movie['title'],
                'release_year': release_year,
                'plot': movie['overview'],
                'cast': cast,
                'rating': movie['vote_average']
            }
            movie_list.append(movie_details)

        return jsonify(movie_list)

    # If there was an error, return an error message
    return jsonify({'error': 'Failed to retrieve movie list'}), 500

if __name__ == '__main__':
    app.run(debug=True)
