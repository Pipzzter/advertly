"""
AI Agents for Ecommerce Landing Pages
=====================================

This package contains AI agents that automate marketing workflows
for creating, translating, optimizing, and compliance-checking landing pages.

Agents:
    - Agent 1: Copy & Image Injection (fills HTML templates with copy and images)
    - Agent 2: Translation & Localisation
    - Agent 3: Policy & Compliance
    - Agent 4: Funnel Optimization (CRO)
    - Agent 5: Product Research

Each agent is independent and operates as a standalone tool.
"""

from app.services.agents.base import BaseAgent
from app.services.agents.image_client import ImageType, OpenAIImageClient
from app.services.agents.llm_client import OpenAIClient, OpenAIResponse
from app.services.agents.copy_injection import (
    CopyInjectionAgent,
    CopyInjectionInput,
    CopyInjectionOutput,
    TemplateService,
    TemplateSummary,
)

__all__ = [
    "BaseAgent",
    "OpenAIClient",
    "OpenAIResponse",
    "OpenAIImageClient",
    "ImageType",
    "CopyInjectionAgent",
    "CopyInjectionInput",
    "CopyInjectionOutput",
    "TemplateService",
    "TemplateSummary",
]

