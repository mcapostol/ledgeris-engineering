from __future__ import annotations

from decimal import Decimal
import unittest

from ledgeris_source_excerpt import format_romanian_number


class RomanianNumberExcerptTests(unittest.TestCase):
    def test_formats_decimal_with_romanian_separators(self):
        self.assertEqual(
            format_romanian_number(Decimal("1234567.89")),
            "1.234.567,89",
        )

    def test_accepts_romanian_formatted_input(self):
        self.assertEqual(format_romanian_number("1.234,5"), "1.234,50")

    def test_accepts_parenthesized_negative_input(self):
        self.assertEqual(format_romanian_number("(1234,5)"), "-1.234,50")

    def test_avoids_binary_float_expansion(self):
        self.assertEqual(format_romanian_number(0.1), "0,10")

    def test_rejects_non_numeric_input(self):
        with self.assertRaisesRegex(ValueError, "Valoare numerică invalidă"):
            format_romanian_number("not-a-number")


if __name__ == "__main__":
    unittest.main()
