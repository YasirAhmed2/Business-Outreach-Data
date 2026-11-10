"""
Free Local Phone Verification Engine for Pakistan Numbers (+92).
Normalizes Pakistani landline, mobile, UAN, and toll-free numbers using google phonenumbers library.
"""

import phonenumbers
from phonenumbers import PhoneNumberType, PhoneNumberFormat
from typing import Dict, Any, Tuple, Optional
import logging
from .quality_scoring import QualityScorer

logger = logging.getLogger("PhoneVerification")


class PhoneVerifier:
    """Normalizes and validates Pakistani telephone numbers."""

    @staticmethod
    def verify_and_normalize_phone(
        raw_phone: str,
        default_region: str = "PK",
        from_official_page: bool = True
    ) -> Dict[str, Any]:
        """
        Validates phone number format against Pakistan national numbering plan (+92).
        Formats to E.164 (+92...) and National formats.
        """
        if not raw_phone:
            return {
                "phone": None,
                "normalized_phone": None,
                "is_valid": False,
                "phone_type": "Unavailable",
                "verification_status": "Unavailable",
                "confidence_score": 0.0,
                "reason": "No phone number provided"
            }

        clean_raw = raw_phone.strip()

        # Handle UAN numbers (e.g. 111-123-456)
        if clean_raw.startswith("111") or " 111 " in clean_raw:
            digits = "".join(c for c in clean_raw if c.isdigit())
            if len(digits) >= 9:
                return {
                    "phone": clean_raw,
                    "normalized_phone": f"UAN: {digits[:3]}-{digits[3:6]}-{digits[6:9]}",
                    "is_valid": True,
                    "phone_type": "Business Mobile / UAN",
                    "verification_status": "Valid PK Phone",
                    "confidence_score": 75.0,
                    "reason": "Recognized Pakistani Universal Access Number (UAN)"
                }

        try:
            parsed = phonenumbers.parse(clean_raw, default_region)
            is_valid = phonenumbers.is_valid_number(parsed)
            is_pk = (parsed.country_code == 92)

            if not is_valid or not is_pk:
                return {
                    "phone": clean_raw,
                    "normalized_phone": clean_raw,
                    "is_valid": False,
                    "phone_type": "Unavailable",
                    "verification_status": "Invalid Format",
                    "confidence_score": 0.0,
                    "reason": "Invalid Pakistani phone number or unrecognized prefix"
                }

            num_type = phonenumbers.number_type(parsed)
            is_fixed = (num_type == PhoneNumberType.FIXED_LINE or num_type == PhoneNumberType.FIXED_LINE_OR_MOBILE)
            is_mobile = (num_type == PhoneNumberType.MOBILE)

            formatted_intl = phonenumbers.format_number(parsed, PhoneNumberFormat.INTERNATIONAL)
            formatted_national = phonenumbers.format_number(parsed, PhoneNumberFormat.NATIONAL)

            score, phone_type, status, reason = QualityScorer.score_phone_confidence(
                is_valid_pk_phone=True,
                is_landline=is_fixed,
                is_mobile_or_uan=is_mobile,
                from_official_contact_page=from_official_page
            )

            return {
                "phone": formatted_national,
                "normalized_phone": formatted_intl,
                "is_valid": True,
                "phone_type": phone_type,
                "verification_status": status,
                "confidence_score": score,
                "reason": reason
            }

        except phonenumbers.NumberParseException as e:
            return {
                "phone": clean_raw,
                "normalized_phone": clean_raw,
                "is_valid": False,
                "phone_type": "Unavailable",
                "verification_status": "Invalid Format",
                "confidence_score": 0.0,
                "reason": f"Phone parse exception: {str(e)}"
            }
