from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.parse import quote

import httpx

from app.config import settings


@dataclass
class Employee:
    adp_number: str
    full_name: str
    branch: str
    department: str
    active: bool


class GraphClient:
    def __init__(self) -> None:
        self._token: str | None = None

    async def _get_token(self) -> str:
        if self._token:
            return self._token
        if not settings.client_secret:
            raise RuntimeError('CLIENT_SECRET not configured. Set CLIENT_SECRET env var to call Microsoft Graph.')

        token_url = f'https://login.microsoftonline.com/{settings.tenant_id}/oauth2/v2.0/token'
        data = {
            'client_id': settings.client_id,
            'client_secret': settings.client_secret,
            'scope': settings.graph_scope,
            'grant_type': 'client_credentials',
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            self._token = response.json()['access_token']
            return self._token

    async def get(self, url: str, params: dict | None = None) -> dict:
        token = await self._get_token()
        headers = {'Authorization': f'Bearer {token}'}
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()


class SharePointService:
    def __init__(self, graph_client: GraphClient | None = None) -> None:
        self.graph = graph_client or GraphClient()

    async def _site_id(self, site_path: str) -> str:
        url = f'https://graph.microsoft.com/v1.0/sites/{settings.qms_site_hostname}:{site_path}'
        data = await self.graph.get(url)
        return data['id']

    async def _list_items(self, site_id: str, list_name: str) -> list[dict]:
        encoded = quote(list_name)
        url = f'https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{encoded}/items'
        data = await self.graph.get(url, params={'$expand': 'fields'})
        return data.get('value', [])

    async def get_eligible_employees(self) -> list[Employee]:
        site_id = await self._site_id(settings.qms_site_path)
        rows = await self._list_items(site_id, 'Employees')
        employees: list[Employee] = []

        for row in rows:
            fields = row.get('fields', {})
            branch = str(fields.get('Branch', '')).strip()
            department = str(fields.get('Department', '')).strip()
            active = str(fields.get('Active', '')).lower() in {'yes', 'true', '1'}
            if active and branch == 'Ennis' and department in {'Quality', 'Tubular'}:
                employees.append(
                    Employee(
                        adp_number=str(fields.get('ADPNumber', '')).strip(),
                        full_name=str(fields.get('Title', '')).strip(),
                        branch=branch,
                        department=department,
                        active=active,
                    )
                )
        return employees

    async def get_work_orders(self) -> list[dict]:
        site_id = await self._site_id(settings.acumatica_site_path)
        return await self._list_items(site_id, 'Production Operations')

    @staticmethod
    def _parse_limits(raw_limits: object) -> dict:
        if isinstance(raw_limits, dict):
            return raw_limits
        if isinstance(raw_limits, str) and raw_limits.strip():
            try:
                parsed = json.loads(raw_limits)
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}
        return {}

    async def get_inspection_recipe(self, connection_name: str) -> dict:
        site_id = await self._site_id(settings.qms_site_path)
        rows = await self._list_items(site_id, 'InspectionRecipes')
        for row in rows:
            fields = row.get('fields', {})
            if str(fields.get('Title', '')).strip() == connection_name:
                fields['limits'] = self._parse_limits(fields.get('limits'))
                return fields
        raise ValueError(f'No recipe found for connection {connection_name}')
