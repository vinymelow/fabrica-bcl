# Ficheiro: app/api/models.py
from pydantic import BaseModel, Field

class CampaignConfiguration(BaseModel):
    client_name: str = Field(..., description="Nome do cliente final, ex: CaveLusa")
    client_email: str = Field(..., description="Email do cliente para notificações")
    campaign_goal: str = Field(..., description="Objetivo principal da campanha")
    brand_tone: str = Field(..., description="Tom de voz da marca")
    sender_persona: str = Field(..., description="Persona que envia a mensagem")
    lead_source_type: str = Field(..., description="Tipo de fonte de leads, ex: webhook, meta")
    
