import unittest
import uuid
from unittest.mock import MagicMock

from app import create_app
from app.routes.movies import is_non_empty_string, parse_movie_id


class IsNonEmptyStringTests(unittest.TestCase):
    def test_accepts_non_empty_strings(self):
        self.assertTrue(is_non_empty_string("Inception"))

    def test_rejects_blank_or_non_string_values(self):
        invalid_values = ("", "   ", None, 42, [])

        for value in invalid_values:
            with self.subTest(value=value):
                self.assertFalse(is_non_empty_string(value))


class ParseMovieIdTests(unittest.TestCase):
    def test_parses_a_valid_uuid(self):
        movie_id = uuid.uuid4()
        self.assertEqual(parse_movie_id(str(movie_id)), movie_id)

    def test_rejects_a_malformed_id(self):
        self.assertIsNone(parse_movie_id("not-a-uuid"))

    def test_rejects_a_non_string_id(self):
        self.assertIsNone(parse_movie_id(None))


class MovieRequestValidationTests(unittest.TestCase):
    def setUp(self):
        self.session_factory = MagicMock()
        self.client = create_app(self.session_factory).test_client()

    def test_create_rejects_json_that_is_not_an_object(self):
        response = self.client.post(
            "/api/movies",
            json=[{"title": "Not an object payload"}],
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(),
            {"error": "Request body must be a JSON object"},
        )
        self.session_factory.assert_not_called()

    def test_update_rejects_json_that_is_not_an_object(self):
        response = self.client.put(f"/api/movies/{uuid.uuid4()}", json="title")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(),
            {"error": "Request body must be a JSON object"},
        )
        self.session_factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
