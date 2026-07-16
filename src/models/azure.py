from src.models.openai import _SoraModel


class AzureModel(_SoraModel):
    PROVIDER = "azure"
