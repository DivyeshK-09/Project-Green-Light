"""
rule_engine.py

Generates the recommendation for a processed image.

Design note:
This module exposes a single entry point, `get_recommendation()`.
Everything else (main.py, frontend) only ever calls that function
and never touches the class underneath. That means the day a real
model exists, you swap PlaceholderRuleEngine -> AIRuleEngine below
and nothing else in the codebase needs to change.

Current implementation: deployment environment and recommendation
rules are not yet finalized by the client, so every image returns
the same placeholder output.

Future implementation: AI model inference (image, and later video/
text, in -> context-aware recommendation out), likely keyed off a
deployment profile (hospital / school / factory / etc.).
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseRuleEngine(ABC):
    @abstractmethod
    def evaluate(
        self,
        image_path: str,
        brightness: float,
        blur: float,
        camera_id: Optional[str] = None,
        location: Optional[str] = None,
    ) -> str:
        """Returns the recommendation string for a processed image."""
        raise NotImplementedError


class PlaceholderRuleEngine(BaseRuleEngine):
    """
    Current, intentional placeholder.

    Every image returns the same output because recommendation logic
    is deployment-specific and the deployment environment has not yet
    been finalized by the client. Brightness/blur are still recorded
    so they're available as features once real rules or a trained
    model exist.
    """

    PLACEHOLDER_OUTPUT = "Improvement Requested"

    def evaluate(
        self,
        image_path: str,
        brightness: float,
        blur: float,
        camera_id: Optional[str] = None,
        location: Optional[str] = None,
    ) -> str:
        return self.PLACEHOLDER_OUTPUT


# ---------------------------------------------------------------------------
# Future seam (not active). Example of what will replace the placeholder
# once a trained model and deployment-specific labels exist:
#
# class AIRuleEngine(BaseRuleEngine):
#     def __init__(self, model_path: str, deployment_profile: str):
#         self.model = load_model(model_path)
#         self.deployment_profile = deployment_profile
#
#     def evaluate(self, image_path, brightness, blur, camera_id=None, location=None):
#         return self.model.predict(image_path, profile=self.deployment_profile)
# ---------------------------------------------------------------------------


_active_engine: BaseRuleEngine = PlaceholderRuleEngine()


def get_active_engine() -> BaseRuleEngine:
    return _active_engine


def get_recommendation(
    image_path: str,
    brightness: float,
    blur: float,
    camera_id: Optional[str] = None,
    location: Optional[str] = None,
) -> str:
    return _active_engine.evaluate(image_path, brightness, blur, camera_id, location)
