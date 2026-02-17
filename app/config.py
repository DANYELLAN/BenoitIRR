from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Benoit IRR Backend'
    environment: str = Field(default='dev', validation_alias=AliasChoices('ENVIRONMENT', 'environment'))
    database_url: str = Field(
        default='postgresql+psycopg://postgres:B3n01tI4I9@localhost:8084/benoitirr',
        validation_alias=AliasChoices('DATABASE_URL', 'database_url'),
    )

    # Azure AD / Microsoft Graph
    tenant_id: str = Field(
        default='519943e3-a90d-49f1-a2a4-dd32f586c05f',
        validation_alias=AliasChoices('TENANT_ID', 'tenant_id'),
    )
    client_id: str = Field(
        default='5520a688-ca19-493f-9050-f5c356fbeaff',
        validation_alias=AliasChoices('CLIENT_ID', 'client_id'),
    )
    client_secret: str = Field(default='', validation_alias=AliasChoices('CLIENT_SECRET', 'client_secret'))
    graph_scope: str = Field(
        default='https://graph.microsoft.com/.default',
        validation_alias=AliasChoices('GRAPH_SCOPE', 'graph_scope'),
    )

    qms_site_hostname: str = Field(
        default='benoitinc.sharepoint.com',
        validation_alias=AliasChoices('QMS_SITE_HOSTNAME', 'qms_site_hostname'),
    )
    qms_site_path: str = Field(default='/sites/QMS1061', validation_alias=AliasChoices('QMS_SITE_PATH', 'qms_site_path'))
    acumatica_site_path: str = Field(
        default='/sites/AcumaticaDataStorage',
        validation_alias=AliasChoices('ACUMATICA_SITE_PATH', 'acumatica_site_path'),
    )


settings = Settings()
