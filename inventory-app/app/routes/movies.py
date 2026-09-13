import uuid

from flask import Blueprint, jsonify, request

from app.models import Movie


def is_non_empty_string(value) -> bool:
    return isinstance(value, str) and value.strip() != ""


def parse_movie_id(movie_id: str):
    try:
        return uuid.UUID(movie_id)
    except (TypeError, ValueError, AttributeError):
        return None


def create_movies_blueprint(session_factory) -> Blueprint:
    movies_blueprint = Blueprint("movies", __name__)

    @movies_blueprint.get("")
    def find_all():
        title = request.args.get("title", "").strip()
        with session_factory() as session:
            query = session.query(Movie)
            if title:
                query = query.filter(Movie.title.ilike(f"%{title}%"))
            movies = query.order_by(Movie.title.asc()).all()
            return jsonify([movie.to_dict() for movie in movies]), 200

    @movies_blueprint.post("")
    def create():
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify({"error": "Request body must be a JSON object"}), 400

        title = body.get("title")
        description = body.get("description")

        if not is_non_empty_string(title) or not is_non_empty_string(description):
            return jsonify(
                {"error": "title and description must be non-empty strings"}
            ), 400

        with session_factory() as session:
            movie = Movie(title=title.strip(), description=description.strip())
            session.add(movie)
            session.commit()
            session.refresh(movie)
            return jsonify(movie.to_dict()), 200

    @movies_blueprint.delete("")
    def delete_all():
        with session_factory() as session:
            deleted = session.query(Movie).delete()
            session.commit()
            return jsonify({"message": "All movies were deleted", "deleted": deleted}), 200

    @movies_blueprint.get("/<movie_id>")
    def find_one(movie_id):
        parsed_id = parse_movie_id(movie_id)
        if parsed_id is None:
            return jsonify({"error": "Movie not found"}), 404

        with session_factory() as session:
            movie = session.get(Movie, parsed_id)
            if movie is None:
                return jsonify({"error": "Movie not found"}), 404
            return jsonify(movie.to_dict()), 200

    @movies_blueprint.put("/<movie_id>")
    def update(movie_id):
        parsed_id = parse_movie_id(movie_id)
        if parsed_id is None:
            return jsonify({"error": "Movie not found"}), 404

        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify({"error": "Request body must be a JSON object"}), 400

        has_title = "title" in body
        has_description = "description" in body

        if not has_title and not has_description:
            return jsonify(
                {"error": "At least one of title or description is required"}
            ), 400

        if (has_title and not is_non_empty_string(body.get("title"))) or (
            has_description and not is_non_empty_string(body.get("description"))
        ):
            return jsonify(
                {"error": "title and description must be non-empty strings"}
            ), 400

        with session_factory() as session:
            movie = session.get(Movie, parsed_id)
            if movie is None:
                return jsonify({"error": "Movie not found"}), 404

            if has_title:
                movie.title = body["title"].strip()
            if has_description:
                movie.description = body["description"].strip()

            session.commit()
            session.refresh(movie)
            return jsonify(movie.to_dict()), 200

    @movies_blueprint.delete("/<movie_id>")
    def delete_one(movie_id):
        parsed_id = parse_movie_id(movie_id)
        if parsed_id is None:
            return jsonify({"error": "Movie not found"}), 404

        with session_factory() as session:
            movie = session.get(Movie, parsed_id)
            if movie is None:
                return jsonify({"error": "Movie not found"}), 404
            session.delete(movie)
            session.commit()
            return jsonify({"message": "Movie was deleted"}), 200

    return movies_blueprint
