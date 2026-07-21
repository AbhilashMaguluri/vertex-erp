from typing import Dict, Optional


class FeatureFlagService:
    def __init__(self):
        # Default flags as defined in PRD §30
        self._flags: Dict[str, bool] = {
            "ai_assistant": False,
            "parent_portal": False,
            "sms_notifications": False,
            "whatsapp_notifications": False,
            "advanced_analytics": True,
            "document_management": True,
            "report_generation": True,
            "digital_signatures": False,
            "bulk_operations": True,
            "attendance_correction": True,
            "custom_forms": False,
            "experimental_features": False,
        }

    async def is_enabled(self, flag_key: str, user_role: Optional[str] = None) -> bool:
        return self._flags.get(flag_key, False)

    def set_flag(self, flag_key: str, enabled: bool):
        self._flags[flag_key] = enabled

    def get_all_flags(self) -> Dict[str, bool]:
        return dict(self._flags)


feature_flag_service = FeatureFlagService()
