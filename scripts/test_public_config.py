import unittest

from check_public_config import violations


class PublicConfigTests(unittest.TestCase):
    def test_private_env_is_rejected_even_if_empty(self):
        self.assertTrue(violations("frontend/.env.local", ""))

    def test_example_connection_values_must_be_blank(self):
        self.assertTrue(violations(".env.example", "POSTGRES_USER=example"))
        self.assertFalse(
            violations(".env.example", "POSTGRES_USER=\nENVIRONMENT=development")
        )

    def test_literal_addresses_and_ports_are_rejected(self):
        address = ".".join(str(part) for part in [192, 0, 2, 1])
        for value in [
            address,
            "[" + ":" * 2 + "1]",
            "BACKEND_PORT=" + str(12345),
            "https://example.test:" + str(12345),
        ]:
            with self.subTest(value=value):
                self.assertTrue(violations("config.txt", value))

    def test_credentials_are_rejected_and_references_allowed(self):
        self.assertTrue(violations("config.txt", "POSTGRES_PASSWORD=" + "dummy"))
        self.assertTrue(violations("config.txt", "postgresql://user:" + "dummy@db/app"))
        self.assertFalse(
            violations(
                "config.txt", "POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Required}"
            )
        )
        self.assertFalse(violations("config.txt", "http://backend:${BACKEND_PORT}"))


if __name__ == "__main__":
    unittest.main()
