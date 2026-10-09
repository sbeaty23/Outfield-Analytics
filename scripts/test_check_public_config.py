import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import check_public_config
from check_public_config import violations


class PublicConfigurationTest(unittest.TestCase):
    def test_public_configuration_is_safe(self) -> None:
        self.assertEqual(violations(), [])

    def test_values_are_allowed_but_credentials_and_published_database_are_rejected(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "frontend").mkdir()
            (root / ".env.example").write_text(
                "API_INTERNAL_URL=https://internal.test\n"
                "MIGRATION_DATABASE_URL=postgresql://published\n"
            )
            (root / "frontend" / ".env.example").write_text(
                "NEXT_PUBLIC_API_URL=https://public.test\n"
            )
            (root / "docker-compose.yml").write_text(
                "  db:\n    ports:\n  backend:\n    env_file: .env\n"
            )
            with patch.object(check_public_config, "ROOT", root):
                errors = violations()
            self.assertFalse(any("API_INTERNAL_URL" in error for error in errors))
            self.assertFalse(any("NEXT_PUBLIC_API_URL" in error for error in errors))
            self.assertTrue(any("MIGRATION_DATABASE_URL" in error for error in errors))
            self.assertIn("PostgreSQL must not publish host ports", errors)
            self.assertIn(
                "Compose services must receive only explicitly listed settings", errors
            )
