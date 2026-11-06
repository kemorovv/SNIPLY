"""
Automated Tests for Privacy Guard:
- Sensitive content filtering (private keys, API keys, JWTs, password labels)
- Excluded foreground process matching
"""

import unittest

from core.privacy import PrivacyGuard


class TestPrivacyGuard(unittest.TestCase):
    def test_sensitive_content_filtering(self) -> None:
        sensitive_samples = [
            "-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXktdjEAAAAABG5vbmU=",
            "sk-proj-1234567890abcdefghijklmnopQRSTUV",
            "ghp_1234567890abcdefghijklmnopQRSTUVWX",
            "AKIAIOSFODNN7EXAMPLE",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U",
            "password = MySuperSecretPassword123!",
        ]
        for sample in sensitive_samples:
            is_sens, rule = PrivacyGuard.inspect_sensitive_text(sample)
            self.assertTrue(is_sens, f"Expected sample to be flagged as sensitive: {sample[:25]}")
            self.assertIsNotNone(rule)

        # Ordinary code or sentences mentioning the word password in prose should NOT be blocked
        safe_samples = [
            "Please reset your password on the settings page.",
            "#A78BFA",
            "https://github.com/kemorovv/SNIPLY",
            "def validate_user_input(name: str) -> bool:\n    return len(name) > 2",
        ]
        for safe in safe_samples:
            is_sens, _ = PrivacyGuard.inspect_sensitive_text(safe)
            self.assertFalse(is_sens, f"Expected safe text not to be blocked: {safe}")

    def test_excluded_application_matching(self) -> None:
        exclusions = ["KeePassXC.exe", "1Password.exe", "Bitwarden.exe"]
        self.assertTrue(
            PrivacyGuard.is_process_excluded(exclusions, active_executable="keepassxc.exe")
        )
        self.assertTrue(
            PrivacyGuard.is_process_excluded(exclusions, active_executable="1Password")
        )
        self.assertFalse(
            PrivacyGuard.is_process_excluded(exclusions, active_executable="Code.exe")
        )


if __name__ == "__main__":
    unittest.main()
