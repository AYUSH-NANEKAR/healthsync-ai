"""
HealthSync AI - AI Service

Provides health analysis through a provider-independent interface.

Current implementation:
    Local rule-based analysis.

Future implementations can use:
    - Local AI model
    - HealthSync AI custom API
    - Other provider

Important:
    - No paid API
    - No API key required
    - No hardcoded patient identity
    - Uses supplied health data
    - This is an informational analysis layer,
      not a medical diagnosis system.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


# ============================================================
# AI PROVIDER INTERFACE
# ============================================================

class AIProvider(ABC):
    """
    Common interface for all HealthSync AI providers.
    """

    @abstractmethod
    def analyze(
        self,
        health_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Analyze supplied health data.
        """
        raise NotImplementedError


# ============================================================
# LOCAL RULE-BASED PROVIDER
# ============================================================

class LocalHealthAIProvider(AIProvider):
    """
    Free local health-analysis provider.

    It uses simple rules and does not require an
    internet connection or API key.
    """

    def analyze(
        self,
        health_data: dict[str, Any],
    ) -> dict[str, Any]:

        observations: list[str] = []
        warnings: list[str] = []
        recommendations: list[str] = []

        heart_rate = health_data.get(
            "heart_rate"
        )

        spo2 = health_data.get(
            "spo2"
        )

        temperature = health_data.get(
            "temperature"
        )

        systolic = health_data.get(
            "systolic_pressure"
        )

        diastolic = health_data.get(
            "diastolic_pressure"
        )

        steps = health_data.get(
            "steps"
        )

        movement = health_data.get(
            "movement"
        )

        # ----------------------------------------------------
        # HEART RATE
        # ----------------------------------------------------

        if heart_rate is not None:

            heart_rate = float(
                heart_rate
            )

            if heart_rate < 50:

                warnings.append(
                    "Heart rate is below the "
                    "configured reference range."
                )

            elif heart_rate > 100:

                warnings.append(
                    "Heart rate is above the "
                    "configured reference range."
                )

            else:

                observations.append(
                    "Heart rate is within the "
                    "configured reference range."
                )

        # ----------------------------------------------------
        # SPO2
        # ----------------------------------------------------

        if spo2 is not None:

            spo2 = float(spo2)

            if spo2 < 90:

                warnings.append(
                    "SpO₂ is significantly below "
                    "the configured reference level."
                )

            elif spo2 < 95:

                warnings.append(
                    "SpO₂ is below the configured "
                    "reference level."
                )

            else:

                observations.append(
                    "SpO₂ is within the configured "
                    "reference range."
                )

        # ----------------------------------------------------
        # TEMPERATURE
        # ----------------------------------------------------

        if temperature is not None:

            temperature = float(
                temperature
            )

            if temperature >= 38.0:

                warnings.append(
                    "Temperature is elevated "
                    "above the configured threshold."
                )

            elif temperature < 35.0:

                warnings.append(
                    "Temperature is below the "
                    "configured reference range."
                )

            else:

                observations.append(
                    "Temperature is within the "
                    "configured reference range."
                )

        # ----------------------------------------------------
        # BLOOD PRESSURE
        # ----------------------------------------------------

        if (
            systolic is not None
            and diastolic is not None
        ):

            systolic = float(
                systolic
            )

            diastolic = float(
                diastolic
            )

            if (
                systolic >= 180
                or diastolic >= 120
            ):

                warnings.append(
                    "Blood pressure reading is "
                    "very high and should be "
                    "reviewed promptly."
                )

            elif (
                systolic >= 140
                or diastolic >= 90
            ):

                warnings.append(
                    "Blood pressure is above "
                    "the configured reference range."
                )

            else:

                observations.append(
                    "Blood pressure is within "
                    "the configured reference range."
                )

        # ----------------------------------------------------
        # ACTIVITY
        # ----------------------------------------------------

        if steps is not None:

            steps = int(
                steps
            )

            if steps == 0:

                observations.append(
                    "No steps have been recorded "
                    "for this reading."
                )

            elif steps > 0:

                observations.append(
                    f"{steps} steps are recorded "
                    "in the supplied activity data."
                )

        if movement:

            observations.append(
                f"Current movement status: {movement}."
            )

        # ----------------------------------------------------
        # RECOMMENDATIONS
        # ----------------------------------------------------

        if warnings:

            recommendations.append(
                "Review the flagged readings "
                "and monitor subsequent measurements."
            )

        if steps is not None and steps == 0:

            recommendations.append(
                "Consider regular movement and "
                "activity when appropriate."
            )

        if not recommendations:

            recommendations.append(
                "Continue monitoring your health "
                "data regularly."
            )

        # ----------------------------------------------------
        # OVERALL STATUS
        # ----------------------------------------------------

        if warnings:

            status = "Attention"

        elif observations:

            status = "Normal"

        else:

            status = "Insufficient Data"

        return {
            "status": status,
            "observations": observations,
            "warnings": warnings,
            "recommendations": recommendations,
            "provider": "LocalHealthAI",
            "is_diagnostic": False,
        }


# ============================================================
# FUTURE HEALTHSYNC AI API PROVIDER
# ============================================================

class HealthSyncAIAPIProvider(AIProvider):
    """
    Future provider for a HealthSync AI backend.

    Not implemented yet.

    Future architecture:

        HealthSync Desktop
                |
                v
        HealthSync AI API
                |
                v
          AI inference

    The AIService interface will remain unchanged.
    """

    def __init__(
        self,
        base_url: str,
    ):
        self.base_url = base_url.rstrip("/")

    def analyze(
        self,
        health_data: dict[str, Any],
    ) -> dict[str, Any]:

        raise NotImplementedError(
            "HealthSync AI API provider "
            "is not implemented yet."
        )


# ============================================================
# AI SERVICE
# ============================================================

class AIService:
    """
    Main AI service used by HealthSync AI.

    Application/UI code should communicate with this class
    instead of directly communicating with an AI provider.
    """

    def __init__(
        self,
        provider: Optional[AIProvider] = None,
    ):

        if provider is None:

            self.provider = (
                LocalHealthAIProvider()
            )

        else:

            self.provider = provider

    def set_provider(
        self,
        provider: AIProvider,
    ) -> None:
        """
        Replace the active AI provider.
        """

        if not isinstance(
            provider,
            AIProvider,
        ):

            raise TypeError(
                "Provider must implement AIProvider."
            )

        self.provider = provider

    def analyze(
        self,
        health_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Analyze supplied health data.
        """

        if not isinstance(
            health_data,
            dict,
        ):

            raise TypeError(
                "health_data must be a dictionary."
            )

        return self.provider.analyze(
            health_data
        )

    def analyze_vitals(
        self,
        heart_rate: Optional[float] = None,
        spo2: Optional[float] = None,
        temperature: Optional[float] = None,
        systolic_pressure: Optional[float] = None,
        diastolic_pressure: Optional[float] = None,
        steps: Optional[int] = None,
        movement: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Convenience method for analyzing wearable vitals.
        """

        health_data = {
            "heart_rate": heart_rate,
            "spo2": spo2,
            "temperature": temperature,
            "systolic_pressure": systolic_pressure,
            "diastolic_pressure": diastolic_pressure,
            "steps": steps,
            "movement": movement,
        }

        return self.analyze(
            health_data
        )


# ============================================================
# DEFAULT SERVICE INSTANCE
# ============================================================

ai_service = AIService()


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "AIProvider",
    "LocalHealthAIProvider",
    "HealthSyncAIAPIProvider",
    "AIService",
    "ai_service",
]