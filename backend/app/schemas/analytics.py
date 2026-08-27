from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    total_contacts: int
    active_contacts: int
    unsubscribed_contacts: int
    bounced_contacts: int
    total_campaigns: int
    active_campaigns: int
    draft_campaigns: int
    paused_campaigns: int
    completed_campaigns: int
    total_templates: int
    total_sent: int
    total_queued: int
    total_processing: int
    total_failed: int
    total_bounced: int
