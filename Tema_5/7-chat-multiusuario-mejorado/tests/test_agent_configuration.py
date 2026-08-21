"""Regresiones de configuración que no necesitan conectarse a OpenAI."""

import unittest

from openai import APIConnectionError, AuthenticationError

from agent.engine import (
    build_model_retry_middleware,
    is_legacy_retry_message,
    is_retryable_model_error,
)


class AgentConfigurationTests(unittest.TestCase):
    def test_exhausted_retries_raise_instead_of_becoming_ai_message(self) -> None:
        middleware = build_model_retry_middleware()

        self.assertEqual(middleware.max_retries, 2)
        self.assertEqual(middleware.on_failure, "error")

    def test_only_transient_errors_are_retried(self) -> None:
        # Las excepciones solo necesitan un objeto request para construirse; no
        # realizan ninguna conexión durante esta prueba.
        import httpx

        request = httpx.Request("POST", "https://api.openai.com/v1/responses")
        connection_error = APIConnectionError(request=request)
        authentication_error = AuthenticationError(
            "Clave no válida",
            response=httpx.Response(401, request=request),
            body=None,
        )

        self.assertTrue(is_retryable_model_error(connection_error))
        self.assertFalse(is_retryable_model_error(authentication_error))

    def test_only_internal_retry_output_is_recognized_for_cleanup(self) -> None:
        self.assertTrue(
            is_legacy_retry_message(
                "Model call failed after 3 attempts with APIConnectionError"
            )
        )
        self.assertFalse(
            is_legacy_retry_message("No pude completar la consulta solicitada.")
        )


if __name__ == "__main__":
    unittest.main()
