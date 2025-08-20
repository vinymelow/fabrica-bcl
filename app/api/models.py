# fabrica-bcl/app/api/models.py

from pydantic import BaseModel

class CampaignDetails(BaseModel):
    """Define a estrutura dos detalhes da campanha vindos do frontend."""
    campaignName: str
    objective: str
    assistantPersona: str
    toneOfVoice: str
    offer: str
    customerProfile: str

class ProvisionRequest(BaseModel):
    """Define a estrutura completa do pedido de provisionamento."""
    campaign_id: str
    user_email: str
    campaign_details: CampaignDetails